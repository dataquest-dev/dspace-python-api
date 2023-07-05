import logging

from utils import read_json, convert_response_to_json, do_api_post


def import_community(metadata_class,
                     handle_class,
                     group_id_dict,
                     community_id_dict,
                     community2logo_dict,
                     statistics_dict):
    """
    Import data into database.
    Mapped tables: community, community2community, metadatavalue, handle
    """
    community_json_name = 'community.json'
    comm2comm_json_name = 'community2community.json'
    community_url = 'core/communities'
    imported_comm = 0
    imported_group = 0
    community_json_list = read_json(community_json_name)
    comm2comm_json_list = read_json(comm2comm_json_name)
    parent_dict = {}
    child_dict = {}
    if comm2comm_json_list is not None:
        for comm2comm in comm2comm_json_list:
            parent_id = comm2comm['parent_comm_id']
            child_id = comm2comm['child_comm_id']
            if parent_id in parent_dict.keys():
                parent_dict[parent_id].append(child_id)
            else:
                parent_dict[parent_id] = [child_id]
            if child_id in child_dict.keys():
                child_dict[child_id].append(parent_id)
            else:
                child_dict[child_id] = parent_id
        statistics_dict['community'] = (len(community_json_list), 0)
    if not community_json_list:
        logging.info("Community JSON is empty.")
        return
    counter = 0
    while community_json_list:
        community_json_p = {}
        # process community only when:
        # comm is not parent and child
        # comm is parent and not child
        # parent comm exists
        # else process it later
        community = community_json_list[counter]
        com_uuid = community['uuid']
        if (com_uuid not in parent_dict.keys() and
            com_uuid not in child_dict.keys()) or\
            com_uuid not in child_dict.keys() or \
                child_dict[com_uuid] in community_id_dict.keys():
            # resource_type_id for community is 4
            handle_comm = handle_class.get_handle(4, community['uuid'])
            if handle_comm:
                community_json_p['handle'] = handle_comm
            metadatavalue_comm_dict = \
                metadata_class.get_metadata_value(community['uuid'])
            if metadatavalue_comm_dict:
                community_json_p['metadata'] = metadatavalue_comm_dict
            # create community
            parent_id = None
            if com_uuid in child_dict:
                parent_id = {'parent': community_id_dict[child_dict[com_uuid]]}
            try:
                response = do_api_post(community_url, parent_id, community_json_p)
                response_comm_id = convert_response_to_json(response)['id']
                community_id_dict[community['uuid']] = response_comm_id
                imported_comm += 1
            except Exception as e:
                logging.error('POST request ' + community_url + ' for id: ' +
                              str(com_uuid) + ' failed. Exception: ' + str(e))
                continue

            # add to community2logo, if community has logo
            if community['logo_bitstream_id'] is not None:
                community2logo_dict[com_uuid] = community["logo_bitstream_id"]

            # create admingroup
            if community['admin'] is not None:
                admin_url = community_url + '/' + response_comm_id + '/adminGroup'
                try:
                    response = do_api_post(admin_url, {}, {})
                    group_id_dict[community['admin']] = [convert_response_to_json(
                        response)['id']]
                    imported_group += 1
                except Exception as e:
                    logging.error('POST request ' + admin_url +
                                  ' failed. Exception: ' + str(e))
            del community_json_list[counter]
        else:
            counter += 1
        if counter == len(community_json_list):
            counter = 0

    if 'community' in statistics_dict:
        statistics_val = (statistics_dict['community'][0], imported_comm)
        statistics_dict['community'] = statistics_val

    statistics_val = (0, imported_group)
    statistics_dict['epersongroup'] = statistics_val
    logging.info("Community and Community2Community were successfully imported!")
