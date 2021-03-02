"""Hive Hotwater Module."""

from .helper.const import HIVETOHA


class Hotwater:
    """Hive Hotwater Code."""

    hotwaterType = "Hotwater"

    def __init__(self, session=None):
        """Initialise hotwater."""
        self.session = session

    async def getHotwater(self, device):
        """Get light data."""
        await self.session.log.log(
            device["hiveID"], self.hotwaterType, "Getting hot water data."
        )
        device["deviceData"].update(
            {"online": await self.session.attr.onlineOffline(device["device_id"])}
        )

        if device["deviceData"]["online"]:

            dev_data = {}
            self.session.helper.deviceRecovered(device["device_id"])
            data = self.session.data.devices[device["device_id"]]
            dev_data = {
                "hiveID": device["hiveID"],
                "hiveName": device["hiveName"],
                "hiveType": device["hiveType"],
                "haName": device["haName"],
                "haType": device["haType"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "status": {"current_operation": await self.getMode(device)},
                "deviceData": data.get("props", None),
                "parentDevice": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.session.attr.stateAttributes(
                    device["device_id"], device["hiveType"]
                ),
            }

            await self.session.log.log(
                device["hiveID"],
                self.hotwaterType,
                "Device update {0}",
                info=dev_data["status"],
            )
            self.session.devices.update({device["hiveID"]: dev_data})
            return self.session.devices[device["hiveID"]]
        else:
            await self.session.log.errorCheck(
                device["device_id"], "ERROR", device["deviceData"]["online"]
            )
            return device

    async def getMode(self, device):
        """Get hotwater current mode."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["mode"]
            if state == "BOOST":
                state = data["props"]["previous"]["mode"]
            final = HIVETOHA[self.hotwaterType].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    @staticmethod
    async def getOperationModes():
        """Get heating list of possible modes."""
        return ["SCHEDULE", "ON", "OFF"]

    async def getBoost(self, device):
        """Get hot water current boost status."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["boost"]
            final = HIVETOHA["Boost"].get(state, "ON")
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getBoostTime(self, device):
        """Get hotwater boost time remaining."""
        state = None
        if await self.getBoost(device) == "ON":
            try:
                data = self.session.data.products[device["hiveID"]]
                state = data["state"]["boost"]
            except KeyError as e:
                await self.session.log.error(e)

        return state

    async def getState(self, device):
        """Get hot water current state."""
        state = None
        final = None

        try:
            data = self.session.data.products[device["hiveID"]]
            state = data["state"]["status"]
            mode_current = await self.getMode(device)
            if mode_current == "SCHEDULE":
                if await self.getBoost(device) == "ON":
                    state = "ON"
                else:
                    snan = self.session.helper.getScheduleNNL(data["state"]["schedule"])
                    state = snan["now"]["value"]["status"]

            final = HIVETOHA[self.hotwaterType].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def getScheduleNowNextLater(self, device):
        """Hive get hotwater schedule now, next and later."""
        state = None

        try:
            mode_current = await self.getMode(device)
            if mode_current == "SCHEDULE":
                data = self.session.data.products[device["hiveID"]]
                state = self.session.helper.getScheduleNNL(data["state"]["schedule"])
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def setMode(self, device, new_mode):
        """Set hot water mode."""
        final = False

        if device["hiveID"] in self.session.data.products:
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device["hiveID"]]
            resp = await self.session.api.setState(
                data["type"], device["hiveID"], mode=new_mode
            )
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

        return final

    async def turnBoostOn(self, device, mins):
        """Turn hot water boost on."""
        final = False

        if (
            mins > 0
            and device["hiveID"] in self.session.data.products
            and device["deviceData"]["online"]
        ):
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device["hiveID"]]
            resp = await self.session.api.setState(
                data["type"], device["hiveID"], mode="BOOST", boost=mins
            )
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

        return final

    async def turnBoostOff(self, device):
        """Turn hot water boost off."""
        final = False

        if (
            device["hiveID"] in self.session.data.products
            and await self.getBoost(device) == "ON"
            and device["deviceData"]["online"]
        ):
            await self.session.hiveRefreshTokens()
            data = self.session.data.products[device["hiveID"]]
            prev_mode = data["props"]["previous"]["mode"]
            resp = await self.session.api.setState(
                data["type"], device["hiveID"], mode=prev_mode
            )
            if resp["original"] == 200:
                await self.session.getDevices(device["hiveID"])
                final = True

        return final
