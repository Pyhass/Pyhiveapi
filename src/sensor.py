"""Hive Sensor Module."""

# pylint: skip-file
from .helper.const import HIVE_TYPES, HIVETOHA, sensor_commands


class HiveSensor:
    """Hive Sensor Code."""

    sensorType = "Sensor"

    async def getState(self, device: dict):
        """Get sensor state.

        Args:
            device (dict): Device to get state off.

        Returns:
            str: State of device.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device.hive_id]
            if data["type"] == "contactsensor":
                state = data["props"]["status"]
                final = HIVETOHA[self.sensorType].get(state, state)
            elif data["type"] == "motionsensor":
                final = data["props"]["motion"]["status"]
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def online(self, device: dict):
        """Get the online status of the Hive hub.

        Args:
            device (dict): Device to get the state of.

        Returns:
            boolean: True/False if the device is online.
        """
        state = None
        final = None

        try:
            data = self.session.data.devices[device["device_id"]]
            state = data["props"]["online"]
            final = HIVETOHA[self.sensorType].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final


class Sensor(HiveSensor):
    """Home Assisatnt sensor code.

    Args:
        HiveSensor (object): Hive sensor code.
    """

    def __init__(self, session: object = None):
        """Initialise sensor.

        Args:
            session (object, optional): session to interact with Hive account. Defaults to None.
        """
        self.session = session

    async def getSensor(self, device: dict):
        """Gets updated sensor data.

        Args:
            device (dict): Device to update.

        Returns:
            dict: Updated device.
        """
        device.device_data.update(
            {"online": await self.session.attr.onlineOffline(device["device_id"])}
        )
        data = {}

        if device.device_data["online"] or device.hive_type in (
            "Availability",
            "Connectivity",
        ):
            if device.hive_type not in ("Availability", "Connectivity"):
                self.session.helper.deviceRecovered(device["device_id"])

            dev_data = {}
            dev_data = {
                "hiveID": device.hive_id,
                "hiveName": device.hive_name,
                "hiveType": device.hive_type,
                "haName": device.ha_name,
                "haType": device["haType"],
                "device_id": device.get("device_id", None),
                "device_name": device.get("device_name", None),
                "deviceData": {},
                "custom": device.get("custom", None),
            }

            if device["device_id"] in self.session.data.devices:
                data = self.session.data.devices.get(device["device_id"], {})
            elif device.hive_id in self.session.data.products:
                data = self.session.data.products.get(device.hive_id, {})

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
                        "status": {"state": await eval(code)},
                        "deviceData": data.get("props", None),
                        "parentDevice": data.get("parent", None),
                    }
                )
            elif device.hive_type in HIVE_TYPES["Sensor"]:
                data = self.session.data.devices.get(device.hive_id, {})
                dev_data.update(
                    {
                        "status": {"state": await self.getState(device)},
                        "deviceData": data.get("props", None),
                        "parentDevice": data.get("parent", None),
                        "attributes": await self.session.attr.stateAttributes(
                            device["device_id"], device.hive_type
                        ),
                    }
                )

            self.session.devices.update({device.hive_id: dev_data})
            return self.session.devices[device.hive_id]
        else:
            await self.session.log.errorCheck(
                device["device_id"], "ERROR", device.device_data["online"]
            )
            return device
