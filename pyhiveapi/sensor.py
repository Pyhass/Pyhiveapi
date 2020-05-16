"""Hive Sensor Module."""
import asyncio
from .hive_data import Data
from .custom_logging import Logger
from .device_attributes import Attributes
from .weather import Weather
from .hub import Hub


class Sensor:
    """Hive Sensor Code."""

    def __init__(self):
        """Initialise."""
        self.log = Logger()
        self.attr = Attributes()
        self.weather = Weather()
        self.hub = Hub()
        self.type = "Sensor"

    async def get_sensor(self, device):
        await self.log.log(device["hive_id"], self.type, "Getting sensor data.")
        online = await self.attr.online_offline(device["hive_id"])
        error = await self.log.error_check(device["hive_id"], self.type, online)

        dev_data = {}
        dev_data = {"hive_id": device["hive_id"],
                    "hive_name": device["hive_name"],
                    "hive_type": device["hive_type"],
                    "ha_name": device["ha_name"],
                    "ha_type": device["ha_type"],
                    }
        if device["hive_type"] == "Weather_OutsideTemperature":
            dev_data.update({"state": await self.weather.temperature()})
        elif device["hive_type"] == "hub_OnlineStatus":
            data = Data.devices.get(device["hive_id"], {})
            dev_data.update({"state": await self.hub.hub_status(device),
                             "device_data": data.get("props", None),
                             "parent_device": data.get("parent", None)})
        elif device["hive_type"] == "sense_SMOKE_CO":
            data = Data.products.get(device["hive_id"], {})
            dev_data.update({"state": await self.hub.hub_smoke(device),
                             "hub_id": device["hub_id"],
                             "device_data": data.get("props", None),
                             "parent_device": data.get("parent", None)})
        elif device["hive_type"] == "sense_DOG_BARK":
            data = Data.products.get(device["hive_id"], {})
            dev_data.update({"state": await self.hub.hub_dog_bark(device),
                             "hub_id": device["hub_id"],
                             "device_data": data.get("props", None),
                             "parent_device": data.get("parent", None)})
        elif device["hive_type"] == "sense_GLASS_BREAK":
            data = Data.products.get(device["hive_id"], {})
            dev_data.update({"state": await self.hub.hub_glass(device),
                             "hub_id": device["hub_id"],
                             "device_data": data.get("props", None),
                             "parent_device": data.get("parent", None)})
        elif device["hive_type"] in Data.HIVE_TYPES["Sensor"]:
            data = Data.devices.get(device["hive_id"], {})
            dev_data.update({"state": await self.get_state(device),
                             "device_data": data.get("props", None),
                             "parent_device": data.get("parent", None),
                             "attributes": await self.attr.state_attributes(device["hive_id"],
                                                                            device["hive_type"])})

        if not error:
            await self.log.log(device["hive_id"], self.type,
                               "Device update {0}", info=dev_data)

        return dev_data

    async def get_state(self, device):
        """Get sensor state."""
        await self.log.log(device["hive_id"], "Extra", "Getting state")
        online = await self.attr.online_offline(device["hive_id"])
        state = None
        state = None
        final = None

        if device["hive_id"] in Data.products:
            if online:
                data = Data.products[device["hive_id"]]
                if data["type"] == "contactsensor":
                    state = data["props"]["status"]
                elif data["type"] == "motionsensor":
                    state = data["props"]["motion"]["status"]
                final = Data.HIVETOHA[self.type].get(state, state)
                await self.log.log(device["hive_id"], "Extra", "Status is {0}", info=final)
            await self.log.error_check(device["hive_id"], "Extra", online)
            final = Data.HIVETOHA[self.type].get(state, state)
            Data.NODES[device["hive_id"]]["State"] = final
        else:
            await self.log.error_check(device["hive_id"], "ERROR", "Failed")

        return final if final is None else Data.NODES[device["hive_id"]]["State"]
