"""Hive Device Attribute Module."""
from .custom_logging import Logger
from .hive_data import Data


class Attributes:
    """Device Attributes Code."""

    def __init__(self):
        self.log = Logger()
        self.type = "Attribute"

    async def state_attributes(self, n_id, _type):
        """Get HA State Attributes"""
        from .hive_session import Session
        await self.log.log(n_id, "Extra", "Getting Attribute data")
        attr = {}

        if n_id in Data.products or n_id in Data.devices:
            attr.update({"available": (await self.online_offline(n_id))})
            if n_id in Data.BATTERY:
                battery = await self.battery(n_id)
                if battery is not None:
                    attr.update({"battery": str(battery) + "%"})
            if n_id in Data.MODE:
                attr.update({"mode": (await self.get_mode(n_id))})

            if _type in Data.HIVE_TYPES["Sensor"]:
                data = Data.products[n_id]
                rec = data["props"].get("presenceLastChanged", False)
                if rec:
                    trim = "{:10.10}".format(str(rec))
                    time = await Session.epochtime(
                        trim, "%d-%m-%Y %H:%M:%S", "from_epoch")
                    attr.update({"state_changed": time})

        await self.log.log(n_id, "Extra", "Attribute data {0}", info=attr)
        return attr

    async def online_offline(self, n_id):
        """Check if device is online"""
        state = None
        final = None

        if n_id in Data.devices:
            data = Data.devices[n_id]
            state = data["props"]["online"]
            final = state
            Data.NODES[n_id]["Availabile"] = final
        else:
            await self.log.error_check(n_id, "ERROR", "Failed")

        return final if final is None else Data.NODES[n_id]["Availabile"]

    async def get_mode(self, n_id):
        """Get sensor mode."""
        online = await self.online_offline(n_id)
        state = None
        final = None

        if n_id in Data.products:
            if online:
                data = Data.products[n_id]
                state = data["state"]["mode"]
            await self.log.error_check(n_id, self.type, state)
            final = Data.HIVETOHA[self.type].get(state, state)
            Data.NODES[n_id]["Device_Mode"] = final
        else:
            await self.log.error_check(n_id, "ERROR", "Failed")

        return final if final is None else Data.NODES[n_id]["Device_Mode"]

    async def battery(self, n_id):
        """Get device battery level."""
        online = await self.online_offline(n_id)
        state = None
        final = None

        if n_id in Data.devices:
            if online:
                data = Data.devices[n_id]
                state = data["props"]["battery"]
                final = state
                Data.NODES[n_id]["BatteryLevel"] = final
            await self.log.error_check(n_id, self.type, state)
        else:
            await self.log.error_check(n_id, "ERROR", "Failed")

        return final if final is None else Data.NODES[n_id]["BatteryLevel"]
