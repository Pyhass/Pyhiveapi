"""Hive Alarm Module."""


class HiveHomeShield:
    """Hive homeshield alarm.

    Returns:
        object: Hive homeshield
    """

    alarm_type = "Alarm"

    async def get_mode(self):
        """Get current mode of the alarm.

        Returns:
            str: Mode if the alarm [armed_home, armed_away, armed_night]
        """
        state = None

        try:
            data = self.session.data.alarm
            state = data["mode"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def get_state(self, device: dict):
        """Get the alarm triggered state.

        Returns:
            boolean: True/False if alarm is triggered.
        """
        state = None

        try:
            data = self.session.data.devices[device["hive_id"]]
            state = data["state"]["alarmActive"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def set_mode(self, device: dict, mode: str):
        """Set the alarm mode.

        Args:
            device (dict): Alarm device.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hive_id"] in self.session.data.devices
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            resp = await self.session.api.set_alarm(mode=mode)
            if resp["original"] == 200:
                final = True
                await self.session.get_alarm()

        return final


class Alarm(HiveHomeShield):
    """Home assistant alarm.

    Args:
        HiveHomeShield (object): Class object.
    """

    def __init__(self, session: object = None):
        """Initialise alarm.

        Args:
            session (object, optional): Used to interact with the hive account. Defaults to None.
        """
        self.session = session

    async def get_alarm(self, device: dict):
        """Get alarm data.

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
                    "state": await self.get_state(device),
                    "mode": await self.get_mode(),
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

        await self.session.log.error_check(
            device["device_id"], device["device_data"]["online"]
        )
        return device
