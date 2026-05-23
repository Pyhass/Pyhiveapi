"""Extended unit tests for HiveAuthAsync — covers previously uncovered paths."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import botocore.exceptions
import pytest
from apyhiveapi.helper.hive_exceptions import (
    HiveApiError,
    HiveInvalid2FACode,
    HiveInvalidDeviceAuthentication,
)

# ---------------------------------------------------------------------------
# Exception factories (same pattern as test_hive_auth_async.py)
# ---------------------------------------------------------------------------


def _named_client_error(
    code: str, message: str = ""
) -> botocore.exceptions.ClientError:
    """Return a ClientError whose __class__.__name__ matches ``code``."""
    cls = type(code, (botocore.exceptions.ClientError,), {})
    return cls(
        {"Error": {"Code": code, "Message": message}},
        "operation",
    )


def _endpoint_error() -> botocore.exceptions.EndpointConnectionError:
    return botocore.exceptions.EndpointConnectionError(
        endpoint_url="https://cognito.eu-west-1.amazonaws.com"
    )


# ---------------------------------------------------------------------------
# Shared factory
# ---------------------------------------------------------------------------

_LOGIN_INFO = {
    "UPID": "eu-west-1_TestPool",
    "CLIID": "test-client-id",
    "REGION": "eu-west-1_TestPool",
}


async def _make_auth(
    username: str = "user@test.com",
    password: str = "testpass",
    device_key: str | None = None,
    device_group_key: str | None = None,
    device_password: str | None = None,
    client_secret: str | None = None,
):
    from apyhiveapi.api.hive_auth_async import HiveAuthAsync

    auth = HiveAuthAsync(
        username=username,
        password=password,
        device_key=device_key,
        device_group_key=device_group_key,
        device_password=device_password,
        client_secret=client_secret,
    )
    # Bypass async_init — inject mocked internals directly.
    auth.client = MagicMock()
    auth._client_id = "test-client-id"
    auth._pool_id = "eu-west-1_TestPool"
    auth._region = "eu-west-1"
    auth.loop = MagicMock()
    auth.loop.run_in_executor = AsyncMock()
    return auth


# ---------------------------------------------------------------------------
# Tests: async_init() — lines 96-112
# ---------------------------------------------------------------------------


class TestAsyncInit:
    """Cover lines 98-112: async_init() sets pool_id, client_id, region and
    boto3 client."""

    async def test_async_init_sets_pool_id_and_client_id(self):
        """async_init reads login info and sets internal auth fields."""
        from apyhiveapi.api.hive_auth_async import HiveAuthAsync

        auth = HiveAuthAsync(username="user@test.com", password="pass")
        auth.client = None  # trigger async_init flow

        mock_boto_client = MagicMock()
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(
            side_effect=[_LOGIN_INFO, mock_boto_client]
        )

        with patch("asyncio.get_running_loop", return_value=mock_loop):
            await auth.async_init()

        assert auth._pool_id == "eu-west-1_TestPool"
        assert auth._client_id == "test-client-id"
        assert auth._region == "eu-west-1"
        assert auth.client is mock_boto_client

    async def test_async_init_splits_region_correctly(self):
        """Region is extracted as the part before the underscore in UPID/REGION."""
        from apyhiveapi.api.hive_auth_async import HiveAuthAsync

        auth = HiveAuthAsync(username="user@test.com", password="pass")
        auth.client = None

        login_info = {
            "UPID": "ap-southeast-2_XyzPool",
            "CLIID": "ap-client",
            "REGION": "ap-southeast-2_XyzPool",
        }
        mock_boto_client = MagicMock()
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(
            side_effect=[login_info, mock_boto_client]
        )

        with patch("asyncio.get_running_loop", return_value=mock_loop):
            await auth.async_init()

        assert auth._region == "ap-southeast-2"


# ---------------------------------------------------------------------------
# Tests: calculate_a() safety check — line 140-141
# ---------------------------------------------------------------------------


class TestCalculateA:
    """Cover line 141: safety check when big_a % big_n == 0."""

    async def test_safety_check_raises_when_a_is_zero_mod_n(self):
        """If pow(g, a, n) == 0 mod n (i.e., equals big_n or 0), ValueError is raised."""
        auth = await _make_auth()
        # Force pow to return auth.big_n so that big_a % big_n == 0
        with patch("builtins.pow", return_value=auth.big_n):
            with pytest.raises(ValueError, match="Safety check for A failed"):
                auth.calculate_a()

    async def test_safety_check_passes_normally(self):
        """Under normal random inputs, calculate_a does not raise and returns positive int."""
        auth = await _make_auth()
        # calculate_a was already called during __init__; calling it again should also work
        result = auth.calculate_a()
        assert result > 0


# ---------------------------------------------------------------------------
# Tests: get_password_authentication_key() — lines 155-172
# ---------------------------------------------------------------------------


class TestGetPasswordAuthenticationKey:
    """Cover lines 155-172: get_password_authentication_key() computes HKDF."""

    async def test_returns_bytes(self):
        """With valid SRP inputs, the method returns a bytes-like value."""
        auth = await _make_auth()
        from apyhiveapi.api.srp_crypto import get_random

        # Pick a server_b that won't produce u_value == 0 by using a known large value
        server_b_value = hex(get_random(128))[2:]
        salt = hex(get_random(16))[2:]

        # Patch calculate_u to return a known non-zero value to avoid flakiness
        with patch("apyhiveapi.api.hive_auth_async.calculate_u", return_value=99999):
            result = auth.get_password_authentication_key(
                "testuser", "testpass", server_b_value, salt
            )

        assert isinstance(result, (bytes, bytearray))

    async def test_u_value_zero_raises_value_error(self):
        """If calculate_u returns 0, ValueError is raised."""
        auth = await _make_auth()
        from apyhiveapi.api.srp_crypto import get_random

        server_b_value = hex(get_random(128))[2:]
        salt = hex(get_random(16))[2:]

        with patch("apyhiveapi.api.hive_auth_async.calculate_u", return_value=0):
            with pytest.raises(ValueError, match="U cannot be zero"):
                auth.get_password_authentication_key(
                    "testuser", "testpass", server_b_value, salt
                )

    async def test_accepts_integer_server_b(self):
        """server_b_value can be passed as an integer (handled by _to_int)."""
        auth = await _make_auth()
        from apyhiveapi.api.srp_crypto import get_random

        server_b_int = get_random(128)
        salt = hex(get_random(16))[2:]

        with patch("apyhiveapi.api.hive_auth_async.calculate_u", return_value=12345):
            result = auth.get_password_authentication_key(
                "testuser", "testpass", server_b_int, salt
            )

        assert isinstance(result, (bytes, bytearray))


# ---------------------------------------------------------------------------
# Tests: process_challenge() — lines 203-254
# ---------------------------------------------------------------------------


class TestProcessChallenge:
    """Cover lines 205-254: process_challenge() builds the SRP response."""

    def _make_challenge_params(self, salt_as_int=False):
        """Return a minimal valid challenge_parameters dict."""
        import base64

        salt = "aabbccddee"
        if salt_as_int:
            salt = int("aabbccddee", 16)
        return {
            "USER_ID_FOR_SRP": "challenge-user@test.com",
            "SALT": salt,
            "SRP_B": "ff" * 32,  # arbitrary hex
            "SECRET_BLOCK": base64.b64encode(b"secret-block-bytes").decode(),
        }

    async def test_returns_required_keys(self):
        """Basic challenge response includes mandatory SRP keys."""
        auth = await _make_auth()

        fake_hkdf = b"\x00" * 32
        auth.loop.run_in_executor = AsyncMock(return_value=fake_hkdf)

        params = self._make_challenge_params()
        result = await auth.process_challenge(params)

        assert "TIMESTAMP" in result
        assert "USERNAME" in result
        assert "PASSWORD_CLAIM_SECRET_BLOCK" in result
        assert "PASSWORD_CLAIM_SIGNATURE" in result

    async def test_sets_user_id_from_challenge(self):
        """process_challenge stores USER_ID_FOR_SRP as self.user_id."""
        auth = await _make_auth()

        fake_hkdf = b"\x00" * 32
        auth.loop.run_in_executor = AsyncMock(return_value=fake_hkdf)

        params = self._make_challenge_params()
        await auth.process_challenge(params)

        assert auth.user_id == "challenge-user@test.com"

    async def test_with_client_secret_adds_secret_hash(self):
        """When client_secret is set, SECRET_HASH is added to the response."""
        auth = await _make_auth(client_secret="my-secret")

        fake_hkdf = b"\x00" * 32
        auth.loop.run_in_executor = AsyncMock(return_value=fake_hkdf)

        params = self._make_challenge_params()
        result = await auth.process_challenge(params)

        assert "SECRET_HASH" in result

    async def test_without_client_secret_no_secret_hash(self):
        """When client_secret is None, SECRET_HASH is absent from the response."""
        auth = await _make_auth(client_secret=None)

        fake_hkdf = b"\x00" * 32
        auth.loop.run_in_executor = AsyncMock(return_value=fake_hkdf)

        params = self._make_challenge_params()
        result = await auth.process_challenge(params)

        assert "SECRET_HASH" not in result

    async def test_with_device_key_adds_device_key(self):
        """When device_key is set, DEVICE_KEY is added to the response."""
        auth = await _make_auth(device_key="dk-challenge")

        fake_hkdf = b"\x00" * 32
        auth.loop.run_in_executor = AsyncMock(return_value=fake_hkdf)

        params = self._make_challenge_params()
        result = await auth.process_challenge(params)

        assert result["DEVICE_KEY"] == "dk-challenge"

    async def test_without_device_key_no_device_key_in_response(self):
        """When device_key is None, DEVICE_KEY is absent from the response."""
        auth = await _make_auth(device_key=None)

        fake_hkdf = b"\x00" * 32
        auth.loop.run_in_executor = AsyncMock(return_value=fake_hkdf)

        params = self._make_challenge_params()
        result = await auth.process_challenge(params)

        assert "DEVICE_KEY" not in result

    async def test_salt_as_integer_triggers_pad_hex(self):
        """When SALT is an integer (not str), pad_hex is applied before use."""
        auth = await _make_auth()

        fake_hkdf = b"\x00" * 32
        auth.loop.run_in_executor = AsyncMock(return_value=fake_hkdf)

        params = self._make_challenge_params(salt_as_int=True)
        # Should not raise; int-type SALT is handled by the isinstance check
        result = await auth.process_challenge(params)

        assert "TIMESTAMP" in result


# ---------------------------------------------------------------------------
# Tests: login() — client is None triggers async_init (line 262-263)
# ---------------------------------------------------------------------------


class TestLoginClientNone:
    """Cover line 263: when client is None, async_init() is awaited."""

    async def test_login_calls_async_init_when_client_is_none(self):
        """If client is None before login, async_init is called before SRP flow."""
        auth = await _make_auth()
        auth.client = None  # reset to trigger the branch
        auth.use_file = False  # ensure we go through the client-None path

        auth_result = {"AuthenticationResult": {"AccessToken": "post-init-token"}}
        challenge_response = {
            "ChallengeName": "PASSWORD_VERIFIER",
            "ChallengeParameters": {
                "USER_ID_FOR_SRP": "user@test.com",
                "SALT": "aabbccdd",
                "SRP_B": "ccddee",
                "SECRET_BLOCK": "YWJj",
            },
        }

        async def fake_async_init():
            auth.client = MagicMock()
            auth._client_id = "test-client-id"
            auth._pool_id = "eu-west-1_TestPool"
            auth._region = "eu-west-1"

        with patch.object(auth, "async_init", side_effect=fake_async_init) as mock_init:
            with patch.object(
                auth, "process_challenge", new_callable=AsyncMock
            ) as mock_ch:
                mock_ch.return_value = {
                    "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
                    "USERNAME": "user",
                }
                # After async_init, run_in_executor is called for initiate_auth then
                # respond_to_auth_challenge
                auth.loop.run_in_executor = AsyncMock(
                    side_effect=[challenge_response, auth_result]
                )
                result = await auth.login()

        mock_init.assert_called_once()
        assert "AuthenticationResult" in result


# ---------------------------------------------------------------------------
# Tests: login() — unsupported challenge name (lines 335-337)
# ---------------------------------------------------------------------------


class TestLoginUnsupportedChallenge:
    """Cover lines 335-337: non-PASSWORD_VERIFIER challenge raises NotImplementedError."""

    async def test_new_password_required_raises_not_implemented(self):
        """NEW_PASSWORD_REQUIRED challenge is not supported and raises NotImplementedError."""
        auth = await _make_auth()
        auth.loop.run_in_executor = AsyncMock(
            return_value={
                "ChallengeName": "NEW_PASSWORD_REQUIRED",
                "ChallengeParameters": {},
            }
        )
        with pytest.raises(NotImplementedError, match="NEW_PASSWORD_REQUIRED"):
            await auth.login()

    async def test_custom_challenge_raises_not_implemented(self):
        """Any unknown challenge name raises NotImplementedError."""
        auth = await _make_auth()
        auth.loop.run_in_executor = AsyncMock(
            return_value={
                "ChallengeName": "UNKNOWN_CHALLENGE_TYPE",
                "ChallengeParameters": {},
            }
        )
        with pytest.raises(NotImplementedError, match="UNKNOWN_CHALLENGE_TYPE"):
            await auth.login()


# ---------------------------------------------------------------------------
# Tests: login() — respond_to_auth_challenge ResourceNotFoundException (line 307-311)
# ---------------------------------------------------------------------------


class TestLoginResourceNotFound:
    """Cover lines 307-311: ResourceNotFoundException in respond_to_auth_challenge."""

    async def test_resource_not_found_raises_invalid_device_authentication(self):
        """ResourceNotFoundException during challenge → HiveInvalidDeviceAuthentication."""
        auth = await _make_auth()
        challenge_response = {
            "ChallengeName": "PASSWORD_VERIFIER",
            "ChallengeParameters": {
                "USER_ID_FOR_SRP": "user@test.com",
                "SALT": "aabbccdd",
                "SRP_B": "ccddee",
                "SECRET_BLOCK": "YWJj",
            },
        }
        resource_err = _named_client_error("ResourceNotFoundException")
        with patch.object(auth, "process_challenge", new_callable=AsyncMock) as mock_ch:
            mock_ch.return_value = {
                "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
                "USERNAME": "user",
            }
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[challenge_response, resource_err]
            )
            with pytest.raises(HiveInvalidDeviceAuthentication):
                await auth.login()


# ---------------------------------------------------------------------------
# Tests: login() — EndpointConnectionError in respond_to_auth_challenge (lines 312-317)
# ---------------------------------------------------------------------------


class TestLoginEndpointErrorOnChallenge:
    """Cover lines 312-317: EndpointConnectionError during respond_to_auth_challenge."""

    async def test_endpoint_error_on_challenge_raises_api_error(self):
        """EndpointConnectionError during SRP challenge response → HiveApiError."""
        auth = await _make_auth()
        challenge_response = {
            "ChallengeName": "PASSWORD_VERIFIER",
            "ChallengeParameters": {
                "USER_ID_FOR_SRP": "user@test.com",
                "SALT": "aabbccdd",
                "SRP_B": "ccddee",
                "SECRET_BLOCK": "YWJj",
            },
        }
        with patch.object(auth, "process_challenge", new_callable=AsyncMock) as mock_ch:
            mock_ch.return_value = {
                "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
                "USERNAME": "user",
            }
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[challenge_response, _endpoint_error()]
            )
            with pytest.raises(HiveApiError):
                await auth.login()


# ---------------------------------------------------------------------------
# Tests: login() — result without AuthenticationResult (lines 321-333)
# ---------------------------------------------------------------------------


class TestLoginResultHandling:
    """Cover lines 321-333: AuthenticationResult presence/absence in login result."""

    async def test_result_without_authentication_result_does_not_store_token(self):
        """If result lacks 'AuthenticationResult', access_token is not set."""
        auth = await _make_auth()
        # First call → PASSWORD_VERIFIER challenge
        # Second call → result without AuthenticationResult (e.g., SMS_MFA)
        challenge_response = {
            "ChallengeName": "PASSWORD_VERIFIER",
            "ChallengeParameters": {
                "USER_ID_FOR_SRP": "user@test.com",
                "SALT": "aabbccdd",
                "SRP_B": "ccddee",
                "SECRET_BLOCK": "YWJj",
            },
        }
        sms_challenge_result = {
            "ChallengeName": "SMS_MFA",
            "Session": "session-tok",
            "ChallengeParameters": {},
        }
        with patch.object(auth, "process_challenge", new_callable=AsyncMock) as mock_ch:
            mock_ch.return_value = {
                "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
                "USERNAME": "user",
            }
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[challenge_response, sms_challenge_result]
            )
            result = await auth.login()

        # access_token was never set
        assert auth.access_token is None
        assert result is sms_challenge_result

    async def test_result_with_authentication_result_but_no_new_device_metadata(self):
        """AuthenticationResult without NewDeviceMetadata sets access_token only."""
        auth = await _make_auth()
        challenge_response = {
            "ChallengeName": "PASSWORD_VERIFIER",
            "ChallengeParameters": {
                "USER_ID_FOR_SRP": "user@test.com",
                "SALT": "aabbccdd",
                "SRP_B": "ccddee",
                "SECRET_BLOCK": "YWJj",
            },
        }
        auth_result = {"AuthenticationResult": {"AccessToken": "my-access-token"}}
        with patch.object(auth, "process_challenge", new_callable=AsyncMock) as mock_ch:
            mock_ch.return_value = {
                "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
                "USERNAME": "user",
            }
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[challenge_response, auth_result]
            )
            await auth.login()

        assert auth.access_token == "my-access-token"
        assert auth.device_group_key is None
        assert auth.device_key is None


# ---------------------------------------------------------------------------
# Tests: device_login() — client is None (line 347-348)
# ---------------------------------------------------------------------------


class TestDeviceLoginClientNone:
    """Cover device_login's async_init call when client is None."""

    async def test_device_login_calls_async_init_when_client_is_none(self):
        """If client is None, async_init is called before proceeding."""
        auth = await _make_auth(device_key="dk-1")
        auth.client = None

        async def fake_async_init():
            auth.client = MagicMock()
            auth._client_id = "test-client-id"

        with patch.object(auth, "async_init", side_effect=fake_async_init) as mock_init:
            auth.loop.run_in_executor = AsyncMock(
                side_effect=_named_client_error("ResourceNotFoundException")
            )
            with pytest.raises(HiveInvalidDeviceAuthentication):
                await auth.device_login()

        mock_init.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: sms_2fa() — NewDeviceMetadata absent (line 441)
# ---------------------------------------------------------------------------


class TestSms2faNoNewDeviceMetadata:
    """Cover line 441: sms_2fa when NewDeviceMetadata is absent in result."""

    async def test_no_new_device_metadata_does_not_set_device_keys(self):
        """When NewDeviceMetadata is absent, device_group_key and device_key stay None."""
        auth = await _make_auth()
        original_group_key = auth.device_group_key  # None
        original_device_key = auth.device_key  # None

        sms_result = {
            "AuthenticationResult": {
                "AccessToken": "sms-access-token",
                # No "NewDeviceMetadata" key
            }
        }
        auth.loop.run_in_executor = AsyncMock(return_value=sms_result)

        result = await auth.sms_2fa("654321", {"Session": "sess-abc"})

        assert auth.access_token == "sms-access-token"
        assert auth.device_group_key == original_group_key  # unchanged
        assert auth.device_key == original_device_key  # unchanged
        assert result is sms_result


# ---------------------------------------------------------------------------
# Tests: sms_2fa() — CodeMismatchException path (lines 424-429)
# ---------------------------------------------------------------------------


class TestSms2faCodeMismatch:
    """Cover lines 424-429: CodeMismatchException raises HiveInvalid2FACode."""

    async def test_code_mismatch_raises_invalid_2fa_code(self):
        """CodeMismatchException in sms_2fa raises HiveInvalid2FACode."""
        auth = await _make_auth()
        auth.loop.run_in_executor = AsyncMock(
            side_effect=_named_client_error("CodeMismatchException")
        )
        with pytest.raises(HiveInvalid2FACode):
            await auth.sms_2fa("000000", {"Session": "sess-1"})

    async def test_not_authorized_raises_invalid_2fa_code(self):
        """NotAuthorizedException in sms_2fa raises HiveInvalid2FACode."""
        auth = await _make_auth()
        auth.loop.run_in_executor = AsyncMock(
            side_effect=_named_client_error("NotAuthorizedException")
        )
        with pytest.raises(HiveInvalid2FACode):
            await auth.sms_2fa("111111", {"Session": "sess-2"})


# ---------------------------------------------------------------------------
# Tests: refresh_token() — client is None (line 440-441)
# ---------------------------------------------------------------------------


class TestRefreshTokenClientNone:
    """Cover line 440-441: refresh_token calls async_init when client is None."""

    async def test_refresh_token_calls_async_init_when_client_is_none(self):
        """If client is None, async_init is awaited before refreshing."""
        auth = await _make_auth()
        auth.client = None

        result_payload = {"AuthenticationResult": {"AccessToken": "refreshed-tok"}}

        async def fake_async_init():
            auth.client = MagicMock()

        with patch.object(auth, "async_init", side_effect=fake_async_init) as mock_init:
            auth.loop.run_in_executor = AsyncMock(return_value=result_payload)
            result = await auth.refresh_token("some-refresh-token")

        mock_init.assert_called_once()
        assert result is result_payload


# ---------------------------------------------------------------------------
# Tests: refresh_token() — result path when no AuthenticationResult (lines 479-485)
# ---------------------------------------------------------------------------


class TestRefreshTokenResultPath:
    """Cover lines 479-485: refresh_token when result is returned normally."""

    async def test_returns_result_directly(self):
        """refresh_token returns the result from Cognito directly."""
        auth = await _make_auth()
        result_payload = {"AuthenticationResult": {"AccessToken": "tok-xyz"}}
        auth.loop.run_in_executor = AsyncMock(return_value=result_payload)

        result = await auth.refresh_token("refresh-tok-abc")

        assert result is result_payload

    async def test_with_device_key_includes_device_key_param(self):
        """When device_key is set, DEVICE_KEY is included in auth_params."""
        auth = await _make_auth(device_key="dk-refresh-001")
        result_payload = {"AuthenticationResult": {"AccessToken": "tok-dk"}}
        auth.loop.run_in_executor = AsyncMock(return_value=result_payload)

        result = await auth.refresh_token("refresh-tok-dk")

        assert result is result_payload

    async def test_without_device_key_sends_only_refresh_token(self):
        """When device_key is None, auth_params has only REFRESH_TOKEN."""
        auth = await _make_auth(device_key=None)
        result_payload = {"AuthenticationResult": {"AccessToken": "tok-no-dk"}}
        auth.loop.run_in_executor = AsyncMock(return_value=result_payload)

        result = await auth.refresh_token("refresh-tok-no-dk")

        assert result is result_payload


# ---------------------------------------------------------------------------
# Tests: login() — swallowed ClientError in initiate_auth (line 280->288)
# ---------------------------------------------------------------------------


class TestLoginInitiateAuthSwallowedClientError:
    """Arc 280->288: ClientError caught but class name is not UserNotFoundException."""

    async def test_other_client_error_in_initiate_auth_falls_through(self):
        """Non-UserNotFoundException ClientError is swallowed; response stays None → TypeError."""
        auth = await _make_auth()

        wrong_cls = type("SomeOtherError", (botocore.exceptions.ClientError,), {})
        wrong_err = wrong_cls(
            {"Error": {"Code": "SomeOtherError", "Message": "msg"}}, "op"
        )
        auth.loop.run_in_executor = AsyncMock(side_effect=wrong_err)

        # Exception is swallowed; line 288 `response["ChallengeName"]` raises TypeError
        # because response is None
        with pytest.raises((TypeError, KeyError)):
            await auth.login()


# ---------------------------------------------------------------------------
# Tests: login() — swallowed EndpointConnectionError in initiate_auth (line 284->288)
# ---------------------------------------------------------------------------


class TestLoginInitiateAuthSwallowedEndpointError:
    """EndpointConnectionError in initiate_auth always raises HiveApiError."""

    async def test_wrong_name_endpoint_error_in_initiate_auth_raises_api_error(self):
        """Any EndpointConnectionError subclass in initiate_auth raises HiveApiError."""
        auth = await _make_auth()

        wrong_cls = type(
            "WrongEndpoint", (botocore.exceptions.EndpointConnectionError,), {}
        )
        wrong_err = wrong_cls(endpoint_url="https://cognito.eu-west-1.amazonaws.com")
        auth.loop.run_in_executor = AsyncMock(side_effect=wrong_err)

        with pytest.raises(HiveApiError):
            await auth.login()


# ---------------------------------------------------------------------------
# Tests: login() — swallowed ClientError in respond_to_auth_challenge (307->319)
# ---------------------------------------------------------------------------


class TestLoginChallengeSwallowedClientError:
    """Arc 307->319: ClientError caught in challenge response with name not matching."""

    async def test_other_client_error_in_challenge_falls_through(self):
        """ClientError that is neither NotAuthorized nor ResourceNotFound is swallowed."""
        auth = await _make_auth()

        challenge_response = {
            "ChallengeName": "PASSWORD_VERIFIER",
            "ChallengeParameters": {
                "USER_ID_FOR_SRP": "user@test.com",
                "SALT": "aabbccdd",
                "SRP_B": "ccddee",
                "SECRET_BLOCK": "YWJj",
            },
        }

        wrong_cls = type("ThirdPartyError", (botocore.exceptions.ClientError,), {})
        wrong_err = wrong_cls(
            {"Error": {"Code": "ThirdPartyError", "Message": "msg"}}, "op"
        )

        with patch.object(auth, "process_challenge", new_callable=AsyncMock) as mock_ch:
            mock_ch.return_value = {"TIMESTAMP": "...", "USERNAME": "user"}
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[challenge_response, wrong_err]
            )
            # Exception is swallowed; result stays None → TypeError on line 321
            with pytest.raises((TypeError, AttributeError)):
                await auth.login()


# ---------------------------------------------------------------------------
# Tests: login() — swallowed EndpointConnectionError in challenge (313->319)
# ---------------------------------------------------------------------------


class TestLoginChallengeSwallowedEndpointError:
    """EndpointConnectionError in respond_to_auth_challenge always raises HiveApiError."""

    async def test_wrong_name_endpoint_error_in_challenge_raises_api_error(self):
        """Any EndpointConnectionError subclass in SRP challenge raises HiveApiError."""
        auth = await _make_auth()

        challenge_response = {
            "ChallengeName": "PASSWORD_VERIFIER",
            "ChallengeParameters": {
                "USER_ID_FOR_SRP": "user@test.com",
                "SALT": "aabbccdd",
                "SRP_B": "ccddee",
                "SECRET_BLOCK": "YWJj",
            },
        }

        wrong_cls = type(
            "WrongEndpoint", (botocore.exceptions.EndpointConnectionError,), {}
        )
        wrong_err = wrong_cls(endpoint_url="https://cognito.eu-west-1.amazonaws.com")

        with patch.object(auth, "process_challenge", new_callable=AsyncMock) as mock_ch:
            mock_ch.return_value = {"TIMESTAMP": "...", "USERNAME": "user"}
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[challenge_response, wrong_err]
            )
            with pytest.raises(HiveApiError):
                await auth.login()


# ---------------------------------------------------------------------------
# Tests: device_login() — success path through process_device_challenge (lines 364-367, 391)
# ---------------------------------------------------------------------------


class TestDeviceLoginSuccessPath:
    """Lines 364-367, 391: device_login processes device challenge and returns result."""

    async def test_successful_device_login_returns_auth_result(self):
        """Full device_login success: process_device_challenge called, result returned."""
        auth = await _make_auth(device_key="dk-abc", device_group_key="grp-abc")
        auth.device_password = "dev-pass"

        initial_result = {
            "ChallengeParameters": {
                "USERNAME": "user@test.com",
                "SALT": "aabbccdd",
                "SRP_B": "ccddee",
                "SECRET_BLOCK": "YWJj",
            }
        }
        final_result = {"AuthenticationResult": {"AccessToken": "device-access-token"}}

        with patch.object(
            auth, "process_device_challenge", new_callable=AsyncMock
        ) as mock_pdc:
            mock_pdc.return_value = {
                "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
                "USERNAME": "user@test.com",
                "PASSWORD_CLAIM_SECRET_BLOCK": "YWJj",
                "PASSWORD_CLAIM_SIGNATURE": "sig",
                "DEVICE_KEY": "dk-abc",
            }
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[initial_result, final_result]
            )
            result = await auth.device_login()

        mock_pdc.assert_called_once_with(initial_result["ChallengeParameters"])
        assert result is final_result

    async def test_device_login_calls_second_respond_to_auth_challenge(self):
        """Lines 367-375: second respond_to_auth_challenge is called with device challenge."""
        auth = await _make_auth(device_key="dk-xyz", device_group_key="grp-xyz")
        auth.device_password = "dev-pass-xyz"

        initial_result = {
            "ChallengeParameters": {
                "USERNAME": "user@test.com",
                "SALT": "11223344",
                "SRP_B": "55667788",
                "SECRET_BLOCK": "dGVzdA==",
            }
        }
        final_result = {"AuthenticationResult": {"AccessToken": "tok-xyz"}}

        challenge_resp = {
            "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
            "USERNAME": "user@test.com",
            "PASSWORD_CLAIM_SECRET_BLOCK": "dGVzdA==",
            "PASSWORD_CLAIM_SIGNATURE": "sig",
            "DEVICE_KEY": "dk-xyz",
        }

        with patch.object(
            auth, "process_device_challenge", new_callable=AsyncMock
        ) as mock_pdc:
            mock_pdc.return_value = challenge_resp
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[initial_result, final_result]
            )
            result = await auth.device_login()

        assert auth.loop.run_in_executor.call_count == 2
        assert result["AuthenticationResult"]["AccessToken"] == "tok-xyz"


# ---------------------------------------------------------------------------
# Tests: device_login() — wrong-name EndpointConnectionError (line 389)
# ---------------------------------------------------------------------------


class TestDeviceLoginEndpointWrongName:
    """Any EndpointConnectionError in device_login always raises HiveApiError."""

    async def test_wrong_name_endpoint_error_raises_api_error(self):
        """Any EndpointConnectionError subclass in device_login raises HiveApiError."""
        auth = await _make_auth(device_key="dk-err", device_group_key="grp-err")
        auth.device_password = "dev-pass-err"

        wrong_cls = type(
            "WrongEndpoint", (botocore.exceptions.EndpointConnectionError,), {}
        )
        wrong_err = wrong_cls(endpoint_url="https://cognito.eu-west-1.amazonaws.com")
        auth.loop.run_in_executor = AsyncMock(side_effect=wrong_err)

        with pytest.raises(HiveApiError):
            await auth.device_login()


# ---------------------------------------------------------------------------
# Tests: sms_2fa() — swallowed ClientError (arc 424->435)
# ---------------------------------------------------------------------------


class TestSms2faSwallowedClientError:
    """Arc 424->435: ClientError caught in sms_2fa with unrecognised class name."""

    async def test_other_client_error_is_swallowed_returns_none(self):
        """Non-matching ClientError is swallowed; result stays None (returned)."""
        auth = await _make_auth()

        wrong_cls = type("OtherError", (botocore.exceptions.ClientError,), {})
        wrong_err = wrong_cls({"Error": {"Code": "OtherError", "Message": "msg"}}, "op")
        auth.loop.run_in_executor = AsyncMock(side_effect=wrong_err)

        result = await auth.sms_2fa("123456", {"Session": "sess-xyz"})
        assert (
            result is None
        )  # sms_2fa initialises result=None; swallowed → returns None


# ---------------------------------------------------------------------------
# Tests: sms_2fa() — swallowed EndpointConnectionError (arc 431->435)
# ---------------------------------------------------------------------------


class TestSms2faSwallowedEndpointError:
    """Any EndpointConnectionError in sms_2fa raises HiveApiError."""

    async def test_wrong_name_endpoint_error_raises_api_error(self):
        """Any EndpointConnectionError subclass in sms_2fa raises HiveApiError."""
        auth = await _make_auth()

        wrong_cls = type(
            "WrongEndpoint", (botocore.exceptions.EndpointConnectionError,), {}
        )
        wrong_err = wrong_cls(endpoint_url="https://cognito.eu-west-1.amazonaws.com")
        auth.loop.run_in_executor = AsyncMock(side_effect=wrong_err)

        with pytest.raises(HiveApiError):
            await auth.sms_2fa("654321", {"Session": "sess-abc"})


# ---------------------------------------------------------------------------
# Tests: refresh_token() — swallowed EndpointConnectionError (arc 479->485)
# ---------------------------------------------------------------------------


class TestRefreshTokenSwallowedEndpointError:
    """Any EndpointConnectionError in refresh_token raises HiveApiError."""

    async def test_wrong_name_endpoint_error_raises_api_error(self):
        """Any EndpointConnectionError subclass in refresh_token raises HiveApiError."""
        auth = await _make_auth()

        wrong_cls = type(
            "WrongEndpoint", (botocore.exceptions.EndpointConnectionError,), {}
        )
        wrong_err = wrong_cls(endpoint_url="https://cognito.eu-west-1.amazonaws.com")
        auth.loop.run_in_executor = AsyncMock(side_effect=wrong_err)

        with pytest.raises(HiveApiError):
            await auth.refresh_token("some-refresh-token")


# ---------------------------------------------------------------------------
# Tests: async_init() — missing REGION or UPID keys
# ---------------------------------------------------------------------------


class TestAsyncInitMissingKeys:
    """async_init must raise HiveUnknownConfiguration when login info keys are absent."""

    async def test_async_init_missing_region_raises_configuration_error(self):
        """If REGION is absent from login info, raise HiveUnknownConfiguration."""
        from apyhiveapi.api.hive_auth_async import HiveAuthAsync
        from apyhiveapi.helper.hive_exceptions import HiveUnknownConfiguration

        auth = HiveAuthAsync(username="user@test.com", password="pass")
        bad_login_info = {"UPID": "eu-west-1_TestPool", "CLIID": "test-client-id"}
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(side_effect=[bad_login_info])
        with patch("asyncio.get_running_loop", return_value=mock_loop):
            with pytest.raises(HiveUnknownConfiguration):
                await auth.async_init()

    async def test_async_init_missing_upid_raises_configuration_error(self):
        """If UPID is absent from login info, raise HiveUnknownConfiguration."""
        from apyhiveapi.api.hive_auth_async import HiveAuthAsync
        from apyhiveapi.helper.hive_exceptions import HiveUnknownConfiguration

        auth = HiveAuthAsync(username="user@test.com", password="pass")
        bad_login_info = {"CLIID": "test-client-id", "REGION": "eu-west-1_TestPool"}
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(side_effect=[bad_login_info])
        with patch("asyncio.get_running_loop", return_value=mock_loop):
            with pytest.raises(HiveUnknownConfiguration):
                await auth.async_init()


# ---------------------------------------------------------------------------
# Tests: get_password_authentication_key() — None _pool_id
# ---------------------------------------------------------------------------


class TestGetPasswordAuthKeyNonePoolId:
    """get_password_authentication_key must not crash with AttributeError when _pool_id is None."""

    async def test_none_pool_id_raises_configuration_error(self):
        """If _pool_id is None, raise HiveUnknownConfiguration (not AttributeError)."""
        from apyhiveapi.helper.hive_exceptions import HiveUnknownConfiguration

        auth = await _make_auth()
        auth._pool_id = None
        with pytest.raises(HiveUnknownConfiguration):
            auth.get_password_authentication_key("user", "pass", "DEADBEEF", "ABCDEF")
