import os
import logging
import requests
import psycopg2

import const

from data_pump.utils import create_dict_from_json, read_json, convert_response_to_json
from support.dspace_proxy import rest_proxy

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("root")


def convert_old_ids_to_new(old_object_ids, map_dict):
    """
    Create list of IDs of dspace 7 from IDs of dspace5 based on their mapping.
    @param old_object_ids:  list of IDs from dspace5
    @param map_dict:        dict of IDs mapping
    @return:                list of IDs of dspace7
    """
    new_ids = [map_dict[old_id] for old_id in old_object_ids]
    return new_ids


def get_data_from_database():
    """
    Get data from dspace5 based on SELECT.
    We want all IDs of items, which are READ able for Anonymous
    and are not workspace or workflow.
    @return:    list od item ids from dspace5
    """
    resource_ids_list = []
    # create database connection
    conn = psycopg2.connect(database=const.CLARIN_DSPACE_NAME,
                            host=const.CLARIN_DSPACE_HOST,
                            user=const.CLARIN_DSPACE_USER,
                            password=const.CLARIN_DSPACE_PASSWORD)
    logging.info("Connection to database " + const.CLARIN_DSPACE_NAME + " was successful!")
    # create select
    # we want all resource_ids for items
    # where the action is READ
    # which are not workspaces or workflows
    # item exists in item table
    # owning group is Anonymous
    cursor = conn.cursor()
    cursor.execute(
        "SELECT distinct resource_id FROM public.resourcepolicy " +
        "WHERE resource_type_id = '2' " +
        "AND action_id IN (0, 9, 10) " +
	    "AND NOT EXISTS (SELECT 'x' FROM public.workspaceitem WHERE " +
        "public.resourcepolicy.resource_id = public.workspaceitem.item_id)"
        "AND NOT EXISTS (SELECT 'x' FROM public.workflowitem WHERE " +
        "public.resourcepolicy.resource_id = public.workflowitem.item_id) " +
        "AND EXISTS (SELECT 'x' FROM public.item WHERE " +
        "public.resourcepolicy.resource_id = public.item.item_id) " +
        "AND epersongroup_id = '0'")
    # list of tuples
    result_t = cursor.fetchall()
    cursor.close()
    conn.close()
    # create list from select result
    for resource_id_t in result_t:
        resource_id = resource_id_t[0]
        resource_ids_list.append(resource_id)
    return resource_ids_list

if __name__ == "__main__":
    item_dict_json = "item_dict.json"
    handle_json = "handle.json"
    # get a dictionary mapping dspace5 IDs to dspace7 IDs for items
    item_dict = create_dict_from_json(item_dict_json)
    # get IDs of item from dspace5 base od select
    old_item_list = get_data_from_database()
    # get IDs for dspace7 from IDs from dspace5 based on map
    new_item_list = convert_old_ids_to_new(old_item_list, item_dict)
    # list od item IDs from dspace7 which can READ Anonymous
    item_ids_list=[]
    # get total pages for search
    # max page size for this request is 100
    response = rest_proxy.get('discover/search/objects?sort=score,DESC&size=100&page=0&configuration=default&dsoType=ITEM&embed=thumbnail&embed=item%2Fthumbnail')
    response_json = convert_response_to_json(response)
    totalPages = objects = response_json['_embedded']['searchResult']['page']['totalPages']
    # get result from each page
    # we don't get items which are withdrawn or discoverable
    for page in range(totalPages):
        response = rest_proxy.get('discover/search/objects?sort=score,DESC&size=100&page=' + str(page) +'&configuration=default&dsoType=ITEM&embed=thumbnail&embed=item%2Fthumbnail')
        response_json = convert_response_to_json(response)
        objects = response_json['_embedded']['searchResult']['_embedded']['objects']
        # add each object to result list
        for item in objects:
            item_ids_list.append(item['_embedded']['indexableObject']['id'])

    # compare expected items in dspace5 and got items from dspace7
    # log items, which we cannot find (NOTE: these items can be discoverable or withdrawn - we did not get these items from dspace7)
    # you should check it in dspace5 if there will be some items in the log
    for id_ in new_item_list:
        if id_ in item_ids_list:
            item_ids_list.remove(id_)
        else:
            _logger.warning('Did not get resource policy for item: ' + id_ + '. Check if item is discoverable or withdraw.')
    #now in new_item_list are items whose resource_policy was not found in dspace5
    # it could be because in dspace7 is using inheritance for resource policies
    # check if you have access for these items in dspace5 based on their handles or there was import error
    item_lindat_url = 'https://lindat.mff.cuni.cz/repository/xmlui/handle/'
    # load handle_json
    handle_json = read_json(handle_json)
    # create dict
    handle_dict = {}
    # handle has to be defined for item and item has to exist
    handle_dict = {item_dict[handle['resource_id']]: handle['handle'] for handle in handle_json if
                   handle['resource_type_id'] == 2 and handle['resource_id'] in item_dict}
    # do request to dspace5 for remaining items
    for id_ in item_ids_list:
        response = requests.get(item_lindat_url + handle_dict[id_])
        if not response.ok:
            _logger.error('Do not exist resource policy of anonymous READ for item: ' + id_ + ' in dspace5!')
