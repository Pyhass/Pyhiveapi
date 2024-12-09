"""Hive Sensor Module."""
# pylint: skip-file
from .helper.const import HIVE_TYPES, HIVETOHA


class HiveSensor:
    """Hive Sensor Code."""

    sensor_type = "Sensor"

    async def get_state(self, device: dict):
        """Get sensor state.

        Args:
            device (dict): Device to get state off.

        Returns:
            str: State of device.
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hive_id"]]
            if data["type"] == "contactsensor":
                state = data["props"]["status"]
                final = HIVETOHA[self.sensor_type].get(state, state)
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
            final = HIVETOHA[self.sensor_type].get(state, state)
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

    async def get_sensor(self, device: dict):
        """Gets updated sensor data.

        Args:
            device (dict): Device to update.

        Returns:
            dict: Updated device.
        """
        device["device_data"].update(
            {"online": await self.session.attr.online_offline(device["device_id"])}
        )
        data = {}

        if device["device_data"]["online"] or device["hive_type"] in (
            "Availability",
            "Connectivity",
        ):
            if device["hive_type"] not in ("Availability", "Connectivity"):
                self.session.helper.device_recovered(device["device_id"])

            dev_data = {}
            dev_data = {
                "hive_id": device["hive_id"],
                "hive_name": device["hive_name"],
                "hive_type": device["hive_type"],
                "ha_name": device["ha_name"],
                "ha_type": device["ha_type"],
                "device_id": device.get("device_id", None),
                "device_name": device.get("device_name", None),
                "device_data": {},
                "custom": device.get("custom", None),
            }

            if device["device_id"] in self.session.data.devices:
                data = self.session.data.devices.get(device["device_id"], {})
            elif device["hive_id"] in self.session.data.products:
                data = self.session.data.products.get(device["hive_id"], {})

            sensor_state = self.session.helper.call_sensor_function(dev_data)
            if sensor_state is not None:
                dev_data.update(
                    {
                        "status": {"state": sensor_state},
                        "device_data": data.get("props", None),
                        "parent_device": data.get("parent", None),
                    }
                )
            elif device["hive_type"] in HIVE_TYPES["Sensor"]:
                data = self.session.data.devices.get(device["hive_id"], {})
                dev_data.update(
                    {
                        "status": {"state": await self.get_state(device)},
                        "device_data": data.get("props", None),
                        "parent_device": data.get("parent", None),
                        "attributes": await self.session.attr.state_attributes(
                            device["device_id"], device["hive_type"]
                        ),
                    }
                )

            self.session.devices.update({device["hive_id"]: dev_data})
            return self.session.devices[device["hive_id"]]
        else:
            await self.session.log.error_check(
                device["device_id"], "ERROR", device["device_data"]["online"]
            )
            return device
