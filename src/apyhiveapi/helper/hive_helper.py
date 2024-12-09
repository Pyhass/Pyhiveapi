"""Helper class for pyhiveapi."""
# pylint: skip-file
import datetime
import operator

from .const import HIVE_TYPES


class HiveHelper:
    """Hive helper class."""

    def __init__(self, session: object = None):
        """Hive Helper.

        Args:
            session (object, optional): Interact with hive account. Defaults to None.
        """
        self.session = session

    def get_device_name(self, n_id: str):
        """Resolve a id into a name.

        Args:
            n_id (str): ID of a device.

        Returns:
            str: Name of device.
        """
        try:
            product_name = self.session.data.products[n_id]["state"]["name"]
        except KeyError:
            product_name = False

        try:
            device_name = self.session.data.devices[n_id]["state"]["name"]
        except KeyError:
            device_name = False

        if product_name:
            return product_name
        elif device_name:
            return device_name
        elif n_id == "No_ID":
            return "Hive"
        else:
            return n_id

    def device_recovered(self, n_id: str):
        """Register that a device has recovered from being offline.

        Args:
            n_id (str): ID of the device.
        """
        # name = HiveHelper.get_device_name(n_id)
        if n_id in self.session.config.errorList:
            self.session.config.errorList.pop(n_id)

    def get_device_from_id(self, n_id: str):
        """Get product/device data from ID.

        Args:
            n_id (str): ID of the device.

        Returns:
            dict: Device data.
        """
        data = False
        try:
            data = self.session.devices[n_id]
        except KeyError:
            pass

        return data

    def get_device_data(self, product: dict):
        """Get device from product data.

        Args:
            product (dict): Product data.

        Returns:
            [type]: Device data.
        """
        device = product
        type = product["type"]
        if type in ("heating", "hotwater"):
            for aDevice in self.session.data.devices:
                if self.session.data.devices[aDevice]["type"] in HIVE_TYPES["Thermo"]:
                    try:
                        if (
                            product["props"]["zone"]
                            == self.session.data.devices[aDevice]["props"]["zone"]
                        ):
                            device = self.session.data.devices[aDevice]
                    except KeyError:
                        pass
        elif type == "trvcontrol":
            device = self.session.data.devices[product["props"]["trvs"][0]]
        elif type == "warmwhitelight" and product["props"]["model"] == "SIREN001":
            device = self.session.data.devices[product["parent"]]
        elif type == "sense":
            device = self.session.data.devices[product["parent"]]
        else:
            device = self.session.data.devices[product["id"]]

        return device

    def convert_minutes_to_time(self, minutes_to_convert: str):
        """Convert minutes string to datetime.

        Args:
            minutes_to_convert (str): minutes in string value.

        Returns:
            timedelta: time object of the minutes.
        """
        hours_converted, minutes_converted = divmod(minutes_to_convert, 60)
        converted_time = datetime.datetime.strptime(
            str(hours_converted) + ":" + str(minutes_converted), "%H:%M"
        )
        converted_time_string = converted_time.strftime("%H:%M")
        return converted_time_string

    def get_schedule_nnl(self, hive_api_schedule: list):
        """Get the schedule now, next and later of a given nodes schedule.

        Args:
            hive_api_schedule (list): Schedule to parse.

        Returns:
            dict: Now, Next and later values.
        """
        schedule_now_and_next = {}
        date_time_now = datetime.datetime.now()
        date_time_now_day_int = date_time_now.today().weekday()

        days_t = (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        )

        days_rolling_list = list(days_t[date_time_now_day_int:] + days_t)[:7]

        full_schedule_list = []

        for day_index in range(0, len(days_rolling_list)):
            current_day_schedule = hive_api_schedule[days_rolling_list[day_index]]
            current_day_schedule_sorted = sorted(
                current_day_schedule,
                key=operator.itemgetter("start"),
                reverse=False,
            )

            for current_slot in range(0, len(current_day_schedule_sorted)):
                current_slot_custom = current_day_schedule_sorted[current_slot]

                slot_date = datetime.datetime.now() + datetime.timedelta(days=day_index)
                slot_time = self.convert_minutes_to_time(current_slot_custom["start"])
                slot_time_date_s = slot_date.strftime("%d-%m-%Y") + " " + slot_time
                slot_time_date_dt = datetime.datetime.strptime(
                    slot_time_date_s, "%d-%m-%Y %H:%M"
                )
                if slot_time_date_dt <= date_time_now:
                    slot_time_date_dt = slot_time_date_dt + datetime.timedelta(days=7)

                current_slot_custom["Start_DateTime"] = slot_time_date_dt
                full_schedule_list.append(current_slot_custom)

        fsl_sorted = sorted(
            full_schedule_list,
            key=operator.itemgetter("Start_DateTime"),
            reverse=False,
        )

        schedule_now = fsl_sorted[-1]
        schedule_next = fsl_sorted[0]
        schedule_later = fsl_sorted[1]

        schedule_now["Start_DateTime"] = schedule_now[
            "Start_DateTime"
        ] - datetime.timedelta(days=7)

        schedule_now["End_DateTime"] = schedule_next["Start_DateTime"]
        schedule_next["End_DateTime"] = schedule_later["Start_DateTime"]
        schedule_later["End_DateTime"] = fsl_sorted[2]["Start_DateTime"]

        schedule_now_and_next["now"] = schedule_now
        schedule_now_and_next["next"] = schedule_next
        schedule_now_and_next["later"] = schedule_later

        return schedule_now_and_next

    def get_heat_on_demand_device(self, device: dict):
        """Use TRV device to get the linked thermostat device.

        Args:
            device ([dictionary]): [The TRV device to lookup.]

        Returns:
            [dictionary]: [Gets the thermostat device linked to TRV.]
        """
        trv = self.session.data.products.get(device["HiveID"])
        thermostat = self.session.data.products.get(trv["state"]["zone"])
        return thermostat

    async def call_sensor_function(self, device):
        """Helper to decide which function to call."""
        if device["hiveType"] == "SMOKE_CO":
            return await self.session.hub.get_smoke_status(device)
        if device["hiveType"] == "DOG_BARK":
            return await self.session.hub.get_dog_bark_status(device)
        if device["hiveType"] == "GLASS_BREAK":
            return await self.session.hub.get_glass_break_status(device)
        if device["hiveType"] == "Camera_Temp":
            return await self.session.camera.getCameraTemperature(device)
        if device["hiveType"] == "Heating_Current_Temperature":
            return await self.session.heating.get_current_temperature(device)
        if device["hiveType"] == "Heating_Target_Temperature":
            return await self.session.heating.get_target_temperature(device)
        if device["hiveType"] == "Heating_State":
            return await self.session.heating.getState(device)
        if device["hiveType"] in ("Heating_Mode", "Hotwater_Mode", "Mode"):
            return await self.session.heating.get_mode(device)
        if device["hiveType"] == "Heating_Boost":
            return await self.session.heating.get_boost_status(device)
        if device["hiveType"] == "Hotwater_State":
            return await self.session.hotwater.getState(device)
        if device["hiveType"] == "Hotwater_Boost":
            return await self.session.hotwater.getBoost(device)
        if device["hiveType"] == "Battery":
            return await self.session.attr.getBattery(device["device_id"])
        if device["hiveType"] in ("Availability", "Connectivity"):
            return await self.online(device)
        if device["hiveType"] == "Power":
            return await self.session.switch.getPowerUsage(device)
        return None

    async def call_products_to_add(self, entity_type, product):
        """Helper to add a product to the list."""
        if entity_type == "sense":
            self.session.add_list(
                "binary_sensor",
                product,
                haName="Glass Detection",
                hiveType="GLASS_BREAK",
            )
            self.session.add_list(
                "binary_sensor", product, haName="Smoke Detection", hiveType="SMOKE_CO"
            )
            self.session.add_list(
                "binary_sensor",
                product,
                haName="Dog Bark Detection",
                hiveType="DOG_BARK",
            )
        if entity_type == "heating":
            self.session.add_list(
                "climate",
                product,
                temperatureunit=self.session.data["user"]["temperatureUnit"],
            )
            self.session.add_list(
                "switch",
                product,
                haName=" Heat on Demand",
                hiveType="Heating_Heat_On_Demand",
                category="config",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Current Temperature",
                hiveType="Heating_Current_Temperature",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Target Temperature",
                hiveType="Heating_Target_Temperature",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" State",
                hiveType="Heating_State",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Mode",
                hiveType="Heating_Mode",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Boost",
                hiveType="Heating_Boost",
                category="diagnostic",
            )
        if entity_type == "trvcontrol":
            self.session.add_list(
                "climate",
                product,
                temperatureunit=self.session.data["user"]["temperatureUnit"],
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Current Temperature",
                hiveType="Heating_Current_Temperature",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Target Temperature",
                hiveType="Heating_Target_Temperature",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" State",
                hiveType="Heating_State",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Mode",
                hiveType="Heating_Mode",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Boost",
                hiveType="Heating_Boost",
                category="diagnostic",
            )
        if entity_type == "hotwater":
            self.session.add_list(
                "water_heater",
                product,
            )
            self.session.add_list(
                "sensor",
                product,
                haName="Hotwater State",
                hiveType="Hotwater_State",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName="Hotwater Mode",
                hiveType="Hotwater_Mode",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName="Hotwater Boost",
                hiveType="Hotwater_Boost",
                category="diagnostic",
            )
        if entity_type == "activeplug":
            self.session.add_list("switch", product)
            self.session.add_list(
                "sensor",
                product,
                haName=" Mode",
                hiveType="Mode",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Availability",
                hiveType="Availability",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Power",
                hiveType="Power",
                category="diagnostic",
            )
        if entity_type == "warmwhitelight":
            self.session.add_list("light", product)
            self.session.add_list(
                "sensor",
                product,
                haName=" Mode",
                hiveType="Mode",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Availability",
                hiveType="Availability",
                category="diagnostic",
            )
        if entity_type == "tuneablelight":
            self.session.add_list("light", product)
            self.session.add_list(
                "sensor",
                product,
                haName=" Mode",
                hiveType="Mode",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Availability",
                hiveType="Availability",
                category="diagnostic",
            )
        if entity_type == "colourtuneablelight":
            self.session.add_list("light", product)
            self.session.add_list(
                "sensor",
                product,
                haName=" Mode",
                hiveType="Mode",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Availability",
                hiveType="Availability",
                category="diagnostic",
            )
        if entity_type == "hivecamera":
            self.session.add_list("camera", product)
            self.session.add_list(
                "sensor",
                product,
                haName=" Mode",
                hiveType="Mode",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Availability",
                hiveType="Availability",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                product,
                haName=" Temperature",
                hiveType="Camera_Temp",
                category="diagnostic",
            )
        if entity_type == "motionsensor":
            self.session.add_list("binary_sensor", product)
        if entity_type == "contactsensor":
            self.session.add_list("binary_sensor", product)
        return None

    async def call_devices_to_add(self, entity_type, device):
        """Helper to add a device to the list."""
        if entity_type == "contactsensor":
            self.session.add_list(
                "sensor",
                device,
                haName=" Battery Level",
                hiveType="Battery",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                device,
                haName=" Availability",
                hiveType="Availability",
                category="diagnostic",
            )
        if entity_type == "hub":
            self.session.add_list(
                "binary_sensor",
                device,
                haName="Hive Hub Status",
                hiveType="Connectivity",
                category="diagnostic",
            )
        if entity_type == "motionsensor":
            self.session.add_list(
                "sensor",
                device,
                haName=" Battery Level",
                hiveType="Battery",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                device,
                haName=" Availability",
                hiveType="Availability",
                category="diagnostic",
            )
        if entity_type == "sense":
            self.session.add_list(
                "binary_sensor",
                device,
                haName="Hive Hub Status",
                hiveType="Connectivity",
            )
        if entity_type == "siren":
            self.session.add_list("alarm_control_panel", device)
        if entity_type == "thermostatui":
            self.session.add_list(
                "sensor",
                device,
                haName=" Battery Level",
                hiveType="Battery",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                device,
                haName=" Availability",
                hiveType="Availability",
                category="diagnostic",
            )
        if entity_type == "trv":
            self.session.add_list(
                "sensor",
                device,
                haName=" Battery Level",
                hiveType="Battery",
                category="diagnostic",
            )
            self.session.add_list(
                "sensor",
                device,
                haName=" Availability",
                hiveType="Availability",
                category="diagnostic",
            )

    async def call_action_to_add(self, action):
        """Helper to add an action to the list."""
        await self.session.add_list(
            "switch",
            action,
            hiveName=action["name"],
            haName=action["name"],
            hiveType="action",
        )
