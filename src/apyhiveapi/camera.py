"""Hive Camera Module."""
# pylint: skip-file


class HiveCamera:
    """Hive camera.

    Returns:
        object: Hive camera
    """

    camera_type = "Camera"

    async def get_camera_temperature(self, device: dict):
        """Get the camera state.

        Returns:
            boolean: True/False if camera is on.
        """
        state = None

        try:
            data = self.session.data.devices[device["hive_id"]]
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
            data = self.session.data.devices[device["hive_id"]]
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
            state = self.session.data.camera[device["hive_id"]]["camera_image"][
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
            state = self.session.data.camera[device["hive_id"]]["camera_recording"]
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
            device["hive_id"] in self.session.data.devices
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            resp = await self.session.api.set_state(mode=mode)
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
            device["hive_id"] in self.session.data.devices
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            resp = await self.session.api.set_state(mode=mode)
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
        device["device_data"].update(
            {"online": await self.session.attr.online_offline(device["device_id"])}
        )
        dev_data = {}

        if device["device_data"]["online"]:
            self.session.helper.device_recovered(device["device_id"])
            data = self.session.data.devices[device["device_id"]]
            dev_data = {
                "hive_id": device["hive_id"],
                "hive_name": device["hive_name"],
                "hive_type": device["hive_type"],
                "ha_name": device["ha_name"],
                "ha_type": device["ha_type"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "status": {
                    "temperature": await self.get_camera_temperature(device),
                    "state": await self.get_camera_state(device),
                    "image_url": await self.get_camera_image_url(device),
                    "recording_url": await self.get_camera_recording_url(device),
                },
                "device_data": data.get("props", None),
                "parent_device": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": await self.session.attr.state_attributes(
                    device["device_id"], device["hive_type"]
                ),
            }

            self.session.devices.update({device["hive_id"]: dev_data})
            return self.session.devices[device["hive_id"]]
        else:
            await self.session.log.error_check(
                device["device_id"], "ERROR", device["device_data"]["online"]
            )
            return device
