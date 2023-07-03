import logging

from const import API_URL
from utils import read_json, convert_response_to_json, do_api_get_all, do_api_post


def import_epersongroup(metadata_class,
                        group_id_dict,
                        statistics_dict):
    """
    Import data into database.
    Mapped tables: epersongroup
    """
    group_json_name = 'epersongroup.json'
    group_url = 'eperson/groups'
    imported = 0
    group_json_a = read_json(group_json_name)
    # group Administrator and Anonymous already exist
    # we need to remember their id
    try:
        response = do_api_get_all(group_url)
        existing_data_dict = convert_response_to_json(response)['_embedded']['groups']
    except Exception:
        logging.error('GET request ' + response.url + ' failed.')

    if existing_data_dict is not None:
        for existing_data in existing_data_dict:
            if existing_data['name'] == 'Anonymous':
                group_id_dict[0] = [existing_data['id']]
            elif existing_data['name'] == 'Administrator':
                group_id_dict[1] = [existing_data['id']]
            else:
                logging.error('Unrecognized eperson group ' + existing_data['name'])

    if not group_json_a:
        logging.info("Epersongroup JSON is empty.")
        return
    for group in group_json_a:
        id = group['eperson_group_id']
        # group Administrator and Anonymous already exist
        # group is created with dspace object too
        if id not in (0, 1) and id not in group_id_dict:
            # get group metadata
            metadatavalue_group_dict = \
                metadata_class.get_metadata_value(6, group['eperson_group_id'])
            if 'dc.title' not in metadatavalue_group_dict:
                logging.error('Metadata for group ' + str(id) +
                              ' does not contain title!')
                continue
            name = metadatavalue_group_dict['dc.title'][0]['value']
            del metadatavalue_group_dict['dc.title']
            # the group_metadata contains the name of the group
            json_p = {'name': name, 'metadata': metadatavalue_group_dict}
            try:
                response = do_api_post(group_url, None, json_p)
                group_id_dict[group['eperson_group_id']] = [
                    convert_response_to_json(response)['id']]
                imported += 1
            except Exception:
                logging.error('POST request ' + response.url + ' for id: ' +
                              str(group['eperson_group_id']) +
                              ' failed. Status: ' + str(response.status_code))
    if 'epersongroup' in statistics_dict:
        statistics_val = (len(group_json_a), statistics_dict['epersongroup'][1] +
                          imported)
        statistics_dict['epersongroup'] = statistics_val
    else:
        statistics_val = (len(group_json_a), imported)
        statistics_dict['epersongroup'] = statistics_val
    logging.info("Eperson group was successfully imported!")


def import_group2group(group_id_dict,
                       statistics_dict):
    """
    Import data into database.
    Mapped tables: group2group
    """
    group2group_json_name = 'group2group.json'
    group2group_url = 'clarin/eperson/groups/'
    imported = 0
    group2group_json_a = read_json(group2group_json_name)
    if not group2group_json_a:
        logging.info("Group2group JSON is empty.")
        return
    for group2group in group2group_json_a:
        parents_a = group_id_dict[group2group['parent_id']]
        childs_a = group_id_dict[group2group['child_id']]
        for parent in parents_a:
            for child in childs_a:
                try:
                    parent_url = group2group_url + parent + '/subgroups'
                    child_url = API_URL + 'eperson/groups/' + child
                    response = do_api_post(parent_url, None, child_url)
                    imported += 1
                except Exception as e:
                    # Sometimes the Exception `e` is type of `int`
                    if isinstance(e, int):
                        logging.error('POST request ' + group2group_url + parent +
                                      '/subgroups' + ' failed.')
                    else:
                        logging.error('POST request ' + response.url + ' for id: ' +
                                      str(parent) + ' failed. Status: ' +
                                      str(response.status_code))

    statistics_val = (len(group2group_json_a), imported)
    statistics_dict['group2group'] = statistics_val
    logging.info("Group2group was successfully imported!")
