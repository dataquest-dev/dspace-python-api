###
# This script changes the policy of items in a community to a specific group. Bulk access.
###
import logging
import os
import sys


_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_this_dir, "../src"))


import dspace  # noqa
import settings  # noqa
import project_settings  # noqa
from dspace.impl.models import Item  # noqa
from dspace.impl.models import Community  # noqa
from utils import init_logging, update_settings  # noqa

_logger = logging.getLogger()

# env settings, update with project_settings
env = update_settings(settings.env, project_settings.settings)
init_logging(_logger, env["log_file"])

if "DSPACE_REST_API" in os.environ:
    env["backend"]["endpoint"] = os.getenv("DSPACE_REST_API")
    env_backend_endpoint = env["backend"]["endpoint"]
    _logger.info(f"Loaded env.backend.endpoint from env DSPACE_REST_API."
                 f" Current value: {env_backend_endpoint}")

def get_all_items_from_collection(coll):
    """
    Get all items from collection
    @param coll:
    @return:
    """
    # Pagination and size because BE has a limit of 100 items per page and if the size is set to 1000 it will return
    # only 100 items
    page = 0
    size = 5
    all_collections = list()
    has_more = True
    while has_more:
        collections_on_page = dspace_be.client.get_items_from_collection(coll.uuid, page=page, size=size)
        if not collections_on_page:
            has_more = False
            break
        page += 1
        all_collections.extend(collections_on_page)
    return all_collections



if __name__ == '__main__':
    dspace_be = dspace.rest(
        env["backend"]["endpoint"],
        env["backend"]["user"],
        env["backend"]["password"],
        env["backend"]["authentication"]
    )

    # Group ID of the group to which the policy will be changed e.g. admin group
    GROUP_ID = "a8980286-7ec9-465c-b696-5dc218968292"

    # Community UUID of the community whose items of collections will be updated
    COM_UPDATE_ITEMS_UUID = 'e640c622-f0de-43e1-8446-bd6007737022'

    # Bundle name
    BUNDLE_NAME = 'ORIGINAL'
    # BUNDLE_NAME = 'THUMBNAIL'

    # !!!Allow only one of the following to be True!!!
    # Update bundle policy of the Item
    BUNDLE_RESOURCE_POLICY = False
    # Update item policy of the Item
    ITEM_RESOURCE_POLICY = True

    COL_SUBCOLLS_URL = f'{dspace_be.endpoint}/core/communities/{COM_UPDATE_ITEMS_UUID}/collections'
    COMMUNITY = Community({
        "id": COM_UPDATE_ITEMS_UUID,
        "type": "community",
        "_links": {
            "collections": {
                "href": COL_SUBCOLLS_URL
            }
        },
    })

    # How many items were updated
    counter = 0
    # How many items were without file
    without_file = 0
    # How many items were without item resource policy
    without_item_r_policy = 0
    # Get all collections of the community
    subcolls = dspace_be.client.get_collections(community=COMMUNITY)
    for coll in subcolls:
        # Counter for items in collection
        collection_counter = 0
        # Get all items of the collection
        items_of_collection = get_all_items_from_collection(coll)
        _logger.info(f'*******************Collection: {coll.name}*******************')
        for item in items_of_collection:
            collection_counter += 1
            _logger.debug(f'Item: {item.uuid}')

            resource_policy = None
            bundle = dspace_be.client.get_bundle_by_name(BUNDLE_NAME, item.uuid)
            item_resource_policy = dspace_be.client.get_resource_policy(item.uuid)

            # Update bundle policy of the Item
            if BUNDLE_RESOURCE_POLICY:
                # Get bundle of the item - ORIGINAL
                # If there is no bundle, skip the item - there is no file
                if not bundle:
                    _logger.debug(f'No ORIGINAL bundle for item uuid={item.uuid}')
                    without_file += 1
                    continue
                resource_policy = dspace_be.client.get_resource_policy(bundle.uuid)
            # Update item policy of the Item
            if ITEM_RESOURCE_POLICY:
                # Get item resource policy
                # If there is no item resource policy, skip the item
                if not item_resource_policy:
                    _logger.debug(f'No resource policy for item uuid={item.uuid}')
                    without_item_r_policy += 1
                    continue
                resource_policy = item_resource_policy

            counter += 1
            if resource_policy is not None:
                _logger.info(
                    f'Changing policy uuid={resource_policy["id"]} for item uuid={item.uuid} to group uuid={GROUP_ID}')
                r = dspace_be.client.update_resource_policy_group(resource_policy["id"], GROUP_ID)
                _logger.debug('Response: ' + str(r))
            else:
                _logger.warning(f'No resource policy for bundle {bundle.uuid} in item uuid={item.uuid}')
        _logger.info(f'===================Updated Items: {collection_counter}=====================')

    _logger.info(f'Items Without file: {without_file}')
    _logger.info(f'Items without resource policy: {without_item_r_policy}')
    _logger.info(f'Total updated Items: {counter}')
