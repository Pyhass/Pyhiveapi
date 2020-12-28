"""Hive Action Module."""
from .hive_session import Session
from .hive_data import Data


class Action(Session):
    """Hive Action Code."""
    actionType = 'Actions'

    async def get_action(self, device):
        """Get smart plug current power usage."""
        await self.logger.log(device["hiveID"], self.actionType, "Getting action data.")
        dev_data = {}

        if device["hiveID"] in Data.actions:
            dev_data = {"hiveID": device["hiveID"],
                        "hiveName": device["hiveName"],
                        "hiveType": device["hiveType"],
                        "haName": device["haName"],
                        "haType": device["haType"],
                        "status": {
                            "state": await self.get_state(device)},
                        "power_usage": None,
                        "deviceData": {},
                        "custom": device.get("custom", None)
                        }

            await self.logger.log(device["hiveID"], self.actionType,
                                  "action update {0}", info=[dev_data["status"]])
            Data.ha_devices.update({device['hiveID']: dev_data})
            return dev_data
        else:
            exists = Data.actions.get('hiveID', False)
            if exists == False:
                return 'REMOVE'
            return device

    async def get_state(self, device):
        """Get action state."""
        await self.logger.log(device["hiveID"], self.actionType + "_Extra", "Getting state")
        state = None
        final = None

        if device["hiveID"] in Data.actions:
            data = Data.actions[device["hiveID"]]
            final = data["enabled"]
            await self.logger.log(device["hiveID"], self.actionType + "_Extra", "Status is {0}", info=[final])
            if device["hiveID"] in Data.errorList:
                Data.errorList.pop(device["hiveID"])
        else:
            await self.logger.error_check(device["hiveID"], "ERROR", "Failed")

        return final

    async def turn_on(self, device):
        """Set action turn on."""
        import json
        await self.logger.log(device["hiveID"], self.actionType + "_Extra", "Enabling action")
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
                await self.logger.log(device["hiveID"], "API", "Enabled action - " + device["hiveName"])
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final

    async def turn_off(self, device):
        """Set action to turn off."""
        import json
        await self.logger.log(device["hiveID"], self.actionType + "_Extra", "Disabling action")
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
                await self.logger.log(device["hiveID"], "API", "Disabled action - " + device["hiveName"])
            else:
                await self.logger.error_check(
                    device["hiveID"], "ERROR", "Failed_API", resp=resp["original"])

        return final
