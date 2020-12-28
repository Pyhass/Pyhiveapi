"""Hive Light Module."""
import colorsys

from .hive_session import Session
from .hive_data import Data


class Light(Session):
    """Hive Light Code."""
    lightType = 'Light'

    async def get_light(self, device):
        """Get light data."""
        await self.logger.log(device["hiveID"], self.lightType, "Getting light data.")
        device['deviceData'].update({"online": await self.attr.online_offline(device["device_id"])})
        dev_data = {}

        if device['deviceData']['online']:
            self.helper.device_recovered(device["device_id"])
            data = Data.devices[device["hiveID"]]
            dev_data = {"hiveID": device["hiveID"],
                        "hiveName": device["hiveName"],
                        "hiveType": device["hiveType"],
                        "haName": device["haName"],
                        "haType": device["haType"],
                        "device_id": device["device_id"],
                        "device_name": device["device_name"],
                        "status": {
                            "state": await self.get_state(device),
                            "brightness": await self.get_brightness(device)},
                        "deviceData": data.get("props", None),
                        "parentDevice": data.get("parent", None),
                        "custom": device.get("custom", None),
                        "attributes": await self.attr.state_attributes(device["hiveID"],
                                                                       device["hiveType"])
                        }

            if device["hiveType"] in ("tuneablelight", "colourtuneablelight"):
                dev_data.update({"min_mireds": await self.get_min_color_temp(device),
                                 "max_mireds": await self.get_max_color_temp(device)})
                dev_data["status"].update({"color_temp": await self.get_color_temp(device)})
            if device["hiveType"] == "colourtuneablelight":
                dev_data["status"].update({"hs_color": await self.get_color(device)})

            await self.logger.log(device["hiveID"], self.lightType,
                                  "Device update {0}", info=[dev_data["status"]])
            Data.ha_devices.update({device['hiveID']: dev_data})
            return dev_data
        else:
            await self.logger.error_check(device["device_id"], "ERROR", device['deviceData']['online'])
            return device

    async def get_state(self, device):
        """Get light current state."""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Getting state")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["state"]["status"]
            await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Status is {0}", info=state)
            final = Data.HIVETOHA[self.lightType].get(state, state)
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_brightness(self, device):
        """Get light current brightness."""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Getting brightness")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["state"]["brightness"]
            final = (state / 100) * 255
            await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Brightness is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_min_color_temp(self, device):
        """Get light minimum color temperature."""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Getting min colour temperature")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["props"]["colourTemperature"]["max"]
            final = round((1 / state) * 1000000)
            await self.logger.log(device["hiveID"], self.lightType + "_Extra",
                                  "Min colour temp is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_max_color_temp(self, device):
        """Get light maximum color temperature."""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Getting max colour temperature")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["props"]["colourTemperature"]["min"]
            final = round((1 / state) * 1000000)
            await self.logger.log(device["hiveID"], self.lightType + "_Extra",
                                  "Max colour temp is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_color_temp(self, device):
        """Get light current color temperature."""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Getting colour temperature")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["state"]["colourTemperature"]
            final = round((1 / state) * 1000000)
            await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Colour temp is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_color(self, device):
        """Get light current colour"""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Getting colour info")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = [
                (data["state"]["hue"]) / 360,
                (data["state"]["saturation"]) / 100,
                (data["state"]["value"]) / 100,
            ]
            final = tuple(
                int(i * 255)
                for i in colorsys.hsv_to_rgb(state[0], state[1], state[2])
            )
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def turn_off(self, device):
        """Set light to turn off."""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Turning off light")
        final = False

        if device["hiveID"] in Data.products and device["deviceData"]["online"]:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(data["type"],
                                            device["hiveID"], status="OFF")

            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])
                await self.logger.log(device["hiveID"], "Extra", "Turned light off")
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_on(self, device, brightness, color_temp, color):
        """Set light to turn on."""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Turning on light")
        final = False

        if device["hiveID"] in Data.products and device["deviceData"]["online"]:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]

            if brightness is not None:
                return await self.set_brightness(device, brightness)
            if color_temp is not None:
                return await self.set_color_temp(device, color_temp)
            if color is not None:
                return await self.set_color(device, color)

            resp = await self.api.set_state(data["type"],
                                            device["hiveID"], status="ON")
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])
                await self.logger.log(device["hiveID"], "Extra", "Light turned on")
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_brightness(self, device, n_brightness):
        """Set brightness of the light."""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Setting brightness")
        final = False

        if device["hiveID"] in Data.products and device["deviceData"]["online"]:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(data["type"],
                                            device["hiveID"], status="ON",
                                            brightness=n_brightness)
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])
                await self.logger.log(device["hiveID"], "API", "Brightness set to:  " + str(n_brightness))
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_color_temp(self, device, color_temp):
        """Set light to turn on."""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Setting color temp")
        final = False

        if device["hiveID"] in Data.products and device["deviceData"]["online"]:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]

            if data["type"] == "tuneablelight":
                resp = await self.api.set_state(data["type"],
                                                device["hiveID"],
                                                colourTemperature=color_temp)
            else:
                resp = await self.api.set_state(data["type"],
                                                device["hiveID"],
                                                colourMode="WHITE",
                                                colourTemperature=color_temp)

            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])
                await self.logger.log(device["hiveID"], "API", "Colour temp set - " + device["hiveName"])
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_color(self, device, new_color):
        """Set light to turn on."""
        await self.logger.log(device["hiveID"], self.lightType + "_Extra", "Setting color")
        final = False

        if device["hiveID"] in Data.products and device["deviceData"]["online"]:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]

            resp = await self.api.set_state(data["type"],
                                            device["hiveID"], colourMode="COLOUR",
                                            hue=str(new_color[0]), saturation=str(new_color[1]),
                                            value=str(new_color[2]))
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])
                await self.logger.log(device["hiveID"], "API", "Colour set - " + device["hiveName"])
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final
