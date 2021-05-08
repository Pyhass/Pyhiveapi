"""Hive Light Module."""
import colorsys

from .helper.const import HIVETOHA


class HiveLight:
    """Hive Light Code.

    Returns:
        object: Hivelight
    """

    lightType = "Light"

    async def getState(self, device: dict):
        """Get light current state.

        Args:
            device (dict): Device to get the state of.

        Returns:
            str: State of the light.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["status"]
            final = HIVETOHA[self.lightType].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getBrightness(self, device: dict):
        """Get light current brightness.

        Args:
            device (dict): Device to get the brightness of.

        Returns:
            int: Brightness value.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["brightness"]
            final = (state / 100) * 255
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getMinColorTemp(self, device: dict):
        """Get light minimum color temperature.

        Args:
            device (dict): Device to get min colour temp for.

        Returns:
            int: Min color temperature.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["props"]["colourTemperature"]["max"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getMaxColorTemp(self, device: dict):
        """Get light maximum color temperature.

        Args:
            device (dict): Device to get max colour temp for.

        Returns:
            int: Min color temperature.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["props"]["colourTemperature"]["min"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getColorTemp(self, device: dict):
        """Get light current color temperature.

        Args:
            device (dict): Device to get colour temp for.

        Returns:
            int: Current Color Temp.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["colourTemperature"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getColor(self, device: dict):
        """Get light current colour.

        Args:
            device (dict): Device to get color for.

        Returns:
            tuple: RGB values for the color.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
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

    async def getColorMode(self, device: dict):
        """Get Colour Mode.

        Args:
            device (dict): Device to get the color mode for.

        Returns:
            str: Colour mode.
        """
        state = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["colourMode"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def setStatusOff(self, device: dict):
        """Set light to turn off.

        Args:
            device (dict): Device to turn off.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device["hiveID"]]
            resp = await self.session.api.setState(
                data["type"], device["hiveID"], status="OFF"
            )

            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

        return final

    async def setStatusOn(self, device: dict):
        """Set light to turn on.

        Args:
            device (dict): Device to turn on.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device["hiveID"]]

            resp = await self.session.api.setState(
                data["type"], device["hiveID"], status="ON"
            )
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

        return final

    async def setBrightness(self, device: dict, n_brightness: int):
        """Set brightness of the light.

        Args:
            device (dict): Device to set brightness for.
            n_brightness (int): Brightness value

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device["hiveID"]]
            resp = await self.session.api.setState(
                data["type"],
                device["hiveID"],
                status="ON",
                brightness=n_brightness,
            )
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

        return final

    async def setColorTemp(self, device: dict, color_temp: int):
        """Set light to turn on.

        Args:
            device (dict): Device to set color temp for.
            color_temp (int): Color temp value.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device["hiveID"]]

            if data["type"] == "tuneablelight":
                resp = await self.session.api.setState(
                    data["type"],
                    device["hiveID"],
                    colourTemperature=color_temp,
                )
            else:
                resp = await self.session.api.setState(
                    data["type"],
                    device["hiveID"],
                    colourMode="WHITE",
                    colourTemperature=color_temp,
                )

            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

        return final

    async def setColor(self, device: dict, new_color: list):
        """Set light to turn on.

        Args:
            device (dict): Device to set color for.
            new_color (list): HSV value to set the light to.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device["hiveID"]]

            resp = await self.session.api.setState(
                data["type"],
                device["hiveID"],
                colourMode="COLOUR",
                hue=str(new_color[0]),
                saturation=str(new_color[1]),
                value=str(new_color[2]),
            )
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

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

    async def getLight(self, device: dict):
        """Get light data.

        Args:
            device (dict): Device to update.

        Returns:
            dict: Updated device.
        """
        device["deviceData"].update(
            {"online": await self.session.attr.onlineOffline(device["device_id"])}
        )
        dev_data = {}

        if device["deviceData"]["online"]:
            self.session.helper.deviceRecovered(device["device_id"])
            data = self.session.data.devices[device["device_id"]]
            dev_data = {
                "hiveID": device["hiveID"],
                "hiveName": device["hiveName"],
                "hiveType": device["hiveType"],
                "haName": device["haName"],
                "haType": device["haType"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "status": {
                    "state": await self.getState(device),
                    "brightness": await self.getBrightness(device),
                },
                "deviceData": data.get("props", None),
                "parentDevice": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.session.attr.stateAttributes(
                    device["device_id"], device["hiveType"]
                ),
            }

            if device["hiveType"] in ("tuneablelight", "colourtuneablelight"):
                dev_data.update(
                    {
                        "min_mireds": await self.getMinColorTemp(device),
                        "max_mireds": await self.getMaxColorTemp(device),
                    }
                )
                dev_data["status"].update(
                    {"color_temp": await self.getColorTemp(device)}
                )
            if device["hiveType"] == "colourtuneablelight":
                mode = await self.getColorMode(device)
                if mode == "COLOUR":
                    dev_data["status"].update(
                        {
                            "hs_color": await self.getColor(device),
                            "mode": await self.getColorMode(device),
                        }
                    )
                else:
                    dev_data["status"].update(
                        {
                            "mode": await self.getColorMode(device),
                        }
                    )

            self.session.devices.update({device["hiveID"]: dev_data})
            return self.session.devices[device["hiveID"]]
        else:
            await self.session.log.errorCheck(
                device["device_id"], "ERROR", device["deviceData"]["online"]
            )
            return device

    async def turnOn(self, device: dict, brightness: int, color_temp: int, color: list):
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
            return await self.setBrightness(device, brightness)
        if color_temp is not None:
            return await self.setColorTemp(device, color_temp)
        if color is not None:
            return await self.setColor(device, color)

        return await self.setStatusOn(device)

    async def turnOff(self, device: dict):
        """Set light to turn off.

        Args:
            device (dict): Device to be turned off.

        Returns:
            boolean: True/False if successful.
        """
        return await self.setStatusOff(device)
