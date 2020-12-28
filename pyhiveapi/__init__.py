"""__init__.py"""
from .hive import Hive
from .hive_session import Session
from .const import *
from .helper import HiveHelper
from .client import Client
from .hive_api import HiveApi
from .hive_async_api import HiveAsync
from .hive_auth_async import HiveAuthAsync


def getMessage(__message, __type):
    """
    Gets a message
    """
    from cryptography.fernet import Fernet
    import os
    import json

    __key = open(os.path.dirname(os.path.realpath(
        __file__)) + "/.info.key", "rb").read()
    __f = Fernet(__key)
    __result = __f.decrypt(__message).decode()

    if __type == "JSON":
        __result = json.loads(__result)
    return __result
