"""Dot notation for dictionary."""

# pylint: skip-file


class Map(dict):
    """dot.notation access to dictionary attributes.

    Args:
        dict (dict): dictionary to map.
    """

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"Map has no key {key!r}") from None

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
