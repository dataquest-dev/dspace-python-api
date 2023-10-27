import json
import os
import logging
from datetime import datetime, timezone
from time import time as time_fnc
_logger = logging.getLogger("pump.utils")


def read_json(file_name: str):
    """
        Read data from file as json.
        @param file_name: file name
        @return: data as json
    """
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"File [{file_name}] does not exist.")
    with open(file_name, mode='r', encoding='utf-8') as f:
        return json.load(f)


def to_dict(arr: list):
    return {int(k): v for k, v in enumerate(arr)}


def ts() -> str:
    return str(datetime.now(timezone.utc))


def time_method(func):
    """
        Timer decorator will store execution time of a function into
        the class which it uses. The time will be stored in
        instance.timed
    """

    def _enclose(self, *args, **kw):
        """ Enclose every function with this one. """
        start = time_fnc()
        res = func(self, *args, **kw)
        took = time_fnc() - start
        _logger.info(f"Method [{func.__name__}] took [{round(took, 2)}] seconds.")
        return res

    return _enclose


def time_function(d):
    """
        Timer decorator will store execution time of a function into
        the specified dict to timed entry.
    """

    def wrap(func):
        """ Simple wrapper around time decorator. """

        def _enclose(*args, **kw):
            """ Simple wrapper around wrap :). """
            start = time_fnc()
            res = func(*args, **kw)
            took = time_fnc() - start
            _logger.debug(f"Function [{func.__name__}] took [{round(took, 2)}] seconds.")
            return res

        return _enclose

    return wrap


def serial_d(data):
    """
        Unify serialisation data.
    """
    return {
        "data": data,
        "timestamp": ts(),
    }


def serialize(file_str: str, data, sorted=True):
    """
        Serialize data into json file.
    """
    os.makedirs(os.path.dirname(file_str), exist_ok=True)
    with open(file_str, encoding="utf-8", mode="w") as fout:
        json.dump(serial_d(data), fout, indent=None, sort_keys=sorted)


def deserialize(file_str: str):
    with open(file_str, encoding="utf-8", mode="r") as fin:
        js = json.load(fin)
    return js["data"]


IMPORT_LIMIT = None
if os.environ.get("IMPORT_LIMIT", "0") != "0":
    IMPORT_LIMIT = int(os.environ["IMPORT_LIMIT"])
    _logger.critical(f"Using import limit [{IMPORT_LIMIT}]")
