"""Custom Logging Module."""
import os
from datetime import datetime

from .hive_data import Data


class Logger:
    """Custom Logging Code."""

    def __init__(self):
        """Logger Initialization"""

    @staticmethod
    async def check_logging():
        """Check Logging Active"""
        Data.l_o_folder = os.path.expanduser("~") + "/pyhiveapi"
        Data.l_o_file = Data.l_o_folder + "/pyhiveapi.log"
        count = 0
        try:

            statinfo = os.stat(os.path.isfile(Data.l_o_file))
            if os.path.isfile(Data.l_o_file) and statinfo.st_size > 1048576:
                os.remove(Data.l_o_file)

            if os.path.isdir(Data.l_o_folder):
                for name in Data.l_files:
                    loc = Data.l_o_folder + "/" + Data.l_files[name]
                    if os.path.isfile(loc):
                        Data.l_values.update({name: True})
                        Data.l_values.update({"enabled": True})
                    elif os.path.isfile(loc) is False:
                        count += 1
                        if count == len(Data.l_files):
                            Data.l_values = {}
        except FileNotFoundError:
            Data.l_values = {}

    @staticmethod
    async def log(n_id, l_type, new_message, **kwargs):
        """Output new log entry if logging is turned on."""
        product_data = Data.products.get(n_id, {})
        name = product_data.get("state", {}).get("name", n_id)
        data = kwargs.get("info", None)
        values = Data.l_values
        if n_id == "No_ID":
            name = "Hive"
        final = False
        if "_" in l_type:
            nxt = l_type.split("_")
            for i in nxt:
                if i in Data.l_values or "All" in Data.l_values and l_type != "Extra":
                    if Data.l_values["enabled"]:
                        final = True
                        break
        elif l_type in values or "All" in values and l_type != "Extra":
            if Data.l_values["enabled"]:
                final = True
        elif l_type in values and Data.l_values["enabled"]:
            final = True

        if final and new_message is not None:
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
        elif error_type == "Failed":
            message = "ERROR - No data found for device."
            result = True
        elif error_type == "Failed_API":
            new_data = str(kwargs.get("resp"))
            message = "ERROR - Received {0} response from API."
            result = True
        await self.log(n_id, n_type, message, info=new_data)
        return result
