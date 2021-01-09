""""Hive Heating Module. """
from .helper.hive_data import Data
from .session import Session


class Heating(Session):
    """Hive Heating Code."""

    heatingType = "Heating"

    async def get_heating(self, device):
        await self.logger.log(
            device["hiveID"], self.heatingType, "Getting heating data."
        )
        device["deviceData"].update(
            {"online": await self.attr.online_offline(device["device_id"])}
        )

        if device["deviceData"]["online"]:
            dev_data = {}
            self.helper.deviceRecovered(device["device_id"])
            data = Data.devices[device["device_id"]]
            dev_data = {
                "hiveID": device["hiveID"],
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
                    "current_temperature": await self.current_temperature(
                        device
                    ),
                    "target_temperature": await self.target_temperature(
                        device
                    ),
                    "action": await self.current_operation(device),
                    "mode": await self.get_mode(device),
                    "boost": await self.boost(device),
                },
                "deviceData": data.get("props", None),
                "parentDevice": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.attr.state_attributes(
                    device["device_id"], device["hiveType"]
                ),
            }
            await self.logger.log(
                device["hiveID"],
                self.heatingType,
                "Device update {0}",
                info=[dev_data["status"]],
            )
            Data.ha_devices.update({device["hiveID"]: dev_data})
            return Data.ha_devices[device["hiveID"]]
        else:
            await self.logger.error_check(
                device["device_id"], "ERROR", device["deviceData"]["online"]
            )
            return device

    @staticmethod
    async def min_temperature(device):
        """Get heating minimum target temperature."""
        if device["hiveType"] == "nathermostat":
            return Data.products[device["hiveID"]]["props"]["minHeat"]
        return 5

    @staticmethod
    async def max_temperature(device):
        """Get heating maximum target temperature."""
        if device["hiveType"] == "nathermostat":
            return Data.products[device["hiveID"]]["props"]["maxHeat"]
        return 32

    async def current_temperature(self, device):
        """Get heating current temperature."""
        from datetime import datetime

        f_state = None
        state = None
        final = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["props"]["temperature"]

            if device["hiveID"] in Data.minMax:
                if Data.minMax[device["hiveID"]]["TodayDate"] != datetime.date(
                    datetime.now()
                ):
                    Data.minMax[device["hiveID"]]["TodayMin"] = 1000
                    Data.minMax[device["hiveID"]]["TodayMax"] = -1000
                    Data.minMax[device["hiveID"]]["TodayDate"] = datetime.date(
                        datetime.now()
                    )

                    if state < Data.minMax[device["hiveID"]]["TodayMin"]:
                        Data.minMax[device["hiveID"]]["TodayMin"] = state

                    if state > Data.minMax[device["hiveID"]]["TodayMax"]:
                        Data.minMax[device["hiveID"]]["TodayMax"] = state

                    if state < Data.minMax[device["hiveID"]]["RestartMin"]:
                        Data.minMax[device["hiveID"]]["RestartMin"] = state

                    if state > Data.minMax[device["hiveID"]]["RestartMax"]:
                        Data.minMax[device["hiveID"]]["RestartMax"] = state
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
            await self.logger.log(
                device["hiveID"],
                self.heatingType + "_Extra",
                "Current Temp is {0}",
                info=[str(state)],
            )

            final = f_state
        except KeyError as e:
            await self.logger.error(e)

        return final

    async def minmax_temperatures(self, device):
        """Min/Max Temp"""
        state = None
        final = None

        try:
            state = Data.minMax[device["hiveID"]]
            final = state
        except KeyError as e:
            await self.logger.error(e)

        return final

    async def target_temperature(self, device):
        """Get heating target temperature."""
        state = None

        try:
            data = Data.products[device["hiveID"]]
            state = float(data["state"].get("target", None))
            state = float(data["state"].get("heat", state))
        except (KeyError, TypeError) as e:
            await self.logger.error(e)

        return state

    async def get_mode(self, device):
        """Get heating current mode."""
        state = None
        final = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["state"]["mode"]
            if state == "BOOST":
                state = data["props"]["previous"]["mode"]
            final = Data.HIVETOHA[self.heatingType].get(state, state)
        except KeyError as e:
            await self.logger.error(e)

        return final

    async def get_state(self, device):
        """Get heating current state."""
        state = None
        final = None

        try:
            current_temp = await self.current_temperature(device)
            target_temp = await self.target_temperature(device)
            if current_temp < target_temp:
                state = "ON"
            else:
                state = "OFF"
            final = Data.HIVETOHA[self.heatingType].get(state, state)
        except KeyError as e:
            await self.logger.error(e)

        return final

    async def current_operation(self, device):
        """Get heating current operation."""
        state = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["props"]["working"]
        except KeyError as e:
            await self.logger.error(e)

        return state

    async def boost(self, device):
        """Get heating boost current status."""
        state = None

        try:
            data = Data.products[device["hiveID"]]
            state = Data.HIVETOHA["Boost"].get(
                data["state"].get("boost", False), "ON"
            )
        except KeyError as e:
            await self.logger.error(e)

        return state

    async def get_boost_time(self, device):
        """Get heating boost time remaining."""
        if await self.boost(device) == "ON":
            state = None

            try:
                data = Data.products[device["hiveID"]]
                state = data["state"]["boost"]
            except KeyError as e:
                await self.logger.error(e)

            return state
        return None

    @staticmethod
    async def get_operation_modes():
        """Get heating list of possible modes."""
        return ["SCHEDULE", "MANUAL", "OFF"]

    async def get_schedule_now_next_later(self, device):
        """Hive get heating schedule now, next and later."""
        state = await self.attr.online_offline(device["device_id"])
        current_mode = await self.get_mode(device)

        try:
            if state != "Offline" and current_mode == "SCHEDULE":
                data = Data.products[device["hiveID"]]
                state = await self.helper.getScheduleNNL(
                    data["state"]["schedule"]
                )
        except KeyError as e:
            await self.logger.error(e)

        return state

    async def set_target_temperature(self, device, new_temp):
        """Set heating target temperature."""
        await self.hiveRefreshTokens()
        final = False

        if (
            device["hiveID"] in Data.products
            and device["deviceData"]["online"]
        ):
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(
                data["type"], device["hiveID"], target=new_temp
            )

            if resp["original"] == 200:
                await self.getDevices(device["hiveID"])
                final = True

        return final

    async def set_mode(self, device, new_mode):
        """Set heating mode."""
        await self.hiveRefreshTokens()
        final = False

        if (
            device["hiveID"] in Data.products
            and device["deviceData"]["online"]
        ):
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(
                data["type"], device["hiveID"], mode=new_mode
            )

            if resp["original"] == 200:
                await self.getDevices(device["hiveID"])
                final = True

        return final

    async def turn_boost_on(self, device, mins, temp):
        """Turn heating boost on."""

        if mins > 0 and temp >= await self.min_temperature(device):
            if temp <= await self.max_temperature(device):
                await self.hiveRefreshTokens()
                final = False

                if (
                    device["hiveID"] in Data.products
                    and device["deviceData"]["online"]
                ):
                    data = Data.products[device["hiveID"]]
                    resp = await self.api.set_state(
                        data["type"],
                        device["hiveID"],
                        mode="BOOST",
                        boost=mins,
                        target=temp,
                    )

                    if resp["original"] == 200:
                        await self.getDevices(device["hiveID"])
                        final = True

                return final
        return None

    async def turn_boost_off(self, device):
        """Turn heating boost off."""
        final = False

        if (
            device["hiveID"] in Data.products
            and device["deviceData"]["online"]
        ):
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            await self.getDevices(device["hiveID"])
            if await self.boost(device) == "ON":
                prev_mode = data["props"]["previous"]["mode"]
                if prev_mode == "MANUAL" or prev_mode == "OFF":
                    pre_temp = data["props"]["previous"].get("target", 7)
                    resp = await self.api.set_state(
                        data["type"],
                        device["hiveID"],
                        mode=prev_mode,
                        target=pre_temp,
                    )
                else:
                    resp = await self.api.set_state(
                        data["type"], device["hiveID"], mode=prev_mode
                    )
                if resp["original"] == 200:
                    await self.getDevices(device["hiveID"])
                    final = True

        return final
