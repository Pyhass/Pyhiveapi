"""Hive Hub Module."""

import logging
from typing import Any

from ..helper.const import HIVETOHA
from ..helper.device_handler_base import BaseDeviceHandler
from ..helper.hivedataclasses import Device

_LOGGER = logging.getLogger(__name__)


class HiveHub(BaseDeviceHandler):
    """Hive hub.

    Returns:
        object: Returns a hub object.
    """

    hub_type = "Hub"
    log_type = "Sensor"

    def __init__(self, session: Any = None):
        """Initialise hub.

        Args:
            session (object, optional): session to interact with Hive account. Defaults to None.
        """
        self.session = session

    async def get_smoke_status(self, device: Device):
        """Get the hub smoke status.

        Args:
            device (dict): device to get status for

        Returns:
            str: Return smoke status.
        """
        _LOGGER.debug("get_smoke_status - Getting smoke status for %s", device.hive_id)
        state = self._get_product_state(
            device, "props", "sensors", "SMOKE_CO", "active"
        )
        if state is None:
            _LOGGER.debug(
                "get_smoke_status - No smoke state found for %s", device.hive_id
            )
            return None
        result = HIVETOHA[self.hub_type]["Smoke"].get(state, state)
        _LOGGER.debug("get_smoke_status - %s smoke status: %s", device.hive_id, result)
        return result

    async def get_dog_bark_status(self, device: Device):
        """Get dog bark status.

        Args:
            device (dict): Device to get status for.

        Returns:
            str: Return status.
        """
        _LOGGER.debug(
            "get_dog_bark_status - Getting dog bark status for %s", device.hive_id
        )
        state = self._get_product_state(
            device, "props", "sensors", "DOG_BARK", "active"
        )
        if state is None:
            _LOGGER.debug(
                "get_dog_bark_status - No dog bark state found for %s", device.hive_id
            )
            return None
        result = HIVETOHA[self.hub_type]["Dog"].get(state, state)
        _LOGGER.debug(
            "get_dog_bark_status - %s dog bark status: %s", device.hive_id, result
        )
        return result

    async def get_glass_break_status(self, device: Device):
        """Get the glass detected status from the Hive hub.

        Args:
            device (dict): Device to get status for.

        Returns:
            str: Return status.
        """
        _LOGGER.debug(
            "get_glass_break_status - Getting glass break status for %s", device.hive_id
        )
        state = self._get_product_state(
            device, "props", "sensors", "GLASS_BREAK", "active"
        )
        if state is None:
            _LOGGER.debug(
                "get_glass_break_status - No glass break state found for %s",
                device.hive_id,
            )
            return None
        result = HIVETOHA[self.hub_type]["Glass"].get(state, state)
        _LOGGER.debug(
            "get_glass_break_status - %s glass break status: %s", device.hive_id, result
        )
        return result
