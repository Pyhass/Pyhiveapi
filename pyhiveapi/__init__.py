"""__init__.py"""
from .const import *
from .helper import Hive_Helper
from .custom_logging import Logger
from .hive_session import Session
from .hive_auth_async import HiveAuthAsync
from .action import Action
from .client import Client
from .hive_api import Hive
from .device_attributes import Attributes
from .heating import Heating
from .hive_async_api import Hive_Async
from .hive_data import Data
from .hotwater import Hotwater
from .hub import Hub
from .light import Light
from .plug import Plug
from .sensor import Sensor


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
