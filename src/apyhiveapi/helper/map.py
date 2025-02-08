"""Dot notation for dictionary."""

from typing import Any


class Map(dict):
    """dot.notation access to dictionary attributes.

    Args:
        dict (dict): dictionary to map.
    """

    def __getattr__(self, item: str) -> Any:
        """Get item from dictionary.

        Args:
            item (str): key to get.

        Returns:
            Any: Value of the key.
        """
        return self.get(item)  # type: ignore

    def __setattr__(self, key: str, value: Any) -> None:
        """Set value to dictionary.

        Args:
            key (str): key to set.
            value (Any): Value to set.
        """
        self[key] = value

    def __delattr__(self, key: str) -> None:
        """Delete item from dictionary.

        Args:
            key (str): Item to delete.
        """
        self.pop(key, None)
