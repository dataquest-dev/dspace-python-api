import datetime
import logging
from tqdm import tqdm
from ._utils import read_json, serialize, deserialize, time_method

_logger = logging.getLogger("pump.item")


class items:
    """
        SQL:
            delete from workspaceitem ;
    """

    TYPE = 2

    def __init__(self,
                 item_file_str: str,
                 ws_file_str: str,
                 wf_file_str: str,
                 col2item_file_str: str):

        self._items = read_json(item_file_str)
        if len(self._items) == 0:
            _logger.info(f"Empty input: [{item_file_str}].")

        self._ws_items = read_json(ws_file_str)
        if len(self._ws_items) == 0:
            _logger.info(f"Empty input: [{ws_file_str}].")

        self._wf_items = read_json(wf_file_str)
        if len(self._wf_items) == 0:
            _logger.info(f"Empty input: [{wf_file_str}].")

        self._col2item = read_json(col2item_file_str)
        if len(self._col2item) == 0:
            _logger.info(f"Empty input: [{col2item_file_str}].")

        self._id2item = {str(e['item_id']): e for e in self._items}
        self._id2uuid = {}
        self._ws_id2uuid = {}
        self._wf_id2uuid = {}
        self._col_id2uuid = {}
        self._migrated_versions = []

        self._imported = {
            "items": 0,
            "wf": 0,
            "ws": 0,
            "cols": 0,
            "versions": 0,
        }
        self._done = []
        self._versions = {
            "not_imported_handles": [],
            "withdrawn": [],
            "not_imported": [],
        }

    def __len__(self):
        return len(self._items)

    def uuid(self, eid: int):
        return self._id2uuid.get(str(eid), None)

    def wf_uuid(self, wfid: int):
        return self._wf_id2uuid.get(str(wfid), None)

    @property
    def imported_ws(self):
        return self._imported['ws']

    @property
    def imported_wf(self):
        return self._imported['wf']

    @property
    def imported_cols(self):
        return self._imported['cols']

    @property
    def imported(self):
        return self._imported['items']

    def item(self, item_id: int):
        return self._id2item[str(item_id)]

    @time_method
    def import_to(self, cache_file, dspace, handles, metadatas, epersons, collections):
        """
            Import data into database.
            Mapped tables: item, collection2item, workspaceitem, cwf_workflowitem,
            metadata, handle
        """
        if "ws" in self._done:
            _logger.info("Skipping workspace import")
        else:
            if self._ws_items is not None:
                self._ws_import_to(dspace, handles, metadatas, epersons, collections)
            self._done.append("ws")
            self.serialize(cache_file)

        if "w2f" in self._done:
            _logger.info("Skipping workflow import")
        else:
            if self._wf_items is not None:
                self._wf_import_to(dspace, handles, metadatas, epersons, collections)
            self._done.append("wf")
            self.serialize(cache_file)

        if "item" in self._done:
            _logger.info("Skipping item import")
        else:
            self._item_import_to(dspace, handles, metadatas, epersons, collections)
            self._done.append("item")
            self.serialize(cache_file)

        if "itemcol" in self._done:
            _logger.info("Skipping itemcol import")
        else:
            self._itemcol_import_to(dspace, handles, metadatas, epersons, collections)
            self._done.append("itemcol")
            self.serialize(cache_file)

    def _import_item(self, dspace, generic_item_d, item, handles, metadatas, epersons, collections) -> bool:
        i_id = item['item_id']

        data = {
            'discoverable': item['discoverable'],
            'inArchive': item['in_archive'],
            'lastModified': item['last_modified'],
            'withdrawn': item['withdrawn']
        }
        i_meta = metadatas.value(items.TYPE, i_id)
        if i_meta is not None:
            data['metadata'] = i_meta

        i_handle = handles.get(items.TYPE, i_id)
        if i_handle is not None:
            data['handle'] = i_handle

        # the params are workspaceitem attributes
        params = {
            'owningCollection': collections.uuid(generic_item_d['collection_id']),
            'multipleTitles': generic_item_d['multiple_titles'],
            'publishedBefore': generic_item_d['published_before'],
            'multipleFiles': generic_item_d['multiple_files'],
            'stageReached': generic_item_d.get('stage_reached', -1),
            'pageReached': generic_item_d.get('page_reached', -1),
            'epersonUUID': epersons.uuid(item['submitter_id'])
        }

        try:
            resp = dspace.put_ws_item(params, data)
            ws_uuid = resp['id']
            self._ws_id2uuid[str(i_id)] = ws_uuid
        except Exception as e:
            _logger.error(f'put_ws_item: [{i_id}] failed [{str(e)}]')
            return False

        try:
            resp = dspace.fetch_item(ws_uuid)
            i_uuid = resp['id']
            self._id2uuid[str(i_id)] = i_uuid
        except Exception as e:
            _logger.error(f'fetch_item: [{ws_uuid}] failed [{str(e)}]')
            return False

        return True

    def _ws_import_to(self, dspace, handles, metadatas, epersons, collections):
        _logger.info(f"Importing workspaceitems [{len(self._ws_items)}]!")

        for ws in tqdm(self._ws_items):
            item = self.item(ws['item_id'])
            ret = self._import_item(dspace, ws, item, handles,
                                    metadatas, epersons, collections)
            if ret:
                self._imported["ws"] += 1
            # ?
            item_id = ws['item_id']
            if item_id in item:
                del item[item_id]

        _logger.info(f"Workspaceitem [{self.imported_ws}] imported!")

    def _wf_import_to(self, dspace, handles, metadatas, epersons, collections):
        _logger.info(f"Importing workflowitems [{len(self._wf_items)}]!")

        # create workflowitem
        # workflowitem is created from workspaceitem
        # -1, because the workflowitem doesn't contain this attribute
        for wf in tqdm(self._wf_items):
            wf_id = wf['item_id']
            item = self.item(wf_id)
            ret = self._import_item(dspace, wf, item, handles,
                                    metadatas, epersons, collections)
            if not ret:
                continue

            # create workflowitem from created workspaceitem
            # TODO(verify)
            params = {'id': str(self._id2uuid[str(wf_id)])}
            try:
                resp = dspace.put_wf_item(params)
                self._wf_id2uuid[str(wf['workflow_id'])] = resp.headers['workflowitem_id']
                self._imported["wf"] += 1
            except Exception as e:
                _logger.error(f'put_wf_item: [{wf_id}] failed [{str(e)}]')

            if wf_id in item:
                del item[wf_id]

        _logger.info(f"Workflow [{self.imported_wf}] imported!")

    def _item_import_to(self, dspace, handles, metadatas, epersons, collections):
        _logger.info(f"Importing items [{len(self._items)}]!")
        without_col = 0

        # create other items
        for item in tqdm(self._items):
            i_id = item['item_id']
            data = {
                'discoverable': item['discoverable'],
                'inArchive': item['in_archive'],
                'lastModified': item['last_modified'],
                'withdrawn': item['withdrawn']
            }

            i_meta = metadatas.value(items.TYPE, i_id)
            if i_meta:
                data['metadata'] = i_meta

            i_handle = handles.get(items.TYPE, i_id)
            if i_handle is not None:
                data['handle'] = i_handle

            if item['owning_collection'] is None:
                _logger.critical(f"Item without collection [{i_id}] is not valid!")
                without_col += 1
                continue

            col_uuid = collections.uuid(item['owning_collection'])
            params = {
                'owningCollection': col_uuid,
                'epersonUUID': epersons.uuid(item['submitter_id']),
            }

            if col_uuid is None:
                _logger.critical(
                    f"Item without collection [{i_id}] cannot be imported here")
                continue

            try:
                resp = dspace.put_item(params, data)
                self._id2uuid[str(i_id)] = resp['id']
                self._imported["items"] += 1
            except Exception as e:
                _logger.error(f'put_item: [{i_id}] failed [{str(e)}]')

        _logger.info(f"Items [{self.imported}] imported, without_col:[{without_col}]!")

    def _itemcol_import_to(self, dspace, handles, metadatas, epersons, collections):
        _logger.info(f"Importing items coll [{len(self._col2item)}]!")

        # Find items which are mapped in more collections and store them into dictionary in this way
        # {'item_uuid': [collection_uuid_1, collection_uuid_2]}
        for col in self._col2item:
            col_item_id = col['item_id']
            # Every item should have mapped only one collection - the owning collection except the items which
            # are mapped into more collections
            item_uuid = self.uuid(col_item_id)
            if item_uuid is None:
                _logger.critical(f"Cannot find collection of item [{col_item_id}]")
                continue
            col_uuid = collections.uuid(col['collection_id'])
            self._col_id2uuid.setdefault(item_uuid, []).append(col_uuid)

        # Call Vanilla REST endpoint which add relation between Item and Collection into the collection2item table
        for item_uuid, cols in tqdm(self._col_id2uuid.items()):
            if len(cols) < 2:
                continue
            try:
                data = self._col_id2uuid[item_uuid]
                dspace.put_item_to_col(item_uuid, data)
                self._imported['cols'] += 1
            except Exception as e:
                _logger.error(f'put_item_to_col: [{item_uuid}] failed [{str(e)}]')

        _logger.info(f"Items added to collections [{self.imported_cols}] imported!")

    # =============

    def serialize(self, file_str: str):
        data = {
            "items": self._items,
            "ws_items": self._ws_items,
            "wf_items": self._wf_items,
            "col2item": self._col2item,
            "id2item": self._id2item,
            "id2uuid": self._id2uuid,
            "ws_id2uuid": self._ws_id2uuid,
            "wf_id2uuid": self._wf_id2uuid,
            "col_id2uuid": self._col_id2uuid,
            "imported": self._imported,
            "done": self._done,
            "versions": self._versions,
            "migrated_versions": self._migrated_versions,
        }
        serialize(file_str, data)

    def deserialize(self, file_str: str):
        data = deserialize(file_str)
        self._items = data["items"]
        self._ws_items = data["ws_items"]
        self._wf_items = data["wf_items"]
        self._col2item = data["col2item"]
        self._id2item = data["id2item"]
        self._id2uuid = data["id2uuid"]
        self._ws_id2uuid = data["ws_id2uuid"]
        self._wf_id2uuid = data["wf_id2uuid"]
        self._col_id2uuid = data["col_id2uuid"]
        self._imported = data["imported"]
        self._done = data["done"]
        self._versions = data["versions"]
        self._migrated_versions = data.get("migrated_versions", [])

    def _migrate_versions(self, env, db7, db5_dspace, metadatas):
        _logger.info(
            f"Migrating versions [{len(self._id2item)}], already done:[{len(self._migrated_versions)}]")

        admin_username = env["backend"]["user"]
        admin_uuid = db7.get_admin_uuid(admin_username)

        self._migrated_versions = []

        # Migrate versions for every Item
        for item_id, item in tqdm(self._id2item.items()):
            # Do not process versions of the item that have already been processed.
            if item_id in self._migrated_versions:
                continue

            # This sequence contains handles of all versions of the Item ordered from the first version to the latest one
            versions = self.get_all_versions(item_id, metadatas)

            # Do not process item which does not have any version
            if len(versions or []) == 0:
                continue

            _logger.debug(f'Processing all versions for the item with ID: {item_id}')

            # All versions of this Item is going to be processed
            # Insert data into `versionhistory` table
            versionhistory_new_id = db7.get_last_id(
                'versionhistory', 'versionhistory_id') + 1
            db7.exe_sql(f"""
INSERT INTO versionhistory(versionhistory_id) VALUES ({versionhistory_new_id})
SELECT setval('versionhistory_seq', {versionhistory_new_id})
""")

            # Insert data into `versionitem` with `versionhistory` id
            versionitem_new_id = db7.get_last_id('versionitem', 'versionitem_id') + 1

            for index, i_handle in enumerate(versions, 1):
                # Get the handle of the x.th version of the Item
                i_handle_d = metadatas.versions.get(i_handle, None)

                # If the item is withdrawn the new version could be stored in our repo or in another. Do import that version
                # only if the item is stored in our repo.
                if i_handle_d is None:
                    current_item = self.item(item_id)
                    if current_item['withdrawn']:
                        _logger.info(
                            f'The item handle: {i_handle} cannot be migrated because it is stored in another repository.')
                        continue

                # Get item_id using the handle
                item_id = i_handle_d['item_id']
                # Get the uuid of the item using the item_id
                item_uuid = self.uuid(item_id)
                # timestamp is required column in the database
                timestamp = datetime.datetime.now()

                db7.exe_sql(
                    f"INSERT INTO public.versionitem(versionitem_id, version_number, version_date, version_summary, versionhistory_id, eperson_id, item_id) VALUES ("
                    f"{versionitem_new_id}, "
                    f"{index}, "
                    f"'{timestamp}', "
                    f"'', "
                    f"{versionhistory_new_id}, "
                    f"'{admin_uuid}', "
                    f"'{item_uuid}');"
                )
                # Update sequence
                db7.exe_sql(f"SELECT setval('versionitem_seq', {versionitem_new_id})")
                versionitem_new_id += 1
                self._migrated_versions.append(item_id)

        _logger.info(f"Migrated versions [{len(self._migrated_versions)}]")

    def raw_after_import(self, env, db7, db5_dspace, metadatas):
        # Migration process
        self._migrate_versions(env, db7, db5_dspace, metadatas)
        self._check_sum(db7, db5_dspace)

    def get_newer_versions(self, item_id: int, metadatas):
        return self._get_versions(item_id, metadatas, metadatas.DC_RELATION_ISREPLACEDBY_ID)

    def get_older_versions(self, item_id: int, metadatas):
        return self._get_versions(item_id, metadatas, metadatas.DC_RELATION_REPLACES_ID)

    def _get_versions(self, item_id: int, metadatas, metadata_field: int):
        """
            Return all previous or newer versions of the item using connection between `dc.relation.replaces` and
            `dc.relation.isreplacedby` item metadata.
            @return: list of versions or empty list
        """

        def _get_version(cur_item_id):
            item_versions = metadatas.value(items.TYPE, cur_item_id, metadata_field)
            if len(item_versions or []) == 0:
                # _logger.debug(f"Item [{cur_item_id}] does not have any version.")
                return None
            return item_versions[0]

        versions = []
        cur_item_id = item_id

        # current_version is handle of previous or newer item
        cur_item_version = _get_version(cur_item_id)

        while cur_item_version is not None:
            #
            if cur_item_version not in metadatas.versions:
                # Check if current item is withdrawn
                # TODO(jm): check original code - item_id
                cur_item = self.item(cur_item_id)
                if cur_item['withdrawn']:
                    # The item is withdrawn and stored in another repository
                    _logger.info(f'Item [{cur_item_version}] is withdrawn')
                    self._versions["withdrawn"].append(cur_item_version)
                else:
                    _logger.error(
                        f'The item with handle: {cur_item_version} has not been imported!')
                    self._versions["not_imported"].append(cur_item_version)
                break

            versions.append(cur_item_version)
            cur_item_id = metadatas.versions[cur_item_version]['item_id']
            cur_item_version = _get_version(cur_item_id)

        return versions

    def get_all_versions(self, item_id: int, metadatas):
        """
            Return all versions of the item in ordered list from the first version to the latest including the handle of the
            current Item
            @return: list of the item versions or if the item doesn't have any version return None
        """
        # The newer versions of the item
        newer_versions = self.get_newer_versions(item_id, metadatas)
        # The previous versions of the item
        previous_versions = self.get_older_versions(item_id, metadatas)
        # Previous versions are in wrong order - reverse the list
        previous_versions = previous_versions[::-1]

        # If this item does not have any version return a None
        if len(newer_versions) == 0 and len(previous_versions) == 0:
            return None

        # Get handle of the current Item
        cur_handle = metadatas.value(items.TYPE, item_id, metadatas.DC_IDENTIFIER_URI_ID)
        if len(cur_handle or []) == 0:
            _logger.error(f'Cannot find handle for the item with id: {item_id}')
            self._versions["not_imported_handles"].append(item_id)
            return None

        return previous_versions + [cur_handle[0]] + newer_versions

    def _check_sum(self, db7, db5_dspace):
        """
            Check if item versions importing was successful
            Select item ids from CLARIN-DSpace5 which has some version metadata
            Select items uuids from CLARIN-DSpace7 `versionitem` table where are stored item's version
            Check if all items from CLARIN-DSpace5 has record in the CLARIN-DSpace7 history version table - check uuids
        """

        # Select item ids from CLARIN-DSpace5 which has some version metadata
        clarin_5_item_ids = db5_dspace.fetch_all(
            "SELECT resource_id FROM metadatavalue WHERE metadata_field_id in (50,51) group by resource_id;"
        )

        # Select item uuids from CLARIN-DSpace7 which record in the `versionitem` table
        clarin_7_item_uuids = db7.fetch_all("select item_id from versionitem;")

        if clarin_5_item_ids is None or clarin_7_item_uuids is None:
            _logger.error('Cannot check result of importing item versions.')
            return

        # Some items could not be imported - uuid
        not_imported_items = []
        clarin_5_ids_to_uuid = [self.uuid(x[0]) for x in clarin_5_item_ids]

        # Check if the clarin_5_uuid is in the clarin_7_historyversion_uuid
        for clarin_7_uuid in clarin_7_item_uuids:
            # clarin_5_uuid = item_id_dict[clarin_5_id]
            if clarin_7_uuid[0] not in clarin_5_ids_to_uuid:
                not_imported_items.append(clarin_7_uuid[0])

        if len(not_imported_items) > 0:
            _logger.warning('Version migration MAYBE was not successful for the items below because the item could be'
                            ' a workspace or previous version is withdrawn.')
            for non_imported_uuid in not_imported_items:
                _logger.warning(
                    f'Please check versions for the Item with: {non_imported_uuid}')
