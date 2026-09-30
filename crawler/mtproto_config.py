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
from telethon.tl.functions.help import GetAppConfigRequest, GetConfigRequest


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "mtproto" / "config"

PRODUCTION_DCS = ("1", "2", "3", "4", "5")
TEST_DCS = ("1-test", "2-test", "3-test")


def normalize_config(value: Any) -> Any:
    data = value.to_dict()
    data["date"] = 0
    data["expires"] = 0
    data["dc_options"] = []
    return data


def normalize_app_config(value: Any) -> Any:
    data = value.to_dict()
    # This value changes independently of the configuration itself.
    data.pop("ton_usd_rate", None)
    return data


def session_name(dc: str) -> str:
    safe = dc.replace("-", "_")
    return os.path.join(
        os.environ.get("TDC_SESSION_DIR", str(ROOT / ".sessions")),
        f"dc_{safe}",
    )


async def collect_dc(dc: str, test_mode: bool) -> None:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]

    client = TelegramClient(
        session_name(dc),
        api_id,
        api_hash,
        test_mode=test_mode,
        device_model="Telegram Developer Crawler",
        system_version="1.0",
        app_version="0.1",
    )

    await client.start()
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
    jobs = [
        collect_dc(dc, False) for dc in PRODUCTION_DCS
    ] + [
        collect_dc(dc, True) for dc in TEST_DCS
    ]
    await asyncio.gather(*jobs)


def main() -> None:
    asyncio.run(collect_all())


if __name__ == "__main__":
    main()
