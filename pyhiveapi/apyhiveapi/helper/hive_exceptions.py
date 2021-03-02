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


class HiveInvalidUsername(Exception):
    """Raise invalid Username."""


class HiveInvalidPassword(Exception):
    """Raise invalid password."""


class HiveInvalid2FACode(Exception):
    """Raise invalid 2FA code."""
