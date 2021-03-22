"""Hive Alarm Module."""


class HiveHomeShield:
    """Hive homeshield alarm.

    Returns:
        object: Hive homeshield
    """

    alarmType = "Alarm"

    async def getMode(self):
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

    async def getState(self, device: dict):
        """Get the alarm triggered state.

        Returns:
            boolean: True/False if alarm is triggered.
        """
        state = None

        try:
            data = self.session.data.devices[device["hiveID"]]
            state = data["state"]["alarmActive"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def setMode(self, device: dict, mode: str):
        """Set the alarm mode.

        Args:
            device (dict): Alarm device.

        Returns:
            boolean: True/False if successful.
        """
        final = False

        if (
            device["hiveID"] in self.session.data.devices
            and device["deviceData"]["online"]
        ):
            await self.session.hiveRefreshTokens()
            resp = await self.session.api.setAlarm(mode=mode)
            if resp["original"] == 200:
                final = True
                await self.session.getAlarm()

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

    async def getAlarm(self, device: dict):
        """Get alarm data.

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
                    "state": await self.getState(device),
                    "mode": await self.getMode(),
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
