"""Hive Camera Module."""
# pylint: skip-file


class HiveCamera:
    """Hive camera.

    Returns:
        object: Hive camera
    """

    cameraType = "Camera"

    async def get_camera_temperature(self, device: dict):
        """Get the camera state.

        Returns:
            boolean: True/False if camera is on.
        """
        state = None

        try:
            data = self.session.data.devices[device["hiveID"]]
            state = data["props"]["temperature"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def get_camera_state(self, device: dict):
        """Get the camera state.

        Returns:
            boolean: True/False if camera is on.
        """
        state = None

        try:
            data = self.session.data.devices[device["hiveID"]]
            state = True if data["state"]["mode"] == "ARMED" else False
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def get_camera_image_url(self, device: dict):
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
            await self.session.log.error(e)

        return state

    async def get_camera_recording_url(self, device: dict):
        """Get the camera recording url.

        Returns:
            str: image url.
        """
        state = None

        try:
            state = self.session.data.camera[device["hiveID"]]["cameraRecording"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def set_camera_on(self, device: dict, mode: str):
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
            await self.session.hive_refresh_tokens()
            resp = await self.session.api.setState(mode=mode)
            if resp["original"] == 200:
                final = True
                await self.session.get_camera()

        return final

    async def set_camera_off(self, device: dict, mode: str):
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
            await self.session.hive_refresh_tokens()
            resp = await self.session.api.setState(mode=mode)
            if resp["original"] == 200:
                final = True
                await self.session.get_camera()

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

    async def get_camera(self, device: dict):
        """Get camera data.

        Args:
            device (dict): Device to update.

        Returns:
            dict: Updated device.
        """
        device["deviceData"].update(
            {"online": await self.session.attr.onlineOffline(device["device_id"])}
        )
        dev_data = {}

        if device["deviceData"]["online"]:
            self.session.helper.deviceRecovered(device["device_id"])
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
                    "temperature": await self.get_camera_temperature(device),
                    "state": await self.get_camera_state(device),
                    "imageURL": await self.get_camera_image_url(device),
                    "recordingURL": await self.get_camera_recording_url(device),
                },
                "deviceData": data.get("props", None),
                "parentDevice": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.session.attr.stateAttributes(
                    device["device_id"], device["hiveType"]
                ),
            }

            self.session.devices.update({device["hiveID"]: dev_data})
            return self.session.devices[device["hiveID"]]
        else:
            await self.session.log.errorCheck(
                device["device_id"], "ERROR", device["deviceData"]["online"]
            )
            return device
