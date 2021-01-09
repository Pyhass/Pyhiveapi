"""Hive Action Module."""
from .helper.hive_data import Data
from .session import Session


class Action(Session):
    """Hive Action Code."""

    actionType = "Actions"

    async def get_action(self, device):
        """Get smart plug current power usage."""
        await self.logger.log(
            device["hiveID"], self.actionType, "Getting action data."
        )
        dev_data = {}

        if device["hiveID"] in Data.actions:
            dev_data = {
                "hiveID": device["hiveID"],
                "hiveName": device["hiveName"],
                "hiveType": device["hiveType"],
                "haName": device["haName"],
                "haType": device["haType"],
                "status": {"state": await self.get_state(device)},
                "power_usage": None,
                "deviceData": {},
                "custom": device.get("custom", None),
            }

            await self.logger.log(
                device["hiveID"],
                self.actionType,
                "action update {0}",
                info=[dev_data["status"]],
            )
            Data.ha_devices.update({device["hiveID"]: dev_data})
            return Data.ha_devices[device["hiveID"]]
        else:
            exists = Data.actions.get("hiveID", False)
            if exists is False:
                return "REMOVE"
            return device

    async def get_state(self, device):
        """Get action state."""
        final = None

        try:
            data = Data.actions[device["hiveID"]]
            final = data["enabled"]
        except KeyError as e:
            await self.logger.error(e)

        return final

    async def turn_on(self, device):
        """Set action turn on."""
        import json

        final = False

        if device["hiveID"] in Data.actions:
            await self.hiveRefreshTokens()
            data = Data.actions[device["hiveID"]]
            data.update({"enabled": True})
            send = json.dumps(data)
            resp = await self.api.set_action(device["hiveID"], send)
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])

        return final

    async def turn_off(self, device):
        """Set action to turn off."""
        import json

        final = False

        if device["hiveID"] in Data.actions:
            await self.hiveRefreshTokens()
            data = Data.actions[device["hiveID"]]
            data.update({"enabled": False})
            send = json.dumps(data)
            resp = await self.api.set_action(device["hiveID"], send)
            if resp["original"] == 200:
                final = True
                await self.getDevices(device["hiveID"])

        return final
