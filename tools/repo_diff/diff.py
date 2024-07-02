import sys
import os
import logging
import argparse
import importlib

_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_this_dir, "../../src"))

import settings
import project_settings
from utils import init_logging, update_settings

_logger = logging.getLogger()

env = update_settings(settings.env, project_settings.settings)
init_logging(_logger, env["log_file"])

import dspace  # noqa


if __name__ == "__main__":
    _logger.info("Loading repo objects")

    parser = argparse.ArgumentParser(description='Diff databases before/after import')
    parser.add_argument('--use', help='Instance to diff', required=True, type=str)
    args = parser.parse_args()

    # update settings with selected one from the command line
    try:
        use_settings_m = importlib.import_module(f"diff_settings.{args.use}")
    except Exception as e:
        _logger.error(f"Unknown instance [{args.use}]")
        sys.exit(1)
    use_env = use_settings_m.settings
    # hack v6 because it is the same as v5 for this context and
    # repo uses `db_dspace_5` to connect to the database
    if "db_dspace_6" in use_env:
        use_env["db_dspace_5"] = use_env["db_dspace_6"]
    # override settings with selected instance
    env.update(use_env)

    from pump._db import db, differ
    from pump._handle import handles
    from pump._bitstreamformatregistry import bitstreamformatregistry
    from pump._community import communities
    from pump._collection import collections
    from pump._registrationdata import registrationdatas
    from pump._userregistration import userregistrations
    from pump._item import items
    from pump._bundle import bundles
    from pump._bitstream import bitstreams

    raw_db_7 = db(env["db_dspace_7"])
    raw_db_old_key = "db_dspace_6" if "db_dspace_6" in use_env else \
        "db_dspace_5"
    raw_db_dspace_old = db(env[raw_db_old_key])

    diff = differ(raw_db_dspace_old, None, raw_db_7)

    diff.validate([handles.validate_table])
    diff.validate([bitstreamformatregistry.validate_table])
    diff.validate([communities.validate_table])
    diff.validate([collections.validate_table])
    diff.validate([registrationdatas.validate_table])
    diff.validate([userregistrations.validate_table])

    diff.validate([items.validate_table])
    diff.validate([bundles.validate_table])
    diff.validate([bitstreams.validate_table])
