"""Test hub framework."""

from pyhiveapi.hub import Hub
from tests.common import MockDevice

hub = Hub()


def test_hub_smoke():
    """Test for hub smoke."""
    device = MockDevice()
    result = hub.hub_smoke(device)

    assert result
