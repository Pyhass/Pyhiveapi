"""Custom Logging Module."""
import logging

from datetime import datetime
from .hive_data import Data
from .helper import HiveHelper

_LOGGER = logging.getLogger(__name__)


class Logger:
    """Custom Logging Code."""

    @staticmethod
    async def checkDebugging(enable_debug: list):
        """Check Logging Active"""

        if len(enable_debug) > 0:
            Data.debugEnabled = True
        else:
            Data.debugEnabled = False

        Data.debugList = enable_debug
        return Data.debugEnabled

    @staticmethod
    async def log(n_id, l_type, new_message, **kwargs):
        """Output new log entry if logging is turned on."""
        name = HiveHelper.get_device_name(n_id) + ' - '
        data = kwargs.get("info", [])
        if "_" in l_type:
            nxt = l_type.split("_")
            for i in nxt:
                if i != "Extra":
                    if i in Data.debugList and "Extra" in Data.debugList:
                        l_type = i
                        break

        if Data.debugEnabled and new_message is not None and any(elem in Data.debugList for elem in [l_type, 'All']):
            if l_type != "ERROR":
                logging_data = name + new_message.format(*data)
                _LOGGER.debug(logging_data)

            try:
                l_file = open(Data.debugOutFile, "a")
                l_file.write(
                    datetime.now().strftime(
                        "%d-%b-%Y %H:%M:%S")
                    + " - "
                    + l_type
                    + " - "
                    + name
                    + " : "
                    + new_message.format(data)
                    + "\n"
                )
                l_file.close()
            except FileNotFoundError:
                pass
        else:
            pass

    async def error_check(self, n_id, n_type, error_type, **kwargs):
        """Error has occurred."""
        message = None
        new_data = None
        result = False
        name = HiveHelper.get_device_name(n_id)

        if error_type == False:
            message = "Device offline could not update entity - " + name
            result = True
            if n_id not in Data.errorList:
                _LOGGER.warning(message)
                Data.errorList.update({n_id: datetime.now()})
        elif error_type == "Failed":
            message = "ERROR - No data found for device - " + name
            result = True
            if n_id not in Data.errorList:
                _LOGGER.error(message)
                Data.errorList.update({n_id: datetime.now()})
        elif error_type == "Failed_API":
            new_data = str(kwargs.get("resp"))
            message = "ERROR - Received {0} response from API."
            result = True
            _LOGGER.error(message.format(new_data))

        await self.log(n_id, n_type, message, info=[new_data])
        return result
