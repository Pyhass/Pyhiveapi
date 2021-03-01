"""Hive Action Module."""


class Action:
    """Hive Action Code."""

    actionType = "Actions"

    def __init__(self, session=None):
        """Initialise Action."""
        self.session = session

    async def get_action(self, device):
        """Get smart plug current power usage."""
        dev_data = {}

        if device["hiveID"] in self.data["action"]:
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

            self.session.devices.update({device["hiveID"]: dev_data})
            return self.session.devices[device["hiveID"]]
        else:
            exists = self.session.data.actions.get("hiveID", False)
            if exists is False:
                return "REMOVE"
            return device

    async def get_state(self, device):
        """Get action state."""
        final = None

        try:
            data = self.session.data.actions[device["hiveID"]]
            final = data["enabled"]
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def turn_on(self, device):
        """Set action turn on."""
        import json

        final = False

        if device["hiveID"] in self.session.data.actions:
            await self.session.hiveRefreshTokens()
            data = self.session.data.actions[device["hiveID"]]
            data.update({"enabled": True})
            send = json.dumps(data)
            resp = await self.session.api.setAction(device["hiveID"], send)
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

        return final

    async def turn_off(self, device):
        """Set action to turn off."""
        import json

        final = False

        if device["hiveID"] in self.session.data.actions:
            await self.session.hiveRefreshTokens()
            data = self.session.data.actions[device["hiveID"]]
            data.update({"enabled": False})
            send = json.dumps(data)
            resp = await self.session.api.setAction(device["hiveID"], send)
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

        return final
