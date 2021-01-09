""""Hive Hotwater Module. """
from .helper.hive_data import Data
from .session import Session


class Hotwater(Session):
    """Hive Hotwater Code."""

    hotwaterType = "Hotwater"

    async def get_hotwater(self, device):
        """Get light data."""
        await self.logger.log(
            device["hiveID"], self.hotwaterType, "Getting hot water data."
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
                "status": {"current_operation": await self.get_mode(device)},
                "deviceData": data.get("props", None),
                "parentDevice": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.attr.state_attributes(
                    device["device_id"], device["hiveType"]
                ),
            }

            await self.logger.log(
                device["hiveID"],
                self.hotwaterType,
                "Device update {0}",
                info=dev_data["status"],
            )
            Data.ha_devices.update({device["hiveID"]: dev_data})
            return Data.ha_devices[device["hiveID"]]
        else:
            await self.logger.error_check(
                device["device_id"], "ERROR", device["deviceData"]["online"]
            )
            return device

    async def get_mode(self, device):
        """Get hotwater current mode."""
        state = None
        final = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["state"]["mode"]
            if state == "BOOST":
                state = data["props"]["previous"]["mode"]
            final = Data.HIVETOHA[self.hotwaterType].get(state, state)
        except KeyError as e:
            await self.logger.error(e)

        return final

    @staticmethod
    async def get_operation_modes():
        """Get heating list of possible modes."""
        return ["SCHEDULE", "ON", "OFF"]

    async def get_boost(self, device):
        """Get hot water current boost status."""
        state = None
        final = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["state"]["boost"]
            final = Data.HIVETOHA["Boost"].get(state, "ON")
        except KeyError as e:
            await self.logger.error(e)

        return final

    async def get_boost_time(self, device):
        """Get hotwater boost time remaining."""
        state = None
        if await self.get_boost(device) == "ON":
            try:
                data = Data.products[device["hiveID"]]
                state = data["state"]["boost"]
            except KeyError as e:
                await self.logger.error(e)

        return state

    async def get_state(self, device):
        """Get hot water current state."""
        state = None
        final = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["state"]["status"]
            mode_current = await self.get_mode(device)
            if mode_current == "SCHEDULE":
                if await self.get_boost(device) == "ON":
                    state = "ON"
                else:
                    snan = await self.helper.getScheduleNNL(
                        data["state"]["schedule"]
                    )
                    state = snan["now"]["value"]["status"]

            final = Data.HIVETOHA[self.hotwaterType].get(state, state)
        except KeyError as e:
            await self.logger.error(e)

        return final

    async def get_schedule_now_next_later(self, device):
        """Hive get hotwater schedule now, next and later."""
        state = None

        try:
            mode_current = await self.get_mode(device)
            if mode_current == "SCHEDULE":
                data = Data.products[device["hiveID"]]
                state = await self.helper.getScheduleNNL(
                    data["state"]["schedule"]
                )
        except KeyError as e:
            await self.logger.error(e)

        return state

    async def set_mode(self, device, new_mode):
        """Set hot water mode."""
        final = False

        if device["hiveID"] in Data.products:
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(
                data["type"], device["hiveID"], mode=new_mode
            )
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])

        return final

    async def turn_boost_on(self, device, mins):
        """Turn hot water boost on."""
        final = False

        if (
            mins > 0
            and device["hiveID"] in Data.products
            and device["deviceData"]["online"]
        ):
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(
                data["type"], device["hiveID"], mode="BOOST", boost=mins
            )
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])

        return final

    async def turn_boost_off(self, device):
        """Turn hot water boost off."""
        final = False

        if (
            device["hiveID"] in Data.products
            and await self.get_boost(device) == "ON"
            and device["deviceData"]["online"]
        ):
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            prev_mode = data["props"]["previous"]["mode"]
            resp = await self.api.set_state(
                data["type"], device["hiveID"], mode=prev_mode
            )
            if resp["original"] == 200:
                await self.getDevices(device["hiveID"])
                final = True

        return final
