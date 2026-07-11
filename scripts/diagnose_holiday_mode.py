"""Diagnose Hive's undocumented /holiday-mode endpoint.

WARNING: this talks to your REAL Hive account and affects REAL heating
behaviour while active. /holiday-mode has never been implemented in this
library (checked back to 2021) -- only the URL was ever recorded, so we are
starting from nothing.

Safety approach:
  1. GET first (read-only) to see the current shape, if any.
  2. Only if GET doesn't reveal enough, try a short-window candidate PUT
     (default: 5 minutes from now), verified by re-fetching afterwards.
  3. Immediately attempt to cancel/revert after a verified success, and
     verify the cancellation too.
  4. Every write step requires an explicit confirmation prompt.

Credentials are never hard-coded or logged: set HIVE_USERNAME / HIVE_PASSWORD
as environment variables before running, or leave them unset and you'll be
prompted (password via getpass, hidden input).

Prerequisite: `pip install -e .` from the repo root, then run:

    python scripts/diagnose_holiday_mode.py
"""

import asyncio
import getpass
import json
import logging
import os
from datetime import datetime, timedelta, timezone

from apyhiveapi import Hive
from apyhiveapi.helper.hive_exceptions import HiveApiError, HiveReauthRequired

logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

TEST_WINDOW_MINUTES = 5

# Guesses only -- informed by whatever GET reveals, tried in order. Each is
# verified by re-fetching /holiday-mode (and the target product's autoBoost)
# afterwards; a 2xx alone is not trusted (autoBoost diagnostics showed Hive
# returns 200 for shapes it silently ignores).
def build_candidate_bodies(start: datetime, end: datetime) -> list[tuple[str, dict]]:
    start_iso = start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_iso = end.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return [
        ("camelCase start/end", {"startDate": start_iso, "endDate": end_iso}),
        ("snake_case start/end", {"start_date": start_iso, "end_date": end_iso}),
        ("short keys", {"start": start_iso, "end": end_iso}),
        (
            "camelCase with enabled flag",
            {"enabled": True, "startDate": start_iso, "endDate": end_iso},
        ),
    ]


async def get_holiday_mode(hive: Hive) -> dict:
    """GET the current holiday-mode resource. Read-only, always safe."""
    url = hive.api.urls["holiday_mode"]
    print(f"\nGET {url}")
    resp = await hive.api._call_endpoint("get", url)  # noqa: SLF001
    print(f"-> HTTP {resp.get('original')} — parsed: {resp.get('parsed')}")
    return resp


async def attempt(hive: Hive, label: str, method: str, body: dict | None) -> tuple[bool, dict]:
    url = hive.api.urls["holiday_mode"]
    print(f"\n=== {label} ({method.upper()}) ===\nBody: {json.dumps(body)}")
    try:
        resp = await hive.api._call_endpoint(  # noqa: SLF001
            method, url, data=json.dumps(body) if body is not None else None
        )
    except HiveApiError:
        print("-> Raised HiveApiError (see log line above for HTTP status + response body)")
        return False, {}
    status = resp.get("original")
    print(f"-> HTTP {status} — parsed: {resp.get('parsed')}")
    return str(status).startswith("20"), resp


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


async def main() -> None:
    username = os.environ.get("HIVE_USERNAME") or input("Hive username (email): ")
    password = os.environ.get("HIVE_PASSWORD") or getpass.getpass("Hive password: ")

    async with Hive(username=username, password=password) as hive:
        await login_with_sms_fallback(hive)
        await hive.start_session()

        print("\nStep 1: read-only GET of /holiday-mode (safe, no changes made).")
        await get_holiday_mode(hive)

        proceed = input(
            "\nStep 2 will send a WRITE request that may activate holiday mode "
            f"on your REAL account for up to {TEST_WINDOW_MINUTES} minutes, and will "
            "immediately try to cancel it afterwards. Type 'yes' to continue, "
            "anything else to stop here: "
        )
        if proceed.strip().lower() != "yes":
            print("Stopping after the read-only GET, as requested.")
            return

        now = datetime.now(timezone.utc)
        end = now + timedelta(minutes=TEST_WINDOW_MINUTES)
        candidates = build_candidate_bodies(now, end)

        heating_products = [
            p for p in hive.data.products.values() if p.get("type") == "heating"
        ]
        node_id = heating_products[0]["id"] if heating_products else None
        baseline_boost = (
            heating_products[0].get("props", {}).get("autoBoost")
            if heating_products
            else None
        )

        for label, body in candidates:
            ok, _ = await attempt(hive, label, "put", body)
            if not ok:
                await asyncio.sleep(1)
                continue

            print("Got 2xx — verifying via re-fetch (GET /holiday-mode + device autoBoost)...")
            await asyncio.sleep(2)
            hm_resp = await get_holiday_mode(hive)
            new_boost = None
            if node_id:
                await hive.get_devices("No_ID")
                new_boost = hive.data.products[node_id].get("props", {}).get("autoBoost")
                print(f"autoBoost now: {new_boost!r} (was: {baseline_boost!r})")

            verified = new_boost is not None and new_boost != baseline_boost
            if not verified:
                print("No verified change — treating as a false positive, trying next shape.")
                await asyncio.sleep(1)
                continue

            print(f"\n*** VERIFIED SUCCESS: {label} -> {json.dumps(body)} ***")
            print(f"holiday-mode GET now shows: {hm_resp.get('parsed')}")
            print("Attempting immediate cancellation...")

            cancelled = await try_cancel(hive)
            if cancelled:
                print("Cancellation verified — holiday mode is back off.")
            else:
                print(
                    "!! Could not verify cancellation. The test window was only "
                    f"{TEST_WINDOW_MINUTES} minutes, so it will lapse on its own, "
                    "but check the Hive app now to be sure."
                )
            return

        print(
            "\nNo candidate body produced a verified holiday-mode activation. "
            "See the GET response above for whatever shape Hive did return -- "
            "that's the most useful lead for a follow-up attempt."
        )


async def try_cancel(hive: Hive) -> bool:
    """Best-effort cancellation attempt, verified via re-fetch."""
    url = hive.api.urls["holiday_mode"]
    for label, method, body in [
        ("DELETE", "delete", None),
        ("PUT enabled=false", "put", {"enabled": False}),
    ]:
        print(f"\nCancel attempt: {label}")
        try:
            resp = await hive.api._call_endpoint(  # noqa: SLF001
                method, url, data=json.dumps(body) if body is not None else None
            )
        except HiveApiError:
            print("-> Raised HiveApiError")
            continue
        print(f"-> HTTP {resp.get('original')} — parsed: {resp.get('parsed')}")
        await asyncio.sleep(2)
        check = await get_holiday_mode(hive)
        parsed = check.get("parsed")
        if isinstance(parsed, dict) and parsed.get("enabled") is False:
            return True
    return False


if __name__ == "__main__":
    asyncio.run(main())
