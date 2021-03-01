"""Custom Logging Module."""
import inspect
import logging
from datetime import datetime


class Logger:
    """Custom Logging Code."""

    LOGGER = logging.getLogger(__name__)

    def __init__(self, session=None):
        """Initialise the logger class."""
        self.debugOutFolder = ""
        self.debugOutFile = ""
        self.debugEnabled = False
        self.debugList = []
        self.session = session

    async def checkDebugging(self, enable_debug: list):
        """Check Logging Active."""
        if len(enable_debug) > 0:
            self.debugEnabled = True
        else:
            self.debugEnabled = False

        self.debugList = enable_debug
        return self.debugEnabled

    async def log(self, n_id, l_type, new_message, **kwargs):
        """Output new log entry if logging is turned on."""
        name = self.session.helper.getDeviceName(n_id) + " - "
        data = kwargs.get("info", [])
        if "_" in l_type:
            nxt = l_type.split("_")
            for i in nxt:
                if i != "Extra":
                    if i in self.debugList and "Extra" in self.debugList:
                        l_type = i
                        break

        if (
            self.debugEnabled
            and new_message is not None
            and any(elem in self.debugList for elem in [l_type, "All"])
        ):
            if l_type != "ERROR":
                logging_data = name + new_message.format(*data)
                self.session.log.debug(logging_data)

            try:
                l_file = open(self.debugOutFile, "a")
                l_file.write(
                    datetime.now().strftime("%d-%b-%Y %H:%M:%S")
                    + " - "
                    + l_type
                    + " - "
                    + name
                    + " : "
                    + new_message.format(*data)
                    + "\n"
                )
                l_file.close()
            except FileNotFoundError:
                pass
        else:
            pass

    async def error(self, e="UNKNOWN"):
        """Process and unexpected error."""
        self.session.log.error(
            f"An unexpected error has occurred whilst"
            f" executing {inspect.stack()[1][3]}"
            f" with exception {e.__class__} {e}"
        )

    async def error_check(self, n_id, n_type, error_type, **kwargs):
        """Error has occurred."""
        message = None
        new_data = None
        result = False
        name = self.session.helper.getDeviceName(n_id)

        if error_type is False:
            message = "Device offline could not update entity - " + name
            result = True
            if n_id not in self.session.config.errorList:
                self.session.log.warning(message)
                self.session.config.errorList.update({n_id: datetime.now()})
        elif error_type == "Failed":
            message = "ERROR - No data found for device - " + name
            result = True
            if n_id not in self.session.config.errorList:
                self.session.log.error(message)
                self.session.config.errorList.update({n_id: datetime.now()})

        await self.log(n_id, n_type, message, info=[new_data])
        return result
