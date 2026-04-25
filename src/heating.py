"""Hive Heating Module."""

# pylint: skip-file
import logging

from .helper.const import HIVETOHA

_LOGGER = logging.getLogger(__name__)


class HiveHeating:
    """Hive Heating Code.

    Returns:
        object: heating
    """

    heatingType = "Heating"

    async def getMinTemperature(self, device: dict):
        """Get heating minimum target temperature.

        Args:
            device (dict): Device to get min temp for.

        Returns:
            int: Minimum temperature
        """
        if device["hiveType"] == "nathermostat":
            return self.session.data.products[device["hiveID"]]["props"]["minHeat"]
        return 5

    async def getMaxTemperature(self, device: dict):
        """Get heating maximum target temperature.

        Args:
            device (dict): Device to get max temp for.

        Returns:
            int: Maximum temperature
        """
        if device["hiveType"] == "nathermostat":
            return self.session.data.products[device["hiveID"]]["props"]["maxHeat"]
        return 32

    async def getCurrentTemperature(self, device: dict):
        """Get heating current temperature.

        Args:
            device (dict): Device to get current temperature for.

        Returns:
            float: current temperature
        """
        from datetime import datetime

        state = None
        final = None
        device_name = device.get("haName", device.get("hiveID", "Unknown"))

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["props"]["temperature"]

            try:
                state = float(state)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "getCurrentTemperature - Non-numeric temperature value '%s' for %s.",
                    state,
                    device_name,
                )
                return None

            if device["hiveID"] in self.session.data.minMax:
                if self.session.data.minMax[device["hiveID"]]["TodayDate"] == str(
                    datetime.date(datetime.now())
                ):
                    if state < self.session.data.minMax[device["hiveID"]]["TodayMin"]:
                        self.session.data.minMax[device["hiveID"]]["TodayMin"] = state

                    if state > self.session.data.minMax[device["hiveID"]]["TodayMax"]:
                        self.session.data.minMax[device["hiveID"]]["TodayMax"] = state
                else:
                    data = {
                        "TodayMin": state,
                        "TodayMax": state,
                        "TodayDate": str(datetime.date(datetime.now())),
                    }
                    self.session.data.minMax[device["hiveID"]].update(data)

                if state < self.session.data.minMax[device["hiveID"]]["RestartMin"]:
                    self.session.data.minMax[device["hiveID"]]["RestartMin"] = state

                if state > self.session.data.minMax[device["hiveID"]]["RestartMax"]:
                    self.session.data.minMax[device["hiveID"]]["RestartMax"] = state
            else:
                data = {
                    "TodayMin": state,
                    "TodayMax": state,
                    "TodayDate": str(datetime.date(datetime.now())),
                    "RestartMin": state,
                    "RestartMax": state,
                }
                self.session.data.minMax[device["hiveID"]] = data

            final = round(state, 1)
        except KeyError as e:
            _LOGGER.error(
                "getCurrentTemperature - KeyError getting temperature for %s: %s",
                device_name,
                str(e),
            )

        return final

    async def getTargetTemperature(self, device: dict):
        """Get heating target temperature.

        Args:
            device (dict): Device to get target temperature for.

        Returns:
            float: Target temperature or None if invalid
        """
        state = None
        device_name = device.get("haName", device.get("hiveID", "Unknown"))

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"].get("target", None)
            if state is None:
                state = data["state"].get("heat", None)

            if state is not None:
                try:
                    state = float(state)
                except (ValueError, TypeError):
                    _LOGGER.warning(
                        "getTargetTemperature - Non-numeric target temperature value '%s' for %s.",
                        state,
                        device_name,
                    )
                    return None
        except (KeyError, TypeError) as e:
            _LOGGER.error(
                "getTargetTemperature - Error getting target temperature for %s: %s",
                device_name,
                str(e),
            )

        return state

    async def getMode(self, device: dict):
        """Get heating current mode.

        Args:
            device (dict): Device to get current mode for.

        Returns:
            str: Current Mode
        """
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["mode"]
            if state == "BOOST":
                state = data["props"]["previous"]["mode"]
            final = HIVETOHA[self.heatingType].get(state, state)
        except KeyError as e:
            _LOGGER.error(e)

        return final

    async def getState(self, device: dict):
        """Get heating current state.

        Args:
            device (dict): Device to get state for.

        Returns:
            str: Current state.
        """
        state = None
        final = None

        try:
            current_temp = await self.getCurrentTemperature(device)
            target_temp = await self.getTargetTemperature(device)
            if current_temp is not None and target_temp is not None:
                if current_temp < target_temp:
                    state = "ON"
                else:
                    state = "OFF"
                final = HIVETOHA[self.heatingType].get(state, state)
        except (KeyError, TypeError) as e:
            _LOGGER.error(e)

        return final

    async def getCurrentOperation(self, device: dict):
        """Get heating current operation.

        Args:
            device (dict): Device to get current operation for.

        Returns:
            str: Current operation.
        """
        state = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["props"]["working"]
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def getBoostStatus(self, device: dict):
        """Get heating boost current status.

        Args:
            device (dict): Device to get boost status for.

        Returns:
            str: Boost status.
        """
        state = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = HIVETOHA["Boost"].get(data["state"].get("boost", False), "ON")
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def getBoostTime(self, device: dict):
        """Get heating boost time remaining.

        Args:
            device (dict): device to get boost time for.

        Returns:
            str: Boost time.
        """
        if await self.getBoostStatus(device) == "ON":
            state = None

            try:
                data = self.session.data.products[device["hiveID"]]
                state = data["state"]["boost"]
            except KeyError as e:
                _LOGGER.error(e)

            return state
        return None

    async def getHeatOnDemand(self, device):
        """Get heat on demand status.

        Args:
            device ([dictionary]): [Get Heat on Demand status for Thermostat device.]

        Returns:
            str: [Return True or False for the Heat on Demand status.]
        """
        state = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["props"]["autoBoost"]["active"]
        except KeyError as e:
            _LOGGER.error(e)

        return state

    @staticmethod
    async def getOperationModes():
        """Get heating list of possible modes.

        Returns:
            list: Operation modes.
        """
        return ["SCHEDULE", "MANUAL", "OFF"]

    async def setTargetTemperature(self, device: dict, new_temp: str):
        """Set heating target temperature.

        Args:
            device (dict): Device to set target temperature for.
            new_temp (str): New temperature.

        Returns:
            boolean: True/False if successful
        """
        device_name = device.get("haName", device.get("hiveID", "Unknown"))
        _LOGGER.info(
            "setTargetTemperature - Setting target temperature to %s°C for %s",
            new_temp,
            device_name,
        )

        await self.session.hiveRefreshTokens()
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            _LOGGER.debug(
                "setTargetTemperature - Device %s is online, proceeding with temperature change",
                device_name,
            )
            data = self.session.data.products[device["hiveID"]]
            resp = await self.session.api.setState(
                data["type"], device["hiveID"], target=new_temp
            )

            if resp["original"] == 200:
                _LOGGER.debug(
                    "setTargetTemperature - Temperature set successfully for %s, refreshing device data",
                    device_name,
                )
                await self.session.getDevices(device["hiveID"])
                final = True
            else:
                _LOGGER.error(
                    "setTargetTemperature - Failed to set temperature for %s, response: %s",
                    device_name,
                    resp["original"],
                )
        else:
            _LOGGER.warning(
                "setTargetTemperature - Device %s not found or offline, cannot set temperature",
                device_name,
            )

        return final

    async def setMode(self, device: dict, new_mode: str):
        """Set heating mode.

        Args:
            device (dict): Device to set mode for.
            new_mode (str): New mode to be set.

        Returns:
            boolean: True/False if successful
        """
        device_name = device.get("haName", device.get("hiveID", "Unknown"))
        _LOGGER.info(
            "setMode - Setting heating mode to %s for %s", new_mode, device_name
        )

        await self.session.hiveRefreshTokens()
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            _LOGGER.debug(
                "setMode - Device %s is online, proceeding with mode change",
                device_name,
            )
            data = self.session.data.products[device["hiveID"]]
            resp = await self.session.api.setState(
                data["type"], device["hiveID"], mode=new_mode
            )

            if resp["original"] == 200:
                _LOGGER.debug(
                    "setMode - Mode set successfully for %s, refreshing device data",
                    device_name,
                )
                await self.session.getDevices(device["hiveID"])
                final = True
            else:
                _LOGGER.error(
                    "setMode - Failed to set mode for %s, response: %s",
                    device_name,
                    resp["original"],
                )
        else:
            _LOGGER.warning(
                "setMode - Device %s not found or offline, cannot set mode", device_name
            )

        return final

    async def setBoostOn(self, device: dict, mins: str, temp: float):
        """Turn heating boost on.

        Args:
            device (dict): Device to boost.
            mins (str): Number of minutes to boost for.
            temp (float): Temperature to boost to.

        Returns:
            boolean: True/False if successful
        """
        if int(mins) > 0 and int(temp) >= await self.getMinTemperature(device):
            if int(temp) <= await self.getMaxTemperature(device):
                await self.session.hiveRefreshTokens()
                final = False

                if (
                    device["hiveID"] in self.session.data.products
                    and device["deviceData"]["online"]
                ):
                    _LOGGER.debug(
                        "setBoostOn - Setting heating boost ON for %s: %s mins at %s degrees.",
                        device["haName"],
                        mins,
                        temp,
                    )
                    data = self.session.data.products[device["hiveID"]]
                    resp = await self.session.api.setState(
                        data["type"],
                        device["hiveID"],
                        mode="BOOST",
                        boost=mins,
                        target=temp,
                    )

                    if resp["original"] == 200:
                        await self.session.getDevices(device["hiveID"])
                        final = True

                return final
        return None

    async def setBoostOff(self, device: dict):
        """Turn heating boost off.

        Args:
            device (dict): Device to update boost for.

        Returns:
            boolean: True/False if successful
        """
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            _LOGGER.debug(
                "setBoostOff - Setting heating boost OFF for %s.", device["haName"]
            )
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device["hiveID"]]
            await self.session.getDevices(device["hiveID"])
            if await self.getBoostStatus(device) == "ON":
                prev_mode = data["props"]["previous"]["mode"]
                if prev_mode == "MANUAL" or prev_mode == "OFF":
                    pre_temp = data["props"]["previous"].get("target", 7)
                    resp = await self.session.api.setState(
                        data["type"],
                        device["hiveID"],
                        mode=prev_mode,
                        target=pre_temp,
                    )
                else:
                    resp = await self.session.api.setState(
                        data["type"], device["hiveID"], mode=prev_mode
                    )
                if resp["original"] == 200:
                    await self.session.getDevices(device["hiveID"])
                    final = True

        return final

    async def setHeatOnDemand(self, device: dict, state: str):
        """Enable or disable Heat on Demand for a Thermostat.

        Args:
            device ([dictionary]): [This is the Thermostat device you want to update.]
            state ([str]): [This is the state you want to set. (Either "ENABLED" or "DISABLED")]

        Returns:
            [boolean]: [Return True or False if the Heat on Demand was set successfully.]
        """
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            _LOGGER.debug(
                "setHeatOnDemand - Setting heat on demand to %s for %s.",
                state,
                device["haName"],
            )
            data = self.session.data.products[device["hiveID"]]
            await self.session.hiveRefreshTokens()
            resp = await self.session.api.setState(
                data["type"], device["hiveID"], autoBoost=state
            )

            if resp["original"] == 200:
                await self.session.getDevices(device["hiveID"])
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

    async def getClimate(self, device: dict):
        """Get heating data.

        Args:
            device (dict): Device to update.

        Returns:
            dict: Updated device.
        """
        if self.session.shouldUseCachedData():
            cached = self.session.getCachedDevice(device)
            if cached is not None:
                _LOGGER.debug(
                    "getClimate - Returning cached state for climate %s (slow/busy poll).",
                    device["haName"],
                )
                return cached
        device["deviceData"].update(
            {"online": await self.session.attr.onlineOffline(device["device_id"])}
        )

        if device["deviceData"]["online"]:
            dev_data = {}
            self.session.helper.deviceRecovered(device["device_id"])
            _LOGGER.debug(
                "getClimate - Updating climate data for %s.", device["haName"]
            )
            data = self.session.data.devices[device["device_id"]]
            dev_data = {
                "hiveID": device["hiveID"],
                "hiveName": device["hiveName"],
                "hiveType": device["hiveType"],
                "haName": device["haName"],
                "haType": device["haType"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "temperatureunit": device["temperatureunit"],
                "min_temp": await self.getMinTemperature(device),
                "max_temp": await self.getMaxTemperature(device),
                "status": {
                    "current_temperature": await self.getCurrentTemperature(device),
                    "target_temperature": await self.getTargetTemperature(device),
                    "action": await self.getCurrentOperation(device),
                    "mode": await self.getMode(device),
                    "boost": await self.getBoostStatus(device),
                },
                "deviceData": data.get("props", None),
                "parentDevice": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.session.attr.stateAttributes(
                    device["device_id"], device["hiveType"]
                ),
            }
            _LOGGER.debug(
                "getHeating - Heating device data for %s: %s",
                device["haName"],
                dev_data["status"],
            )
            return self.session.setCachedDevice(device, dev_data)
        else:
            await self.session.helper.errorCheck(
                device["device_id"], "ERROR", device["deviceData"]["online"]
            )
            device.setdefault(
                "status",
                {
                    "current_temperature": None,
                    "target_temperature": None,
                    "action": None,
                    "mode": None,
                    "boost": None,
                    "state": None,
                },
            )
            return device

    async def getScheduleNowNextLater(self, device: dict):
        """Hive get heating schedule now, next and later.

        Args:
            device (dict): Device to get schedule for.

        Returns:
            dict: Schedule now, next and later
        """
        online = await self.session.attr.onlineOffline(device["device_id"])
        current_mode = await self.getMode(device)
        state = None

        try:
            if online and current_mode == "SCHEDULE":
                data = self.session.data.products[device["hiveID"]]
                state = self.session.helper.getScheduleNNL(data["state"]["schedule"])
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def minmaxTemperature(self, device: dict):
        """Min/Max Temp.

        Args:
            device (dict): device to get min/max temperature for.

        Returns:
            dict: Shows min/max temp for the day.
        """
        state = None
        final = None

        try:
            state = self.session.data.minMax[device["hiveID"]]
            final = state
        except KeyError as e:
            _LOGGER.error(e)

        return final
