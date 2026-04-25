"""Hive Switch Module."""

# pylint: disable=C0103,E1101

import logging

from .helper.const import HIVETOHA

_LOGGER = logging.getLogger(__name__)


class HiveSmartPlug:
    """Plug Device.

    Returns:
        object: Returns Plug object
    """

    plugType = "Switch"

    async def getState(self, device: dict):
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

    async def getPowerUsage(self, device: dict):
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

    async def setStatusOn(self, device: dict):
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
            _LOGGER.debug("setStatusOn - Turning plug ON for %s.", device.ha_name)
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device.hive_id]
            resp = await self.session.api.setState(
                data["type"], data["id"], status="ON"
            )
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device.hive_id)

        return final

    async def setStatusOff(self, device: dict):
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
            _LOGGER.debug("setStatusOff - Turning plug OFF for %s.", device.ha_name)
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device.hive_id]
            resp = await self.session.api.setState(
                data["type"], data["id"], status="OFF"
            )
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device.hive_id)

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

    async def getSwitch(self, device: dict):
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
                    "getSwitch - Returning cached state for switch %s (slow/busy poll).",
                    device.ha_name,
                )
                return cached
        device.device_data.update(
            {"online": await self.session.attr.onlineOffline(device.device_id)}
        )
        dev_data = {}

        if device.device_data["online"]:
            self.session.helper.deviceRecovered(device.device_id)
            _LOGGER.debug("getSwitch - Updating switch data for %s.", device.ha_name)
            data = self.session.data.devices[device.device_id]
            dev_data = {
                "hiveID": device.hive_id,
                "hiveName": device.hive_name,
                "hiveType": device.hive_type,
                "haName": device.ha_name,
                "haType": device.ha_type,
                "device_id": device.device_id,
                "device_name": device.device_name,
                "status": {
                    "state": await self.getSwitchState(device),
                },
                "deviceData": data.get("props", None),
                "parentDevice": data.get("parent", None),
                "custom": getattr(device, "custom", None),
                "attributes": {},
            }

            if device.hive_type == "activeplug":
                dev_data.update(
                    {
                        "status": {
                            "state": dev_data["status"]["state"],
                            "power_usage": await self.getPowerUsage(device),
                        },
                        "attributes": await self.session.attr.stateAttributes(
                            device.device_id, device.hive_type
                        ),
                    }
                )

            _LOGGER.debug(
                "getSwitch - Switch device data for %s: %s",
                device.ha_name,
                dev_data["status"],
            )

            return self.session.set_cached_device(device, dev_data)
        await self.session.helper.errorCheck(
            device.device_id, "ERROR", device.device_data["online"]
        )
        device.status = device.status or {"state": None}
        return device

    async def getSwitchState(self, device: dict):
        """Home Assistant wrapper to get updated switch state.

        Args:
            device (dict): Device to get state for

        Returns:
            boolean: Return True or False for the state.
        """
        if device.hive_type == "Heating_Heat_On_Demand":
            return await self.session.heating.getHeatOnDemand(device)
        return await self.getState(device)

    async def turnOn(self, device: dict):
        """Home Assisatnt wrapper for turning switch on.

        Args:
            device (dict): Device to switch on.

        Returns:
            function: Calls relevant function.
        """
        if device.hive_type == "Heating_Heat_On_Demand":
            return await self.session.heating.setHeatOnDemand(device, "ENABLED")
        return await self.setStatusOn(device)

    async def turnOff(self, device: dict):
        """Home Assisatnt wrapper for turning switch off.

        Args:
            device (dict): Device to switch off.

        Returns:
            function: Calls relevant function.
        """
        if device.hive_type == "Heating_Heat_On_Demand":
            return await self.session.heating.setHeatOnDemand(device, "DISABLED")
        return await self.setStatusOff(device)
