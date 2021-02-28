"""Hive exception class."""


class FileInUse(Exception):
    """File in use exception."""


class NoApiToken(Exception):
    """No API token exception."""


class HiveApiError(Exception):
    """Api error."""


class HiveReauthRequired(Exception):
    """Re-Authentication is required."""


class HiveUnknownConfiguration(Exception):
    """Unknown Hive Configuration."""
