"""Unit tests for Map — dot-notation dict wrapper."""

from apyhiveapi.helper.map import Map


def test_attribute_read():
    """Test attribute-style read access on Map."""
    m = Map({"key": "value"})
    assert m.key == "value"


def test_dict_read():
    """Test bracket-style dict read access on Map."""
    m = Map({"key": "value"})
    assert m["key"] == "value"


def test_missing_key_returns_none_not_keyerror():
    """Test that missing keys return None instead of raising KeyError."""
    m = Map({})
    assert m.missing is None


def test_nested_access():
    """Test nested dict access through Map."""
    m = Map({"products": {"id-1": {"state": "ON"}}})
    assert m.products["id-1"]["state"] == "ON"


def test_attribute_write():
    """Test attribute-style write access on Map."""
    m = Map({})
    m.foo = "bar"
    assert m["foo"] == "bar"
