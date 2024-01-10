import logging
import os
import zipfile

import src.dspace  # noqa
import src.settings  # noqa
import src.project_settings  # noqa

from src.dspace.impl.models import Item
from src.utils import update_settings

env = update_settings(src.settings.env, src.project_settings.settings)

MULTIPART_CONTENT_TYPE = 'multipart/form-data'
COPIES_COUNT = 100

TEMPLATE_FILE_PATH = 'template.png'
ZIP_FILE_PATH = 'zipfile.zip'
BIG_FILE_PATH = 'bigfile.txt'

COMMUNITY_2_CREATE = {
    "type": {
        "value": "community"
    },
    "metadata": {
        "dc.title": [
            {
                "language": None,
                "value": "Test Item Community"
            }
        ],
    }
}

COLLECTION_2_CREATE = {
    "type": {
        "value": "collection"
    },
    "metadata": {
        "dc.title": [
            {
                "language": None,
                "value": "Test Item Collection"
            }
        ]
    },
}

ITEM_2_CREATE = {
    "type": {
        "value": "item"
    },
    "metadata": {
        "dc.title": [
            {
                "language": None,
                "value": "Test Item"
            }
        ]
    },
    "inArchive": True,
    "discoverable": True,
    "withdrawn": False,
}

def remove_file(path):
    """
    Remove file from path.
    @param path: path to the file
    """
    try:
        os.remove(path)
    except OSError as e:
        logging.warning(f"Error: {e.filename} - {e.strerror}.")


def create_bistreams(dspace_client, item, is_bigfile=False, is_zipfile=False, is_hundred_files=False):
    """
    Create bitstreams for item.
    @param dspace_client: dsapce client
    @param item: item where the bitstreams will be created
    @param is_bigfile: if create an Item with big file
    @param is_zipfile: if create an Item with zip file
    @param is_hundred_files: if create an Item with 100 files
    """
    # Create a bundle for item where the files will be uploaded
    original_bundle = dspace_client.create_bundle(item)
    if not original_bundle:
        logging.warning(f'Bundle was not created.')

    if is_hundred_files:
        for i in range(COPIES_COUNT):
            # create bitstream
            logging.info(f'Creating bitstream with file: template_{i}')
            dspace_client.create_bitstream(original_bundle, TEMPLATE_FILE_PATH, TEMPLATE_FILE_PATH,
                                           MULTIPART_CONTENT_TYPE)
        return

    if is_zipfile:
        # generate zip file
        zipfile.ZipFile(ZIP_FILE_PATH, mode='w').write(TEMPLATE_FILE_PATH)

        # create bitstream
        logging.info(f'Creating bitstream with file: {ZIP_FILE_PATH}')
        dspace_client.create_bitstream(original_bundle, ZIP_FILE_PATH, ZIP_FILE_PATH, MULTIPART_CONTENT_TYPE)
        remove_file(ZIP_FILE_PATH)
        return

    if is_bigfile:
        # generate big file
        with open(BIG_FILE_PATH, 'wb') as f:
            # 3GB
            f.seek(3 * 1024 * 1024 * 1024)
            f.write(b'\0')

        # create bitstream
        logging.info(f'Creating bitstream with file: {BIG_FILE_PATH}')
        dspace_client.create_bitstream(original_bundle, BIG_FILE_PATH, BIG_FILE_PATH,
                                       MULTIPART_CONTENT_TYPE)
        remove_file(BIG_FILE_PATH)
        return


def create_item_with_title(dspace_client, parent, title):
    """
    Create item with specific title.
    @param dspace_client: dspace client
    @param parent: collection where the item will be created
    @param title: title of the item
    @return: created item or None if item was not created
    """
    item2create = ITEM_2_CREATE
    item2create['metadata']['dc.title'][0]['value'] = title
    return dspace_client.create_item(parent.uuid, Item(item2create))


if __name__ == '__main__':
    dspace_be = src.dspace.rest(
        env["backend"]["endpoint"],
        env["backend"]["user"],
        env["backend"]["password"],
        env["backend"]["authentication"]
    )

    # Create community
    community = dspace_be.create_community(None, COMMUNITY_2_CREATE)
    if not community:
        logging.warning(f'Community was not created.')

    # Create collection
    collection = dspace_be.create_collection(community.uuid, COLLECTION_2_CREATE)
    if not collection:
        logging.warning(f'Collection was not created.')

    # TODO Update existing item if it doesn't exist or create a new one
    # Create item with 100 bitstreams
    item_hundred_files = create_item_with_title(dspace_be, collection, 'Hundred Files')
    create_bistreams(dspace_be, item_hundred_files, is_hundred_files=True)

    # Create item with zip bitstream
    item_zip_files = create_item_with_title(dspace_be, collection, 'Zip File')
    create_bistreams(dspace_be, item_zip_files, is_zipfile=True)

    # Create item with big bitstream
    item_big_file = create_item_with_title(dspace_be, collection, 'Big File')
    create_bistreams(dspace_be, item_big_file, is_bigfile=True)
