import logging

from utils import read_json, convert_response_to_json, do_api_post


def import_collection(metadata_class,
                      handle_class,
                      group_id_dict,
                      community_id_dict,
                      collection_id_dict,
                      collection2logo_dict,
                      temp_item2group_dict,
                      statistics_dict):
    """
    Import data into database.
    Mapped tables: collection, community2collection, metadatavalue, handle
    """
    collection_json_name = 'collection.json'
    com2col_json_name = 'community2collection.json'
    group_json_name = 'epersongroup.json'
    collection_url = 'core/collections'
    imported_coll = 0
    imported_group = 0
    collection_json_list = read_json(collection_json_name)
    comm2coll_json_list = read_json(com2col_json_name)
    coll2comm_dict = {}

    if not comm2coll_json_list:
        logging.info("Community2collection JSON is empty.")
        return
    for comm2coll in comm2coll_json_list:
        coll2comm_dict[comm2coll['collection_id']] = comm2coll['community_id']

    # because the role DEFAULT_READ is without old group id in collection
    read_default_dict = {}
    group_json_list = read_json(group_json_name)
    default_read_str = '_DEFAULT_READ'
    for group in group_json_list:
        name = group['name']
        if default_read_str in name:
            positions = [ind for ind, ch in enumerate(name) if ch == '_']
            read_default_dict[name[positions[0] + 1: positions[1]]] = group['uuid']

    if not collection_json_list:
        logging.info("Collection JSON is empty.")
        return
    for collection in collection_json_list:
        # collection is part of default read
        collection_json_p = {}
        metadata_col_dict =\
            metadata_class.get_metadata_value(collection['uuid'])
        if metadata_col_dict:
            collection_json_p['metadata'] = metadata_col_dict
        handle_col = handle_class.get_handle(3, collection['uuid'])
        if handle_col:
            collection_json_p['handle'] = handle_col
        params = {
            'parent': community_id_dict[coll2comm_dict[collection['uuid']]]
        }
        try:
            response = do_api_post(collection_url, params, collection_json_p)
            coll_id = convert_response_to_json(response)['id']
            collection_id_dict[collection['uuid']] = coll_id
            imported_coll += 1
        except Exception as e:
            logging.error(
                'POST request ' + collection_url + ' for id: ' +
                str(collection['uuid']) + 'failed. Exception: ' + str(e))
            continue

        # add to collection2logo, if collection has logo
        if collection['logo_bitstream_id'] is not None:
            collection2logo_dict[collection['uuid']] = \
                collection["logo_bitstream_id"]

        # add template item exists, add it to dict
        if collection['template_item_id'] is not None:
            if collection['template_item_id'] in temp_item2group_dict:
                temp_item2group_dict[collection['template_item_id']].append(coll_id)
            else:
                temp_item2group_dict[collection['template_item_id']] = [coll_id]

        # greate groups
        if collection['workflow_step_1'] is not None:
            workflow_groups_url = collection_url + '/' + \
                coll_id + '/workflowGroups/reviewer'
            try:
                response = do_api_post(workflow_groups_url, {}, {})
                group_id_dict[collection['workflow_step_1']] = [
                    convert_response_to_json(response)['id']]
                imported_group += 1
            except Exception as e:
                logging.error('POST request ' + workflow_groups_url +
                              ' failed. Exception: ' + str(e))
        if collection['workflow_step_2'] is not None:
            workflow_groups_url = collection_url + '/' + \
                coll_id + '/workflowGroups/editor'
            try:
                response = do_api_post(workflow_groups_url, {}, {})
                group_id_dict[collection['workflow_step_2']] = [
                    convert_response_to_json(response)['id']]
                imported_group += 1
            except Exception as e:
                logging.error('POST request ' + workflow_groups_url +
                              ' failed. Exception: ' + str(e))

        if collection['workflow_step_3'] is not None:
            workflow_groups_url = collection_url + '/' + \
                coll_id + '/workflowGroups/finaleditor'
            try:
                response = do_api_post(workflow_groups_url, {}, {})
                group_id_dict[collection['workflow_step_3']] = [
                    convert_response_to_json(response)['id']]
                imported_group += 1
            except Exception as e:
                logging.error('POST request ' + workflow_groups_url +
                              ' failed. Exception: ' + str(e))
        if collection['submitter'] is not None:
            submitters_group_url = collection_url + '/' + \
                coll_id + '/submittersGroup'
            try:
                response = do_api_post(submitters_group_url, {}, {})
                group_id_dict[collection['submitter']] = \
                    [convert_response_to_json(response)['id']]
                imported_group += 1
            except Exception as e:
                logging.error('POST request ' + submitters_group_url +
                              ' failed. Exception: ' + str(e))
        if collection['admin'] is not None:
            admin_group_url = collection_url + '/' + \
                coll_id + '/adminGroup'
            try:
                response = do_api_post(admin_group_url, {}, {})
                group_id_dict[collection['admin']] = \
                    [convert_response_to_json(response)['id']]
                imported_group += 1
            except Exception as e:
                logging.error('POST request ' + admin_group_url +
                              ' failed. Exception: ' + str(e))

        bitstream_read_group_url = collection_url + '/' + \
            coll_id + '/bitstreamReadGroup'
        item_read_group_url = collection_url + '/' + \
            coll_id + '/itemReadGroup'
        if collection['collection_id'] in read_default_dict:
            create_default_read(bitstream_read_group_url, collection['collection_id'],
                                group_id_dict, read_default_dict, imported_group)
            create_default_read(item_read_group_url, collection['collection_id'],
                                group_id_dict, read_default_dict, imported_group)
        if collection['uuid'] in read_default_dict:
            create_default_read(bitstream_read_group_url, collection['uuid'],
                                group_id_dict, read_default_dict, imported_group)
            create_default_read(item_read_group_url, collection['uuid'],
                                group_id_dict, read_default_dict, imported_group)

    statistics_val = (len(collection_json_list), imported_coll)
    statistics_dict['collection'] = statistics_val
    statistics_val = (0, statistics_dict['epersongroup'][1] + imported_group)
    statistics_dict['epersongroup'] = statistics_val
    logging.info("Collection and Community2collection were successfully imported!")


def create_default_read(url, key, group_id_dict, read_default_dict, imported_group):
    try:
        response = do_api_post(url, {}, {})
        group_id_dict[read_default_dict[key]] = \
            [convert_response_to_json(response)['id']]
        imported_group += 1
    except Exception as e:
        logging.error('POST request ' + url +
                      ' failed. Exception: ' + str(e))
