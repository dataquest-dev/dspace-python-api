import logging
from ._utils import read_json, time_method, serialize, deserialize, progress_bar

_logger = logging.getLogger("pump.userregistration")


class userregistrations:

    def __init__(self, ur_file_str: str):
        self._ur = read_json(ur_file_str)
        self._imported = {
            "users": 0,
        }

        self._id2uuid = {}

        if len(self._ur) == 0:
            _logger.info(f"Empty input: [{ur_file_str}].")
            return

    def __len__(self):
        return len(self._ur)

    def uuid(self, e_id: int):
        return self._id2uuid[str(e_id)]

    @property
    def imported(self):
        return self._imported['users']

    @time_method
    def import_to(self, dspace, epersons):
        """
            Import data into database.
            Mapped tables: user_registration
        """
        _logger.info(f"Importing userregistration [{len(self)}]!")

        for ur in progress_bar(self._ur):
            data = {
                'email': ur['email'],
                'organization': ur['organization'],
                'confirmation': ur['confirmation']
            }
            e_id = ur['eperson_id']
            e_id_by_email = epersons.by_email(ur['email'])
            data['ePersonID'] = epersons.uuid(
                e_id_by_email) if e_id_by_email is not None else None
            try:
                resp = dspace.put_userregistration(data)
                self._id2uuid[str(e_id)] = resp['id']
                self._imported['users'] += 1
            except Exception as e:
                _logger.error(f'put_userregistration: [{e_id}] failed [{str(e)}]')

        _logger.info(f"Userregistration [{self.imported}] imported!")

    # =============

    def serialize(self, file_str: str):
        data = {
            "ur": self._ur,
            "id2uuid": self._id2uuid,
            "imported": self._imported,
        }
        serialize(file_str, data)

    def deserialize(self, file_str: str):
        data = deserialize(file_str)
        self._ur = data["ur"]
        self._id2uuid = data["id2uuid"]
        self._imported = data["imported"]
