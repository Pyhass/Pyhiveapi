"""Hive Camera Module."""

# pylint: skip-file


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
            data = self.session.data.devices[device.hive_id]
            state = data["props"]["temperature"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def getCameraState(self, device: dict):
        """Get the camera state.

        Returns:
            boolean: True/False if camera is on.
        """
        state = None

        try:
            data = self.session.data.devices[device.hive_id]
            state = True if data["state"]["mode"] == "ARMED" else False
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def getCameraImageURL(self, device: dict):
        """Get the camera image url.

        Returns:
            str: image url.
        """
        state = None

        try:
            state = self.session.data.camera[device.hive_id]["cameraImage"][
                "thumbnailUrls"
            ][0]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def getCameraRecodringURL(self, device: dict):
        """Get the camera recording url.

        Returns:
            str: image url.
        """
        state = None

        try:
            state = self.session.data.camera[device.hive_id]["cameraRecording"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def setCameraOn(self, device: dict, mode: str):
        """Set the camera state to on.

        Args:
            device (dict): Camera device.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if device.hive_id in self.session.data.devices and device.device_data["online"]:
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

        if device.hive_id in self.session.data.devices and device.device_data["online"]:
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
        device.device_data.update(
            {"online": await self.session.attr.onlineOffline(device["device_id"])}
        )
        dev_data = {}

        if device.device_data["online"]:
            self.session.helper.deviceRecovered(device["device_id"])
            data = self.session.data.devices[device["device_id"]]
            dev_data = {
                "hiveID": device.hive_id,
                "hiveName": device.hive_name,
                "hiveType": device.hive_type,
                "haName": device.ha_name,
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
                    device["device_id"], device.hive_type
                ),
            }

            self.session.devices.update({device.hive_id: dev_data})
            return self.session.devices[device.hive_id]
        else:
            await self.session.log.errorCheck(
                device["device_id"], "ERROR", device.device_data["online"]
            )
            return device
