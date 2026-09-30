"""MTProto configuration collector.

This module is deliberately small and transport-oriented. The first version
uses Telethon so the collector can call official MTProto methods directly.
Raw responses are normalized before they are written to data/ so volatile
values do not create meaningless Git diffs.
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
    # This value changes independently of the configuration itself.
    data.pop("ton_usd_rate", None)
    return data


async def collect_dc(dc: str, test_mode: bool, endpoint: tuple[str, int]) -> None:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]

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

    await client.start(bot_token=os.environ["TG_BOT_TOKEN"])
    try:
        config = await client(GetConfigRequest())
        app_config = await client(GetAppConfigRequest())

        target = DATA_ROOT / ("test" if test_mode else "production") / f"dc{dc.replace('-test', '')}"
        target.mkdir(parents=True, exist_ok=True)

        (target / "config.json").write_text(
            json.dumps(normalize_config(config), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (target / "app-config.json").write_text(
            json.dumps(normalize_app_config(app_config), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    finally:
        await client.disconnect()


async def collect_all() -> None:
    endpoints = json.loads(os.environ["TDC_DC_ENDPOINTS"])
    jobs = []
    for dc in PRODUCTION_DCS:
        jobs.append(collect_dc(dc, False, tuple(endpoints[dc])))
    for dc in TEST_DCS:
        jobs.append(collect_dc(dc, True, tuple(endpoints[dc])))
    await asyncio.gather(*jobs)


def main() -> None:
    asyncio.run(collect_all())


if __name__ == "__main__":
    main()
