"""Hive Heating Module."""

from datetime import datetime

from .helper.const import HIVETOHA

class HiveHeating:
    """Hive Heating Code.

    Returns:
        object: heating
    """

    heatingType = "Heating"

    async def get_min_temperature(self, device: dict):
        """Get heating minimum target temperature.

        Args:
            device (dict): Device to get min temp for.

        Returns:
            int: Minimum temperature
        """
        if device["hive_type"] == "nathermostat":
            return self.session.data.products[device["hive_id"]]["props"]["minHeat"]
        return 5

    async def get_max_temperature(self, device: dict):
        """Get heating maximum target temperature.

        Args:
            device (dict): Device to get max temp for.

        Returns:
            int: Maximum temperature
        """
        if device["hive_type"] == "nathermostat":
            return self.session.data.products[device["hive_id"]]["props"]["maxHeat"]
        return 32

    async def get_current_temperature(self, device: dict):
        """Get heating current temperature.

        Args:
            device (dict): Device to get current temperature for.

        Returns:
            float: current temperature
        """

        f_state = None
        state = None
        final = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["props"]["temperature"]

            if device["hive_id"] in self.session.data.min_max:
                if self.session.data.min_max[device["hive_id"]]["TodayDate"] == str(
                    datetime.date(datetime.now())
                ):
                    if state < self.session.data.min_max[device["hive_id"]]["TodayMin"]:
                        self.session.data.min_max[device["hive_id"]]["TodayMin"] = state

                    if state > self.session.data.min_max[device["hive_id"]]["TodayMax"]:
                        self.session.data.min_max[device["hive_id"]]["TodayMax"] = state
                else:
                    data = {
                        "TodayMin": state,
                        "TodayMax": state,
                        "TodayDate": str(datetime.date(datetime.now())),
                    }
                    self.session.data.min_max[device["hive_id"]].update(data)

                if state < self.session.data.min_max[device["hive_id"]]["RestartMin"]:
                    self.session.data.min_max[device["hive_id"]]["RestartMin"] = state

                if state > self.session.data.min_max[device["hive_id"]]["RestartMax"]:
                    self.session.data.min_max[device["hive_id"]]["RestartMax"] = state
            else:
                data = {
                    "TodayMin": state,
                    "TodayMax": state,
                    "TodayDate": str(datetime.date(datetime.now())),
                    "RestartMin": state,
                    "RestartMax": state,
                }
                self.session.data.min_max[device["hive_id"]] = data

            f_state = round(float(state), 1)
            final = f_state
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def get_target_temperature(self, device: dict):
        """Get heating target temperature.

        Args:
            device (dict): Device to get target temperature for.

        Returns:
            str: Target temperature.
        """
        state = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = float(data["state"].get("target", None))
            state = float(data["state"].get("heat", state))
        except (KeyError, TypeError) as e:
            await self.session.log.error(e)

        return state

    async def get_mode(self, device: dict):
        """Get heating current mode.

        Args:
            device (dict): Device to get current mode for.

        Returns:
            str: Current Mode
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["state"]["mode"]
            if state == "BOOST":
                state = data["props"]["previous"]["mode"]
            final = HIVETOHA[self.heatingType].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def get_state(self, device: dict):
        """Get heating current state.

        Args:
            device (dict): Device to get state for.

        Returns:
            str: Current state.
        """
        state = None
        final = None

        try:
            current_temp = await self.get_current_temperature(device)
            target_temp = await self.get_target_temperature(device)
            if current_temp < target_temp:
                state = "ON"
            else:
                state = "OFF"
            final = HIVETOHA[self.heatingType].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def get_current_operation(self, device: dict):
        """Get heating current operation.

        Args:
            device (dict): Device to get current operation for.

        Returns:
            str: Current operation.
        """
        state = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["props"]["working"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def get_boost_status(self, device: dict):
        """Get heating boost current status.

        Args:
            device (dict): Device to get boost status for.

        Returns:
            str: Boost status.
        """
        state = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = HIVETOHA["Boost"].get(data["state"].get("boost", False), "ON")
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def get_boost_time(self, device: dict):
        """Get heating boost time remaining.

        Args:
            device (dict): device to get boost time for.

        Returns:
            str: Boost time.
        """
        if await self.get_boost_status(device) == "ON":
            state = None

            try:
                data = self.session.data.products[device["hive_id"]]
                state = data["state"]["boost"]
            except KeyError as e:
                await self.session.log.error(e)

            return state
        return None

    async def get_heat_on_demand(self, device):
        """Get heat on demand status.

        Args:
            device ([dictionary]): [Get Heat on Demand status for Thermostat device.]

        Returns:
            str: [Return True or False for the Heat on Demand status.]
        """
        state = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["props"]["autoBoost"]["active"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    @staticmethod
    async def get_operation_modes():
        """Get heating list of possible modes.

        Returns:
            list: Operation modes.
        """
        return ["SCHEDULE", "MANUAL", "OFF"]

    async def set_target_temperature(self, device: dict, new_temp: str):
        """Set heating target temperature.

        Args:
            device (dict): Device to set target temperature for.
            new_temp (str): New temperature.

        Returns:
            boolean: True/False if successful
        """
        await self.session.hive_refresh_tokens()
        final = False

        if (
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device["hive_id"]]
            resp = await self.session.api.set_state(
                data["type"], device["hive_id"], target=new_temp
            )

            if resp["original"] == 200:
                await self.session.get_devices(device["hive_id"])
                final = True

        return final

    async def set_mode(self, device: dict, new_mode: str):
        """Set heating mode.

        Args:
            device (dict): Device to set mode for.
            new_mode (str): New mode to be set.

        Returns:
            boolean: True/False if successful
        """
        await self.session.hive_refresh_tokens()
        final = False

        if (
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            data = self.session.data.products[device["hive_id"]]
            resp = await self.session.api.set_state(
                data["type"], device["hive_id"], mode=new_mode
            )

            if resp["original"] == 200:
                await self.session.get_devices(device["hive_id"])
                final = True

        return final

    async def set_boost_on(self, device: dict, mins: str, temp: float):
        """Turn heating boost on.

        Args:
            device (dict): Device to boost.
            mins (str): Number of minutes to boost for.
            temp (float): Temperature to boost to.

        Returns:
            boolean: True/False if successful
        """
        if int(mins) > 0 and int(temp) >= await self.get_min_temperature(device):
            if int(temp) <= await self.get_max_temperature(device):
                await self.session.hive_refresh_tokens()
                final = False

                if (
                    device["hive_id"] in self.session.data.products
                    and device["device_data"]["online"]
                ):
                    data = self.session.data.products[device["hive_id"]]
                    resp = await self.session.api.set_state(
                        data["type"],
                        device["hive_id"],
                        mode="BOOST",
                        boost=mins,
                        target=temp,
                    )

                    if resp["original"] == 200:
                        await self.session.get_devices(device["hive_id"])
                        final = True

                return final
        return None

    async def set_boost_off(self, device: dict):
        """Turn heating boost off.

        Args:
            device (dict): Device to update boost for.

        Returns:
            boolean: True/False if successful
        """
        final = False

        if (
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device["hive_id"]]
            await self.session.get_devices(device["hive_id"])
            if await self.get_boost_status(device) == "ON":
                prev_mode = data["props"]["previous"]["mode"]
                if prev_mode in ("MANUAL", "OFF"):
                    pre_temp = data["props"]["previous"].get("target", 7)
                    resp = await self.session.api.set_state(
                        data["type"],
                        device["hive_id"],
                        mode=prev_mode,
                        target=pre_temp,
                    )
                else:
                    resp = await self.session.api.set_state(
                        data["type"], device["hive_id"], mode=prev_mode
                    )
                if resp["original"] == 200:
                    await self.session.get_devices(device["hive_id"])
                    final = True

        return final

    async def set_heat_on_demand(self, device: dict, state: str):
        """Enable or disable Heat on Demand for a Thermostat.

        Args:
            device ([dictionary]): [This is the Thermostat device you want to update.]
            state ([str]): [This is the state you want to set. (Either "ENABLED" or "DISABLED")]

        Returns:
            [boolean]: [Return True or False if the Heat on Demand was set successfully.]
        """
        final = False

        if (
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            data = self.session.data.products[device["hive_id"]]
            await self.session.hive_refresh_tokens()
            resp = await self.session.api.set_state(
                data["type"], device["hive_id"], autoBoost=state
            )

            if resp["original"] == 200:
                await self.session.get_devices(device["hive_id"])
                final = True

        return final


class Climate(HiveHeating):
    """Climate class for Home Assistant.

    Args:
        Heating (object): Heating class
    """

    def __init__(self, session: object = None):
        """Initialise heating.

        Args:
            session (object, optional): Used to interact with hive account. Defaults to None.
        """
        self.session = session

    async def get_climate(self, device: dict):
        """Get heating data.

        Args:
            device (dict): Device to update.

        Returns:
            dict: Updated device.
        """
        device["device_data"].update(
            {"online": await self.session.attr.online_offline(device["device_id"])}
        )

        if device["device_data"]["online"]:
            dev_data = {}
            self.session.helper.device_recovered(device["device_id"])
            data = self.session.data.devices[device["device_id"]]
            dev_data = {
                "hive_id": device["hive_id"],
                "hive_name": device["hive_name"],
                "hive_type": device["hive_type"],
                "ha_name": device["ha_name"],
                "ha_type": device["ha_type"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "temperatureunit": device["temperatureunit"],
                "min_temp": await self.get_min_temperature(device),
                "max_temp": await self.get_max_temperature(device),
                "status": {
                    "current_temperature": await self.get_current_temperature(device),
                    "target_temperature": await self.get_target_temperature(device),
                    "action": await self.get_current_operation(device),
                    "mode": await self.get_mode(device),
                    "boost": await self.get_boost_status(device),
                },
                "device_data": data.get("props", None),
                "parent_device": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.session.attr.state_attributes(
                    device["device_id"], device["hive_type"]
                ),
            }
            self.session.devices.update({device["hive_id"]: dev_data})
            return self.session.devices[device["hive_id"]]

        await self.session.log.error_check(
            device["device_id"], device["device_data"]["online"]
        )
        return device

    async def get_schedule_now_next_later(self, device: dict):
        """Hive get heating schedule now, next and later.

        Args:
            device (dict): Device to get schedule for.

        Returns:
            dict: Schedule now, next and later
        """
        online = await self.session.attr.online_offline(device["device_id"])
        current_mode = await self.get_mode(device)
        state = None

        try:
            if online and current_mode == "SCHEDULE":
                data = self.session.data.products[device["hive_id"]]
                state = self.session.helper.get_schedule_nnl(data["state"]["schedule"])
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def min_max_temperature(self, device: dict):
        """Min/Max Temp.

        Args:
            device (dict): device to get min/max temperature for.

        Returns:
            dict: Shows min/max temp for the day.
        """
        state = None
        final = None

        try:
            state = self.session.data.min_max[device["hive_id"]]
            final = state
        except KeyError as e:
            await self.session.log.error(e)

        return final
