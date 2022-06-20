"""Device data class."""
# pylint: skip-file

from dataclasses import dataclass


@dataclass
class Device:
    """Class for keeping track of an device."""

    hiveID: str
    hiveName: str
    hiveType: str
    haType: str
    deviceData: dict
    status: dict
    data: dict
    parentDevice: str
    isGroup: bool
    device_id: str
    device_name: str
