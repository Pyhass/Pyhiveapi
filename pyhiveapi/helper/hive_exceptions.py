"""Hive exception class"""


class FileInUse(Exception):
    pass


class NoApiToken(Exception):
    pass


class HiveApiError(Exception):
    pass
