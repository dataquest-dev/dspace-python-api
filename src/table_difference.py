import logging

import settings
import tul_settings
from utils import init_logging, update_settings

_logger = logging.getLogger()

env = update_settings(settings.env, tul_settings.settings)
init_logging(_logger, env["log_file"])

import dspace  # noqa
import pump

if __name__ == "__main__":
    dspace_be = dspace.rest(
        env["backend"]["endpoint"],
        env["backend"]["user"],
        env["backend"]["password"],
        env["backend"]["authentication"]
    )

    _logger.info("Loading repo objects")

    _logger.info("New instance database status:")
    raw_db_7 = pump.db(env["db_dspace_7"])
    raw_db_7.status()
    _logger.info("Reference database dspace status:")
    raw_db_tul = pump.db(env["db_tul"])
    raw_db_tul.status()
