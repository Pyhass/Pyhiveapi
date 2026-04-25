"""Hive Camera Module."""

# pylint: skip-file
import logging

_LOGGER = logging.getLogger(__name__)


class HiveCamera:
    """Hive camera.

    Returns:
        object: Hive camera
    """

    cameraType = "Camera"

    async def getCameraTemperature(self, device: dict):
        """Get the camera state.

        Returns:
            boolean: True/False if camera is on.
        """
        state = None

        try:
            data = self.session.data.devices[device["hiveID"]]
            state = data["props"]["temperature"]
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def getCameraState(self, device: dict):
        """Get the camera state.

        Returns:
            boolean: True/False if camera is on.
        """
        state = None

        try:
            data = self.session.data.devices[device["hiveID"]]
            state = True if data["state"]["mode"] == "ARMED" else False
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def getCameraImageURL(self, device: dict):
        """Get the camera image url.

        Returns:
            str: image url.
        """
        state = None

        try:
            state = self.session.data.camera[device["hiveID"]]["cameraImage"][
                "thumbnailUrls"
            ][0]
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def getCameraRecodringURL(self, device: dict):
        """Get the camera recording url.

        Returns:
            str: image url.
        """
        state = None

        try:
            state = self.session.data.camera[device["hiveID"]]["cameraRecording"]
        except KeyError as e:
            _LOGGER.error(e)

        return state

    async def setCameraOn(self, device: dict, mode: str):
        """Set the camera state to on.

        Args:
            device (dict): Camera device.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hiveID"] in self.session.data.devices
            and device["deviceData"]["online"]
        ):
            _LOGGER.debug("setCameraOn - Setting camera ON for %s.", device["haName"])
            await self.session.hiveRefreshTokens()
            resp = await self.session.api.setState(mode=mode)
            if resp["original"] == 200:
                final = True
                await self.session.getCamera()

        return final

    async def setCameraOff(self, device: dict, mode: str):
        """Set the camera state to on.

        Args:
            device (dict): Camera device.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hiveID"] in self.session.data.devices
            and device["deviceData"]["online"]
        ):
            _LOGGER.debug("setCameraOff - Setting camera OFF for %s.", device["haName"])
            await self.session.hiveRefreshTokens()
            resp = await self.session.api.setState(mode=mode)
            if resp["original"] == 200:
                final = True
                await self.session.getCamera()

        return final


class Camera(HiveCamera):
    """Home assistant camera.

    Args:
        HiveCamera (object): Class object.
    """

    def __init__(self, session: object = None):
        """Initialise camera.

        Args:
            session (object, optional): Used to interact with the hive account. Defaults to None.
        """
        self.session = session

    async def getCamera(self, device: dict):
        """Get camera data.

        Args:
            device (dict): Device to update.

        Returns:
            dict: Updated device.
        """
        if self.session.shouldUseCachedData():
            cached = self.session.getCachedDevice(device)
            if cached is not None:
                _LOGGER.debug(
                    "getCamera - Returning cached state for camera %s (slow/busy poll).",
                    device["haName"],
                )
                return cached
        device["deviceData"].update(
            {"online": await self.session.attr.onlineOffline(device["device_id"])}
        )
        dev_data = {}

        if device["deviceData"]["online"]:
            self.session.helper.deviceRecovered(device["device_id"])
            _LOGGER.debug("getCamera - Updating camera data for %s.", device["haName"])
            data = self.session.data.devices[device["device_id"]]
            dev_data = {
                "hiveID": device["hiveID"],
                "hiveName": device["hiveName"],
                "hiveType": device["hiveType"],
                "haName": device["haName"],
                "haType": device["haType"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "status": {
                    "temperature": await self.getCameraTemperature(device),
                    "state": await self.getCameraState(device),
                    "imageURL": await self.getCameraImageURL(device),
                    "recordingURL": await self.getCameraRecodringURL(device),
                },
                "deviceData": data.get("props", None),
                "parentDevice": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.session.attr.stateAttributes(
                    device["device_id"], device["hiveType"]
                ),
            }

            return self.session.setCachedDevice(device, dev_data)
        else:
            await self.session.helper.errorCheck(
                device["device_id"], "ERROR", device["deviceData"]["online"]
            )
            device.setdefault("status", {"state": None})
            return device
