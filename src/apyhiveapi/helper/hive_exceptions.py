"""Hive exception class."""
# pylint: skip-file


class FileInUse(Exception):
    """File in use exception.

    Args:
        Exception (object): Exception object to invoke
    """


class NoApiToken(Exception):
    """No API token exception.

    Args:
        Exception (object): Exception object to invoke
    """


class HiveApiError(Exception):
    """Api error.

    Args:
        Exception (object): Exception object to invoke
    """


class HiveReauthRequired(Exception):
    """Re-Authentication is required.

    Args:
        Exception (object): Exception object to invoke
    """


class HiveUnknownConfiguration(Exception):
    """Unknown Hive Configuration.

    Args:
        Exception (object): Exception object to invoke
    """


class HiveInvalidUsername(Exception):
    """Raise invalid Username.

    Args:
        Exception (object): Exception object to invoke
    """


class HiveInvalidPassword(Exception):
    """Raise invalid password.

    Args:
        Exception (object): Exception object to invoke
    """


class HiveInvalid2FACode(Exception):
    """Raise invalid 2FA code.

    Args:
        Exception (object): Exception object to invoke
    """


class HiveInvalidDeviceAuthentication(Exception):
    """Raise invalid device authentication.

    Args:
        Exception (object): Exception object to invoke
    """


class HiveFailedToRefreshTokens(Exception):
    """Raise invalid refresh tokens.

    Args:
        Exception (object): Exception object to invoke
    """
