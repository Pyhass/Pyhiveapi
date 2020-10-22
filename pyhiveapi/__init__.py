"""__init__.py"""
from .const import *
from .hive_session import Session
from .hiveauth import HiveAuth
from .action import Action
from .client import Client
from .custom_logging import Logger
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
from .weather import Weather


from cryptography.fernet import Fernet
import os
import json


def get_message(message, type):
    """
    Gets a message
    """
    key = open(os.path.dirname(os.path.realpath(__file__)) + "/.info.key", "rb").read()
    f = Fernet(key)
    result = f.decrypt(message).decode()

    if type == "JSON":
        result = json.loads(result)
    return result
