"""Hive Action Module."""

# pylint: skip-file
import logging

_LOGGER = logging.getLogger(__name__)


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
        if self.session.should_use_cached_data():
            cached = self.session.get_cached_device(device)
            if cached is not None:
                _LOGGER.debug(
                    "Returning cached state for action %s (slow/busy poll).",
                    device["haName"],
                )
                return cached
        dev_data = {}

        if device["hiveID"] in self.data["action"]:
            dev_data = {
                "hiveID": device["hiveID"],
                "hiveName": device["hiveName"],
                "hiveType": device["hiveType"],
                "haName": device["haName"],
                "haType": device["haType"],
                "status": {"state": await self.getState(device)},
                "power_usage": None,
                "deviceData": {},
                "custom": device.get("custom", None),
            }

            return self.session.set_cached_device(device, dev_data)
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
            data = self.session.data.actions[device["hiveID"]]
            final = data["enabled"]
        except KeyError as e:
            _LOGGER.error(e)

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

        if device["hiveID"] in self.session.data.actions:
            _LOGGER.debug("Enabling action %s.", device["haName"])
            await self.session.hiveRefreshTokens()
            data = self.session.data.actions[device["hiveID"]]
            data.update({"enabled": True})
            send = json.dumps(data)
            resp = await self.session.api.setAction(device["hiveID"], send)
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

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

        if device["hiveID"] in self.session.data.actions:
            _LOGGER.debug("Disabling action %s.", device["haName"])
            await self.session.hiveRefreshTokens()
            data = self.session.data.actions[device["hiveID"]]
            data.update({"enabled": False})
            send = json.dumps(data)
            resp = await self.session.api.setAction(device["hiveID"], send)
            if resp["original"] == 200:
                final = True
                await self.session.getDevices(device["hiveID"])

        return final
