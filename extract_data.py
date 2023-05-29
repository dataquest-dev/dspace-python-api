import os

from pyunpack import Archive

import const
from support.logs import Severity, log

OUTPUT_FOLDER = "."
# os.makedirs(OUTPUT_FOLDER, exist_ok=True) // if output folder was not "." this is good idea. Like this = useless
def extract_data():
    log("Extracting data from " + const.data_import_location, Severity.WARN)
    Archive(const.data_import_location).extractall(OUTPUT_FOLDER)
    log("Extracting data finished", Severity.DEBUG)
