"""Start Hive Session."""
# pylint: skip-file
import sys
import traceback
from os.path import expanduser
from typing import Optional

from aiohttp import ClientSession
from loguru import logger

from .action import HiveAction
from .alarm import Alarm
from .camera import Camera
from .heating import Climate
from .hotwater import WaterHeater
from .hub import HiveHub
from .light import Light
from .plug import Switch
from .sensor import Sensor
from .session import HiveSession

debug = []
home = expanduser("~")
logger.add(
    home + "/pyhiveapi_debug.log", filter=lambda record: record["level"].name == "DEBUG"
)
logger.add(
    home + "/pyhiveapi_info.log", filter=lambda record: record["level"].name == "INFO"
)
logger.add(
    home + "/pyhiveapi_error.log", filter=lambda record: record["level"].name == "ERROR"
)


def exception_handler(exctype, value, tb):
    """Custom exception handler.

    Args:
        exctype ([type]): [description]
        value ([type]): [description]
        tb ([type]): [description]
    """
    last = len(traceback.extract_tb(tb)) - 1
    logger.error(
        f"-> \n"
        f"Error in {traceback.extract_tb(tb)[last].filename}\n"
        f"when running {traceback.extract_tb(tb)[last].name} function\n"
        f"on line {traceback.extract_tb(tb)[last].lineno} - "
        f"{traceback.extract_tb(tb)[last].line} \n"
        f"with vars {traceback.extract_tb(tb)[last].locals}"
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

                logger.debug(
                    f"Call to {func_name} on line {func_line_no} "
                    f"of {func_filename[1]} from line {caller_line_no} "
                    f"of {caller_filename[1]}"
                )
            elif event == "return":
                logger.debug(f"returning {arg}")

        return trace_debug


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
        self.camera = Camera(self.session)
        self.heating = Climate(self.session)
        self.hotwater = WaterHeater(self.session)
        self.hub = HiveHub(self.session)
        self.light = Light(self.session)
        self.switch = Switch(self.session)
        self.sensor = Sensor(self.session)
        self.logger = logger
        if debug:
            sys.settrace(trace_debug)

    def setDebugging(self, debugger: list):
        """Set function to debug.

        Args:
            debugger (list): a list of functions to debug

        Returns:
            object: Returns traceback object.
        """
        global debug
        debug = debugger
        if debug:
            return sys.settrace(trace_debug)
        return sys.settrace(None)
