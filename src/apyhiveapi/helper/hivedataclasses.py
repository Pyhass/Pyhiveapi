"""Device data class."""

from dataclasses import dataclass


@dataclass
class Device:
    """Class for keeping track of an device."""

    hive_id: str
    hive_name: str
    hive_type: str
    ha_type: str
    device_data: dict
    status: dict
    data: dict
    parent_device: str
    is_group: bool
    device_id: str
    device_name: str
