""""Hive Heating Module. """
from .hive_session import Session
from .hive_data import Data


class Heating(Session):
    """Hive Heating Code."""
    heatingType = 'Heating'

    async def get_heating(self, device):
        await self.logger.log(device["hiveID"], self.heatingType, "Getting heating data.")
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
                        "temperatureunit": device["temperatureunit"],
                        "min_temp": await self.min_temperature(device),
                        "max_temp": await self.max_temperature(device),
                        "status": {
                            "current_temperature": await self.current_temperature(device),
                            "target_temperature": await self.target_temperature(device),
                            "action": await self.current_operation(device),
                            "mode": await self.get_mode(device),
                            "boost": await self.boost(device)},
                        "deviceData": data.get("props", None),
                        "parentDevice": data.get("parent", None),
                        "custom": device.get("custom", None),
                        "attributes": await self.attr.state_attributes(device["device_id"],
                                                                       device["hiveType"])
                        }
            await self.logger.log(device["hiveID"], self.heatingType,
                                  "Device update {0}", info=[dev_data["status"]])
            Data.ha_devices.update({device['hiveID']: dev_data})
            return dev_data
        else:
            await self.logger.error_check(device["device_id"], "ERROR", device['deviceData']['online'])
            return device

    @ staticmethod
    async def min_temperature(device):
        """Get heating minimum target temperature."""
        if device["hiveType"] == "nathermostat":
            return Data.products[device["hiveID"]]["props"]["minHeat"]
        return 5

    @ staticmethod
    async def max_temperature(device):
        """Get heating maximum target temperature."""
        if device["hiveType"] == "nathermostat":
            return Data.products[device["hiveID"]]["props"]["maxHeat"]
        return 32

    async def current_temperature(self, device):
        """Get heating current temperature."""
        from datetime import datetime

        await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Getting current temp")
        f_state = None
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["props"]["temperature"]

            if device["hiveID"] in Data.minMax:
                if Data.minMax[device["hiveID"]]["TodayDate"] != datetime.date(
                    datetime.now()
                ):
                    Data.minMax[device["hiveID"]]["TodayMin"] = 1000
                    Data.minMax[device["hiveID"]]["TodayMax"] = -1000
                    Data.minMax[device["hiveID"]]["TodayDate"] = datetime.date(
                        datetime.now())

                    if state < Data.minMax[device["hiveID"]]["TodayMin"]:
                        Data.minMax[device["hiveID"]
                                    ]["TodayMin"] = state

                    if state > Data.minMax[device["hiveID"]]["TodayMax"]:
                        Data.minMax[device["hiveID"]
                                    ]["TodayMax"] = state

                    if state < Data.minMax[device["hiveID"]]["RestartMin"]:
                        Data.minMax[device["hiveID"]
                                    ]["RestartMin"] = state

                    if state > Data.minMax[device["hiveID"]]["RestartMax"]:
                        Data.minMax[device["hiveID"]
                                    ]["RestartMax"] = state
            else:
                data = {
                    "TodayMin": state,
                    "TodayMax": state,
                    "TodayDate": str(datetime.date(datetime.now())),
                    "RestartMin": state,
                    "RestartMax": state,
                }
                Data.minMax[device["hiveID"]] = data
            f_state = round(float(state), 1)
            await self.logger.log(device["hiveID"], self.heatingType + "_Extra",
                                  "Current Temp is {0}", info=[str(state)])

            final = f_state
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def minmax_temperatures(self, device):
        """Min/Max Temp"""
        await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Getting Min/Max temp")
        state = None
        final = None

        if device["hiveID"] in Data.minMax:
            state = Data.minMax[device["hiveID"]]
            await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Min/Max is {0}", info=[state])
            final = state
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def target_temperature(self, device):
        """Get heating target temperature."""
        await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Getting target temp")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = float(data["state"].get("target", None))
            state = float(data["state"].get("heat", state))
            await self.logger.log(device["hiveID"], self.heatingType + "_Extra",
                                  "Target temp is {0}", info=[str(state)])
            final = state
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_mode(self, device):
        """Get heating current mode."""
        await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Getting mode")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["state"]["mode"]
            if state == "BOOST":
                state = data["props"]["previous"]["mode"]
            await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Mode is {0}", info=[str(state)])
            final = Data.HIVETOHA[self.heatingType].get(state, state)
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_state(self, device):
        """Get heating current state."""
        await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Getting state")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            current_temp = await self.current_temperature(device)
            target_temp = await self.target_temperature(device)
            if current_temp < target_temp:
                state = "ON"
            else:
                state = "OFF"
            await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "State is {0}", info=[str(state)])
            final = Data.HIVETOHA[self.heatingType].get(state, state)
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def current_operation(self, device):
        """Get heating current operation."""
        await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Getting current operation")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = data["props"]["working"]
            await self.logger.log(device["hiveID"], self.heatingType + "_Extra",
                                  "Current operation is {0}", info=[str(state)])
            final = state
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def boost(self, device):
        """Get heating boost current status."""
        await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Getting boost status")
        state = None
        final = None

        if device["hiveID"] in Data.products:
            data = Data.products[device["hiveID"]]
            state = Data.HIVETOHA["Boost"].get(
                data["state"].get("boost", False), "ON")
            await self.logger.log(device["hiveID"], self.heatingType + "_Extra",
                                  "Boost state is {0}", info=[str(state)])
            final = state
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def get_boost_time(self, device):
        """Get heating boost time remaining."""
        if await self.boost(device) == "ON":
            await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Getting boost time")
            state = None
            final = None

            if device["hiveID"] in Data.products:
                data = Data.products[device["hiveID"]]
                state = data["state"]["boost"]
                await self.logger.log(
                    device["hiveID"], self.heatingType, "Time left on boost is {0}", info=[str(state)]
                )
                if device["hiveID"] in Data.errorList:
                    Data.errorList.pop(device["hiveID"])
                final = state
            else:
                await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

            return final
        return None

    @staticmethod
    async def get_operation_modes():
        """Get heating list of possible modes."""
        return ["SCHEDULE", "MANUAL", "OFF"]

    async def get_schedule_now_next_later(self, device):
        """Hive get heating schedule now, next and later."""
        await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Getting schedule")
        state = await self.attr.online_offline(device["device_id"])
        current_mode = await self.get_mode(device)
        state = None
        final = None

        if device["hiveID"] in Data.products:
            if state != "Offline" and current_mode == "SCHEDULE":
                data = Data.products[device["hiveID"]]
                state = await self.p_get_schedule_nnl(
                    data["state"]["schedule"])
                await self.logger.log(device["hiveID"], self.heatingType + "_Extra",
                                      "Schedule is {0}", info=[str(state)])
            await self.logger.error_check(device["hiveID"], self.heatingType + "_Extra", state)
            final = state
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def set_target_temperature(self, device, new_temp):
        """Set heating target temperature."""
        final = False

        if device["hiveID"] in Data.products and device["deviceData"]["online"]:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(data["type"],
                                            device["hiveID"],  target=new_temp)

            if resp["original"] == 200:
                await self.getDevices(device["hiveID"])
                final = True
                await self.logger.log(device["hiveID"], "API", "Temperature set - " + device["hiveName"])
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def set_mode(self, device, new_mode):
        """Set heating mode."""
        await self.hiveRefreshTokens()
        final = False

        if device["hiveID"] in Data.products and device["deviceData"]["online"]:
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(data["type"],
                                            device["hiveID"], mode=new_mode)

            if resp["original"] == 200:
                await self.getDevices(device["hiveID"])
                final = True
                await self.logger.log(device["hiveID"], "API", "Mode updated - " + device["hiveName"])
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_boost_on(self, device, mins, temp):
        """Turn heating boost on."""

        if mins > 0 and temp >= await self.min_temperature(device):
            if temp <= await self.max_temperature(device):
                await self.logger.log(device["hiveID"], self.heatingType + "_Extra", "Enabling boost for {0}")
                await self.hiveRefreshTokens()
                final = False

                if device["hiveID"] in Data.products and device["deviceData"]["online"]:
                    data = Data.products[device["hiveID"]]
                    resp = await self.api.set_state(data["type"],
                                                    device["hiveID"], mode="BOOST", boost=mins, target=temp)

                    if resp["original"] == 200:
                        await self.getDevices(device["hiveID"])
                        final = True
                        await self.logger.log(
                            device["hiveID"], "API", "Boost enabled - " +
                            "" + device["hiveName"]
                        )
                    else:
                        await self.logger.error_check(
                            device["hiveID"], "ERROR", "Failed_API", resp=resp["original"]
                        )

                return final
        return None

    async def turn_boost_off(self, device):
        """Turn heating boost off."""
        await self.logger.log(self.heatingType, "Disabling boost for {0}", device["hiveID"])
        final = False

        if device["hiveID"] in Data.products and device["deviceData"]["online"]:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            await self.getDevices(device["hiveID"])
            if await self.boost(device) == "ON":
                prev_mode = data["props"]["previous"]["mode"]
                if prev_mode == "MANUAL" or prev_mode == "OFF":
                    pre_temp = data["props"]["previous"].get("target", 7)
                    resp = await self.api.set_state(data["type"],
                                                    device["hiveID"],
                                                    mode=prev_mode,
                                                    target=pre_temp)
                else:
                    resp = await self.api.set_state(data["type"],
                                                    device["hiveID"], mode=prev_mode)
                if resp["original"] == 200:
                    await self.getDevices(device["hiveID"])
                    final = True
                    await self.logger.log(
                        device["hiveID"], "API", "Boost disabled - " + "" + device["hiveName"])
                else:
                    await self.logger.error_check(
                        device["hiveID"], "ERROR", "Failed_API", resp=resp["original"]
                    )

        return final
