"""Custom Logging Module."""

import inspect
from datetime import datetime


class Logger:
    """Custom Logging Code."""

    def __init__(self, session=None):
        """Initialise the logger class."""
        self.session = session

    async def error(self, e: Exception = Exception("UNKNOWN")) -> None:
        """Process an unexpected error."""
        self.session.logger.error(
            "An unexpected error has occurred whilst "
            "executing %s with exception %s %s",
            inspect.stack()[1][3],
            e.__class__,
            e,
        )

    async def error_check(self, n_id: str, error_type: bool) -> None:
        """Error has occurred."""
        message = None
        name = self.session.helper.get_device_name(n_id)

        if error_type is False:
            message = "Device offline could not update entity - " + name
            if n_id not in self.session.config.error_list:
                self.session.logger.warning(message)
                self.session.config.error_list.update({n_id: datetime.now()})
        elif error_type == "Failed":
            message = "ERROR - No data found for device - " + name
            if n_id not in self.session.config.error_list:
                self.session.logger.error(message)
                self.session.config.error_list.update({n_id: datetime.now()})
