"""Hive Light Module."""

import colorsys

from .helper.const import HIVETOHA


class HiveLight:
    """Hive Light Code.

    Returns:
        object: Hivelight
    """

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

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["state"]["status"]
            final = HIVETOHA[self.light_type].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

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

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["state"]["brightness"]
            final = (state / 100) * 255
        except KeyError as e:
            await self.session.log.error(e)

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
            data = self.session.data.products[device["hive_id"]]
            state = data["props"]["colourTemperature"]["max"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            await self.session.log.error(e)

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
            data = self.session.data.products[device["hive_id"]]
            state = data["props"]["colourTemperature"]["min"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            await self.session.log.error(e)

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
            data = self.session.data.products[device["hive_id"]]
            state = data["state"]["colourTemperature"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            await self.session.log.error(e)

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
            data = self.session.data.products[device["hive_id"]]
            state = [
                (data["state"]["hue"]) / 360,
                (data["state"]["saturation"]) / 100,
                (data["state"]["value"]) / 100,
            ]
            final = tuple(
                int(i * 255) for i in colorsys.hsv_to_rgb(state[0], state[1], state[2])
            )
        except KeyError as e:
            await self.session.log.error(e)

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
            data = self.session.data.products[device["hive_id"]]
            state = data["state"]["colourMode"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def set_status_off(self, device: dict):
        """Set light to turn off.

        Args:
            device (dict): Device to turn off.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device["hive_id"]]
            resp = await self.session.api.set_state(
                data["type"], device["hive_id"], status="OFF"
            )

            if resp["original"] == 200:
                final = True
                await self.session.get_devices()

        return final

    async def set_status_on(self, device: dict):
        """Set light to turn on.

        Args:
            device (dict): Device to turn on.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device["hive_id"]]

            resp = await self.session.api.set_state(
                data["type"], device["hive_id"], status="ON"
            )
            if resp["original"] == 200:
                final = True
                await self.session.get_devices()

        return final

    async def set_brightness(self, device: dict, n_brightness: int):
        """Set brightness of the light.

        Args:
            device (dict): Device to set brightness for.
            n_brightness (int): Brightness value

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device["hive_id"]]
            resp = await self.session.api.set_state(
                data["type"],
                device["hive_id"],
                status="ON",
                brightness=n_brightness,
            )
            if resp["original"] == 200:
                final = True
                await self.session.get_devices()

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
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device["hive_id"]]

            if data["type"] == "tuneablelight":
                resp = await self.session.api.set_state(
                    data["type"],
                    device["hive_id"],
                    colourTemperature=color_temp,
                )
            else:
                resp = await self.session.api.set_state(
                    data["type"],
                    device["hive_id"],
                    colourMode="WHITE",
                    colourTemperature=color_temp,
                )

            if resp["original"] == 200:
                final = True
                await self.session.get_devices()

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
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device["hive_id"]]

            resp = await self.session.api.set_state(
                data["type"],
                device["hive_id"],
                colourMode="COLOUR",
                hue=str(new_color[0]),
                saturation=str(new_color[1]),
                value=str(new_color[2]),
            )
            if resp["original"] == 200:
                final = True
                await self.session.get_devices()

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
        device["device_data"].update(
            {"online": await self.session.attr.online_offline(device["device_id"])}
        )
        dev_data = {}

        if device["device_data"]["online"]:
            self.session.helper.device_recovered(device["device_id"])
            data = self.session.data.devices[device["device_id"]]
            dev_data = {
                "hive_id": device["hive_id"],
                "hive_name": device["hive_name"],
                "hive_type": device["hive_type"],
                "ha_name": device["ha_name"],
                "ha_type": device["ha_type"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "status": {
                    "state": await self.get_state(device),
                    "brightness": await self.get_brightness(device),
                },
                "device_data": data.get("props", None),
                "parent_device": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.session.attr.state_attributes(
                    device["device_id"], device["hive_type"]
                ),
            }

            if device["hive_type"] in ("tuneablelight", "colourtuneablelight"):
                dev_data.update(
                    {
                        "min_mireds": await self.get_min_color_temp(device),
                        "max_mireds": await self.get_max_color_temp(device),
                    }
                )
                dev_data["status"].update(
                    {"color_temp": await self.get_color_temp(device)}
                )
            if device["hive_type"] == "colourtuneablelight":
                mode = await self.get_color_mode(device)
                if mode == "COLOUR":
                    dev_data["status"].update(
                        {
                            "hs_color": await self.get_color(device),
                            "mode": await self.get_color_mode(device),
                        }
                    )
                else:
                    dev_data["status"].update(
                        {
                            "mode": await self.get_color_mode(device),
                        }
                    )

            self.session.devices.update({device["hive_id"]: dev_data})
            return self.session.devices[device["hive_id"]]

        await self.session.log.error_check(
            device["device_id"], device["device_data"]["online"]
        )
        return device

    async def turn_on(self, device: dict, brightness: int, color_temp: int, color: list):
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
