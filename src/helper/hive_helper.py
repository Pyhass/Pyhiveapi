"""Helper class for pyhiveapi."""

# pylint: skip-file
import copy
import datetime
import logging
import operator
from typing import Any

from .const import HIVE_TYPES

_LOGGER = logging.getLogger(__name__)


class HiveHelper:
    """Hive helper class."""

    def __init__(self, session: object = None):
        """Hive Helper.

        Args:
            session (object, optional): Interact with hive account. Defaults to None.
        """
        self.session = session

    async def getDeviceName(self, n_id: str):
        """Resolve a id into a name.

        Args:
            n_id (str): ID of a device.

        Returns:
            str: Name of device.
        """
        product_name = False
        device_name = False

        try:
            product_name = self.session.data.products[n_id]["state"]["name"]
        except KeyError:
            pass

        try:
            device_name = self.session.data.devices[n_id]["state"]["name"]
        except KeyError:
            pass

        if not product_name and not device_name:
            _LOGGER.warning(
                "getDeviceName - No product or device name found for ID: %s", n_id
            )

        if product_name:
            final_name = product_name
        elif device_name:
            final_name = device_name
        elif n_id == "No_ID":
            final_name = "Hive"
        else:
            final_name = n_id

        return final_name

    def deviceRecovered(self, n_id: str):
        """Register that a device has recovered from being offline.

        Args:
            n_id (str): ID of the device.
        """
        # name = HiveHelper.getDeviceName(n_id)
        if n_id in self.session.config.errorList:
            self.session.config.errorList.pop(n_id)

    async def errorCheck(self, n_id, n_type, error_type, **kwargs):
        """Error has occurred."""
        message = None
        name = await self.getDeviceName(n_id)
        device_name = name if isinstance(name, str) else n_id

        if error_type is False:
            message = "Device offline could not update entity - " + str(device_name)
            if n_id not in self.session.config.errorList:
                _LOGGER.warning(message)
                self.session.config.errorList.update({n_id: datetime.datetime.now()})
        elif error_type == "Failed":
            message = "ERROR - No data found for device - " + str(device_name)
            if n_id not in self.session.config.errorList:
                _LOGGER.error(message)
                self.session.config.errorList.update({n_id: datetime.datetime.now()})

    def getDeviceFromID(self, n_id: str):
        """Get product/device data from ID.

        Args:
            n_id (str): ID of the device.

        Returns:
            dict: Device data.
        """
        if hasattr(self.session, "entityCache"):
            for cached_id, cached in self.session.entityCache.items():
                if cached.get("hiveID") == n_id or cached.get("device_id") == n_id:
                    _LOGGER.debug(
                        "getDeviceFromID - Found cached device for ID %s: %s",
                        n_id,
                        cached.get("haName", cached_id),
                    )
                    return cached
        return False

    def getDeviceData(self, product: dict):
        """Get device from product data.

        Args:
            product (dict): Product data.

        Returns:
            [type]: Device data.
        """
        product_id = product.get("id", "Unknown")
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
                    except KeyError as e:
                        _LOGGER.warning(
                            "getDeviceData - KeyError accessing zone data for device %s: %s",
                            aDevice,
                            str(e),
                        )
                        pass
        elif type == "trvcontrol":
            trv_present = len(product["props"]["trvs"]) > 0
            if trv_present:
                device = self.session.data.devices[product["props"]["trvs"][0]]
            else:
                _LOGGER.error(
                    "getDeviceData - No TRVs found for product %s", product_id
                )
                raise KeyError
        elif type == "warmwhitelight" and product["props"]["model"] == "SIREN001":
            device = self.session.data.devices[product["parent"]]
        elif type == "sense":
            device = self.session.data.devices[product["parent"]]
        else:
            device = self.session.data.devices[product["id"]]

        return device

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
        _LOGGER.debug(
            "getScheduleNNL - Parsing schedule NNL for %d days", len(hive_api_schedule)
        )
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
        _LOGGER.debug("getScheduleNNL - Days rolling list: %s", days_rolling_list)

        full_schedule_list = []

        for day_index in range(0, len(days_rolling_list)):
            current_day_schedule = hive_api_schedule[days_rolling_list[day_index]]
            current_day_schedule_sorted = sorted(
                current_day_schedule,
                key=operator.itemgetter("start"),
                reverse=False,
            )
            _LOGGER.debug(
                "getScheduleNNL - Processing day %s with %d schedule slots",
                days_rolling_list[day_index],
                len(current_day_schedule_sorted),
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

        if len(fsl_sorted) >= 3:
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

            _LOGGER.debug(
                "getScheduleNNL - Schedule NNL parsed successfully - now: %s, next: %s, later: %s",
                schedule_now.get("Start_DateTime"),
                schedule_next.get("Start_DateTime"),
                schedule_later.get("Start_DateTime"),
            )
        else:
            _LOGGER.warning(
                "getScheduleNNL - Insufficient schedule data (%d slots) for NNL calculation",
                len(fsl_sorted),
            )

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

    def _sanitize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of payload with sensitive values masked for logs."""

        def _mask(value: Any) -> Any:
            if isinstance(value, str):
                if len(value) <= 8:
                    return "***"
                return f"{value[:4]}...{value[-4:]}"
            elif isinstance(value, dict):
                return {k: _mask(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_mask(item) for item in value]
            else:
                return value

        def _walk(node: Any) -> Any:
            if isinstance(node, dict):
                result: dict[str, Any] = {}
                for key, value in node.items():
                    key_lower = key.lower()
                    if any(
                        part in key_lower
                        for part in (
                            "password",
                            "token",
                            "tokens",
                            "secret",
                            "code",
                            "session",
                            "accesstoken",
                            "device_data",
                            "authenticationresult",
                            "responsemetadata",
                            "newdevicemetadata",
                        )
                    ):
                        result[key] = _mask(value)
                    else:
                        result[key] = _walk(value)
                return result
            if isinstance(node, list):
                return [_walk(item) for item in node]
            return node

        return _walk(copy.deepcopy(payload))
