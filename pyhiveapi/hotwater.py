""""Hive Hotwater Module. """
from .hive_session import Session
from .hive_data import Data


class Hotwater(Session):
    """Hive Hotwater Code."""
    hotwaterType = 'Hotwater'

    async def get_hotwater(self, device):
        """Get light data."""
        await self.logger.log(device["hiveID"], self.hotwaterType, "Getting hot water data.")
        device['deviceData'].update({"online": await self.attr.online_offline(device["device_id"])})

        if device['deviceData']['online']:

            dev_data = {}
            self.helper.device_recovered(device["device_id"])
            data = Data.devices[device["device_id"]]
            dev_data = {"hiveID": device["hiveID"],
                        "hiveName": device["hiveName"],
                        "hiveType": device["hiveType"],
                        "haName": device["haName"],
                        "haType": device["haType"],
                        "device_id": device["device_id"],
                        "device_name": device["device_name"],
                        "status": {
                            "current_operation": await self.get_mode(device)},
                        "deviceData": data.get("props", None),
                        "parentDevice": data.get("parent", None),
                        "custom": device.get("custom", None),
                        "attributes": await self.attr.state_attributes(device["device_id"],
                                                                       device["hiveType"])
                        }

            await self.logger.log(device["hiveID"], self.hotwaterType,
                                  "Device update {0}", info=dev_data['status'])
            Data.ha_devices.update({device['hiveID']: dev_data})
            return dev_data
        else:
            await self.logger.error_check(device["device_id"], "ERROR", device['deviceData']['online'])
            return device

    async def get_mode(self, device):
        """Get hotwater current mode."""
        await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Getting mode")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["state"]["mode"]
            if state == "BOOST":
                state = data["props"]["previous"]["mode"]
            final = Data.HIVETOHA[self.hotwaterType].get(state, state)
            await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Mode is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    @staticmethod
    async def get_operation_modes():
        """Get heating list of possible modes."""
        return ["SCHEDULE", "ON", "OFF"]

    async def get_boost(self, device):
        """Get hot water current boost status."""
        await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Getting boost")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["state"]["boost"]
            final = Data.HIVETOHA["Boost"].get(state, "ON")
            await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Boost is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_boost_time(self, device):
        """Get hotwater boost time remaining."""
        state = None
        final = None
        if await self.get_boost(device) == "ON":
            await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Getting boost time")
            if device["hiveID"] in Data.products:
                data = Data.products[device["hiveID"]]
                state = data["state"]["boost"]
                await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra",
                                      "Boost time is {0}", info=[state])
                final = state
            else:
                await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_state(self, device):
        """Get hot water current state."""
        await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Getting state")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["state"]["status"]
            mode_current = await self.get_mode(device)
            if mode_current == "SCHEDULE":
                if await self.get_boost(device) == "ON":
                    state = "ON"
                else:
                    snan = await self.p_get_schedule_nnl(
                        data["state"]["schedule"])
                    state = snan["now"]["value"]["status"]

            final = Data.HIVETOHA[self.hotwaterType].get(state, state)
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_schedule_now_next_later(self, device):
        """Hive get hotwater schedule now, next and later."""
        await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Getting schedule info.")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            await self.hiveRefreshTokens()
            mode_current = await self.get_mode(device)
            if mode_current == "SCHEDULE":
                data = Data.products[device["hiveID"]]
                state = await self.p_get_schedule_nnl(
                    data["state"]["schedule"])
            final = state
            await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Schedule is {0}", info=[final])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def set_mode(self, device, new_mode):
        """Set hot water mode."""
        await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Setting Mode to {0}", info=[new_mode])
        final = False

        if device["hiveID"] in Data.products:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(data["type"],
                                            device["hiveID"], mode=new_mode)
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])
                await self.logger.log(
                    device["hiveID"], "API", "Mode set to {0} - " + device["hiveName"], info=[new_mode]
                )
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

            return final

    async def turn_boost_on(self, device, mins):
        """Turn hot water boost on."""
        await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Turning on boost")
        final = False

        if mins > 0 and device["hiveID"] in Data.products and device["deviceData"]["online"]:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(data["type"],
                                            device["hiveID"], mode="BOOST",
                                            boost=mins)
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])
                await self.logger.log(device["hiveID"], "API", "Boost on - " + device["hiveName"])
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_boost_off(self, device):
        """Turn hot water boost off."""
        await self.logger.log(device["hiveID"], self.hotwaterType + "_Extra", "Turning off boost")
        final = False

        if device["hiveID"] in Data.products and await self.get_boost(device) == "ON" \
                and device["deviceData"]["online"]:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            prev_mode = data["props"]["previous"]["mode"]
            resp = await self.api.set_state(data["type"],
                                            device["hiveID"], mode=prev_mode)
            if resp["original"] == 200:
                await self.getDevices(device["hiveID"])
                final = True
                await self.logger.log(device["hiveID"], "API", "Boost off - " + device["hiveName"])
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final
