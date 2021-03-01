"""Hive Sensor Module."""
import ast

from .heating import Heating  # noqa: F401
from .helper.const import HIVE_TYPES, HIVETOHA, sensor_commands
from .hotwater import Hotwater  # noqa: F401
from .hub import Hub  # noqa: F401


class Sensor:
    """Hive Sensor Code."""

    sensorType = "Sensor"

    def __init__(self, session):
        """Initialise sensor."""
        self.session = session

    async def get_sensor(self, device):
        """Gets updated sensor data."""
        await self.session.log.log(
            device["hiveID"], self.sensorType, "Getting sensor data."
        )
        device["deviceData"].update(
            {"online": await self.session.attr.online_offline(device["device_id"])}
        )
        data = {}

        if device["deviceData"]["online"] or device["hiveType"] in (
            "Availability",
            "Connectivity",
        ):
            if device["hiveType"] not in ("Availability", "Connectivity"):
                self.session.helper.deviceRecovered(device["device_id"])

            dev_data = {}
            dev_data = {
                "hiveID": device["hiveID"],
                "hiveName": device["hiveName"],
                "hiveType": device["hiveType"],
                "haName": device["haName"],
                "haType": device["haType"],
                "device_id": device.get("device_id", None),
                "device_name": device.get("device_name", None),
                "deviceData": {},
                "custom": device.get("custom", None),
            }

            if device["device_id"] in self.session.data.devices:
                data = self.session.data.devices.get(device["device_id"], {})
            elif device["hiveID"] in self.session.data.products:
                data = self.session.data.products.get(device["hiveID"], {})

            if (
                dev_data["hiveType"] in sensor_commands
                or dev_data.get("custom", None) in sensor_commands
            ):
                code = sensor_commands.get(
                    dev_data["hiveType"],
                    sensor_commands.get(dev_data["custom"]),
                )
                dev_data.update(
                    {
                        "status": {"state": await ast.literal_eval(code)},
                        "deviceData": data.get("props", None),
                        "parentDevice": data.get("parent", None),
                    }
                )
            elif device["hiveType"] in HIVE_TYPES["Sensor"]:
                data = self.session.data.devices.get(device["hiveID"], {})
                dev_data.update(
                    {
                        "status": {"state": await self.get_state(device)},
                        "deviceData": data.get("props", None),
                        "parentDevice": data.get("parent", None),
                        "attributes": await self.session.attr.state_attributes(
                            device["device_id"], device["hiveType"]
                        ),
                    }
                )

            await self.session.log.log(
                device["hiveID"],
                self.sensorType,
                "Device update {0}",
                info=[dev_data["status"]],
            )
            self.session.devices.update({device["hiveID"]: dev_data})
            return self.session.devices[device["hiveID"]]
        else:
            await self.session.log.error_check(
                device["device_id"], "ERROR", device["deviceData"]["online"]
            )
            return device

    async def get_state(self, device):
        """Get sensor state."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            if data["type"] == "contactsensor":
                state = data["props"]["status"]
                final = HIVETOHA[self.sensorType].get(state, state)
            elif data["type"] == "motionsensor":
                final = data["props"]["motion"]["status"]
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def online(self, device):
        """Get the online status of the Hive hub."""
        state = None
        final = None

        try:
            data = self.session.data.devices[device["device_id"]]
            state = data["props"]["online"]
            final = HIVETOHA[self.sensorType].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final
