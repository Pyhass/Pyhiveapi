"""Hive Light Module."""
import colorsys

from .helper.const import HIVETOHA


class Light:
    """Hive Light Code."""

    lightType = "Light"

    def __init__(self, session=None):
        """Initialise light."""
        self.session = session

    async def getLight(self, device):
        """Get light data."""
        await self.session.log.log(
            device["hiveID"], self.lightType, "Getting light data."
        )
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

            await self.session.log.log(
                device["hiveID"],
                self.lightType,
                "Device update {0}",
                info=[dev_data["status"]],
            )
            self.session.devices.update({device["hiveID"]: dev_data})
            return self.session.devices[device["hiveID"]]
        else:
            await self.session.log.errorCheck(
                device["device_id"], "ERROR", device["deviceData"]["online"]
            )
            return device

    async def getState(self, device):
        """Get light current state."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["status"]
            final = HIVETOHA[self.lightType].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getBrightness(self, device):
        """Get light current brightness."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["brightness"]
            final = (state / 100) * 255
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getMinColorTemp(self, device):
        """Get light minimum color temperature."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["props"]["colourTemperature"]["max"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getMaxColorTemp(self, device):
        """Get light maximum color temperature."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["props"]["colourTemperature"]["min"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getColorTemp(self, device):
        """Get light current color temperature."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["colourTemperature"]
            final = round((1 / state) * 1000000)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getColor(self, device):
        """Get light current colour."""
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

    async def getColorMode(self, device):
        """Get Colour Mode."""
        state = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["colourMode"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def turnOff(self, device):
        """Set light to turn off."""
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

    async def turnOn(self, device, brightness, color_temp, color):
        """Set light to turn on."""
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device["hiveID"]]

            if brightness is not None:
                return await self.setBrightness(device, brightness)
            if color_temp is not None:
                return await self.setColorTemp(device, color_temp)
            if color is not None:
                return await self.setColor(device, color)

            resp = await self.session.api.setState(
                data["type"], device["hiveID"], status="ON"
            )
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

        return final

    async def setBrightness(self, device, n_brightness):
        """Set brightness of the light."""
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

    async def setColorTemp(self, device, color_temp):
        """Set light to turn on."""
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

    async def setColor(self, device, new_color):
        """Set light to turn on."""
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
