"""Start Hive Session."""
from typing import Optional

from aiohttp import ClientSession

from .action import HiveAction
from .alarm import Alarm
from .heating import Climate
from .hotwater import WaterHeater
from .hub import HiveHub
from .light import Light
from .plug import Switch
from .sensor import Sensor
from .session import HiveSession


class Hive(HiveSession):
    """Hive Class.

    Args:
        HiveSession (object): Interact with Hive Account
    """

    def __init__(
        self,
        websession: Optional[ClientSession] = None,
        username: str = None,
        password: str = None,
    ):
        """Generate a Hive session.

        Args:
            websession (Optional[ClientSession], optional): This is a websession that can be used for the api. Defaults to None.
            username (str, optional): This is the Hive username used for login. Defaults to None.
            password (str, optional): This is the Hive password used for login. Defaults to None.
        """
        super().__init__(username, password, websession)
        self.session = self
        self.action = HiveAction(self.session)
        self.alarm = Alarm(self.session)
        self.heating = Climate(self.session)
        self.hotwater = WaterHeater(self.session)
        self.hub = HiveHub(self.session)
        self.light = Light(self.session)
        self.switch = Switch(self.session)
        self.sensor = Sensor(self.session)
