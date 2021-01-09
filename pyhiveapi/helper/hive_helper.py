import datetime
import operator

from .hive_data import Data


class HiveHelper:
    def __init__(self):
        """Hive Helper."""

    def getDeviceName(n_id):
        """Resolve a id into a name"""
        try:
            product_name = Data.products[n_id]["state"]["name"]
        except KeyError:
            product_name = False

        try:
            device_name = Data.devices[n_id]["state"]["name"]
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

    def deviceRecovered(self, n_id):
        """"Register that a device has recovered from being offline."""
        # name = HiveHelper.getDeviceName(n_id)
        if n_id in Data.errorList:
            Data.errorList.pop(n_id)

    def getDeviceFromID(self, n_id):
        """Get product/device data from ID"""
        data = False
        try:
            data = Data.ha_devices[n_id]
        except KeyError:
            pass

        return data

    def convertMinutesToTime(self, minutes_to_convert):
        """Convert minutes string to datetime."""
        hours_converted, minutes_converted = divmod(minutes_to_convert, 60)
        converted_time = datetime.strptime(
            str(hours_converted) + ":" + str(minutes_converted), "%H:%M"
        )
        converted_time_string = converted_time.strftime("%H:%M")
        return converted_time_string

    def getScheduleNNL(self, hive_api_schedule):
        """Get the schedule now, next and later of a given nodes schedule."""
        schedule_now_and_next = {}
        date_time_now = datetime.now()
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
            current_day_schedule = hive_api_schedule[
                days_rolling_list[day_index]
            ]
            current_day_schedule_sorted = sorted(
                current_day_schedule,
                key=operator.itemgetter("start"),
                reverse=False,
            )

            for current_slot in range(0, len(current_day_schedule_sorted)):
                current_slot_custom = current_day_schedule_sorted[current_slot]

                slot_date = datetime.now() + datetime.timedelta(days=day_index)
                slot_time = self.convertMinutesToTime(
                    current_slot_custom["start"]
                )
                slot_time_date_s = (
                    slot_date.strftime("%d-%m-%Y") + " " + slot_time
                )
                slot_time_date_dt = datetime.strptime(
                    slot_time_date_s, "%d-%m-%Y %H:%M"
                )
                if slot_time_date_dt <= date_time_now:
                    slot_time_date_dt = slot_time_date_dt + datetime.timedelta(
                        days=7
                    )

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
