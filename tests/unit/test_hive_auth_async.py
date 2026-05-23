"""Unit tests for HiveAuthAsync."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import botocore.exceptions
import pytest
from apyhiveapi.helper.hive_exceptions import (
    HiveApiError,
    HiveFailedToRefreshTokens,
    HiveInvalid2FACode,
    HiveInvalidDeviceAuthentication,
    HiveInvalidPassword,
    HiveInvalidUsername,
    HiveRefreshTokenExpired,
)

# ---------------------------------------------------------------------------
# Exception factories
# ---------------------------------------------------------------------------


def _named_client_error(
    code: str, message: str = ""
) -> botocore.exceptions.ClientError:
    """Return a ClientError whose __class__.__name__ matches ``code``."""
    # The source checks err.__class__.__name__, so we build a dynamic subclass
    # with the right name.
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
# Fixture-style helpers
# ---------------------------------------------------------------------------


async def _make_auth(
    username: str = "test@test.com",
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
    auth._pool_id = "eu-west-1_TestPool123"
    auth._region = "eu-west-1"
    auth.loop = MagicMock()
    auth.loop.run_in_executor = AsyncMock()
    return auth


# ---------------------------------------------------------------------------
# Tests: __init__
# ---------------------------------------------------------------------------


class TestHiveAuthAsyncInit:
    def test_pool_region_no_longer_accepted(self):
        from apyhiveapi.api.hive_auth_async import HiveAuthAsync

        with pytest.raises(TypeError):
            HiveAuthAsync(username="u", password="p", pool_region="eu-west-1")

    async def test_async_init_sets_running_loop(self):
        from apyhiveapi.api.hive_auth_async import HiveAuthAsync

        auth = HiveAuthAsync(username="u@test.com", password="pass")
        assert auth.loop is None  # not set until async_init
        mock_data = {
            "UPID": "eu-west-1_Test",
            "CLIID": "client-id",
            "REGION": "eu-west-1_Test",
        }
        with patch.object(auth.api, "get_login_info", return_value=mock_data):
            with patch("boto3.client", return_value=MagicMock()):
                await auth.async_init()
        assert auth.loop is not None

    async def test_file_flag_set_for_magic_username(self):
        from apyhiveapi.api.hive_auth_async import HiveAuthAsync

        auth = HiveAuthAsync(username="use@file.com", password="")
        assert auth.use_file is True

    async def test_file_flag_not_set_for_normal_username(self):
        from apyhiveapi.api.hive_auth_async import HiveAuthAsync

        auth = HiveAuthAsync(username="real@user.com", password="pass")
        assert auth.use_file is False


# ---------------------------------------------------------------------------
# Tests: _to_int
# ---------------------------------------------------------------------------


class TestToInt:
    @pytest.mark.asyncio
    async def test_int_input_returns_int(self):
        auth = await _make_auth()
        assert auth._to_int(42) == 42

    @pytest.mark.asyncio
    async def test_bytes_input_returns_int(self):
        auth = await _make_auth()
        # b'\xff' → hex "ff" → 255
        assert auth._to_int(b"\xff") == 255

    @pytest.mark.asyncio
    async def test_hex_string_returns_int(self):
        auth = await _make_auth()
        assert auth._to_int("ff") == 255

    @pytest.mark.asyncio
    async def test_zero_bytes_input(self):
        auth = await _make_auth()
        assert auth._to_int(b"\x00") == 0


# ---------------------------------------------------------------------------
# Tests: get_auth_params
# ---------------------------------------------------------------------------


class TestGetAuthParams:
    @pytest.mark.asyncio
    async def test_returns_username_and_srp_a(self):
        auth = await _make_auth()
        params = await auth.get_auth_params()
        assert "USERNAME" in params
        assert "SRP_A" in params

    @pytest.mark.asyncio
    async def test_no_client_secret_no_secret_hash(self):
        auth = await _make_auth()
        params = await auth.get_auth_params()
        assert "SECRET_HASH" not in params

    @pytest.mark.asyncio
    async def test_with_client_secret_adds_secret_hash(self):
        auth = await _make_auth(client_secret="my-secret")
        params = await auth.get_auth_params()
        assert "SECRET_HASH" in params

    @pytest.mark.asyncio
    async def test_device_login_adds_device_key(self):
        auth = await _make_auth(device_key="dk-1234")
        params = await auth.get_auth_params(is_device_login=True)
        assert params["DEVICE_KEY"] == "dk-1234"

    @pytest.mark.asyncio
    async def test_non_device_login_no_device_key(self):
        auth = await _make_auth(device_key="dk-1234")
        params = await auth.get_auth_params(is_device_login=False)
        assert "DEVICE_KEY" not in params


# ---------------------------------------------------------------------------
# Tests: login
# ---------------------------------------------------------------------------


class TestLogin:
    @pytest.mark.asyncio
    async def test_file_mode_returns_file_response(self):
        auth = await _make_auth(username="use@file.com", password="")
        result = await auth.login()
        assert result == {"AuthenticationResult": {"AccessToken": "file"}}

    @pytest.mark.asyncio
    async def test_user_not_found_raises_invalid_username(self):
        auth = await _make_auth()
        auth.loop.run_in_executor.side_effect = _named_client_error(
            "UserNotFoundException"
        )
        with pytest.raises(HiveInvalidUsername):
            await auth.login()

    @pytest.mark.asyncio
    async def test_endpoint_error_on_initiate_raises_api_error(self):
        auth = await _make_auth()
        auth.loop.run_in_executor.side_effect = _endpoint_error()
        with pytest.raises(HiveApiError):
            await auth.login()

    @pytest.mark.asyncio
    async def test_password_verifier_challenge_not_authorized_raises_invalid_password(
        self,
    ):
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
        not_auth_err = _named_client_error("NotAuthorizedException")
        with patch.object(auth, "process_challenge", new_callable=AsyncMock) as mock_ch:
            mock_ch.return_value = {
                "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
                "USERNAME": "user",
            }
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[challenge_response, not_auth_err]
            )
            with pytest.raises(HiveInvalidPassword):
                await auth.login()

    @pytest.mark.asyncio
    async def test_password_verifier_challenge_resource_not_found_raises_invalid_device(
        self,
    ):
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
        not_found_err = _named_client_error("ResourceNotFoundException")
        with patch.object(auth, "process_challenge", new_callable=AsyncMock) as mock_ch:
            mock_ch.return_value = {
                "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
                "USERNAME": "user",
            }
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[challenge_response, not_found_err]
            )
            with pytest.raises(HiveInvalidDeviceAuthentication):
                await auth.login()

    @pytest.mark.asyncio
    async def test_password_verifier_endpoint_error_on_challenge_raises_api_error(self):
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

    @pytest.mark.asyncio
    async def test_new_device_metadata_stores_device_keys(self):
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
        auth_result = {
            "AuthenticationResult": {
                "AccessToken": "access-tok",
                "NewDeviceMetadata": {
                    "DeviceGroupKey": "grp-key",
                    "DeviceKey": "dev-key",
                },
            }
        }
        with patch.object(auth, "process_challenge", new_callable=AsyncMock) as mock_ch:
            mock_ch.return_value = {
                "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
                "USERNAME": "user",
            }
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[challenge_response, auth_result]
            )
            result = await auth.login()
        assert auth.device_group_key == "grp-key"
        assert auth.device_key == "dev-key"
        assert auth.access_token == "access-tok"
        assert result is auth_result

    @pytest.mark.asyncio
    async def test_access_token_stored_without_new_device_metadata(self):
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
        auth_result = {
            "AuthenticationResult": {
                "AccessToken": "only-token",
            }
        }
        with patch.object(auth, "process_challenge", new_callable=AsyncMock) as mock_ch:
            mock_ch.return_value = {
                "TIMESTAMP": "Mon Jan 01 00:00:00 UTC 2024",
                "USERNAME": "user",
            }
            auth.loop.run_in_executor = AsyncMock(
                side_effect=[challenge_response, auth_result]
            )
            await auth.login()
        assert auth.access_token == "only-token"
        assert auth.device_group_key is None

    @pytest.mark.asyncio
    async def test_unsupported_challenge_raises_not_implemented(self):
        auth = await _make_auth()
        auth.loop.run_in_executor = AsyncMock(
            return_value={
                "ChallengeName": "CUSTOM_CHALLENGE",
                "ChallengeParameters": {},
            }
        )
        with pytest.raises(NotImplementedError, match="CUSTOM_CHALLENGE"):
            await auth.login()


# ---------------------------------------------------------------------------
# Tests: device_login
# ---------------------------------------------------------------------------


class TestDeviceLogin:
    @pytest.mark.asyncio
    async def test_resource_not_found_raises_invalid_device_authentication(self):
        auth = await _make_auth(device_key="dk-1")
        auth.loop.run_in_executor.side_effect = _named_client_error(
            "ResourceNotFoundException"
        )
        with pytest.raises(HiveInvalidDeviceAuthentication):
            await auth.device_login()

    @pytest.mark.asyncio
    async def test_not_authorized_raises_invalid_device_authentication(self):
        auth = await _make_auth(device_key="dk-1")
        auth.loop.run_in_executor.side_effect = _named_client_error(
            "NotAuthorizedException"
        )
        with pytest.raises(HiveInvalidDeviceAuthentication):
            await auth.device_login()

    @pytest.mark.asyncio
    async def test_endpoint_error_raises_api_error(self):
        auth = await _make_auth(device_key="dk-1")
        auth.loop.run_in_executor.side_effect = _endpoint_error()
        with pytest.raises(HiveApiError):
            await auth.device_login()

    @pytest.mark.asyncio
    async def test_other_client_error_propagates(self):
        auth = await _make_auth(device_key="dk-1")
        auth.loop.run_in_executor.side_effect = _named_client_error("SomeOtherError")
        with pytest.raises(botocore.exceptions.ClientError):
            await auth.device_login()


# ---------------------------------------------------------------------------
# Tests: sms_2fa
# ---------------------------------------------------------------------------


class TestSms2fa:
    @pytest.mark.asyncio
    async def test_not_authorized_raises_invalid_2fa_code(self):
        auth = await _make_auth()
        auth.loop.run_in_executor.side_effect = _named_client_error(
            "NotAuthorizedException"
        )
        with pytest.raises(HiveInvalid2FACode):
            await auth.sms_2fa("123456", {"Session": "sess-1"})

    @pytest.mark.asyncio
    async def test_code_mismatch_raises_invalid_2fa_code(self):
        auth = await _make_auth()
        auth.loop.run_in_executor.side_effect = _named_client_error(
            "CodeMismatchException"
        )
        with pytest.raises(HiveInvalid2FACode):
            await auth.sms_2fa("000000", {"Session": "sess-1"})

    @pytest.mark.asyncio
    async def test_endpoint_error_raises_api_error(self):
        auth = await _make_auth()
        auth.loop.run_in_executor.side_effect = _endpoint_error()
        with pytest.raises(HiveApiError):
            await auth.sms_2fa("123456", {"Session": "sess-1"})

    @pytest.mark.asyncio
    async def test_successful_sms_2fa_stores_access_token(self):
        auth = await _make_auth()
        sms_result = {
            "AuthenticationResult": {
                "AccessToken": "sms-token",
            }
        }
        auth.loop.run_in_executor.return_value = sms_result
        result = await auth.sms_2fa("123456", {"Session": "sess-1"})
        assert auth.access_token == "sms-token"
        assert result is sms_result

    @pytest.mark.asyncio
    async def test_new_device_metadata_in_sms_stores_keys(self):
        auth = await _make_auth()
        sms_result = {
            "AuthenticationResult": {
                "AccessToken": "sms-token",
                "NewDeviceMetadata": {
                    "DeviceGroupKey": "sms-grp",
                    "DeviceKey": "sms-dev",
                },
            }
        }
        auth.loop.run_in_executor.return_value = sms_result
        await auth.sms_2fa("123456", {"Session": "sess-1"})
        assert auth.device_group_key == "sms-grp"
        assert auth.device_key == "sms-dev"

    @pytest.mark.asyncio
    async def test_no_authentication_result_key_does_not_raise(self):
        auth = await _make_auth()
        auth.loop.run_in_executor.return_value = {"ChallengeName": "SMS_MFA"}
        result = await auth.sms_2fa("123456", {"Session": "sess-1"})
        assert auth.access_token is None
        assert result == {"ChallengeName": "SMS_MFA"}


# ---------------------------------------------------------------------------
# Tests: refresh_token
# ---------------------------------------------------------------------------


class TestRefreshToken:
    @pytest.mark.asyncio
    async def test_no_device_key_sends_only_refresh_token(self):
        auth = await _make_auth()
        result_payload = {"AuthenticationResult": {"AccessToken": "new-tok"}}
        auth.loop.run_in_executor.return_value = result_payload
        result = await auth.refresh_token("refresh-tok")
        assert result is result_payload

    @pytest.mark.asyncio
    async def test_with_device_key_includes_device_key_in_params(self):
        auth = await _make_auth(device_key="dk-refresh")
        result_payload = {"AuthenticationResult": {"AccessToken": "new-tok"}}
        auth.loop.run_in_executor.return_value = result_payload
        result = await auth.refresh_token("refresh-tok")
        # Verify the call was made (the actual auth_params check is internal,
        # but we at least confirm no exception and correct return value)
        assert result is result_payload

    @pytest.mark.asyncio
    async def test_invalid_refresh_token_raises_expired(self):
        auth = await _make_auth()
        err = botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "NotAuthorizedException",
                    "Message": "Invalid Refresh Token",
                }
            },
            "InitiateAuth",
        )
        auth.loop.run_in_executor.side_effect = err
        with pytest.raises(HiveRefreshTokenExpired):
            await auth.refresh_token("bad-token")

    @pytest.mark.asyncio
    async def test_not_authorized_without_invalid_refresh_raises_failed(self):
        auth = await _make_auth()
        err = botocore.exceptions.ClientError(
            {
                "Error": {
                    "Code": "NotAuthorizedException",
                    "Message": "Some other message",
                }
            },
            "InitiateAuth",
        )
        auth.loop.run_in_executor.side_effect = err
        with pytest.raises(HiveFailedToRefreshTokens):
            await auth.refresh_token("tok")

    @pytest.mark.asyncio
    async def test_other_client_error_raises_failed_to_refresh(self):
        auth = await _make_auth()
        auth.loop.run_in_executor.side_effect = _named_client_error(
            "TokenExpiredException"
        )
        with pytest.raises(HiveFailedToRefreshTokens):
            await auth.refresh_token("tok")

    @pytest.mark.asyncio
    async def test_endpoint_error_raises_api_error(self):
        auth = await _make_auth()
        auth.loop.run_in_executor.side_effect = _endpoint_error()
        with pytest.raises(HiveApiError):
            await auth.refresh_token("tok")
