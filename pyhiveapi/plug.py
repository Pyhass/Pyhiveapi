"""Hive Switch Module."""
from .helper.hive_data import Data
from .session import Session


class Plug(Session):
    """Hive Switch Code."""

    plugType = "Switch"

    async def get_plug(self, device):
        """Get smart plug data."""
        await self.logger.log(
            device["hiveID"], self.plugType, "Getting switch data."
        )
        device["deviceData"].update(
            {"online": await self.attr.online_offline(device["device_id"])}
        )
        dev_data = {}

        if device["deviceData"]["online"]:
            self.helper.deviceRecovered(device["device_id"])
            data = Data.devices[device["hiveID"]]
            dev_data = {
                "hiveID": device["hiveID"],
                "hiveName": device["hiveName"],
                "hiveType": device["hiveType"],
                "haName": device["haName"],
                "haType": device["haType"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "status": {
                    "state": await self.get_state(device),
                    "power_usage": await self.get_power_usage(device),
                },
                "deviceData": data.get("props", None),
                "parentDevice": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.attr.state_attributes(
                    device["hiveID"], device["hiveType"]
                ),
            }

            await self.logger.log(
                device["hiveID"],
                self.plugType,
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

    async def get_state(self, device):
        """Get plug current state."""
        state = None
        final = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["state"]["status"]
            final = Data.HIVETOHA["Switch"].get(state, state)
        except KeyError as e:
            await self.logger.error(e)

        return final

    async def get_power_usage(self, device):
        """Get smart plug current power usage."""
        state = None

        try:
            data = Data.products[device["hiveID"]]
            state = data["props"]["powerConsumption"]
        except KeyError as e:
            await self.logger.error(e)

        return state

    async def turn_on(self, device):
        """Set smart plug to turn on."""
        final = False

        if (
            device["hiveID"] in Data.products
            and device["deviceData"]["online"]
        ):
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(
                data["type"], data["id"], status="ON"
            )
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])

        return final

    async def turn_off(self, device):
        """Set smart plug to turn off."""
        final = False

        if (
            device["hiveID"] in Data.products
            and device["deviceData"]["online"]
        ):
            await self.hiveRefreshTokens()
            data = Data.products[device["hiveID"]]
            resp = await self.api.set_state(
                data["type"], data["id"], status="OFF"
            )
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])

        return final
