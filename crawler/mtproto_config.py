"""Collect MTProto configuration snapshots from Telegram.

Production DC endpoints are discovered from Telegram through help.getConfig.
Test DCs use the same application API credentials with separate test-network
endpoints and fresh in-memory sessions.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

from telethon import TelegramClient
from telethon.sessions import MemorySession, StringSession
from telethon.tl.functions.help import (
    GetAppConfigRequest,
    GetCdnConfigRequest,
    GetConfigRequest,
    GetCountriesListRequest,
    GetPremiumPromoRequest,
)
from telethon.tl.functions.messages import GetAvailableReactionsRequest

from .safety import validate_snapshot

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "mtproto"

PRODUCTION_DCS = ("1", "2", "3", "4", "5")
TEST_DCS = ("1-test", "2-test", "3-test")

# Telegram's standard MTProto test DC IPv4 endpoints.
# TDC_TEST_DC_ENDPOINTS can override these values when Telegram changes
# the endpoint used by a specific test environment.
DEFAULT_TEST_DC_ENDPOINTS: dict[str, tuple[str, int]] = {
    "1-test": ("149.154.175.10", 80),
    "2-test": ("149.154.167.40", 80),
    "3-test": ("149.154.175.117", 80),
}


def json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def normalize_config(value: Any) -> Any:
    data = json_safe(value.to_dict())
    data["date"] = 0
    data["expires"] = 0
    data["dc_options"] = []
    data["autologin_token"] = None
    return data


def normalize_app_config(value: Any) -> Any:
    data = json_safe(value.to_dict())
    data["hash"] = 0
    data.pop("ton_usd_rate", None)
    return data


def normalize_premium_promo(value: Any) -> Any:
    data = json_safe(value.to_dict())
    data["users"] = []
    data["status_text"] = "crawler"
    data["status_entities"] = []
    data["period_options"] = []
    return data


def parse_dc_options(config: Any) -> dict[str, tuple[str, int]]:
    endpoints: dict[str, tuple[str, int]] = {}

    for option in config.dc_options:
        values = option.to_dict() if hasattr(option, "to_dict") else option
        dc_id = str(values.get("id", ""))
        ip = values.get("ip_address")
        port = values.get("port")

        if not dc_id or not ip or not port or ":" in str(ip):
            continue

        key = dc_id.replace("-test", "")
        if key in PRODUCTION_DCS and key not in endpoints:
            endpoints[key] = (str(ip), int(port))

    missing = set(PRODUCTION_DCS) - endpoints.keys()
    if missing:
        raise RuntimeError(
            "Telegram help.getConfig did not provide endpoints for DCs: "
            + ", ".join(sorted(missing))
        )

    return endpoints


def load_test_endpoints() -> dict[str, tuple[str, int]]:
    endpoints = dict(DEFAULT_TEST_DC_ENDPOINTS)
    raw = os.getenv("TDC_TEST_DC_ENDPOINTS", "").strip()
    if not raw:
        return endpoints

    values = json.loads(raw)
    for dc in TEST_DCS:
        endpoint = values.get(dc)
        if endpoint:
            endpoints[dc] = (str(endpoint[0]), int(endpoint[1]))
    return endpoints


def read_previous(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_snapshot(path: Path, value: Any) -> None:
    previous = read_previous(path)
    if previous is not None:
        validate_snapshot(previous, value)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value if isinstance(value, dict) else value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


async def discover_production_endpoints() -> dict[str, tuple[str, int]]:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    client = TelegramClient(
        MemorySession(),
        api_id,
        api_hash,
        device_model="Telegram Developer Crawler",
        system_version="1.0",
        app_version="0.1",
    )
    await client.connect()
    try:
        config = await client(GetConfigRequest())
        return parse_dc_options(config)
    finally:
        await client.disconnect()


async def collect_dc(
    dc: str,
    test_mode: bool,
    endpoint: tuple[str, int],
    api_id: int,
    api_hash: str,
) -> None:
    # Test DCs must always use a fresh in-memory session. Do not reuse a
    # production authorization key on the test network. Telethon's current
    # test-server guidance notes that port 443 may not work, so if a default
    # 443 endpoint is supplied, retry the same host on port 80.
    endpoints = [endpoint]
    if test_mode and endpoint[1] == 443:
        endpoints.append((endpoint[0], 80))

    last_error: BaseException | None = None
    for server_address, port in endpoints:
        session = MemorySession()
        dc_id = int(dc.replace("-test", ""))
        session.set_dc(dc_id, server_address, port)
        client = TelegramClient(
            session,
            api_id,
            api_hash,
            device_model="Telegram Developer Crawler",
            system_version="1.0",
            app_version="0.1",
        )

        try:
            await client.connect()
            config = await client(GetConfigRequest())
            countries = await client(GetCountriesListRequest(lang_code="en", hash=0))
            app_config = await client(GetAppConfigRequest(0))

            network = "test" if test_mode else "production"
            dc_name = f"dc{dc.replace('-test', '')}"

            # Keep distinct Telegram datasets in distinct top-level categories.
            # help.getConfig is server/MTProto configuration, while
            # help.getAppConfig is client-specific application configuration.
            write_snapshot(
                DATA_ROOT / "configs" / network / dc_name / "config.json",
                normalize_config(config),
            )
            write_snapshot(
                DATA_ROOT / "countries-list" / network / dc_name / "countries-list.json",
                json_safe(countries.to_dict()),
            )
            write_snapshot(
                DATA_ROOT / "app-config" / network / dc_name / "app-config.json",
                normalize_app_config(app_config),
            )
            return
        except (OSError, asyncio.TimeoutError, ConnectionError) as exc:
            last_error = exc
            if len(endpoints) == 1:
                raise
        finally:
            await client.disconnect()

    assert last_error is not None
    raise last_error


async def collect_bot_global_config() -> None:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    client = TelegramClient(
        MemorySession(),
        api_id,
        api_hash,
        device_model="Telegram Developer Crawler",
        system_version="1.0",
        app_version="0.1",
    )

    await client.connect()
    try:
        cdn_config = await client(GetCdnConfigRequest())
        write_snapshot(
            DATA_ROOT / "global" / "cdn-config.json",
            json_safe(cdn_config.to_dict()),
        )
    finally:
        await client.disconnect()


async def collect_user_only_config() -> None:
    session_string = os.getenv("TG_USER_SESSION", "").strip()
    if not session_string:
        print(
            "User-only MTProto datasets skipped: TG_USER_SESSION is not configured. "
            "This is required for messages.getAvailableReactions and help.getPremiumPromo."
        )
        return

    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    client = TelegramClient(
        StringSession(session_string),
        api_id,
        api_hash,
        device_model="Telegram Developer Crawler",
        system_version="1.0",
        app_version="0.1",
    )

    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise RuntimeError("TG_USER_SESSION is not authorized")

        reactions = await client(GetAvailableReactionsRequest(hash=0))
        premium = await client(GetPremiumPromoRequest())

        target = DATA_ROOT / "global"
        write_snapshot(
            target / "available-reactions.json",
            json_safe(reactions.to_dict()),
        )
        write_snapshot(
            target / "premium-promo.json",
            normalize_premium_promo(premium),
        )
    finally:
        await client.disconnect()


async def collect_all() -> None:
    production = await discover_production_endpoints()
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]

    jobs = [
        collect_dc(
            dc,
            False,
            production[dc],
            api_id,
            api_hash,
        )
        for dc in PRODUCTION_DCS
    ]

    # Telegram's test environment uses the same application api_id/api_hash.
    # Only the DC endpoints and fresh MTProto session differ.
    test_endpoints = load_test_endpoints()
    jobs.extend(
        collect_dc(
            dc,
            True,
            test_endpoints[dc],
            api_id,
            api_hash,
        )
        for dc in TEST_DCS
        if dc in test_endpoints
    )

    await asyncio.gather(
        *jobs,
        collect_bot_global_config(),
        collect_user_only_config(),
    )


def main() -> None:
    asyncio.run(collect_all())


if __name__ == "__main__":
    main()
