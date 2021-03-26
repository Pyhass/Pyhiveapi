"""Custom Logging Module."""

import inspect
from datetime import datetime


class Logger:
    """Custom Logging Code."""

    def __init__(self, session=None):
        """Initialise the logger class."""
        self.session = session

    async def error(self, e="UNKNOWN"):
        """Process and unexpected error."""
        self.session.logger.error(
            f"An unexpected error has occurred whilst"
            f" executing {inspect.stack()[1][3]}"
            f" with exception {e.__class__} {e}"
        )

    async def errorCheck(self, n_id, n_type, error_type, **kwargs):
        """Error has occurred."""
        message = None
        name = self.session.helper.getDeviceName(n_id)

        if error_type is False:
            message = "Device offline could not update entity - " + name
            if n_id not in self.session.config.errorList:
                self.session.logger.warning(message)
                self.session.config.errorList.update({n_id: datetime.now()})
        elif error_type == "Failed":
            message = "ERROR - No data found for device - " + name
            if n_id not in self.session.config.errorList:
                self.session.logger.error(message)
                self.session.config.errorList.update({n_id: datetime.now()})
