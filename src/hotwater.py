"""Hive Hotwater Module."""

import logging
from typing import Any

from .helper.const import HIVETOHA

_LOGGER = logging.getLogger(__name__)


class HiveHotwater:
    """Hive Hotwater Code.

    Returns:
        object: Hotwater Object.
    """

    session: Any
    hotwater_type = "Hotwater"

    async def get_mode(self, device: dict):
        """Get hotwater current mode.

        Args:
            device (dict): Device to get the mode for.

        Returns:
            str: Return mode.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device.hive_id]
            state = data["state"]["mode"]
            if state == "BOOST":
                state = data["props"]["previous"]["mode"]
            final = HIVETOHA[self.hotwater_type].get(state, state)
        except KeyError as e:
            _LOGGER.error(e)

        return final

    @staticmethod
    async def get_operation_modes():
        """Get heating list of possible modes.

        Returns:
            list: Return list of operation modes.
        """
        return ["SCHEDULE", "ON", "OFF"]

    async def get_boost(self, device: dict):
        """Get hot water current boost status.

        Args:
            device (dict): Device to get boost status for

        Returns:
            str: Return boost status.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device.hive_id]
            state = data["state"]["boost"]
            final = HIVETOHA["Boost"].get(state, "ON")
        except KeyError as e:
            _LOGGER.error(e)

        return final

    async def get_boost_time(self, device: dict):
        """Get hotwater boost time remaining.

        Args:
            device (dict): Device to get boost time for.

        Returns:
            str: Return time remaining on the boost.
        """
        state = None
        if await self.get_boost(device) == "ON":
            try:
                data = self.session.data.products[device.hive_id]
                state = data["state"]["boost"]
            except KeyError as e:
                _LOGGER.error(e)

        return state

    async def get_state(self, device: dict):
        """Get hot water current state.

        Args:
            device (dict): Device to get the state for.

        Returns:
            str: return state of device.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device.hive_id]
            state = data["state"]["status"]
            mode_current = await self.get_mode(device)
            if mode_current == "SCHEDULE":
                if await self.get_boost(device) == "ON":
                    state = "ON"
                else:
                    snan = self.session.helper.get_schedule_nnl(
                        data["state"]["schedule"]
                    )
                    state = snan["now"]["value"]["status"]

            final = HIVETOHA[self.hotwater_type].get(state, state)
        except KeyError as e:
            _LOGGER.error(e)

        return final

    async def set_mode(self, device: dict, new_mode: str):
        """Set hot water mode.

        Args:
            device (dict): device to update mode.
            new_mode (str): Mode to set the device to.

        Returns:
            boolean: return True/False if boost was successful.
        """
        final = False

        if device.hive_id in self.session.data.products:
            _LOGGER.debug(
                "set_mode - Setting hot water mode to %s for %s.",
                new_mode,
                device.ha_name,
            )
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device.hive_id]
            resp = await self.session.api.set_state(
                data["type"], device.hive_id, mode=new_mode
            )
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device.hive_id)

        return final

    async def set_boost_on(self, device: dict, mins: int):
        """Turn hot water boost on.

        Args:
            device (dict): Deice to boost.
            mins (int): Number of minutes to boost it for.

        Returns:
            boolean: return True/False if boost was successful.
        """
        final = False

        if (
            int(mins) > 0
            and device.hive_id in self.session.data.products
            and device.device_data["online"]
        ):
            _LOGGER.debug(
                "set_boost_on - Setting hot water boost ON for %s: %s mins.",
                device.ha_name,
                mins,
            )
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device.hive_id]
            resp = await self.session.api.set_state(
                data["type"], device.hive_id, mode="BOOST", boost=mins
            )
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device.hive_id)

        return final

    async def set_boost_off(self, device: dict):
        """Turn hot water boost off.

        Args:
            device (dict): device to set boost off

        Returns:
            boolean: return True/False if boost was successful.
        """
        final = False

        if (
            device.hive_id in self.session.data.products
            and await self.get_boost(device) == "ON"
            and device.device_data["online"]
        ):
            _LOGGER.debug(
                "set_boost_off - Setting hot water boost OFF for %s.", device.ha_name
            )
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device.hive_id]
            prev_mode = data["props"]["previous"]["mode"]
            resp = await self.session.api.set_state(
                data["type"], device.hive_id, mode=prev_mode
            )
            if resp["original"] == 200:
                await self.session.get_devices(device.hive_id)
                final = True

        return final


class WaterHeater(HiveHotwater):
    """Water heater class.

    Args:
        Hotwater (object): Hotwater class.
    """

    def __init__(self, session: object = None):
        """Initialise water heater.

        Args:
            session (object, optional): Session to interact with account. Defaults to None.
        """
        self.session = session

    async def get_water_heater(self, device: dict):
        """Update water heater device.

        Args:
            device (dict): device to update.

        Returns:
            dict: Updated device.
        """
        if self.session.should_use_cached_data():
            cached = self.session.get_cached_device(device)
            if cached is not None:
                _LOGGER.debug(
                    "get_water_heater - Returning cached state for"
                    " water heater %s (slow/busy poll).",
                    device.ha_name,
                )
                return cached
        device.device_data.update(
            {"online": await self.session.attr.online_offline(device.device_id)}
        )

        if device.device_data["online"]:

            dev_data = {}
            self.session.helper.device_recovered(device.device_id)
            _LOGGER.debug(
                "get_water_heater - Updating hot water data for %s.", device.ha_name
            )
            data = self.session.data.devices[device.device_id]
            dev_data = {
                "hiveID": device.hive_id,
                "hiveName": device.hive_name,
                "hiveType": device.hive_type,
                "haName": device.ha_name,
                "haType": device.ha_type,
                "device_id": device.device_id,
                "device_name": device.device_name,
                "status": {"current_operation": await self.get_mode(device)},
                "deviceData": data.get("props", None),
                "parentDevice": data.get("parent", None),
                "custom": getattr(device, "custom", None),
                "attributes": await self.session.attr.state_attributes(
                    device.device_id, device.hive_type
                ),
            }

            _LOGGER.debug(
                "get_water_heater - Water heater device data for %s: %s",
                device.ha_name,
                dev_data["status"],
            )

            return self.session.set_cached_device(device, dev_data)
        await self.session.helper.error_check(
            device.device_id, "ERROR", device.device_data["online"]
        )
        device.status = device.status or {"current_operation": None}
        return device

    async def get_schedule_now_next_later(self, device: dict):
        """Hive get hotwater schedule now, next and later.

        Args:
            device (dict): device to get schedule for.

        Returns:
            dict: return now, next and later schedule.
        """
        state = None

        try:
            mode_current = await self.get_mode(device)
            if mode_current == "SCHEDULE":
                data = self.session.data.products[device.hive_id]
                state = self.session.helper.get_schedule_nnl(data["state"]["schedule"])
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def setMode(
        self, device: dict, new_mode: str
    ):  # pylint: disable=invalid-name
        """Backwards-compatible alias for set_mode."""
        return await self.set_mode(device, new_mode)

    async def setBoostOn(self, device: dict, mins: int):  # pylint: disable=invalid-name
        """Backwards-compatible alias for set_boost_on."""
        return await self.set_boost_on(device, mins)

    async def setBoostOff(self, device: dict):  # pylint: disable=invalid-name
        """Backwards-compatible alias for set_boost_off."""
        return await self.set_boost_off(device)

    async def getWaterHeater(self, device: dict):  # pylint: disable=invalid-name
        """Backwards-compatible alias for get_water_heater."""
        return await self.get_water_heater(device)
