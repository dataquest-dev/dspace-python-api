import logging
from ._utils import read_json, time_method, IMPORT_LIMIT, serialize, deserialize, log_before_import, log_after_import
from ._item import items

_logger = logging.getLogger("pump.handle")


class handles:
    """
        SQL:
            delete from handle ;
    """
    validate_table = [
        ["handle", {
            "compare": ["handle", "resource_type_id"],
        }],
    ]

    def __init__(self, file_str: str):
        self._handles = {}
        self._imported = 0

        js = read_json(file_str)
        for h in js:
            res_type_id = h['resource_type_id']
            res_id = h['resource_id']
            arr = self._handles.setdefault(str(res_type_id), {}).setdefault(str(res_id), [])
            arr.append(h)

    def __len__(self):
        return len(self._handles)

    @property
    def imported(self):
        return self._imported

    # =============

    def serialize(self, file_str: str):
        # cannot serialize tuples as keys
        d = {
            "handles": self._handles,
            "imported": self._imported,
        }
        serialize(file_str, d, sorted=False)

    def deserialize(self, file_str: str):
        data = deserialize(file_str)
        self._handles = data["handles"]
        self._imported = data["imported"]

    # =============

    @time_method
    def import_to(self, dspace):
        # external
        arr = self._handles.get(None, {}).get(None, [])[:IMPORT_LIMIT]
        expected = len(arr)
        log_key = "external handles"
        log_before_import(log_key, expected)
        cnt = dspace.put_handles(arr)
        log_after_import(log_key, expected, cnt)
        self._imported += cnt

        # no object
        arr = self._handles[str(items.TYPE)].get(None, [])[:IMPORT_LIMIT]
        expected = len(arr)
        log_key = "handles"
        log_before_import(log_key, expected)
        cnt = dspace.clarin_put_handles(arr)
        log_after_import(log_key, expected, cnt)
        self._imported += cnt

    # =============

    def get(self, type_id: int, obj_id: int):
        """
            Get handle based on object type and its id.
        """
        type_id = str(type_id)
        obj_id = str(obj_id)
        if type_id not in self._handles:
            return None
        if obj_id not in self._handles[type_id]:
            return None
        # self._imported += 1 ???
        return self._handles[type_id][obj_id][0]['handle']
