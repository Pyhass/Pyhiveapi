
from .hive_data import Data


class Hive_Helper:

    def __init__():
        """intialise the helper class."""

    def get_device_name(n_id):
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

    def device_recovered(n_id):
        """"Register that a device has recovered from being offline."""
        name = Hive_Helper.get_device_name(n_id)
        if n_id in Data.s_error_list:
            Data.s_error_list.pop(n_id)

    def get_device_from_id(n_id):
        """Get product/device data from ID"""
        data = False
        try:
            data = Data.ha_devices[n_id]
        except KeyError:
            pass

        return data
