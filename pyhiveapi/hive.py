from typing import Optional
from aiohttp import ClientSession
from .hive_data import Data


from .hive_session import Session
from .action import Action
from .heating import Heating
from .hotwater import Hotwater
from .hub import Hub
from .light import Light
from .plug import Plug
from .sensor import Sensor


class Hive:
    """Hive Class."""

    def __init__(self, websession: Optional[ClientSession] = None) -> None:
        Data.haWebsession = websession
        self.session = Session()
        self.action = Action()
        self.heating = Heating()
        self.hotwater = Hotwater()
        self.hub = Hub()
        self.light = Light()
        self.switch = Plug()
        self.sensor = Sensor()
        self.devices = {}
