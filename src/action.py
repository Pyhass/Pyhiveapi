"""Hive Action Module."""

# pylint: skip-file


class HiveAction:
    """Hive Action Code.

    Returns:
        object: Return hive action object.
    """

    actionType = "Actions"

    def __init__(self, session: object = None):
        """Initialise Action.

        Args:
            session (object, optional): session to interact with hive account. Defaults to None.
        """
        self.session = session

    async def getAction(self, device: dict):
        """Action device to update.

        Args:
            device (dict): Device to be updated.

        Returns:
            dict: Updated device.
        """
        dev_data = {}

        if device.hive_id in self.data["action"]:
            dev_data = {
                "hiveID": device.hive_id,
                "hiveName": device.hive_name,
                "hiveType": device.hive_type,
                "haName": device.ha_name,
                "haType": device.ha_type,
                "status": {"state": await self.getState(device)},
                "power_usage": None,
                "deviceData": {},
                "custom": getattr(device, "custom", None),
            }

            self.session.devices.update({device.hive_id: dev_data})
            return self.session.devices[device.hive_id]
        else:
            exists = self.session.data.actions.get("hiveID", False)
            if exists is False:
                return "REMOVE"
            return device

    async def getState(self, device: dict):
        """Get action state.

        Args:
            device (dict): Device to get state of.

        Returns:
            str: Return state.
        """
        final = None

        try:
            data = self.session.data.actions[device.hive_id]
            final = data["enabled"]
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def setStatusOn(self, device: dict):
        """Set action turn on.

        Args:
            device (dict): Device to set state of.

        Returns:
            boolean: True/False if successful.
        """
        import json

        final = False

        if device.hive_id in self.session.data.actions:
            await self.session.hiveRefreshTokens()
            data = self.session.data.actions[device.hive_id]
            data.update({"enabled": True})
            send = json.dumps(data)
            resp = await self.session.api.setAction(device.hive_id, send)
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device.hive_id)

        return final

    async def setStatusOff(self, device: dict):
        """Set action to turn off.

        Args:
            device (dict): Device to set state of.

        Returns:
            boolean: True/False if successful.
        """
        import json

        final = False

        if device.hive_id in self.session.data.actions:
            await self.session.hiveRefreshTokens()
            data = self.session.data.actions[device.hive_id]
            data.update({"enabled": False})
            send = json.dumps(data)
            resp = await self.session.api.setAction(device.hive_id, send)
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device.hive_id)

        return final
