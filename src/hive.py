"""Start Hive Session."""

import asyncio
import logging
import sys
import traceback
from os.path import expanduser

from aiohttp import ClientSession

from .action import HiveAction
from .heating import Climate
from .hotwater import WaterHeater
from .hub import HiveHub
from .light import Light
from .plug import Switch
from .sensor import Sensor
from .session import HiveSession

_LOGGER = logging.getLogger(__name__)

debug: list[str] = []
home = expanduser("~")


def exception_handler(_exctype, _value, tb):
    """Custom exception handler.

    Args:
        exctype ([type]): [description]
        value ([type]): [description]
        tb ([type]): [description]
    """
    last = len(traceback.extract_tb(tb)) - 1
    tb_entry = traceback.extract_tb(tb)[last]
    _LOGGER.error(
        "-> \nError in %s\nwhen running %s function\non line %s - %s \nwith vars %s",
        tb_entry.filename,
        tb_entry.name,
        tb_entry.lineno,
        tb_entry.line,
        tb_entry.locals,
    )
    traceback.print_exc(tb)


sys.excepthook = exception_handler


def trace_debug(frame, event, arg):
    """Trace functions.

    Args:
        frame (object): The current frame being debugged.
        event (str): The event type
        arg (dict): arguments in debug function..

    Returns:
        object: returns itself as per tracing docs
    """
    if "pyhiveapi/" in str(frame):
        co = frame.f_code
        func_name = co.co_name
        func_line_no = frame.f_lineno
        if func_name in debug:
            if event == "call":
                func_filename = co.co_filename.rsplit("/", 1)
                caller = frame.f_back
                caller_line_no = caller.f_lineno
                caller_filename = caller.f_code.co_filename.rsplit("/", 1)

                _LOGGER.debug(
                    "Call to %s on line %s of %s from line %s of %s",
                    func_name,
                    func_line_no,
                    func_filename[1],
                    caller_line_no,
                    caller_filename[1],
                )
            elif event == "return":
                _LOGGER.debug("returning %s", arg)

    return trace_debug


class Hive(HiveSession):
    """Hive Class.

    Args:
        HiveSession (object): Interact with Hive Account
    """

    def __init__(
        self,
        websession: ClientSession | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        """Generate a Hive session.

        Args:
            websession (Optional[ClientSession], optional): Websession for API calls.
                Defaults to None.
            username (str, optional): This is the Hive username used for login. Defaults to None.
            password (str, optional): This is the Hive password used for login. Defaults to None.
        """
        super().__init__(username, password, websession)
        self.session = self
        self.action = HiveAction(self.session)
        self.heating = Climate(self.session)
        self.hotwater = WaterHeater(self.session)
        self.hub = HiveHub(self.session)
        self.light = Light(self.session)
        self.switch = Switch(self.session)
        self.sensor = Sensor(self.session)

        if debug:
            sys.settrace(trace_debug)

    def set_debugging(self, debugger: list):
        """Set function to debug.

        Args:
            debugger (list): a list of functions to debug

        Returns:
            object: Returns traceback object.
        """
        global debug  # pylint: disable=global-statement  # noqa: PLW0603
        debug = debugger
        if debug:
            return sys.settrace(trace_debug)
        return sys.settrace(None)

    async def force_update(self) -> bool:
        """Immediately poll the Hive API, bypassing the 2-minute interval.

        For power users only. If a poll is already in progress, skips and
        returns False. Otherwise polls and returns True on success.
        """
        if self.update_lock.locked():
            _LOGGER.debug("force_update called while poll in progress — skipping.")
            return False
        async with self.update_lock:
            self._update_task = asyncio.current_task()
            try:
                return await self._poll_devices()
            finally:
                self._update_task = None
