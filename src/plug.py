"""Hive Switch Module."""

import logging
from typing import Any

from .helper.const import HIVETOHA

_LOGGER = logging.getLogger(__name__)


class HiveSmartPlug:
    """Plug Device.

    Returns:
        object: Returns Plug object
    """

    session: Any
    plug_type = "Switch"

    async def get_state(self, device: dict):
        """Get smart plug state.

        Args:
            device (dict): Device to get the plug state for.

        Returns:
            boolean: Returns True or False based on if the plug is on
        """
        state = None

        try:
            data = self.session.data.products[device.hive_id]
            state = data["state"]["status"]
            state = HIVETOHA["Switch"].get(state, state)
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def get_power_usage(self, device: dict):
        """Get smart plug current power usage.

        Args:
            device (dict): [description]

        Returns:
            [type]: [description]
        """
        state = None

        try:
            data = self.session.data.products[device.hive_id]
            state = data["props"]["powerConsumption"]
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def set_status_on(self, device: dict):
        """Set smart plug to turn on.

        Args:
            device (dict): Device to switch on.

        Returns:
            boolean: True/False if successful
        """
        final = False

        if (
            device.hive_id in self.session.data.products
            and device.device_data["online"]
        ):
            _LOGGER.debug("set_status_on - Turning plug ON for %s.", device.ha_name)
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device.hive_id]
            resp = await self.session.api.set_state(
                data["type"], data["id"], status="ON"
            )
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device.hive_id)

        return final

    async def set_status_off(self, device: dict):
        """Set smart plug to turn off.

        Args:
            device (dict): Device to switch off.

        Returns:
            boolean: True/False if successful
        """
        final = False

        if (
            device.hive_id in self.session.data.products
            and device.device_data["online"]
        ):
            _LOGGER.debug("set_status_off - Turning plug OFF for %s.", device.ha_name)
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device.hive_id]
            resp = await self.session.api.set_state(
                data["type"], data["id"], status="OFF"
            )
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device.hive_id)

        return final


class Switch(HiveSmartPlug):
    """Home Assistant switch class.

    Args:
        SmartPlug (Class): Initialises the Smartplug Class.
    """

    def __init__(self, session: object):
        """Initialise switch.

        Args:
            session (object): This is the session object to interact with the current session.
        """
        self.session = session

    async def get_switch(self, device: dict):
        """Home assistant wrapper to get switch device.

        Args:
            device (dict): Device to be update.

        Returns:
            dict: Return device after update is complete.
        """
        if self.session.should_use_cached_data():
            cached = self.session.get_cached_device(device)
            if cached is not None:
                _LOGGER.debug(
                    "get_switch - Returning cached state for switch %s (slow/busy poll).",
                    device.ha_name,
                )
                return cached
        online = await self.session.attr.online_offline(device.device_id)
        if not isinstance(device.device_data, dict):
            device.device_data = {}
        device.device_data["online"] = online

        if device.device_data["online"]:
            self.session.helper.device_recovered(device.device_id)
            _LOGGER.debug("get_switch - Updating switch data for %s.", device.ha_name)
            data = self.session.data.devices[device.device_id]
            device.status = {"state": await self.get_switch_state(device)}
            props = data.get("props") or {}
            props["online"] = online
            device.device_data = props
            device.parent_device = data.get("parent", None)
            device.attributes = {}

            if device.hive_type == "activeplug":
                device.status["power_usage"] = await self.get_power_usage(device)
                device.attributes = await self.session.attr.state_attributes(
                    device.device_id, device.hive_type
                )

            _LOGGER.debug(
                "get_switch - Switch device data for %s: %s",
                device.ha_name,
                device.status,
            )

            return self.session.set_cached_device(device)
        await self.session.helper.error_check(
            device.device_id, "ERROR", device.device_data["online"]
        )
        device.status = device.status or {"state": None}
        return device

    async def get_switch_state(self, device: dict):
        """Home Assistant wrapper to get updated switch state.

        Args:
            device (dict): Device to get state for

        Returns:
            boolean: Return True or False for the state.
        """
        if device.hive_type == "Heating_Heat_On_Demand":
            return await self.session.heating.get_heat_on_demand(device)
        return await self.get_state(device)

    async def turn_on(self, device: dict):
        """Home Assisatnt wrapper for turning switch on.

        Args:
            device (dict): Device to switch on.

        Returns:
            function: Calls relevant function.
        """
        if device.hive_type == "Heating_Heat_On_Demand":
            return await self.session.heating.set_heat_on_demand(device, "ENABLED")
        return await self.set_status_on(device)

    async def turn_off(self, device: dict):
        """Home Assisatnt wrapper for turning switch off.

        Args:
            device (dict): Device to switch off.

        Returns:
            function: Calls relevant function.
        """
        if device.hive_type == "Heating_Heat_On_Demand":
            return await self.session.heating.set_heat_on_demand(device, "DISABLED")
        return await self.set_status_off(device)

    async def turnOn(self, device: dict):  # pylint: disable=invalid-name
        """Backwards-compatible alias for turn_on."""
        return await self.turn_on(device)

    async def turnOff(self, device: dict):  # pylint: disable=invalid-name
        """Backwards-compatible alias for turn_off."""
        return await self.turn_off(device)

    async def getSwitch(self, device: dict):  # pylint: disable=invalid-name
        """Backwards-compatible alias for get_switch."""
        return await self.get_switch(device)
