"""Hive Light Module."""

import colorsys
import logging
from typing import Any, Optional

from .helper.const import HIVETOHA

_LOGGER = logging.getLogger(__name__)


class HiveLight:
    """Hive Light Code.

    Returns:
        object: Hivelight
    """

    session: Any
    light_type = "Light"

    async def get_state(self, device: dict):
        """Get light current state.

        Args:
            device (dict): Device to get the state of.

        Returns:
            str: State of the light.
        """
        state = None
        final = None
        device_name = device.ha_name

        try:
            data = self.session.data.products[device.hive_id]
            state = data["state"]["status"]
            final = HIVETOHA[self.light_type].get(state, state)
        except KeyError as e:
            _LOGGER.error(
                "KeyError getting light state for %s: %s", device_name, str(e)
            )

        return final

    async def get_brightness(self, device: dict):
        """Get light current brightness.

        Args:
            device (dict): Device to get the brightness of.

        Returns:
            int: Brightness value.
        """
        state = None
        final = None
        device_name = device.ha_name

        try:
            data = self.session.data.products[device.hive_id]
            state = data["state"]["brightness"]
            final = (state / 100) * 255
        except KeyError as e:
            _LOGGER.error(
                "KeyError getting light brightness for %s: %s", device_name, str(e)
            )

        return final

    async def get_min_color_temp(self, device: dict):
        """Get light minimum color temperature.

        Args:
            device (dict): Device to get min colour temp for.

        Returns:
            int: Min color temperature.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device.hive_id]
            state = data["props"]["colourTemperature"]["max"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            _LOGGER.error(e)

        return final

    async def get_max_color_temp(self, device: dict):
        """Get light maximum color temperature.

        Args:
            device (dict): Device to get max colour temp for.

        Returns:
            int: Min color temperature.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device.hive_id]
            state = data["props"]["colourTemperature"]["min"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            _LOGGER.error(e)

        return final

    async def get_color_temp(self, device: dict):
        """Get light current color temperature.

        Args:
            device (dict): Device to get colour temp for.

        Returns:
            int: Current Color Temp.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device.hive_id]
            state = data["state"]["colourTemperature"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            _LOGGER.error(e)

        return final

    async def get_color(self, device: dict):
        """Get light current colour.

        Args:
            device (dict): Device to get color for.

        Returns:
            tuple: RGB values for the color.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device.hive_id]
            state = [
                (data["state"]["hue"]) / 360,
                (data["state"]["saturation"]) / 100,
                (data["state"]["value"]) / 100,
            ]
            final = tuple(
                int(i * 255) for i in colorsys.hsv_to_rgb(state[0], state[1], state[2])
            )
        except KeyError as e:
            _LOGGER.error(e)

        return final

    async def get_color_mode(self, device: dict):
        """Get Colour Mode.

        Args:
            device (dict): Device to get the color mode for.

        Returns:
            str: Colour mode.
        """
        state = None

        try:
            data = self.session.data.products[device.hive_id]
            state = data["state"]["colourMode"]
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def set_status_off(self, device: dict):
        """Set light to turn off.

        Args:
            device (dict): Device to turn off.

        Returns:
            boolean: True/False if successful
        """
        device_name = device.ha_name
        _LOGGER.info("Turning off light %s", device_name)

        await self.session.hive_refresh_tokens()
        final = False

        if (
            device.hive_id in self.session.data.products
            and device.device_data["online"]
        ):
            _LOGGER.debug(
                "set_status_off - Device %s is online, proceeding with turn off",
                device_name,
            )
            data = self.session.data.products[device.hive_id]
            resp = await self.session.api.set_state(
                data["type"], device.hive_id, status="OFF"
            )

            if resp["original"] == 200:
                _LOGGER.debug(
                    "set_status_off - Light turned off successfully for %s, refreshing device data",
                    device_name,
                )
                await self.session.get_devices(device.hive_id)
                final = True
            else:
                _LOGGER.error(
                    "Failed to turn off light %s, response: %s",
                    device_name,
                    resp["original"],
                )
        else:
            _LOGGER.warning(
                "Device %s not found or offline, cannot turn off", device_name
            )

        return final

    async def set_status_on(self, device: dict):
        """Set light to turn on.

        Args:
            device (dict): Device to turn on.

        Returns:
            boolean: True/False if successful
        """
        device_name = device.ha_name
        _LOGGER.info("Turning on light %s", device_name)

        await self.session.hive_refresh_tokens()
        final = False

        if (
            device.hive_id in self.session.data.products
            and device.device_data["online"]
        ):
            _LOGGER.debug(
                "set_status_on - Device %s is online, proceeding with turn on",
                device_name,
            )
            data = self.session.data.products[device.hive_id]
            resp = await self.session.api.set_state(
                data["type"], device.hive_id, status="ON"
            )

            if resp["original"] == 200:
                _LOGGER.debug(
                    "set_status_on - Light turned on successfully for %s, refreshing device data",
                    device_name,
                )
                await self.session.get_devices(device.hive_id)
                final = True
            else:
                _LOGGER.error(
                    "Failed to turn on light %s, response: %s",
                    device_name,
                    resp["original"],
                )
        else:
            _LOGGER.warning(
                "Device %s not found or offline, cannot turn on", device_name
            )

        return final

    async def set_brightness(self, device: dict, n_brightness: int):
        """Set brightness of the light.

        Args:
            device (dict): Device to set brightness of.
            n_brightness (int): Brightness value to set the light to.

        Returns:
            boolean: True/False if successful
        """
        device_name = device.ha_name
        _LOGGER.info("Setting brightness to %s for light %s", n_brightness, device_name)

        await self.session.hive_refresh_tokens()
        final = False

        if (
            device.hive_id in self.session.data.products
            and device.device_data["online"]
        ):
            _LOGGER.debug(
                "set_brightness - Device %s is online, proceeding with brightness change",
                device_name,
            )
            data = self.session.data.products[device.hive_id]
            resp = await self.session.api.set_state(
                data["type"], device.hive_id, status="ON", brightness=n_brightness
            )

            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device.hive_id)

        return final

    async def set_color_temp(self, device: dict, color_temp: int):
        """Set light to turn on.

        Args:
            device (dict): Device to set color temp for.
            color_temp (int): Color temp value.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device.hive_id in self.session.data.products
            and device.device_data["online"]
        ):
            _LOGGER.debug(
                "set_color_temp - Setting colour temperature to %s for %s.",
                color_temp,
                device.ha_name,
            )
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device.hive_id]

            if data["type"] == "tuneablelight":
                resp = await self.session.api.set_state(
                    data["type"],
                    device.hive_id,
                    colourTemperature=color_temp,
                )
            else:
                resp = await self.session.api.set_state(
                    data["type"],
                    device.hive_id,
                    colourMode="WHITE",
                    colourTemperature=color_temp,
                )

            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device.hive_id)

        return final

    async def set_color(self, device: dict, new_color: list):
        """Set light to turn on.

        Args:
            device (dict): Device to set color for.
            new_color (list): HSV value to set the light to.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device.hive_id in self.session.data.products
            and device.device_data["online"]
        ):
            _LOGGER.debug(
                "set_color - Setting colour to %s for %s.", new_color, device.ha_name
            )
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device.hive_id]

            resp = await self.session.api.set_state(
                data["type"],
                device.hive_id,
                colourMode="COLOUR",
                hue=str(new_color[0]),
                saturation=str(new_color[1]),
                value=str(new_color[2]),
            )
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device.hive_id)

        return final


class Light(HiveLight):
    """Home Assistant Light Code.

    Args:
        HiveLight (object): HiveLight Code.
    """

    def __init__(self, session: object = None):
        """Initialise light.

        Args:
            session (object, optional): Used to interact with the hive account. Defaults to None.
        """
        self.session = session

    async def get_light(self, device: dict):
        """Get light data.

        Args:
            device (dict): Device to update.

        Returns:
            dict: Updated device.
        """
        if self.session.should_use_cached_data():
            cached = self.session.get_cached_device(device)
            if cached is not None:
                _LOGGER.debug(
                    "get_light - Returning cached state for light %s (slow/busy poll).",
                    device.ha_name,
                )
                return cached
        online = await self.session.attr.online_offline(device.device_id)
        if not isinstance(device.device_data, dict):
            device.device_data = {}
        device.device_data["online"] = online

        if device.device_data["online"]:
            self.session.helper.device_recovered(device.device_id)
            _LOGGER.debug("get_light - Updating light data for %s.", device.ha_name)
            data = self.session.data.devices[device.device_id]
            device.status = {
                "state": await self.get_state(device),
                "brightness": await self.get_brightness(device),
            }
            props = data.get("props") or {}
            props["online"] = online
            device.device_data = props
            device.parent_device = data.get("parent", None)
            device.attributes = await self.session.attr.state_attributes(
                device.device_id, device.hive_type
            )

            if device.hive_type in ("tuneablelight", "colourtuneablelight"):
                device.status["color_temp"] = await self.get_color_temp(device)
            if device.hive_type == "colourtuneablelight":
                mode = await self.get_color_mode(device)
                device.status["mode"] = mode
                if mode == "COLOUR":
                    device.status["hs_color"] = await self.get_color(device)

            _LOGGER.debug(
                "get_light - Light device data for %s: %s",
                device.ha_name,
                device.status,
            )

            return self.session.set_cached_device(device)
        await self.session.helper.error_check(
            device.device_id, "ERROR", device.device_data["online"]
        )
        device.status = device.status or {"state": None}
        return device

    async def turn_on(
        self,
        device: dict,
        brightness: Optional[int],
        color_temp: Optional[int],
        color: Optional[list],
    ):
        """Set light to turn on.

        Args:
            device (dict): Device to turn on
            brightness (int): Brightness value to set the light to.
            color_temp (int): Color Temp value to set the light to.
            color (list): colour values to set the light to.

        Returns:
            boolean: True/False if successful.
        """
        if brightness is not None:
            return await self.set_brightness(device, brightness)
        if color_temp is not None:
            return await self.set_color_temp(device, color_temp)
        if color is not None:
            return await self.set_color(device, color)

        return await self.set_status_on(device)

    async def turn_off(self, device: dict):
        """Set light to turn off.

        Args:
            device (dict): Device to be turned off.

        Returns:
            boolean: True/False if successful.
        """
        return await self.set_status_off(device)

    async def turnOn(
        self, device: dict, brightness: int, color_temp: int, color: list
    ):  # pylint: disable=invalid-name
        """Backwards-compatible alias for turn_on."""
        return await self.turn_on(device, brightness, color_temp, color)

    async def turnOff(self, device: dict):  # pylint: disable=invalid-name
        """Backwards-compatible alias for turn_off."""
        return await self.turn_off(device)

    async def getLight(self, device: dict):  # pylint: disable=invalid-name
        """Backwards-compatible alias for get_light."""
        return await self.get_light(device)
