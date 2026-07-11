"""Diagnose the Heat on Demand MALFORMED_REQUEST error (issue #204).

WARNING: this talks to your REAL Hive account and REAL thermostat, not a
sandbox. It stops at the first payload shape that gets a verified state
change (HTTP 2xx AND a re-fetch confirming autoBoost actually changed --
Hive's backend has been observed returning 200 for shapes it silently
ignores). A verified success will actually flip Heat on Demand on your real
device.

Credentials are never hard-coded or logged: set HIVE_USERNAME / HIVE_PASSWORD
as environment variables before running, or leave them unset and you'll be
prompted (password via getpass, hidden input).

Prerequisite: `pip install -e .` from the repo root so `apyhiveapi` resolves
to this local source tree, then run:

    python scripts/diagnose_heat_on_demand.py
"""

import asyncio
import getpass
import json
import logging
import os

from apyhiveapi import Hive
from apyhiveapi.helper.hive_exceptions import HiveApiError, HiveReauthRequired

logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

# Ordered from "reproduce the known bug" to increasingly different shapes.
# None of these are confirmed against Hive's backend -- they're guesses. A
# 200 response is NOT enough to call a shape correct: Hive's backend was
# observed accepting {"auto_boost": "ENABLED"} with HTTP 200 while silently
# not applying it. So every 2xx response gets re-verified against a re-fetch
# of the device before being trusted.
CANDIDATE_BODIES = [
    ("current code (expected to fail with MALFORMED_REQUEST)", {"autoBoost": "ENABLED"}),
    ("boolean value", {"autoBoost": True}),
    ("lowercase value", {"autoBoost": "enabled"}),
    (
        "snake_case field name (known false positive: 200 but no effect)",
        {"auto_boost": "ENABLED"},
    ),
    ("nested object matching read-side shape", {"autoBoost": {"active": True}}),
    (
        "nested object, full read-side shape echoed back",
        None,  # filled in once we know the device's current props
    ),
    ("snake_case field, nested object", {"auto_boost": {"active": True}}),
    ("nested under props", {"props": {"autoBoost": {"active": True}}}),
    ("wrapped in products array", None),  # filled in once we know node_id
]


async def attempt(hive: Hive, node_type: str, node_id: str, label: str, body: dict) -> bool:
    """POST *body* to the node's state endpoint and report the outcome."""
    url = hive.api.urls["nodes"].format(node_type, node_id)
    print(f"\n=== {label} ===\nPOST {url}\nBody: {json.dumps(body)}")
    try:
        resp = await hive.api._call_endpoint(  # noqa: SLF001 -- deliberate direct call for diagnostics
            "post", url, data=json.dumps(body)
        )
    except HiveApiError:
        print("-> Raised HiveApiError (see log line above for HTTP status + response body)")
        return False
    status = resp.get("original")
    print(f"-> HTTP {status} — parsed: {resp.get('parsed')}")
    return str(status).startswith("20")


async def verify_state_changed(hive: Hive, node_id: str, baseline: dict) -> dict | None:
    """Re-fetch the device and return the new autoBoost value if it differs from *baseline*."""
    await asyncio.sleep(2)  # give Hive's backend a moment to settle
    await hive.get_devices("No_ID")
    new_boost = hive.data.products[node_id].get("props", {}).get("autoBoost")
    print(f"Re-fetched autoBoost: {new_boost!r} (was: {baseline!r})")
    return new_boost if new_boost != baseline else None


async def login_with_sms_fallback(hive: Hive) -> None:
    """Log in, prompting for an SMS code if challenged.

    If Hive's "remembered device" flow rejects us (HiveReauthRequired --
    device is known but Cognito wants it re-verified via SMS, a path
    hive.login() doesn't surface directly), drop any stale device
    credentials and retry once as a plain fresh login so Cognito issues a
    top-level SMS_MFA challenge instead.
    """
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

        heating_products = [
            p for p in hive.data.products.values() if p.get("type") == "heating"
        ]
        if not heating_products:
            print("No 'heating' product found on this account — nothing to test.")
            return

        product = heating_products[0]
        node_id = product["id"]
        current_boost = product.get("props", {}).get("autoBoost")
        print(
            f"\nTarget device: {node_id} (current autoBoost value: {current_boost!r})"
        )
        input(
            "This will send several test requests to your REAL thermostat and may "
            "change its Heat on Demand setting. Press Enter to continue, Ctrl+C to abort..."
        )

        full_shape_echo = dict(current_boost) if isinstance(current_boost, dict) else {}
        full_shape_echo["active"] = True
        for i, (label, body) in enumerate(CANDIDATE_BODIES):
            if body is None and "full read-side shape" in label:
                CANDIDATE_BODIES[i] = (label, {"autoBoost": full_shape_echo})
            elif body is None and "products array" in label:
                CANDIDATE_BODIES[i] = (
                    label,
                    {"products": [{"id": node_id, "props": {"autoBoost": full_shape_echo}}]},
                )

        baseline = current_boost
        for label, body in CANDIDATE_BODIES:
            got_2xx = await attempt(hive, "heating", node_id, label, body)
            if not got_2xx:
                await asyncio.sleep(1)
                continue

            new_boost = await verify_state_changed(hive, node_id, baseline)
            if new_boost is not None:
                print(f"\n*** VERIFIED SUCCESS: {label} -> {json.dumps(body)} ***")
                print(f"autoBoost actually changed: {baseline!r} -> {new_boost!r}")
                print("This is the payload shape to report on issue #204.")
                return

            print(
                "HTTP 2xx but the device did NOT actually change — false positive, "
                "trying next shape."
            )
            await asyncio.sleep(1)

        print(
            "\nNone of the candidate shapes produced a verified change. Copy the "
            "HTTP status + response bodies above into issue #204 -- the response "
            "text often names the exact field Hive's backend is rejecting."
        )


if __name__ == "__main__":
    asyncio.run(main())
