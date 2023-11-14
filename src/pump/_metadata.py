import logging
from ._utils import read_json, time_method, serialize, deserialize, progress_bar, log_before_import, log_after_import

_logger = logging.getLogger("pump.metadata")


class metadatas:
    """
        SQL:
            delete from metadatavalue ; delete from metadatafieldregistry ; delete from metadataschemaregistry ;
    """
    validate_table = [
        ["metadataschemaregistry", {
            "compare": ["namespace", "short_id"],
        }],
        ["metadatafieldregistry", {
            "compare": ["element", "qualifier"],
        }],
        ["metadatavalue", {
            "compare": ["text_value"],
        }],
    ]

    DC_RELATION_REPLACES_ID = 50
    DC_RELATION_ISREPLACEDBY_ID = 51
    DC_IDENTIFIER_URI_ID = 25

    def __init__(self, env, dspace, value_file_str: str, field_file_str: str, schema_file_str: str):
        self._dspace = dspace
        self._values = {}

        self._fields = read_json(field_file_str)
        self._fields_id2uuid = {}
        self._fields_id2js = {x['metadata_field_id']: x for x in self._fields}

        self._schemas = read_json(schema_file_str)
        self._schemas_id2id = {}
        self._schemas_id2js = {x['metadata_schema_id']: x for x in self._schemas}

        # read dynamically
        self._versions = {}

        self._imported = {
            "schema_imported": 0,
            "schema_existed": 0,
            "schema_part_matching": 0,
            "field_imported": 0,
            "field_existed": 0,
        }

        # Find out which field is `local.sponsor`, check only `sponsor` string
        sponsor_field_id = -1
        sponsors = [x for x in self._fields if x['element'] == 'sponsor']
        if len(sponsors) != 1:
            _logger.warning(f"Found [{len(sponsors)}] elements with name [sponsor]")
        else:
            sponsor_field_id = sponsors[0]['metadata_field_id']

        # norm
        js_value = read_json(value_file_str)
        for val in js_value:
            # replace separator @@ by ;
            val['text_value'] = val['text_value'].replace("@@", ";")

            # replace `local.sponsor` data sequence
            # from `<ORG>;<PROJECT_CODE>;<PROJECT_NAME>;<TYPE>`
            # to `<TYPE>;<PROJECT_CODE>;<ORG>;<PROJECT_NAME>`
            if val['metadata_field_id'] == sponsor_field_id:
                val['text_value'] = metadatas._fix_local_sponsor(val['text_value'])

        # fill values
        for val in js_value:
            res_type_id = str(val['resource_type_id'])
            res_id = str(val['resource_id'])
            arr = self._values.setdefault(res_type_id, {}).setdefault(res_id, [])
            arr.append(val)

        # fill values
        for val in js_value:
            # Store item handle and item id connection in dict
            if not val['text_value'].startswith(env["dspace"]["handle_prefix"]):
                continue

            # metadata_field_id 25 is Item's handle
            if val['metadata_field_id'] == metadatas.DC_IDENTIFIER_URI_ID:
                d = self._versions.get(val['text_value'], {})
                d['item_id'] = val['resource_id']
                self._versions[val['text_value']] = d

    def __len__(self):
        return sum(len(x) for x in self._values.values())

    @property
    def schemas(self):
        return self._schemas

    @property
    def fields(self):
        return self._fields

    @property
    def versions(self):
        return self._versions

    @property
    def imported_schemas(self):
        return self._imported['schema_imported']

    @property
    def existed_schemas(self):
        return self._imported['schema_existed']

    @property
    def existed_schemas(self):
        return self._imported['schema_part_matching']

    @property
    def imported_fields(self):
        return self._imported['field_imported']

    @property
    def existed_fields(self):
        return self._imported['field_existed']

    @time_method
    def import_to(self, dspace):
        self._import_schema(dspace)
        self._import_fields(dspace)

    # =============

    def schema_id(self, internal_id: int):
        return self._schemas_id2id.get(str(internal_id), None)

    # =============

    def serialize(self, file_str: str):
        data = {
            "schemas_id2id": self._schemas_id2id,
            "fields_id2uuid": self._fields_id2uuid,
            "imported": self._imported,
        }
        serialize(file_str, data)

    def deserialize(self, file_str: str):
        data = deserialize(file_str)
        self._schemas_id2id = data["schemas_id2id"]
        self._fields_id2uuid = data["fields_id2uuid"]
        self._imported = data["imported"]

    # =============

    @staticmethod
    def _fix_local_sponsor(wrong_sequence_str):
        """
            Replace `local.sponsor` data sequence
            from `<ORG>;<PROJECT_CODE>;<PROJECT_NAME>;<TYPE>;<EU_IDENTIFIER>`
            to `<TYPE>;<PROJECT_CODE>;<ORG>;<PROJECT_NAME>;<EU_IDENTIFIER>`
        """
        sep = ';'
        # sponsor list could have length 4 or 5
        sponsor_list = wrong_sequence_str.split(sep)
        org, p_code, p_name, p_type = sponsor_list[0:4]
        eu_id = '' if len(sponsor_list) < 5 else sponsor_list[4]
        # compose the `local.sponsor` sequence in the right way
        return sep.join([p_type, p_code, org, p_name, eu_id])

    def _import_schema(self, dspace):
        """
            Import data into database.
            Mapped tables: metadataschemaregistry
        """
        expected = len(self._schemas)
        log_key = "metadata schemas"
        log_before_import(log_key, expected)

        # get all existing data from database table
        existed_schemas = dspace.fetch_metadata_schemas() or []

        def find_existing(short_id: str, ns: str):
            return next((e for e in existed_schemas if e['prefix'] == short_id and e['namespace'] == ns), None)

        for schema in progress_bar(self._schemas):
            meta_id = schema['metadata_schema_id']

            existing = find_existing(schema['short_id'], schema['namespace'])
            if existing is not None:
                _logger.debug(
                    f'Metadataschemaregistry prefix: {schema["short_id"]} already exists!')
                schema_id = existing['id']
                self._imported["schema_existed"] += 1
            else:
                data = {
                    'namespace': schema['namespace'],
                    'prefix': schema['short_id']
                }
                try:
                    resp = dspace.put_metadata_schema(data)
                    schema_id = resp['id']
                    self._imported["schema_imported"] += 1
                except Exception as e:
                    _logger.error(
                        f'put_metadata_schema [{meta_id}] failed. Exception: {str(e)}')
                    existing = next((e for e in existed_schemas if e['prefix'] == schema['short_id']), None)
                    if existing is not None:
                        _logger.warning(
                            f'Metadata_schema short_id {schema["short_id"]} '
                            f'exists in database with different namespace: {existing["namespace"]}.')
                    else:
                        existing = next((e for e in existed_schemas if e['namespace'] == schema['namespace']), None)
                        if existing is not None:
                            _logger.warning(
                                f'Metadata_schema namespace {schema["namespace"]} '
                                f'exists in database with different short_id: {existing["short_id"]}.')
                        else:
                            continue
                    schema_id = existing['id']
                    self._imported["schema_part_matching"] += 1

            self._schemas_id2id[str(meta_id)] = schema_id

        log_after_import(f'{log_key} [existed:{self.existed_schemas}]',
                         expected, self.imported_schemas + self.existed_schemas)

    def _import_fields(self, dspace):
        """
            Import data into database.
            Mapped tables: metadatafieldregistry
        """
        expected = len(self._fields)
        log_key = "metadata fields"
        log_before_import(log_key, expected)

        existed_fields = dspace.fetch_metadata_fields() or []

        def find_existing(field):
            schema_id = field['metadata_schema_id']
            sch_id = self.schema_id(schema_id)
            if sch_id is None:
                return None
            for e in existed_fields:
                if e['_embedded']['schema']['id'] != sch_id or \
                        e['element'] != field['element'] or \
                        e['qualifier'] != field['qualifier']:
                    continue
                return e
            return None

        existing_arr = []
        for field in progress_bar(self._fields):
            field_id = field["metadata_field_id"]
            schema_id = field['metadata_schema_id']
            e = field['element']
            q = field['qualifier']

            existing = find_existing(field)
            if existing is not None:
                _logger.debug(f'Metadatafield: {e}.{q} already exists!')
                existing_arr.append(field)
                ext_field_id = existing['id']
                self._imported["field_existed"] += 1
            else:
                data = {
                    'element': field['element'],
                    'qualifier': field['qualifier'],
                    'scopeNote': field['scope_note']
                }
                params = {'schemaId': self.schema_id(schema_id)}
                try:
                    resp = dspace.put_metadata_field(data, params)
                    ext_field_id = resp['id']
                    self._imported["field_imported"] += 1
                except Exception as e:
                    _logger.error(
                        f'put_metadata_field [{str(field_id)}] failed. Exception: {str(e)}')
                    continue

            self._fields_id2uuid[str(field_id)] = ext_field_id

        log_after_import(f'{log_key} [existing:{self.existed_fields}]',
                         expected, self.imported_fields + self.existed_fields)

    def _get_key_v1(self, val):
        """
            Using dspace backend.
        """
        int_meta_field_id = val['metadata_field_id']
        try:
            ext_meta_field_id = self.get_field_id(int_meta_field_id)
            field_js = self._dspace.fetch_metadata_field(ext_meta_field_id)
            if field_js is None:
                return None
        except Exception as e:
            _logger.error(f'fetch_metadata_field request failed. Exception: [{str(e)}]')
            return None

        # get metadataschema
        try:
            obj_id = field_js['_embedded']['schema']['id']
            schema_js = self._dspace.fetch_schema(obj_id)
            if schema_js is None:
                return None
        except Exception as e:
            _logger.error(f'fetch_schema request failed. Exception: [{str(e)}]')
            return None

        # define and insert key and value of dict
        key = schema_js['prefix'] + '.' + field_js['element']
        if field_js['qualifier']:
            key += '.' + field_js['qualifier']
        return key

    def _get_key_v2(self, val):
        """
            Using data.
        """
        int_meta_field_id = val['metadata_field_id']
        field_js = self._fields_id2js.get(int_meta_field_id, None)
        if field_js is None:
            return None
        # get metadataschema
        schema_id = field_js["metadata_schema_id"]
        schema_js = self._schemas_id2js.get(schema_id, None)
        if schema_js is None:
            return None
        # define and insert key and value of dict
        key = schema_js['short_id'] + '.' + field_js['element']
        if field_js['qualifier']:
            key += '.' + field_js['qualifier']
        return key

    def value(self, res_type_id: int, res_id: int, text_for_field_id: int = None, log_missing: bool = True):
        """
            Get metadata value for dspace object.
        """
        res_type_id = str(res_type_id)
        res_id = str(res_id)
        log_miss = _logger.info if log_missing else _logger.debug

        if res_type_id not in self._values:
            log_miss(f'Metadata missing [{res_type_id}] type')
            return None
        tp_values = self._values[res_type_id]
        if res_id not in tp_values:
            log_miss(f'Metadata for [{res_id}] are missing in [{res_type_id}] type')
            return None

        vals = tp_values[res_id]

        vals = [x for x in vals if self.exists_field(x['metadata_field_id'])]
        if len(vals) == 0:
            return {}

        # special case - return only text_value
        if text_for_field_id is not None:
            vals = [x['text_value']
                    for x in vals if x['metadata_field_id'] == text_for_field_id]
            return vals

        res_d = {}
        # create list of object metadata
        for val in vals:
            # key = self._get_key_v1(val)
            key = self._get_key_v2(val)

            # if key != key2:
            #     _logger.critical(f"Incorrect v2 impl.")

            d = {
                'value': val['text_value'],
                'language': val['text_lang'],
                'authority': val['authority'],
                'confidence': val['confidence'],
                'place': val['place']
            }
            res_d.setdefault(key, []).append(d)

        return res_d

    def exists_field(self, id: int) -> bool:
        return str(id) in self._fields_id2uuid

    def get_field_id(self, id: int) -> int:
        return self._fields_id2uuid[str(id)]
