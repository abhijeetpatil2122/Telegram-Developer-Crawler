"""Collect MTProto configuration snapshots from Telegram.

Production DC endpoints are discovered from Telegram through help.getConfig.
Test DCs use separate optional credentials and explicitly configured endpoints.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from telethon import TelegramClient
from telethon.sessions import MemorySession
from telethon.tl.functions.help import GetAppConfigRequest, GetConfigRequest

from .safety import validate_snapshot

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "mtproto" / "config"

PRODUCTION_DCS = ("1", "2", "3", "4", "5")
TEST_DCS = ("1-test", "2-test", "3-test")


def json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
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
    return data


def normalize_app_config(value: Any) -> Any:
    data = json_safe(value.to_dict())
    data.pop("ton_usd_rate", None)
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
    raw = os.getenv("TDC_TEST_DC_ENDPOINTS", "").strip()
    if not raw:
        return {}

    values = json.loads(raw)
    result: dict[str, tuple[str, int]] = {}
    for dc in TEST_DCS:
        endpoint = values.get(dc)
        if endpoint:
            result[dc] = (str(endpoint[0]), int(endpoint[1]))
    return result


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
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


async def discover_production_endpoints() -> dict[str, tuple[str, int]]:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    bot_token = os.environ["TG_BOT_TOKEN"]

    client = TelegramClient(
        MemorySession(),
        api_id,
        api_hash,
        device_model="Telegram Developer Crawler",
        system_version="1.0",
        app_version="0.1",
    )
    await client.start(bot_token=bot_token)
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
    bot_token: str,
) -> None:
    session = MemorySession()
    dc_id = int(dc.replace("-test", ""))
    session.set_dc(dc_id, endpoint[0], endpoint[1])

    client = TelegramClient(
        session,
        api_id,
        api_hash,
        test_mode=test_mode,
        device_model="Telegram Developer Crawler",
        system_version="1.0",
        app_version="0.1",
    )

    await client.start(bot_token=bot_token)
    try:
        config = await client(GetConfigRequest())
        app_config = await client(GetAppConfigRequest())

        target = DATA_ROOT / ("test" if test_mode else "production") / f"dc{dc.replace('-test', '')}"
        write_snapshot(target / "config.json", normalize_config(config))
        write_snapshot(target / "app-config.json", normalize_app_config(app_config))
    finally:
        await client.disconnect()


async def collect_all() -> None:
    production = await discover_production_endpoints()
    production_api_id = int(os.environ["TG_API_ID"])
    production_api_hash = os.environ["TG_API_HASH"]
    production_bot_token = os.environ["TG_BOT_TOKEN"]

    jobs = [
        collect_dc(
            dc,
            False,
            production[dc],
            production_api_id,
            production_api_hash,
            production_bot_token,
        )
        for dc in PRODUCTION_DCS
    ]

    test_endpoints = load_test_endpoints()
    test_api_id = os.getenv("TG_TEST_API_ID")
    test_api_hash = os.getenv("TG_TEST_API_HASH")
    test_bot_token = os.getenv("TG_TEST_BOT_TOKEN")

    if test_endpoints and test_api_id and test_api_hash and test_bot_token:
        jobs.extend(
            collect_dc(
                dc,
                True,
                test_endpoints[dc],
                int(test_api_id),
                test_api_hash,
                test_bot_token,
            )
            for dc in TEST_DCS
            if dc in test_endpoints
        )
    else:
        print("Test DC collection skipped: test credentials/endpoints are not configured.")

    await asyncio.gather(*jobs)


def main() -> None:
    asyncio.run(collect_all())


if __name__ == "__main__":
    main()
