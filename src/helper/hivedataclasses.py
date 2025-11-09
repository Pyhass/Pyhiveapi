"""Device data class."""

# pylint: skip-file

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class Device:
    """Class for keeping track of a device."""

    hive_id: str
    hive_name: str
    hive_type: str
    ha_type: str
    device_id: str
    device_name: str
    device_data: dict
    parent_device: Optional[str] = None
    is_group: bool = False
    ha_name: str = ""
    category: Optional[str] = None
    temperature_unit: Optional[str] = None
    # Add status and data as optional since not always populated at creation
    status: Optional[dict] = None
    data: Optional[dict] = None


@dataclass
class EntityConfig:
    """Configuration for creating a device entity."""

    entity_type: Literal[
        "sensor",
        "binary_sensor",
        "climate",
        "light",
        "switch",
        "water_heater",
        "alarm_control_panel",
        "camera",
    ]
    ha_name: str = ""
    hive_type: str = ""
    category: Optional[str] = None
    temperature_unit: Optional[str] = None
