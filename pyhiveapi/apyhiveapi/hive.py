"""Start Hive Session."""
from typing import Optional

from aiohttp import ClientSession

from .action import Action
from .heating import Heating
from .hotwater import Hotwater
from .hub import Hub
from .light import Light
from .plug import Plug
from .sensor import Sensor
from .session import Session


class Hive(Session):
    """Hive Class."""

    def __init__(
        self, websession: Optional[ClientSession] = None, username=None, password=None
    ):
        """Generate Hive Session."""
        super().__init__(username, password, websession)
        self.session = self
        self.action = Action(self.session)
        self.heating = Heating(self.session)
        self.hotwater = Hotwater(self.session)
        self.hub = Hub(self.session)
        self.light = Light(self.session)
        self.switch = Plug(self.session)
        self.sensor = Sensor(self.session)
