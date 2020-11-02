"""Custom Logging Module."""
import logging

from datetime import datetime
from .hive_data import Data

_LOGGER = logging.getLogger(__name__)


class Logger:
    """Custom Logging Code."""

    def __init__(self):
        """Logger Initialization"""

    @staticmethod
    async def check_debuging(enable_debug: list):
        """Check Logging Active"""

        if len(enable_debug) > 0:
            Data.d_enabled = True
        else:
            Data.d_enabled = False

        Data.d_list = enable_debug
        return Data.d_enabled

    @staticmethod
    async def log(n_id, l_type, new_message, **kwargs):
        """Output new log entry if logging is turned on."""
        product_data = Data.products.get(n_id, {})
        name = product_data.get("state", {}).get("name", n_id)
        data = kwargs.get("info", None)
        if n_id == "No_ID":
            name = "Hive"
        if "_" in l_type:
            nxt = l_type.split("_")
            for i in nxt:
                if i in Data.d_list or "All" in Data.d_list and l_type != "Extra":
                    break

        if Data.d_enabled and new_message is not None and any(elem in Data.d_list for elem in [l_type, 'All']):
            if l_type != "ERROR":
                _LOGGER.debug(new_message.format(data))

            try:
                l_file = open(Data.l_o_file, "a")
                l_file.write(
                    datetime.now().strftime("%d-%b-%Y %H:%M:%S")
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
        if error_type == False:
            message = "Device offline could not update entity."
            result = True
            if not Data.s_file:
                _LOGGER.warning(message)
        elif error_type == "Failed":
            message = "ERROR - No data found for device."
            result = True
            if not Data.s_file:
                _LOGGER.error(message)
        elif error_type == "Failed_API":
            new_data = str(kwargs.get("resp"))
            message = "ERROR - Received {0} response from API."
            result = True
            if not Data.s_file:
                _LOGGER.error(message.format(new_data))

        await self.log(n_id, n_type, message, info=new_data)
        return result
