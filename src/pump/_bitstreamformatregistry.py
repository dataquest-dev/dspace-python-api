import logging
from ._utils import read_json, time_method, serialize, deserialize, progress_bar

_logger = logging.getLogger("pump.bitstreamformatregistry")


class bitstreamformatregistry:
    """
        SQL:
            delete from fileextension ; delete from bitstreamformatregistry ;
    """

    def __init__(self, bfr_file_str: str):
        self._reg = read_json(bfr_file_str)
        self._imported = {
            "reg": 0,
            "existed": 0,
        }

        self._id2uuid = {}
        self._unknown_format_id = None

        if len(self) == 0:
            _logger.info(f"Empty input: [{bfr_file_str}].")
            return

    def __len__(self):
        return len(self._reg)

    def uuid(self, f_id: int):
        return self._id2uuid.get(str(f_id), None)

    @property
    def imported(self):
        return self._imported['reg']

    @property
    def imported_existed(self):
        return self._imported['existed']

    @property
    def unknown_format_id(self):
        return self._unknown_format_id

    @time_method
    def import_to(self, dspace):
        """
            Mapped tables: bitstreamformatregistry
        """
        _logger.info(f"Importing bitstreamformatregistry [{len(self)}]")

        existing_bfr2id = {}
        bfr_js = dspace.fetch_bitstreamregistry()
        if bfr_js is not None:
            for bf in bfr_js:
                existing_bfr2id[bf['shortDescription']] = bf['id']
                if bf['description'] == 'Unknown data format':
                    self._unknown_format_id = bf['id']

        map = {
            0: 'UNKNOWN',
            1: 'KNOWN',
            2: 'SUPPORTED',
        }

        for bf in progress_bar(self._reg):
            try:
                level_str = map[bf['support_level']]
            except Exception as e:
                _logger.error(
                    f'Unsupported bitstream format registry id: [{bf["support_level"]}]')
                continue

            bf_id = bf['bitstream_format_id']
            ext_id = existing_bfr2id.get(bf['short_description'], None)

            if ext_id is not None:
                self._imported["existed"] += 1
                _logger.debug(
                    f'Bitstreamformatregistry [{bf["short_description"]}] already exists!')
            else:
                data = {
                    'mimetype': bf['mimetype'],
                    'description': bf['description'],
                    'shortDescription': bf['short_description'],
                    'supportLevel': level_str,
                    'internal': bf['internal']
                }
                try:
                    resp = dspace.put_bitstreamregistry(data)
                    ext_id = resp['id']
                except Exception as e:
                    _logger.error(f'put_bitstreamregistry: [{bf_id}] failed [{str(e)}]')
                    continue

            self._id2uuid[str(bf_id)] = ext_id
            self._imported["reg"] += 1

        _logger.info(
            f"Bitstreamformatregistry [{self.imported}] imported, [existed:{self.imported_existed}]")

    # =============

    def serialize(self, file_str: str):
        data = {
            "reg": self._reg,
            "id2uuid": self._id2uuid,
            "imported": self._imported,
            "unknown_format_id": self._unknown_format_id,
        }
        serialize(file_str, data)

    def deserialize(self, file_str: str):
        data = deserialize(file_str)
        self._reg = data["reg"]
        self._id2uuid = data["id2uuid"]
        self._imported = data["imported"]
        self._unknown_format_id = data["unknown_format_id"]
