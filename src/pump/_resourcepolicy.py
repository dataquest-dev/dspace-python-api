import logging
from ._utils import read_json, time_method, serialize, deserialize, progress_bar, log_before_import, log_after_import

_logger = logging.getLogger("pump.resourcepolicy")


class uuider:
    def __init__(self, repo):
        self.repo = repo

    def get(self, res_type_id: int, res_id: int):
        # find object id based on its type
        try:
            if res_type_id == self.repo.communities.TYPE:
                return self.repo.communities.uuid(res_id)
            if res_type_id == self.repo.collections.TYPE:
                return self.repo.collections.uuid(res_id)
            if res_type_id == self.repo.items.TYPE:
                return self.repo.items.uuid(res_id)
            if res_type_id == self.repo.bitstreams.TYPE:
                return self.repo.bitstreams.uuid(res_id)
            if res_type_id == self.repo.bundles.TYPE:
                return self.repo.bundles.uuid(res_id)
        except Exception as e:
            return None
        return None


class resourcepolicies:
    """
        SQL:
            delete from resourcepolicy ;
    """

    def __init__(self, resourcepolicy_file_str: str):
        self._respol = read_json(resourcepolicy_file_str)
        if len(self._respol) == 0:
            _logger.info(f"Empty input: [{resourcepolicy_file_str}].")
        self._id2uuid = {}
        self._imported = {
            "respol": 0,
        }

    def __len__(self):
        return len(self._respol)

    def uuid(self, b_id: int):
        return self._id2uuid[str(b_id)]

    @property
    def imported(self):
        return self._imported['respol']

    @time_method
    def import_to(self, env, dspace, repo):
        expected = len(self)
        log_key = "resourcepolicies"
        log_before_import(log_key, expected)

        uuder = uuider(repo)
        dspace_actions = env["dspace"]["actions"]
        failed = 0

        def_read = 0

        for res_policy in progress_bar(self._respol):
            res_id = res_policy['resource_id']
            res_type_id = res_policy['resource_type_id']
            res_uuid = uuder.get(res_type_id, res_id)
            if res_uuid is None:
                _logger.critical(f"Cannot find uuid for [{res_type_id}] [{res_id}]")
                continue
            params = {}
            if res_uuid is not None:
                params['resource'] = res_uuid
            # in resource there is action as id, but we need action as text
            actionId = res_policy['action_id']

            # control, if action is entered correctly
            if actionId < 0 or actionId >= len(dspace_actions):
                _logger.error(f"action_id [{actionId}] is out of range.")
                failed += 1
                continue

            # create object for request
            data = {
                'action': dspace_actions[actionId],
                'startDate': res_policy['start_date'],
                'endDate': res_policy['end_date'],
                'name': res_policy['rpname'],
                'policyType': res_policy['rptype'],
                'description': res_policy['rpdescription']
            }

            # resource policy has defined eperson or group, not the both
            # get eperson if it is not none
            if res_policy['eperson_id'] is not None:
                params['eperson'] = repo.epersons.uuid(res_policy['eperson_id'])
                try:
                    resp = dspace.put_resourcepolicy(params, data)
                    self._imported["respol"] += 1
                except Exception as e:
                    _logger.error(
                        f'put_resourcepolicy: [{res_policy["policy_id"]}] failed [{str(e)}]')
                continue

            # get group if it is not none
            eg_id = res_policy['epersongroup_id']
            if eg_id is not None:
                group_list1 = [repo.groups.uuid(eg_id)]
                group_list2 = repo.collections.group_uuid(eg_id)
                group_list = set(group_list1 + group_list2)
                if len(group_list) > 1:
                    def_read += 1
                for group in group_list:
                    params['group'] = group
                    try:
                        resp = dspace.put_resourcepolicy(params, data)
                        self._imported["respol"] += 1
                    except Exception as e:
                        _logger.error(
                            f'put_resourcepolicy: [{res_policy["policy_id"]}] failed [{str(e)}]')
                continue

            _logger.error(f"Cannot import resource policy {res_policy['policy_id']} "
                          f"because neither eperson nor group is defined")
            failed += 1

        log_after_import(log_key, expected, self.imported)

    # =============

    def serialize(self, file_str: str):
        data = {
            "respol": self._respol,
            "id2uuid": self._id2uuid,
            "imported": self._imported,
        }
        serialize(file_str, data)

    def deserialize(self, file_str: str):
        data = deserialize(file_str)
        self._respol = data["respol"]
        self._id2uuid = data["id2uuid"]
        self._imported = data["imported"]
