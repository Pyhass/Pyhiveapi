"""Hive Switch Module."""
# pylint: skip-file
from .helper.const import HIVETOHA


class HiveSmartPlug:
    """Plug Device.

    Returns:
        object: Returns Plug object
    """

    plug_type = "Switch"

    async def get_state(self, device: dict):
        """Get smart plug state.

        Args:
            device (dict): Device to get the plug state for.

        Returns:
            boolean: Returns True or False based on if the plug is on
        """
        state = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["state"]["status"]
            state = HIVETOHA["Switch"].get(state, state)
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def get_power_usage(self, device: dict):
        """Get smart plug current power usage.

        Args:
            device (dict): [description]

        Returns:
            [type]: [description]
        """
        state = None

        try:
            data = self.session.data.products[device["hive_id"]]
            state = data["props"]["powerConsumption"]
        except KeyError as e:
            await self.session.log.error(e)

        return state

    async def set_status_on(self, device: dict):
        """Set smart plug to turn on.

        Args:
            device (dict): Device to switch on.

        Returns:
            boolean: True/False if successful
        """
        final = False

        if (
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device["hive_id"]]
            resp = await self.session.api.set_state(
                data["type"], data["id"], status="ON"
            )
            if resp["original"] == 200:
                final = True
                await self.session.get_devices()

        return final

    async def set_status_off(self, device: dict):
        """Set smart plug to turn off.

        Args:
            device (dict): Device to switch off.

        Returns:
            boolean: True/False if successful
        """
        final = False

        if (
            device["hive_id"] in self.session.data.products
            and device["device_data"]["online"]
        ):
            await self.session.hive_refresh_tokens()
            data = self.session.data.products[device["hive_id"]]
            resp = await self.session.api.set_state(
                data["type"], data["id"], status="OFF"
            )
            if resp["original"] == 200:
                final = True
                await self.session.get_devices()

        return final


class Switch(HiveSmartPlug):
    """Home Assistant switch class.

    Args:
        SmartPlug (Class): Initialises the Smartplug Class.
    """

    def __init__(self, session: object):
        """Initialise switch.

        Args:
            session (object): This is the session object to interact with the current session.
        """
        self.session = session

    async def get_switch(self, device: dict):
        """Home assistant wrapper to get switch device.

        Args:
            device (dict): Device to be update.

        Returns:
            dict: Return device after update is complete.
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
                    "state": await self.get_switch_state(device),
                },
                "device_data": data.get("props", None),
                "parent_device": data.get("parent", None),
                "custom": device.get("custom", None),
                "attributes": {},
            }

            if device["hive_type"] == "activeplug":
                dev_data.update(
                    {
                        "status": {
                            "state": dev_data["status"]["state"],
                            "power_usage": await self.get_power_usage(device),
                        },
                        "attributes": await self.session.attr.state_attributes(
                            device["device_id"], device["hive_type"]
                        ),
                    }
                )

            self.session.devices.update({device["hive_id"]: dev_data})
            return self.session.devices[device["hive_id"]]
        else:
            await self.session.log.error_check(
                device["device_id"], "ERROR", device["device_data"]["online"]
            )
            return device

    async def get_switch_state(self, device: dict):
        """Home Assistant wrapper to get updated switch state.

        Args:
            device (dict): Device to get state for

        Returns:
            boolean: Return True or False for the state.
        """
        if device["hive_type"] == "Heating_Heat_On_Demand":
            return await self.session.heating.get_heat_on_demand(device)
        else:
            return await self.get_state(device)

    async def turn_on(self, device: dict):
        """Home Assisatnt wrapper for turning switch on.

        Args:
            device (dict): Device to switch on.

        Returns:
            function: Calls relevant function.
        """
        if device["hive_type"] == "Heating_Heat_On_Demand":
            return await self.session.heating.set_heat_on_demand(device, "ENABLED")
        else:
            return await self.set_status_on(device)

    async def turn_off(self, device: dict):
        """Home Assisatnt wrapper for turning switch off.

        Args:
            device (dict): Device to switch off.

        Returns:
            function: Calls relevant function.
        """
        if device["hive_type"] == "Heating_Heat_On_Demand":
            return await self.session.heating.set_heat_on_demand(device, "DISABLED")
        else:
            return await self.set_status_off(device)
