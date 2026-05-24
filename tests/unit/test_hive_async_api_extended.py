"""Extended unit tests for HiveApiAsync — covers previously uncovered lines."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web_exceptions
from apyhiveapi.api.hive_async_api import HiveApiAsync
from apyhiveapi.helper.hive_exceptions import HiveApiError

# ---------------------------------------------------------------------------
# Shared helpers (same pattern as test_hive_async_api.py)
# ---------------------------------------------------------------------------


def _make_mock_response(status=200, json_data=None):
    resp = MagicMock()
    resp.status = status
    resp.text = AsyncMock(return_value="")
    resp.json = AsyncMock(return_value=json_data or {"data": "test"})
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def _make_api(status=200, json_data=None, token="test-token", file_mode=False):
    resp = _make_mock_response(status=status, json_data=json_data)
    websession = MagicMock()
    websession.request.return_value = resp
    websession.closed = False
    websession.close = AsyncMock()
    session = MagicMock()
    session.tokens = MagicMock()
    session.tokens.token_data = {"token": token}
    session.config = MagicMock()
    session.config.file = file_mode
    return HiveApiAsync(hive_session=session, websession=websession)


# ---------------------------------------------------------------------------
# Tests: request() branch — url is not None and status is not None (non-auth error)
# ---------------------------------------------------------------------------


class TestRequestNonAuthErrorBranch:
    """Cover lines 100-108: url/status not None branch leading to HiveApiError."""

    async def test_404_logs_and_raises_hive_api_error(self):
        """A 404 falls through to the url/status branch and raises HiveApiError."""
        api = _make_api(status=404)
        with pytest.raises(HiveApiError):
            await api.request("get", "https://beekeeper.hivehome.com/1.0/nodes/all")

    async def test_503_logs_and_raises_hive_api_error(self):
        """A 503 falls through to the url/status branch and raises HiveApiError."""
        api = _make_api(status=503)
        with pytest.raises(HiveApiError):
            await api.request("get", "https://beekeeper.hivehome.com/1.0/nodes/all")

    async def test_422_logs_and_raises_hive_api_error(self):
        """A 422 also falls through (not 401/403) and raises HiveApiError."""
        api = _make_api(status=422)
        with pytest.raises(HiveApiError):
            await api.request("get", "https://beekeeper.hivehome.com/1.0/devices")


# ---------------------------------------------------------------------------
# Tests: get_login_info() — sync method (lines 110-129)
# ---------------------------------------------------------------------------


class TestGetLoginInfo:
    """Cover lines 112-129: get_login_info() parses HTML and returns login dict."""

    def test_returns_upid_cliid_region(self):
        """Successful fetch returns correct keys from parsed HTML."""
        html_content = (
            b"<script>"
            b'window.HiveSSOPoolId="eu-west-1_abc123",'
            b'window.HiveSSOPublicCognitoClientId="client-xyz"'
            b"</script>"
        )
        mock_response = MagicMock()
        mock_response.content = html_content

        api = _make_api()
        with patch(
            "apyhiveapi.api.hive_async_api.requests.get", return_value=mock_response
        ):
            result = api.get_login_info()

        assert result["UPID"] == "eu-west-1_abc123"
        assert result["CLIID"] == "client-xyz"
        # REGION is set to HiveSSOPoolId value
        assert result["REGION"] == "eu-west-1_abc123"

    def test_makes_request_to_sso_url(self):
        """Verifies requests.get is called with the SSO URL."""
        html_content = (
            b"<script>"
            b'window.HiveSSOPoolId="eu-west-1_pool",'
            b'window.HiveSSOPublicCognitoClientId="cid"'
            b"</script>"
        )
        mock_response = MagicMock()
        mock_response.content = html_content

        api = _make_api()
        with patch(
            "apyhiveapi.api.hive_async_api.requests.get", return_value=mock_response
        ) as mock_get:
            api.get_login_info()

        mock_get.assert_called_once_with(
            url="https://sso.hivehome.com/", timeout=api.timeout
        )

    def test_uses_first_script_tag(self):
        """PyQuery selects the first script — extra scripts are ignored."""
        html_content = (
            b"<script>"
            b'window.HiveSSOPoolId="eu-west-1_first",'
            b'window.HiveSSOPublicCognitoClientId="cid-first"'
            b"</script>"
            b'<script>window.SomeOtherThing="ignored"</script>'
        )
        mock_response = MagicMock()
        mock_response.content = html_content

        api = _make_api()
        with patch(
            "apyhiveapi.api.hive_async_api.requests.get", return_value=mock_response
        ):
            result = api.get_login_info()

        assert result["UPID"] == "eu-west-1_first"


# ---------------------------------------------------------------------------
# Tests: motion_sensor() — lines 213-235
# ---------------------------------------------------------------------------


class TestMotionSensor:
    """Cover lines 215-235: motion_sensor() success and error paths."""

    async def test_success_returns_status_and_parsed(self):
        """Successful call returns status and parsed JSON."""
        payload = [{"event": "motion", "timestamp": 1234567890}]
        api = _make_api(status=200, json_data=payload)
        # motion_sensor uses urls["base"] which doesn't exist in HiveApiAsync;
        # add it so the URL can be constructed
        api.urls["base"] = ""
        sensor = {"type": "motionsensor", "id": "sensor-001"}

        result = await api.motion_sensor(sensor, fromepoch=1000000, toepoch=2000000)

        assert result["original"] == 200
        assert result["parsed"] == payload

    async def test_url_is_built_correctly(self):
        """Verifies the URL is assembled with correct sensor type and id."""
        api = _make_api(status=200, json_data=[])
        api.urls["base"] = "https://beekeeper-uk.hivehome.com/1.0"
        sensor = {"type": "contactsensor", "id": "abc-123"}

        captured_url = []
        original_request = api.request

        async def capture_request(method, url, **kwargs):
            captured_url.append(url)
            return await original_request(method, url, **kwargs)

        with patch.object(api, "request", side_effect=capture_request):
            await api.motion_sensor(sensor, fromepoch=100, toepoch=200)

        assert len(captured_url) == 1
        assert "contactsensor" in captured_url[0]
        assert "abc-123" in captured_url[0]
        assert "from=100" in captured_url[0]
        assert "to=200" in captured_url[0]

    async def test_os_error_raises_http_error(self):
        """OSError inside the try block causes error() → HTTPError."""
        api = _make_api(status=200)
        api.urls["base"] = ""
        sensor = {"type": "motionsensor", "id": "sensor-001"}
        api.websession.request.side_effect = OSError("fail")
        with pytest.raises(web_exceptions.HTTPError):
            await api.motion_sensor(sensor, fromepoch=1000, toepoch=2000)

    async def test_runtime_error_raises_http_error(self):
        """RuntimeError inside the try block causes error() → HTTPError."""
        api = _make_api(status=200)
        api.urls["base"] = ""
        sensor = {"type": "motionsensor", "id": "sensor-002"}
        api.websession.request.side_effect = RuntimeError("unexpected")
        with pytest.raises(web_exceptions.HTTPError):
            await api.motion_sensor(sensor, fromepoch=1000, toepoch=2000)

    async def test_zero_division_raises_http_error(self):
        """ZeroDivisionError inside the try block causes error() → HTTPError."""
        api = _make_api(status=200)
        api.urls["base"] = ""
        sensor = {"type": "motionsensor", "id": "sensor-003"}
        api.websession.request.side_effect = ZeroDivisionError()
        with pytest.raises(web_exceptions.HTTPError):
            await api.motion_sensor(sensor, fromepoch=1000, toepoch=2000)


# ---------------------------------------------------------------------------
# Tests: get_weather() — lines 237-249
# ---------------------------------------------------------------------------


class TestGetWeather:
    """Cover lines 239-249: get_weather() success, space encoding, and error paths."""

    async def test_success_returns_status_and_parsed(self):
        """Successful call returns status and parsed weather JSON."""
        payload = {"temperature": {"value": 15, "unit": "C"}}
        api = _make_api(status=200, json_data=payload)

        result = await api.get_weather("?lat=51.5&lon=-0.1")

        assert result["original"] == 200
        assert result["parsed"] == payload

    async def test_space_in_weather_url_is_encoded(self):
        """Spaces in the weather_url are replaced with %20."""
        api = _make_api(status=200, json_data={})

        captured_url = []
        original_request = api.request

        async def capture_request(method, url, **kwargs):
            captured_url.append(url)
            return await original_request(method, url, **kwargs)

        with patch.object(api, "request", side_effect=capture_request):
            await api.get_weather("?postcode=SW1A 2AA")

        assert len(captured_url) == 1
        assert " " not in captured_url[0]
        assert "%20" in captured_url[0]

    async def test_url_is_prefixed_with_weather_base(self):
        """The weather base URL is prepended to the given weather_url."""
        api = _make_api(status=200, json_data={})

        captured_url = []
        original_request = api.request

        async def capture_request(method, url, **kwargs):
            captured_url.append(url)
            return await original_request(method, url, **kwargs)

        with patch.object(api, "request", side_effect=capture_request):
            await api.get_weather("?lat=51.5")

        assert captured_url[0].startswith("https://weather.prod.bgchprod.info/weather")

    async def test_os_error_raises_http_error(self):
        """OSError inside the try block causes error() → HTTPError."""
        api = _make_api(status=200)
        api.websession.request.side_effect = OSError("network fail")
        with pytest.raises(web_exceptions.HTTPError):
            await api.get_weather("?lat=51.5")

    async def test_runtime_error_raises_http_error(self):
        """RuntimeError inside the try block causes error() → HTTPError."""
        api = _make_api(status=200)
        api.websession.request.side_effect = RuntimeError("unexpected")
        with pytest.raises(web_exceptions.HTTPError):
            await api.get_weather("?lat=51.5")

    async def test_zero_division_raises_http_error(self):
        """ZeroDivisionError inside the try block causes error() → HTTPError."""
        api = _make_api(status=200)
        api.websession.request.side_effect = ZeroDivisionError()
        with pytest.raises(web_exceptions.HTTPError):
            await api.get_weather("?lat=51.5")

    async def test_connection_error_raises_http_error(self):
        """ConnectionError inside the try block causes error() → HTTPError."""
        api = _make_api(status=200)
        api.websession.request.side_effect = ConnectionError("disconnected")
        with pytest.raises(web_exceptions.HTTPError):
            await api.get_weather("?lat=51.5")


# ---------------------------------------------------------------------------
# Tests: set_state() JSON encoding — Fix A
# ---------------------------------------------------------------------------


class TestSetStateJsonEncoding:
    """set_state must produce valid JSON even when kwarg values contain special characters."""

    async def test_set_state_escapes_quotes_in_value(self):
        """A value containing double-quotes must produce valid, parseable JSON."""
        import json  # noqa: PLC0415

        session = MagicMock()
        session.tokens.token_data = {"token": "tok"}
        session.config.file = False
        api = HiveApiAsync(hive_session=session)
        api.urls = {"nodes": "https://beekeeper.hivehome.com/1.0/nodes/{}/{}"}

        captured = {}

        async def fake_request(_method, _url, **kwargs):
            captured["data"] = kwargs.get("data")
            resp = MagicMock()
            resp.status = 200
            resp.json = AsyncMock(return_value={})
            return resp

        with patch.object(api, "request", side_effect=fake_request):
            with patch.object(api, "is_file_being_used", new=AsyncMock()):
                await api.set_state("heating", "node-1", mode='MANUAL"injected')

        parsed = json.loads(captured["data"])
        assert parsed["mode"] == 'MANUAL"injected'
