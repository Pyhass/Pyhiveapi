"""Hive Action Module."""

import json
class HiveAction:
    """Hive Action Code.

    Returns:
        object: Return hive action object.
    """

    action_type = "Actions"

    def __init__(self, session: object = None):
        """Initialise Action.

        Args:
            session (object, optional): session to interact with hive account. Defaults to None.
        """
        self.session = session

    async def get_action(self, device: dict):
        """Action device to update.

        Args:
            device (dict): Device to be updated.

        Returns:
            dict: Updated device.
        """
        dev_data = {}

        if device["hive_id"] in self.session.data.actions:
            dev_data = {
                "hive_id": device["hive_id"],
                "hive_name": device["hive_name"],
                "hive_type": device["hive_type"],
                "ha_name": device["ha_name"],
                "ha_type": device["ha_type"],
                "status": {"state": await self.get_state(device)},
                "power_usage": None,
                "device_data": {},
                "custom": device.get("custom", None),
            }

            self.session.devices.update({device["hive_id"]: dev_data})
            return self.session.devices[device["hive_id"]]

        exists = self.session.data.actions.get("hive_id", False)
        if exists is False:
            return "REMOVE"
        return device

    async def get_state(self, device: dict):
        """Get action state.

        Args:
            device (dict): Device to get state of.

        Returns:
            str: Return state.
        """
        final = None

        try:
            data = self.session.data.actions[device["hive_id"]]
            final = data["enabled"]
        except KeyError as e:
            await self.session.log.error(e)

        return final

    async def set_status_on(self, device: dict):
        """Set action turn on.

        Args:
            device (dict): Device to set state of.

        Returns:
            boolean: True/False if successful.
        """


        final = False

        if device["hive_id"] in self.session.data.actions:
            await self.session.hive_refresh_tokens()
            data = self.session.data.actions[device["hive_id"]]
            data.update({"enabled": True})
            send = json.dumps(data)
            resp = await self.session.api.set_action(device["hive_id"], send)
            if resp["original"] == 200:
                final = True
                await self.session.get_devices()

        return final

    async def set_status_off(self, device: dict):
        """Set action to turn off.

        Args:
            device (dict): Device to set state of.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if device["hive_id"] in self.session.data.actions:
            await self.session.hive_refresh_tokens()
            data = self.session.data.actions[device["hive_id"]]
            data.update({"enabled": False})
            send = json.dumps(data)
            resp = await self.session.api.set_action(device["hive_id"], send)
            if resp["original"] == 200:
                final = True
                await self.session.get_devices()

        return final
