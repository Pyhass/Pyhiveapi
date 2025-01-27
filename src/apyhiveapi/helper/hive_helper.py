"""Helper class for pyhiveapi."""

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
        if device_name:
            return device_name
        if n_id == "No_ID":
            return "Hive"

        return n_id

    def device_recovered(self, n_id: str):
        """Register that a device has recovered from being offline.

        Args:
            n_id (str): ID of the device.
        """
        # name = HiveHelper.get_device_name(n_id)
        if n_id in self.session.config.error_list:
            self.session.config.error_list.pop(n_id)

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
        device_type = product["type"]
        if device_type in ("heating", "hotwater"):
            for a_device in self.session.data.devices:
                if self.session.data.devices[a_device]["type"] in HIVE_TYPES["Thermo"]:
                    try:
                        if (
                            product["props"]["zone"]
                            == self.session.data.devices[a_device]["props"]["zone"]
                        ):
                            device = self.session.data.devices[a_device]
                    except KeyError:
                        pass
        elif device_type == "trvcontrol":
            trv_present = len(product["props"]["trvs"]) > 0
            if trv_present:
                device = self.session.data.devices[product["props"]["trvs"][0]]
            else:
                raise KeyError
        elif device_type == "warmwhitelight" and product["props"]["model"] == "SIREN001":
            device = self.session.data.devices[product["parent"]]
        elif device_type == "sense":
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

    def get_schedule_nnl(self, hive_api_schedule: list) -> dict:
        """Get the schedule now, next, and later of a given node's schedule.

        Args:
            hive_api_schedule (list): Schedule to parse.

        Returns:
            dict: Now, Next, and later values.
        """
        schedule_now_and_next = {}
        now = datetime.datetime.now()
        day_int = now.weekday()

        days_t = (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        )

        days_rolling_list = list(days_t[day_int:] + days_t[:day_int])

        full_schedule_list = []

        for day_index, day_name in enumerate(days_rolling_list):
            current_day_schedule = hive_api_schedule.get(day_name, [])
            current_day_schedule_sorted = sorted(
                current_day_schedule,
                key=operator.itemgetter("start"),
                reverse=False,
            )

            for current_slot_custom in current_day_schedule_sorted:
                slot_date = now + datetime.timedelta(days=day_index)
                slot_time = self.convert_minutes_to_time(current_slot_custom["start"])
                slot_time_date_s = f"{slot_date.strftime('%d-%m-%Y')} {slot_time}"
                slot_time_date_dt = datetime.datetime.strptime(
                    slot_time_date_s, "%d-%m-%Y %H:%M"
                )
                if slot_time_date_dt <= now:
                    slot_time_date_dt += datetime.timedelta(days=7)

                current_slot_custom["Start_DateTime"] = slot_time_date_dt
                full_schedule_list.append(current_slot_custom)

        full_schedule_list.sort(key=operator.itemgetter("Start_DateTime"))

        if len(full_schedule_list) < 3:
            raise ValueError("Schedule list must contain at least three entries.")

        schedule_now, schedule_next, schedule_later = (
            full_schedule_list[-1],
            full_schedule_list[0],
            full_schedule_list[1],
        )

        schedule_now["Start_DateTime"] -= datetime.timedelta(days=7)
        schedule_now["End_DateTime"] = schedule_next["Start_DateTime"]
        schedule_next["End_DateTime"] = schedule_later["Start_DateTime"]
        schedule_later["End_DateTime"] = full_schedule_list[2]["Start_DateTime"]

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
        trv = self.session.data.products.get(device["hive_id"])
        thermostat = self.session.data.products.get(trv["state"]["zone"])
        return thermostat
