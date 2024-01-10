import logging
import os

from data_pump.utils import create_bitstream, create_community, create_collection, create_item, create_bundle
from support.dspace_interface.models import Item

MULTIPART_CONTENT_TYPE = 'multipart/form-data'
HUNDRED_FILES_PATH = 'hundred_of_files'
ZIP_FILES_PATH = 'zip_files'

COMMUNITY_2_CREATE = {
    "type": {
        "value": "community"
    },
    "metadata": {
        "dc.title": [
            {
                "language": None,
                "value": "Commmm2"
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
                "value": "Colll"
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
                "value": "Itemmm"
            }
        ]
    },
    "inArchive": True,
    "discoverable": True,
    "withdrawn": False,
}


def load_files_from_folder(folder_path):
    """
    Load all files from folder.
    @param folder_path: path to the folder
    @return: list of files or None if folder does not exist
    """
    # Check if the folder path exists
    if not os.path.exists(folder_path):
        logging.warning(f"The folder '{folder_path}' does not exist.")
        return None

    f = []
    for (dirpath, dirnames, filenames) in os.walk(folder_path):
        f.extend(filenames)
        break

    return f


def create_bistreams_from_folder(item, folder_path):
    """
    Create a bitstream for each file from specific folder.
    @param item: item where the bitstreams will be created
    @param folder_path: folder path where the files are located
    """
    # Create a bundle for item where the files will be uploaded
    original_bundle = create_bundle(item)
    if not original_bundle:
        logging.warning(f'Bundle was not created.')

    # Load files from folder
    files = load_files_from_folder(folder_path)
    if not files:
        logging.warning(f'No files were loaded from the folder {folder_path}')
    for file_name in files:
        logging.info(f'Creating bitstream with file: {file_name}')
        create_bitstream(original_bundle, file_name, f'{folder_path}/{file_name}', MULTIPART_CONTENT_TYPE)


def create_item_with_title(parent, title):
    """
    Create item with specific title.
    @param parent: collection where the item will be created
    @param title: title of the item
    @return: created item or None if item was not created
    """
    item2create = ITEM_2_CREATE
    item2create['metadata']['dc.title'][0]['value'] = title
    return create_item(parent.uuid, Item(item2create))


if __name__ == '__main__':
    # Create community
    community = create_community(None, COMMUNITY_2_CREATE)
    if not community:
        logging.warning(f'Community was not created.')

    # Create collection
    collection = create_collection(community.uuid, COLLECTION_2_CREATE)
    if not collection:
        logging.warning(f'Collection was not created.')

    # Create item with 100 bitstreams
    item_hundred_files = create_item_with_title(collection, 'Hundred Files')
    create_bistreams_from_folder(item_hundred_files, HUNDRED_FILES_PATH)

    # Create item with zip bitstream
    item_zip_file = create_item_with_title(collection, 'Zip File')
    create_bistreams_from_folder(item_zip_file, ZIP_FILES_PATH)
