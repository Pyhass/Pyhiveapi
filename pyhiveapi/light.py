"""Hive Light Module."""
import colorsys
import asyncio
from typing import Optional
from aiohttp import ClientSession

from .hive_session import Session
from .hive_data import Data
from .custom_logging import Logger
from .device_attributes import Attributes
from .hive_async_api import Hive_Async


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
        online = await self.attr.online_offline(device["hive_id"])
        error = await self.log.error_check(device["hive_id"], self.type, online)

        dev_data = {}
        if device["hive_id"] in Data.devices:
            data = Data.devices[device["hive_id"]]
            dev_data = {"hive_id": device["hive_id"],
                        "hive_name": device["hive_name"],
                        "hive_type": device["hive_type"],
                        "ha_name": device["ha_name"],
                        "ha_type": device["ha_type"],
                        "device_id": device["device_id"],
                        "device_name": device["device_name"],
                        "state": await self.get_state(device),
                        "brightness": await self.get_brightness(device),
                        "device_data": data.get("props", None),
                        "parent_device": data.get("parent", None),
                        "custom": device.get("custom", None),
                        "attributes": await self.attr.state_attributes(device["hive_id"],
                                                                       device["hive_type"])
                        }

            if device["hive_type"] in ("tuneablelight", "colourtuneablelight"):
                dev_data.update({"min_mireds": await self.get_min_color_temp(device),
                                 "max_mireds": await self.get_max_color_temp(device),
                                 "color_temp": await self.get_color_temp(device)})
            if device["hive_type"] == "colourtuneablelight":
                dev_data.update({"hs_color": await self.get_color(device)})

        if not error:
            await self.log.log(device["hive_id"], self.type,
                               "Device update {0}", info=dev_data)

        return dev_data

    async def get_state(self, device):
        """Get light current state."""
        await self.log.log(device["hive_id"], "Extra", "Getting state")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["state"]["status"]
                await self.log.log(device["hive_id"], "Extra", "Status is {0}", info=state)
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = Data.HIVETOHA[self.type].get(state, state)
            Data.NODES[device["hive_id"]]["State"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["State"]

    async def get_brightness(self, device):
        """Get light current brightness."""
        await self.log.log(device["hive_id"], "Extra", "Getting brightness")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["state"]["brightness"]
                final = (state / 100) * 255
                Data.NODES[device["hive_id"]]["Brightness"] = final
                await self.log.log(device["hive_id"], "Extra", "Brightness is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", online)
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Brightness"]

    async def get_min_color_temp(self, device):
        """Get light minimum color temperature."""
        await self.log.log(device["hive_id"], "Extra", "Getting min colour temperature")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["props"]["colourTemperature"]["max"]
            final = round((1 / state) * 1000000)
            Data.NODES[device["hive_id"]]["Min_CT"] = final
            await self.log.log(device["hive_id"], "Extra",
                               "Min colour temp is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", online)
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Min_CT"]

    async def get_max_color_temp(self, device):
        """Get light maximum color temperature."""
        await self.log.log(device["hive_id"], "Extra", "Getting max colour temperature")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            data = Data.products[device["hive_id"]]
            state = data["props"]["colourTemperature"]["min"]
            final = round((1 / state) * 1000000)
            Data.NODES[device["hive_id"]]["Max_CT"] = final
            await self.log.log(device["hive_id"], "Extra",
                               "Max colour temp is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", online)
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Max_CT"]

    async def get_color_temp(self, device):
        """Get light current color temperature."""
        await self.log.log(device["hive_id"], "Extra", "Getting colour temperature")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                state = data["state"]["colourTemperature"]
                final = round((1 / state) * 1000000)
                Data.NODES[device["hive_id"]]["CT"] = final
                await self.log.log(device["hive_id"], "Extra", "Colour temp is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", online)
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["CT"]

    async def get_color(self, device):
        """Get light current colour"""
        await self.log.log(device["hive_id"], "Extra", "Getting colour info")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
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
                Data.NODES[device["hive_id"]]["Colour"] = final
            await self.log.error_check(device["hive_id"], "Extra", online)
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["Colour"]

    async def turn_off(self, device):
        """Set light to turn off."""
        await self.log.log(device["hive_id"], "Extra", "Turning off light")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(Data.sess_id, data["type"],
                                             device["hive_id"], status="OFF")

            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Light off - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_on(self, device, brightness, color_temp, color):
        """Set light to turn on."""
        await self.log.log(device["hive_id"], "Extra", "Turning on light")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]

            if brightness is not None:
                return await self.set_brightness(device, brightness)
            if color_temp is not None:
                return await self.set_color_temp(device, color_temp)
            if color is not None:
                return await self.set_color(device, color)

            resp = await self.hive.set_state(Data.sess_id, data["type"],
                                             device["hive_id"], status="ON")
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Light on - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_brightness(self, device, n_brightness):
        """Set brightness of the light."""
        await self.log.log(device["hive_id"], "Extra", "Setting brightness")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]
            resp = await self.hive.set_state(Data.sess_id, data["type"],
                                             device["hive_id"], status="ON",
                                             brightness=n_brightness)
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Brightness set - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_color_temp(self, device, color_temp):
        """Set light to turn on."""
        await self.log.log(device["hive_id"], "Extra", "Setting color temp")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]

            if data["type"] == "tuneablelight":
                resp = await self.hive.set_state(Data.sess_id, data["type"],
                                                 device["hive_id"],
                                                 colourTemperature=color_temp)
            else:
                await self.hive.set_state(Data.sess_id, data["type"], device["hive_id"],
                                          colourMode="COLOUR", hue="48", saturation="70",
                                          value="96")
                resp = await self.hive.set_state(Data.sess_id, data["type"],
                                                 device["hive_id"],
                                                 colourMode="WHITE",
                                                 colourTemperature=color_temp)

            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Colour temp set - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_color(self, device, new_color):
        """Set light to turn on."""
        await self.log.log(device["hive_id"], "Extra", "Setting color")
        final = False

        if device["hive_id"] in Data.products:
            await self.session.hive_api_logon()
            data = Data.products[device["hive_id"]]

            resp = await self.hive.set_state(Data.sess_id, data["type"],
                                             device["hive_id"], colourMode="COLOUR",
                                             hue=str(new_color[0]), saturation=str(new_color[1]),
                                             value=str(new_color[2]))
            if resp["original"] == 200:
                final = True
                await self.session.get_devices(device["hive_id"])
                await self.log.log(device["hive_id"], "API", "Colour set - API response 200")
            else:
                await self.log.error_check(
                    device["hive_id"], "ERROR", "Failed_API", resp=resp["original"])

        return final
