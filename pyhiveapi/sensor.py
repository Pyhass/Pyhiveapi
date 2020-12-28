"""Hive Sensor Module."""
from .hive_session import Session
from .hive_data import Data
from .hub import Hub
from .heating import Heating
from .hotwater import Hotwater


class Sensor(Session):
    """Hive Sensor Code."""
    sensorType = 'Sensor'

    async def get_sensor(self, device):
        await self.logger.log(device["hiveID"], self.sensorType, "Getting sensor data.")
        device['deviceData'].update({"online": await self.attr.online_offline(device["device_id"])})
        data = {}
        
        if device['deviceData']['online'] or device["hiveType"] in ('Availability', 'Connectivity'):
            if device["hiveType"] not in ('Availability', 'Connectivity'):
                self.helper.device_recovered(device['device_id'])

            dev_data = {}
            dev_data = {"hiveID": device["hiveID"],
                        "hiveName": device["hiveName"],
                        "hiveType": device["hiveType"],
                        "haName": device["haName"],
                        "haType": device["haType"],
                        "device_id": device.get("device_id", None),
                        "device_name": device.get("device_name", None),
                        "deviceData": {},
                        "custom": device.get("custom", None)
                        }


            if device["device_id"] in Data.devices:
                data = Data.devices.get(device["device_id"], {})
            elif device["hiveID"] in Data.products:
                data = Data.products.get(device["hiveID"], {})


            if dev_data["hiveType"] in Data.sensor_commands or dev_data.get("custom", None) in Data.sensor_commands:
                code = Data.sensor_commands.get(
                    dev_data["hiveType"], Data.sensor_commands.get(dev_data["custom"]))
                dev_data.update({"status": {"state": await eval(code)},
                                 "deviceData": data.get("props", None),
                                 "parentDevice": data.get("parent", None)})
            elif device["hiveType"] in Data.HIVE_TYPES["Sensor"]:
                data = Data.devices.get(device["hiveID"], {})
                dev_data.update({"status": {"state": await self.get_state(device)},
                                 "deviceData": data.get("props", None),
                                 "parentDevice": data.get("parent", None),
                                 "attributes": await self.attr.state_attributes(device["hiveID"],
                                                                                device["hiveType"])})

            await self.logger.log(device["hiveID"], self.sensorType,
                                  "Device update {0}", info=[dev_data["status"]])
            Data.ha_devices.update({device['hiveID']: dev_data})
            return dev_data
        else:
            await self.logger.error_check(device['device_id'], "ERROR", device['deviceData']['online'])
            return device

    async def get_state(self, device):
        """Get sensor state."""
        await self.logger.log(device["hiveID"], self.sensorType + "_Extra", "Getting state")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            if data["type"] == "contactsensor":
                state = data["props"]["status"]
                final = Data.HIVETOHA[self.sensorType].get(state, state)
            elif data["type"] == "motionsensor":
                final = data["props"]["motion"]["status"]
            await self.logger.log(device["hiveID"], self.sensorType + "_Extra", "Status is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def online(self, device):
        """Get the online status of the Hive hub."""
        await self.logger.log(device["hiveID"], self.sensorType + "_Extra", "Getting status")
        state = None
        final = None

        if device["hiveID"] in Data.devices:
            data = Data.devices[device["hiveID"]]
            state = data["props"]["online"]
            final = Data.HIVETOHA[self.sensorType].get(state, state)
            await self.logger.log(device["hiveID"], self.sensorType + "_Extra", "Status is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final
