"""Live end-to-end test of the new HiveHub holiday mode support.

WARNING: this talks to your REAL Hive account. Test 1 schedules a real
Holiday Mode window starting 1 hour from now -- since "enabled" (scheduled)
and "active" (currently in effect) are separate, this never actually goes
active as long as you cancel it before the hour is up (the script does this
for you). Test 2 tries a start time in the past, which is expected to be
rejected the same way the Hive app/website reject it.

Credentials are never hard-coded or logged: set HIVE_USERNAME / HIVE_PASSWORD
as environment variables before running, or leave them unset and you'll be
prompted (password via getpass, hidden input).

Prerequisite: `pip install -e .` from the repo root, then run:

    python scripts/test_holiday_mode_live.py
"""

import asyncio
import getpass
import logging
import os
from datetime import datetime, timedelta, timezone

from apyhiveapi import Hive
from apyhiveapi.helper.hive_exceptions import HiveApiError, HiveReauthRequired

logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")


def fmt(dt: datetime) -> str:
    """Render a datetime as both UTC and local time, for comparing against the Hive app."""
    local = dt.astimezone()
    return f"{dt.isoformat()} (local: {local.isoformat()})"


def fmt_epoch_ms(epoch_ms: int | None) -> str:
    """Render epoch milliseconds from a Hive API response as UTC + local time."""
    if epoch_ms is None:
        return "None"
    return fmt(datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc))


def fmt_state(state: dict | None) -> str:
    """Render a get_holiday_mode() response with human-readable start/end times."""
    if not state:
        return repr(state)
    rendered = dict(state)
    if "start" in rendered:
        rendered["start"] = fmt_epoch_ms(rendered["start"])
    if "end" in rendered:
        rendered["end"] = fmt_epoch_ms(rendered["end"])
    return repr(rendered)


async def login_with_sms_fallback(hive: Hive) -> None:
    """Log in, prompting for an SMS code if challenged (see diagnose_heat_on_demand.py)."""
    try:
        login_result = await hive.login()
    except HiveReauthRequired:
        print(
            "Device re-authentication required — retrying as a fresh login "
            "to force an SMS code prompt..."
        )
        hive.auth.device_group_key = None
        hive.auth.device_key = None
        hive.auth.device_password = None
        login_result = await hive.login()

    if login_result and login_result.get("ChallengeName") == hive.auth.SMS_MFA_CHALLENGE:
        code = input("Enter the SMS 2FA code sent to your phone: ")
        await hive.sms2fa(code, login_result)


async def test_valid_future_schedule(hive: Hive) -> None:
    print("\n" + "=" * 80)
    print("TEST 1: schedule holiday mode starting 1 hour from now")
    print("=" * 80)

    now = datetime.now(timezone.utc)
    start = now + timedelta(hours=1)
    end = start + timedelta(days=7)
    print(f"start: {fmt(start)}")
    print(f"end:   {fmt(end)}")

    confirm = input(
        "\nThis will schedule Holiday Mode on your REAL account (won't go "
        "active for an hour, and this script cancels it before then). "
        "Type 'yes' to proceed, anything else to skip: "
    )
    if confirm.strip().lower() != "yes":
        print("Skipped.")
        return

    ok = await hive.hub.set_holiday_mode(start, end, 12)
    print(f"set_holiday_mode() -> {ok}")

    input("Check the Hive app/website now, then press Enter to continue...")

    state = await hive.hub.get_holiday_mode()
    print(f"get_holiday_mode() -> {fmt_state(state)}")

    if state:
        expected_start_ms = int(start.timestamp() * 1000)
        expected_end_ms = int(end.timestamp() * 1000)
        # Hive rounds to the nearest minute in practice; allow slack.
        start_close = abs(state.get("start", 0) - expected_start_ms) < 60_000
        end_close = abs(state.get("end", 0) - expected_end_ms) < 60_000
        verified = bool(state.get("enabled")) and start_close and end_close
        print(f"Verified scheduled with matching start/end: {verified}")
    else:
        print("Could not read back holiday mode state.")

    print("\nCancelling now (before it can go active)...")
    cancelled = await hive.hub.cancel_holiday_mode()
    print(f"cancel_holiday_mode() -> {cancelled}")
    final_state = await hive.hub.get_holiday_mode()
    print(f"get_holiday_mode() after cancel -> {fmt_state(final_state)}")
    if final_state and final_state.get("enabled") is False:
        print("Confirmed cancelled.")
    else:
        print("!! Could not confirm cancellation — check the Hive app.")


async def test_start_in_the_past(hive: Hive) -> None:
    print("\n" + "=" * 80)
    print("TEST 2: start time in the past (expected to be rejected)")
    print("=" * 80)

    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=1)
    end = start + timedelta(days=7)
    print(f"start: {fmt(start)} (1 hour ago)")
    print(f"end:   {fmt(end)}")

    try:
        ok = await hive.hub.set_holiday_mode(start, end, 12)
    except HiveApiError:
        print(
            "-> Raised HiveApiError (see log line above for HTTP status + "
            "response body). This matches the expectation that a past start "
            "time is rejected, same as the Hive app/website."
        )
        return

    print(f"set_holiday_mode() -> {ok} (did NOT raise — Hive accepted a past start time)")

    input("Check the Hive app/website now, then press Enter to continue...")

    state = await hive.hub.get_holiday_mode()
    print(f"get_holiday_mode() -> {fmt_state(state)}")
    if ok and state and state.get("enabled"):
        print("It was accepted and applied. Cancelling now to be safe...")
        cancelled = await hive.hub.cancel_holiday_mode()
        print(f"cancel_holiday_mode() -> {cancelled}")


async def main() -> None:
    username = os.environ.get("HIVE_USERNAME") or input("Hive username (email): ")
    password = os.environ.get("HIVE_PASSWORD") or getpass.getpass("Hive password: ")

    async with Hive(username=username, password=password) as hive:
        await login_with_sms_fallback(hive)
        await hive.start_session()

        print("\nCurrent holiday mode state:")
        print(fmt_state(await hive.hub.get_holiday_mode()))

        await test_valid_future_schedule(hive)
        await test_start_in_the_past(hive)


if __name__ == "__main__":
    asyncio.run(main())
