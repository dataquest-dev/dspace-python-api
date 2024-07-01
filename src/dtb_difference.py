import logging

import settings
import tul_settings
from utils import init_logging, update_settings

_logger = logging.getLogger()

env = update_settings(settings.env, tul_settings.settings)
init_logging(_logger, env["log_file"])

import dspace  # noqa
import pump


def difference_dtb(old_dtb: dict, new_dtb: dict):
    """
    Compare the counts of data in two databases and log the differences.

    Parameters:
    old_dtb (dict): The dictionary representing the old database.
                    Keys are table names and values are their respective counts.
    new_dtb (dict): The dictionary representing the new database.
                    Keys are table names and values are their respective counts.

    The result is based on the counts in new_dtb.
    Example: If table1 in old_dtb has 6 items and new_dtb has 5 items, the output is:
        table1:     1 deficit -> because in new_dtb there is 1 item missing (based on count)
    If table1 in old_dtb has 6 items and new_dtb has 7 items, the output is:
        table1:     1 surplus -> because in new_dtb there is 1 item more (based on count)
    If the counts are equal, the output is:
        table1:     0
    """
    msg = ""
    no_exist7 = []
    no_exist5 = []
    for name in sorted(old_dtb.keys()):
        if name not in new_dtb:
            no_exist7.append(name)
        else:
            difference = int(new_dtb[name]) - int(old_dtb[name])
            result = "surplus " if difference > 0 else (
                "deficit " if difference < 0 else "")
            msg += f"{name: >40}: {int(difference): >8d} {result}\n"
            del new_dtb[name]
    for name in sorted(new_dtb.keys()):
        no_exist5.append(name)
    _logger.info(
        f"\n{msg}Nonexistent tables in DSpace 7: {', '.join(no_exist7)}\nCount: {len(no_exist7)}"
        f"\nNonexistent tables in DSpace 5: {', '.join(no_exist5)}\nCount: {len(no_exist5)}")
    _logger.info(40 * "=")


if __name__ == "__main__":
    _logger.info("Loading repo objects")
    _logger.info("Database difference (v6 vs v7):")
    raw_db_7 = pump.db(env["db_dspace_7"])
    raw_db_tul = pump.db(env["db_tul"])
    difference_dtb(raw_db_tul.table_count(), raw_db_7.table_count())
