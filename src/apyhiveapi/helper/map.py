"""Dot notation for dictionary."""
# pylint: skip-file


class Map(dict):
    """dot.notation access to dictionary attributes.

    Args:
        dict (dict): dictionary to map.
    """

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
