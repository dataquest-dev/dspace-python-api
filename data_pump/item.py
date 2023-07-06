import logging

from data_pump.utils import read_json, convert_response_to_json, do_api_post, \
    save_dict_as_json
from support.dspace_proxy import rest_proxy
from const import API_URL


def import_item(metadata_class,
                handle_class,
                workflowitem_id_dict,
                item_id_dict,
                collection_id_dict,
                eperson_id_dict,
                temp_item2group_dict,
                statistics_dict,
                save_dict):
    """
    Import data into database.
    Mapped tables: item, collection2item, workspaceitem, cwf_workflowitem,
    metadata, handle
    """
    item_json_name = "item.json"
    workspaceitem_json_name = "workspaceitem.json"
    saved_workspace_json_name = "workspaceitem_dict.json"
    workflowitem_json_name = 'workflowitem.json'
    saved_workflow_json_name = "workflow_dict.json"
    item_url = 'clarin/import/item'
    saved_item_json_name = "item_dict.json"
    workflowitem_url = 'clarin/import/workflowitem'
    imported_workspaceitem = 0
    imported_workflowitem = 0
    imported_item = 0
    workspaceitem_id_dict = {}
    # create dict from items by item id
    item_json_list = read_json(item_json_name)
    items_dict = {}
    if not item_json_list:
        logging.info("Item JSON is empty.")
        return
    for item in item_json_list:
        items_dict[item['uuid']] = item
    statistics_dict['item'] = (len(item_json_list), 0)

    # create item and workspaceitem
    workspaceitem_json_list = read_json(workspaceitem_json_name)
    if workspaceitem_json_list is not None:
        for workspaceitem in workspaceitem_json_list:
            item = items_dict[workspaceitem['item_id']]
            import_workspaceitem(item, workspaceitem['collection_id'],
                                 workspaceitem['multiple_titles'],
                                 workspaceitem['published_before'],
                                 workspaceitem['multiple_files'],
                                 workspaceitem['stage_reached'],
                                 workspaceitem['page_reached'],
                                 metadata_class,
                                 handle_class,
                                 workspaceitem_id_dict,
                                 item_id_dict,
                                 collection_id_dict,
                                 temp_item2group_dict,
                                 eperson_id_dict)
            imported_workspaceitem += 1
            del items_dict[workspaceitem['item_id']]

        statistics_dict['workspaceitem'] = (len(workspaceitem_json_list),
                                            imported_workspaceitem)
        imported_item += imported_workspaceitem
        # save workspaceitem dict as json
        if save_dict:
            save_dict_as_json(saved_workspace_json_name, workspaceitem_id_dict)
        logging.info("Workspaceitem was successfully imported!")
    else:
        logging.info("Workspaceitem JSON is empty.")
    # create workflowitem
    # workflowitem is created from workspaceitem
    # -1, because the workflowitem doesn't contain this attribute
    workflowitem_json_list = read_json(workflowitem_json_name)
    if workflowitem_json_list is not None:
        for workflowitem in workflowitem_json_list:
            item = items_dict[workflowitem['item_id']]
            import_workspaceitem(item, workflowitem['collection_id'],
                                 workflowitem['multiple_titles'],
                                 workflowitem['published_before'],
                                 workflowitem['multiple_files'],
                                 -1,
                                 -1,
                                 metadata_class,
                                 handle_class,
                                 workspaceitem_id_dict,
                                 item_id_dict,
                                 collection_id_dict,
                                 temp_item2group_dict,
                                 eperson_id_dict)
            # create workflowitem from created workspaceitem
            params = {'id': str(workspaceitem_id_dict[workflowitem['item_id']])}
            try:
                response = do_api_post(workflowitem_url, params, None)
                workflowitem_id_dict[workflowitem['workflow_id']] = \
                    response.headers['workflowitem_id']
                imported_workflowitem += 1
            except Exception as e:
                logging.error('POST request ' + workflowitem_url + ' for id: ' +
                              str(workflowitem['item_id']) + ' failed. Exception: ' +
                              str(e))
            del items_dict[workflowitem['item_id']]

        # save workflow dict as json
        if save_dict:
            save_dict_as_json(saved_workflow_json_name, workflowitem_id_dict)
        statistics_val = (len(workflowitem_json_list), imported_workflowitem)
        statistics_dict['workflowitem'] = statistics_val
        imported_item += imported_workflowitem
        logging.info("Cwf_workflowitem was successfully imported!")
    else:
        logging.info("Workflowitem JSON is empty.")

    # create other items
    for item in items_dict.values():
        item_json_p = {
            'discoverable': item['discoverable'],
            'inArchive': item['in_archive'],
            'lastModified': item['last_modified'],
            'withdrawn': item['withdrawn']
        }
        metadatvalue_item_dict = metadata_class.get_metadata_value(item['uuid'])
        if metadatvalue_item_dict:
            item_json_p['metadata'] = metadatvalue_item_dict
        handle_item = handle_class.get_handle(2, item['uuid'])
        if handle_item is not None:
            item_json_p['handle'] = handle_item
        if item['owning_collection'] is None:
            logging.error("Item owning collection is null!")
            continue
        params = {
            'owningCollection': collection_id_dict[item['owning_collection']],
            'epersonUUID': eperson_id_dict[item['submitter_id']]
        }
        try:
            response = do_api_post(item_url, params, item_json_p)
            response_json = convert_response_to_json(response)
            item_id_dict[item['uuid']] = response_json['id']
            imported_item += 1
        except Exception as e:
            logging.error('POST request ' + item_url + ' for id: ' +
                          str(item['uuid']) + ' failed. Exception: ' + str(e))

    # save item dict as json
    if save_dict:
        save_dict_as_json(saved_item_json_name, item_id_dict)
    statistics_val = (statistics_dict['item'][0], imported_item)
    statistics_dict['item'] = statistics_val
    logging.info("Item and Collection2item were successfully imported!")


def import_workspaceitem(item,
                         owning_collectin_id,
                         multiple_titles,
                         published_before,
                         multiple_files,
                         stagereached,
                         page_reached,
                         metadata_class,
                         handle_class,
                         workspaceitem_id_dict,
                         item_id_dict,
                         collection_id_dict,
                         temp_item2group_dict,
                         eperson_id_dict):
    """
    Auxiliary method for import item.
    Import data into database.
    Mapped tables: workspaceitem, metadata, handle
    """
    workspaceitem_url = 'clarin/import/workspaceitem'
    workspaceitem_json_p = {
        'discoverable': item['discoverable'],
        'inArchive': item['in_archive'],
        'lastModified': item['last_modified'],
        'withdrawn': item['withdrawn']
    }
    metadatavalue_item_dict = metadata_class.get_metadata_value(item['uuid'])
    if metadatavalue_item_dict is not None:
        workspaceitem_json_p['metadata'] = metadatavalue_item_dict
    handle_workspaceitem = handle_class.get_handle(2, item['uuid'])
    if handle_workspaceitem is not None:
        workspaceitem_json_p['handle'] = handle_workspaceitem
    # the params are workspaceitem attributes
    params = {
        'owningCollection': collection_id_dict[owning_collectin_id],
        'multipleTitles': multiple_titles,
        'publishedBefore': published_before,
        'multipleFiles': multiple_files, 'stageReached': stagereached,
        'pageReached': page_reached,
        'epersonUUID': eperson_id_dict[item['submitter_id']]
    }
    try:
        response = do_api_post(workspaceitem_url, params, workspaceitem_json_p)
        workspaceitem_id = convert_response_to_json(response)['id']
        workspaceitem_id_dict[item['uuid']] = workspaceitem_id
        item_url = API_URL + 'clarin/import/' + str(workspaceitem_id) + "/item"
        try:
            response = rest_proxy.d.api_get(item_url, None, None)
            item_id_dict[item['uuid']] = convert_response_to_json(response)['id']
            # # add item as template item in group
            # if item['item_id'] in temp_item2group_dict.keys():
            #     groups_a = temp_item2group_dict[item['item_id']]
            #     for group in groups_a:
            #
        except Exception as e:
            logging.error('POST request ' + item_url +
                          ' failed. Exception: ' + str(e))
    except Exception as e:
        logging.error('POST request ' + workspaceitem_url + ' for id: ' +
                      str(item['uuid']) +
                      ' failed. Exception: ' + str(e))
