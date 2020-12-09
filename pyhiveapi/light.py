"""Hive Light Module."""
import colorsys
from typing import Optional
from aiohttp import ClientSession

from .hive_session import Session
from .hive_data import Data
from .custom_logging import Logger
from .device_attributes import Attributes
from .hive_async_api import Hive_Async
from .helper import Hive_Helper


class Light:
    """Hive Light Code."""

    def __init__(self, websession: Optional[ClientSession] = None):
        """Initialise."""
        self.hive = Hive_Async(websession)
        self.session = Session(websession)
        self.log = Logger()
        self.attr = Attributes()
        self.type = "Light"

    async def get_light(self, device):
        """Get light data."""
        await self.log.log(device["hive_id"], self.type, "Getting light data.")
        online = await self.attr.online_offline(device["device_id"])
        dev_data = {}

        if online:
            Hive_Helper.device_recovered(device["device_id"])
            data = Data.devices[device["hive_id"]]
            dev_data = {"hive_id": device["hive_id"],
                        "hive_name": device["hive_name"],
                        "hive_type": device["hive_type"],
                        "ha_name": device["ha_name"],
                        "ha_type": device["ha_type"],
                        "device_id": device["device_id"],
                        "device_name": device["device_name"],
                        "status": {
                            "state": await self.get_state(device),
                            "brightness": await self.get_brightness(device)},
                        "device_data": data.get("props", None),
                        "parent_device": data.get("parent", None),
                        "custom": device.get("custom", None),
                        "attributes": await self.attr.state_attributes(device["hive_id"],
                                                                       device["hive_type"])
                        }

            if device["hive_type"] in ("tuneablelight", "colourtuneablelight"):
                dev_data.update({"min_mireds": await self.get_min_color_temp(device),
                                 "max_mireds": await self.get_max_color_temp(device)})
                dev_data["status"].update({"color_temp": await self.get_color_temp(device)})
            if device["hive_type"] == "colourtuneablelight":
                dev_data["status"].update({"hs_color": await self.get_color(device)})

            await self.log.log(device["hive_id"], self.type,
                               "Device update {0}", info=[dev_data["status"]])
            Data.ha_devices.update({device['hive_id']: dev_data})
            return dev_data
        else:
            await self.log.error_check(device["device_id"], "ERROR", online)
            return device

    async def get_state(self, device):
        """Get light current state."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting state")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["state"]["status"]
            await self.log.log(device["hive_id"], self.type + "_Extra", "Status is {0}", info=state)
            final = Data.HIVETOHA[self.type].get(state, state)
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def get_brightness(self, device):
        """Get light current brightness."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting brightness")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["state"]["brightness"]
            final = (state / 100) * 255
            await self.log.log(device["hive_id"], self.type + "_Extra", "Brightness is {0}", info=[final])
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def get_min_color_temp(self, device):
        """Get light minimum color temperature."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting min colour temperature")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["props"]["colourTemperature"]["max"]
            final = round((1 / state) * 1000000)
            await self.log.log(device["hive_id"], self.type + "_Extra",
                               "Min colour temp is {0}", info=[final])
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def get_max_color_temp(self, device):
        """Get light maximum color temperature."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting max colour temperature")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["props"]["colourTemperature"]["min"]
            final = round((1 / state) * 1000000)
            await self.log.log(device["hive_id"], self.type + "_Extra",
                               "Max colour temp is {0}", info=[final])
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def get_color_temp(self, device):
        """Get light current color temperature."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting colour temperature")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["state"]["colourTemperature"]
            final = round((1 / state) * 1000000)
            await self.log.log(device["hive_id"], self.type + "_Extra", "Colour temp is {0}", info=[final])
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def get_color(self, device):
        """Get light current colour"""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Getting colour info")
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
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
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final

    async def turn_off(self, device):
        """Set light to turn off."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Turning off light")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_refresh_tokens()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(data["type"],
                                             device["hive_id"], status="OFF")

            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "Extra", "Turned light off")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_on(self, device, brightness, color_temp, color):
        """Set light to turn on."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Turning on light")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_refresh_tokens()
            data = Data.products[device["hive_id"]]

            if brightness is not None:
                return await self.set_brightness(device, brightness)
            if color_temp is not None:
                return await self.set_color_temp(device, color_temp)
            if color is not None:
                return await self.set_color(device, color)

            resp = await self.hive.set_state(data["type"],
                                             device["hive_id"], status="ON")
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "Extra", "Light turned on")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_brightness(self, device, n_brightness):
        """Set brightness of the light."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Setting brightness")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_refresh_tokens()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(data["type"],
                                             device["hive_id"], status="ON",
                                             brightness=n_brightness)
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Brightness set to:  " + str(n_brightness))
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_color_temp(self, device, color_temp):
        """Set light to turn on."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Setting color temp")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_refresh_tokens()
            data = Data.products[device["hive_id"]]

            if data["type"] == "tuneablelight":
                resp = await self.hive.set_state(data["type"],
                                                 device["hive_id"],
                                                 colourTemperature=color_temp)
            else:
                resp = await self.hive.set_state(data["type"],
                                                 device["hive_id"],
                                                 colourMode="WHITE",
                                                 colourTemperature=color_temp)

            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Colour temp set - " + device["hive_name"])
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_color(self, device, new_color):
        """Set light to turn on."""
        await self.log.log(device["hive_id"], self.type + "_Extra", "Setting color")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_refresh_tokens()
            data = Data.products[device["hive_id"]]

            resp = await self.hive.set_state(data["type"],
                                             device["hive_id"], colourMode="COLOUR",
                                             hue=str(new_color[0]), saturation=str(new_color[1]),
                                             value=str(new_color[2]))
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Colour set - " + device["hive_name"])
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final
