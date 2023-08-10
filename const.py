import enum
import logging

user = "test@test.edu"
password = "dspace"
# password = "admin"
# user = "m@edu.com"
# password = "dspace"

# http or https
use_ssl = False
# host = "localhost"
host = "dev-5.pc"
# fe_port = ":4000"
fe_port = None
# be_port = ":8080"
be_port = None
be_location = "/server/"

# config logging
logging.basicConfig(filename='logs.log', encoding='utf-8', level=logging.INFO)

on_dev_5 = host == "dev-5.pc"

# there should be no need to modify this part, unless adding new tests.
# mainly concatenates and parses settings above
protocol = "https://" if use_ssl else "http://"
url = protocol + host
FE_url = url + (fe_port if fe_port else "")
BE_url = url + (be_port if be_port else "") + be_location
OAI_url = BE_url + "oai/"
OAI_req = OAI_url + "request?verb=ListRecords&metadataPrefix=oai_dc&set="
OAI_openaire_dc = OAI_url + "openaire_data?verb=ListRecords&" \
                            "metadataPrefix=oai_dc&set="
OAI_openaire_datacite = OAI_url + "openaire_data?verb=ListRecords&" \
                                  "metadataPrefix=oai_datacite&set="
OAI_olac = OAI_url + "request?verb=ListRecords&metadataPrefix=olac&set="
OAI_cmdi = OAI_url + "request?verb=ListRecords&metadataPrefix=cmdi&set="
API_URL = BE_url + "api/"
IMPORT_DATA_PATH = "data/license_import/"
COM = "BB-TEST-COM"
com_UUID = None
COL = "BB-TEST-COL"
col_UUID = None
ITM_prefix = "BB-TEST-ITM-"
EMBEDDED = "_embedded"


class ItemType(enum.Enum):
    ITEM = 1
    COMMUNITY = 2
    COLLECTION = 3
