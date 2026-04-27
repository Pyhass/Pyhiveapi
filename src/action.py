"""Hive Action Module."""

import json
import logging

from .helper.const import HTTP_OK

_LOGGER = logging.getLogger(__name__)


class HiveAction:
    """Hive Action Code.

    Returns:
        object: Return hive action object.
    """

    action_type = "Actions"

    def __init__(self, session: object = None):
        """Initialise Action.

        Args:
            session (object, optional): session to interact with hive account. Defaults to None.
        """
        self.session = session

    async def get_action(self, device: dict):
        """Action device to update.

        Args:
            device (dict): Device to be updated.

        Returns:
            dict: Updated device.
        """
        if self.session.should_use_cached_data():
            cached = self.session.get_cached_device(device)
            if cached is not None:
                _LOGGER.debug(
                    "Returning cached state for action %s (slow/busy poll).",
                    device.ha_name,
                )
                return cached
        if device.hive_id in self.session.data.actions:
            device.status = {"state": await self.get_state(device)}
            device.device_data = {}
            return self.session.set_cached_device(device)
        return "REMOVE"

    async def get_state(self, device: dict):
        """Get action state.

        Args:
            device (dict): Device to get state of.

        Returns:
            str: Return state.
        """
        final = None

        try:
            data = self.session.data.actions[device.hive_id]
            final = data["enabled"]
        except KeyError as e:
            _LOGGER.error(e)

        return final

    async def _set_action_state(self, device: dict, enabled: bool) -> bool:
        """Set action enabled/disabled state.

        Args:
            device (dict): Device to set state of.
            enabled (bool): True to enable, False to disable.

        Returns:
            bool: True if successful.
        """
        final = False

        if device.hive_id in self.session.data.actions:
            _LOGGER.debug(
                "%s action %s.",
                "Enabling" if enabled else "Disabling",
                device.ha_name,
            )
            await self.session.hive_refresh_tokens()
            data = self.session.data.actions[device.hive_id].copy()
            data.update({"enabled": enabled})
            resp = await self.session.api.set_action(device.hive_id, json.dumps(data))
            if resp["original"] == HTTP_OK:
                final = True
                await self.session.get_devices(device.hive_id)

        return final

    async def set_status_on(self, device: dict):
        """Set action turn on.

        Args:
            device (dict): Device to set state of.

        Returns:
            bool: True if successful.
        """
        return await self._set_action_state(device, True)

    async def set_status_off(self, device: dict):
        """Set action to turn off.

        Args:
            device (dict): Device to set state of.

        Returns:
            bool: True if successful.
        """
        return await self._set_action_state(device, False)

    # Backwards-compatible camelCase aliases
    async def getAction(self, device: dict):  # pylint: disable=invalid-name
        """Backwards-compatible alias for get_action."""
        return await self.get_action(device)

    async def setStatusOn(self, device: dict):  # pylint: disable=invalid-name
        """Backwards-compatible alias for set_status_on."""
        return await self.set_status_on(device)

    async def setStatusOff(self, device: dict):  # pylint: disable=invalid-name
        """Backwards-compatible alias for set_status_off."""
        return await self.set_status_off(device)
