"""Unit tests for HiveApiAsync."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web_exceptions
from apyhiveapi.api.hive_async_api import HiveApiAsync
from apyhiveapi.helper.hive_exceptions import (
    FileInUse,
    HiveApiError,
    HiveAuthError,
    NoApiToken,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_response(status=200, json_data=None):
    resp = MagicMock()
    resp.status = status
    resp.text = AsyncMock(return_value="")
    resp.json = AsyncMock(return_value=json_data or {"data": "test"})
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def _make_mock_websession(status=200, json_data=None):
    resp = _make_mock_response(status=status, json_data=json_data)
    websession = MagicMock()
    websession.request.return_value = resp
    websession.closed = False
    websession.close = AsyncMock()
    return websession


def _make_api(status=200, json_data=None, token="test-token", file_mode=False):
    websession = _make_mock_websession(status=status, json_data=json_data)
    session = MagicMock()
    session.tokens = MagicMock()
    session.tokens.token_data = {"token": token}
    session.config = MagicMock()
    session.config.file = file_mode
    return HiveApiAsync(hive_session=session, websession=websession)


def _make_api_no_token(_url_contains_sso=False):
    """Return an API instance whose session raises KeyError on token lookup."""
    websession = _make_mock_websession(status=200)
    session = MagicMock()
    session.tokens = MagicMock()
    # Raise KeyError when "token" key is accessed
    session.tokens.token_data = {}
    session.config = MagicMock()
    session.config.file = False
    return HiveApiAsync(hive_session=session, websession=websession)


# ---------------------------------------------------------------------------
# Tests: HiveApiAsync.request
# ---------------------------------------------------------------------------


class TestHiveApiAsyncRequest:
    async def test_successful_200_returns_response(self):
        api = _make_api(status=200, json_data={"ok": True})
        resp = await api.request("get", "https://beekeeper.hivehome.com/1.0/nodes/all")
        assert resp.status == 200

    async def test_201_also_succeeds(self):
        api = _make_api(status=201)
        resp = await api.request("post", "https://beekeeper.hivehome.com/1.0/nodes/x/y")
        assert resp.status == 201

    async def test_sso_url_without_token_does_not_raise(self):
        api = _make_api_no_token()
        # Should not raise NoApiToken because "sso" is in the URL
        resp = await api.request("get", "https://sso.hivehome.com/")
        assert resp.status == 200

    async def test_non_sso_without_token_raises_no_api_token(self):
        api = _make_api_no_token()
        with pytest.raises(NoApiToken):
            await api.request("get", "https://beekeeper.hivehome.com/1.0/nodes/all")

    async def test_401_raises_hive_auth_error(self):
        api = _make_api(status=401)
        with pytest.raises(HiveAuthError):
            await api.request("get", "https://beekeeper.hivehome.com/1.0/nodes/all")

    async def test_403_raises_hive_auth_error(self):
        api = _make_api(status=403)
        with pytest.raises(HiveAuthError):
            await api.request("get", "https://beekeeper.hivehome.com/1.0/nodes/all")

    async def test_500_raises_hive_api_error(self):
        api = _make_api(status=500)
        with pytest.raises(HiveApiError):
            await api.request("get", "https://beekeeper.hivehome.com/1.0/nodes/all")

    async def test_404_raises_hive_api_error(self):
        api = _make_api(status=404)
        with pytest.raises(HiveApiError):
            await api.request("get", "https://beekeeper.hivehome.com/1.0/nodes/all")


# ---------------------------------------------------------------------------
# Tests: HiveApiAsync.get_all
# ---------------------------------------------------------------------------


class TestGetAll:
    async def test_successful_get_all_returns_parsed_json(self):
        payload = {"products": [], "devices": []}
        api = _make_api(status=200, json_data=payload)
        result = await api.get_all()
        assert result["original"] == 200
        assert result["parsed"] == payload

    async def test_timeout_error_propagates(self):
        api = _make_api(status=200)
        api.websession.request.side_effect = asyncio.TimeoutError
        with pytest.raises(asyncio.TimeoutError):
            await api.get_all()

    async def test_os_error_calls_error_method(self):
        api = _make_api(status=200)
        api.websession.request.side_effect = OSError("network down")
        with pytest.raises(web_exceptions.HTTPError):
            await api.get_all()

    async def test_runtime_error_calls_error_method(self):
        api = _make_api(status=200)
        api.websession.request.side_effect = RuntimeError("boom")
        with pytest.raises(web_exceptions.HTTPError):
            await api.get_all()


# ---------------------------------------------------------------------------
# Tests: HiveApiAsync.get_devices / get_products / get_actions
# ---------------------------------------------------------------------------


class TestGetEndpoints:
    async def test_get_devices_returns_parsed_json(self):
        payload = [{"id": "dev1"}]
        api = _make_api(status=200, json_data=payload)
        result = await api.get_devices()
        assert result["original"] == 200
        assert result["parsed"] == payload

    async def test_get_products_returns_parsed_json(self):
        payload = [{"id": "prod1"}]
        api = _make_api(status=200, json_data=payload)
        result = await api.get_products()
        assert result["original"] == 200
        assert result["parsed"] == payload

    async def test_get_actions_returns_parsed_json(self):
        payload = [{"id": "act1"}]
        api = _make_api(status=200, json_data=payload)
        result = await api.get_actions()
        assert result["original"] == 200
        assert result["parsed"] == payload

    async def test_get_devices_os_error_raises_http_error(self):
        api = _make_api(status=200)
        api.websession.request.side_effect = OSError
        with pytest.raises(web_exceptions.HTTPError):
            await api.get_devices()

    async def test_get_products_os_error_raises_http_error(self):
        api = _make_api(status=200)
        api.websession.request.side_effect = OSError
        with pytest.raises(web_exceptions.HTTPError):
            await api.get_products()

    async def test_get_actions_os_error_raises_http_error(self):
        api = _make_api(status=200)
        api.websession.request.side_effect = OSError
        with pytest.raises(web_exceptions.HTTPError):
            await api.get_actions()


# ---------------------------------------------------------------------------
# Tests: HiveApiAsync.set_state
# ---------------------------------------------------------------------------


class TestSetState:
    async def test_file_in_use_returns_file_response(self):
        api = _make_api(status=200, file_mode=True)
        result = await api.set_state("heating", "node-1", mode="MANUAL")
        assert result == {"original": "file"}

    async def test_successful_set_state(self):
        payload = {"id": "node-1", "mode": "MANUAL"}
        api = _make_api(status=200, json_data=payload)
        result = await api.set_state("heating", "node-1", mode="MANUAL")
        assert result["original"] == 200
        assert result["parsed"] == payload

    async def test_os_error_calls_error_method(self):
        api = _make_api(status=200)
        api.websession.request.side_effect = OSError("fail")
        with pytest.raises(web_exceptions.HTTPError):
            await api.set_state("heating", "node-1", mode="MANUAL")

    async def test_runtime_error_calls_error_method(self):
        api = _make_api(status=200)
        api.websession.request.side_effect = RuntimeError("fail")
        with pytest.raises(web_exceptions.HTTPError):
            await api.set_state("heating", "node-1", mode="MANUAL")


# ---------------------------------------------------------------------------
# Tests: HiveApiAsync.set_action
# ---------------------------------------------------------------------------


class TestSetAction:
    async def test_file_in_use_returns_file_response(self):
        api = _make_api(status=200, file_mode=True)
        result = await api.set_action("action-1", '{"status": "on"}')
        assert result == {"original": "file"}

    async def test_successful_set_action_returns_status_200(self):
        payload = {"id": "action-1", "status": "on"}
        api = _make_api(status=200, json_data=payload)
        result = await api.set_action("action-1", '{"status": "on"}')
        assert result["original"] == 200
        assert result["parsed"] == payload

    async def test_runtime_error_calls_error_method(self):
        api = _make_api(status=200)
        api.websession.request.side_effect = RuntimeError("fail")
        with pytest.raises(web_exceptions.HTTPError):
            await api.set_action("action-1", "{}")

    async def test_os_error_calls_error_method(self):
        api = _make_api(status=200)
        api.websession.request.side_effect = OSError
        with pytest.raises(web_exceptions.HTTPError):
            await api.set_action("action-1", "{}")


# ---------------------------------------------------------------------------
# Tests: HiveApiAsync.motion_sensor
# ---------------------------------------------------------------------------


class TestMotionSensor:
    async def test_url_does_not_double_base_url(self):
        payload = [{"timestamp": 12345}]
        api = _make_api(status=200, json_data=payload)
        captured = {}
        original_request = api.request

        async def capture_request(method, url, **kwargs):
            captured["url"] = url
            return await original_request(method, url, **kwargs)

        api.request = capture_request
        sensor = {"type": "motionsensor", "id": "ms-001"}
        await api.motion_sensor(sensor, 1000000, 2000000)
        url = captured["url"]
        assert url.startswith(api.base_url + "/products/")
        assert "motionsensor/ms-001" in url
        assert url.count("https://beekeeper") == 1

    async def test_motion_sensor_returns_parsed_json(self):
        payload = [{"timestamp": 12345}]
        api = _make_api(status=200, json_data=payload)
        sensor = {"type": "motionsensor", "id": "ms-001"}
        result = await api.motion_sensor(sensor, 1000000, 2000000)
        assert result["original"] == 200
        assert result["parsed"] == payload


# ---------------------------------------------------------------------------
# Tests: HiveApiAsync.refresh_tokens
# ---------------------------------------------------------------------------


class TestRefreshTokens:
    async def test_no_name_error_when_session_is_none(self):
        websession = _make_mock_websession(status=200)
        api = HiveApiAsync(hive_session=None, websession=websession)
        api.request = AsyncMock()
        result = await api.refresh_tokens()
        assert result == api.json_return


# ---------------------------------------------------------------------------
# Tests: HiveApiAsync.error
# ---------------------------------------------------------------------------


class TestError:
    async def test_error_raises_http_error(self):
        api = _make_api()
        with pytest.raises(web_exceptions.HTTPError):
            await api.error()


# ---------------------------------------------------------------------------
# Tests: HiveApiAsync.is_file_being_used
# ---------------------------------------------------------------------------


class TestIsFileBeingUsed:
    async def test_file_mode_raises_file_in_use(self):
        api = _make_api(file_mode=True)
        with pytest.raises(FileInUse):
            await api.is_file_being_used()

    async def test_not_file_mode_does_not_raise(self):
        api = _make_api(file_mode=False)
        await api.is_file_being_used()  # Should not raise


# ---------------------------------------------------------------------------
# Tests: HiveApiAsync.__init__
# ---------------------------------------------------------------------------


class TestInit:
    async def test_default_websession_created_when_none_passed(self):
        session = MagicMock()
        session.tokens = MagicMock()
        session.tokens.token_data = {"token": "tok"}
        session.config = MagicMock()
        api = HiveApiAsync(hive_session=session)
        assert api.websession is not None
        await api.websession.close()

    def test_custom_websession_is_used(self):
        session = MagicMock()
        ws = MagicMock()
        api = HiveApiAsync(hive_session=session, websession=ws)
        assert api.websession is ws

    def test_base_url_is_set(self):
        api = _make_api()
        assert api.base_url == "https://beekeeper.hivehome.com/1.0"

    def test_default_timeout(self):
        api = _make_api()
        assert api.timeout == 5
