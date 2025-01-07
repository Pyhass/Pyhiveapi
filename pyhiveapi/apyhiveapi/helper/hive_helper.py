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

    def getDeviceName(self, n_id: str):
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

    def deviceRecovered(self, n_id: str):
        """Register that a device has recovered from being offline.

        Args:
            n_id (str): ID of the device.
        """
        # name = HiveHelper.getDeviceName(n_id)
        if n_id in self.session.config.errorList:
            self.session.config.errorList.pop(n_id)

    def getDeviceFromID(self, n_id: str):
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

    def getDeviceData(self, product: dict):
        """Get device from product data.

        Args:
            product (dict): Product data.

        Returns:
            [type]: Device data.
        """
        device_id = product["id"]
        type = product["type"]
        if type in ("heating", "hotwater"):
            for aDevice in self.session.data.devices:
                if self.session.data.devices[aDevice]["type"] in HIVE_TYPES["Thermo"]:
                    try:
                        if (
                            product["props"]["zone"]
                            == self.session.data.devices[aDevice]["props"]["zone"]
                        ):
                            device_id = self.session.data.devices[aDevice]["id"]
                    except KeyError:
                        pass
        elif type == "trvcontrol":
            trv_present = len(product["props"]["trvs"]) > 0
            if trv_present:
                device_id = self.session.data.devices[product["props"]["trvs"][0]]["id"]
            else:
                raise KeyError
        elif type == "warmwhitelight" and product["props"]["model"] == "SIREN001":
            device_id = self.session.data.devices[product["parent"]]
        elif type == "sense":
            device_id = self.session.data.devices[product["parent"]]
        else:
            device_id = self.session.data.devices[product["id"]]

        return device_id

    def convertMinutesToTime(self, minutes_to_convert: str):
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

    def getScheduleNNL(self, hive_api_schedule: list):
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
                slot_time = self.convertMinutesToTime(current_slot_custom["start"])
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

    def getHeatOnDemandDevice(self, device: dict):
        """Use TRV device to get the linked thermostat device.

        Args:
            device ([dictionary]): [The TRV device to lookup.]

        Returns:
            [dictionary]: [Gets the thermostat device linked to TRV.]
        """
        trv = self.session.data.products.get(device["HiveID"])
        thermostat = self.session.data.products.get(trv["state"]["zone"])
        return thermostat
