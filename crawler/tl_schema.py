"""Collect Telegram's official MTProto/TL schemas.

Sources:
- https://core.telegram.org/schema
- https://core.telegram.org/schema/json
- https://core.telegram.org/schema/mtproto
- https://core.telegram.org/schema/mtproto-json

The collector keeps both the human-readable TL source and the official JSON
representation. JSON snapshots are also used for object-level safety checks so
a broken/partial download cannot silently replace a good schema.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "mtproto" / "tl"

API_TL_URL = "https://core.telegram.org/schema"
API_JSON_URL = "https://core.telegram.org/schema/json"
MTPROTO_TL_URL = "https://core.telegram.org/schema/mtproto"
MTPROTO_JSON_URL = "https://core.telegram.org/schema/mtproto-json"

DEFINITION_RE = re.compile(r"^\s*([A-Za-z0-9_.]+)(?:#([0-9a-fA-F]+))?.*\s=\s*[A-Za-z0-9_.<>]+;\s*$")


def normalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalize_json(child) for key, child in value.items()}
    if isinstance(value, list):
        return [normalize_json(child) for child in value]
    return value


def render_json(value: Any) -> str:
    return json.dumps(
        normalize_json(value),
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"


def normalize_tl(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def schema_object_keys(value: Any) -> set[str]:
    if not isinstance(value, dict):
        return set()

    keys: set[str] = set()
    for collection_name in ("constructors", "methods"):
        collection = value.get(collection_name)
        if not isinstance(collection, list):
            continue
        for item in collection:
            if not isinstance(item, dict):
                continue
            identifier = item.get("id")
            name = item.get("predicate") or item.get("method")
            if identifier is None or not name:
                continue
            keys.add(f"{collection_name}:{identifier}:{name}")
    return keys


def validate_schema_json(previous: Any | None, current: Any) -> None:
    if not isinstance(current, dict):
        raise ValueError("TL schema JSON must be an object")

    constructors = current.get("constructors")
    methods = current.get("methods")
    if not isinstance(constructors, list) or not constructors:
        raise ValueError("TL schema JSON has no constructors")
    if not isinstance(methods, list) or not methods:
        raise ValueError("TL schema JSON has no methods")

    for collection_name, collection in (("constructors", constructors), ("methods", methods)):
        for item in collection:
            if not isinstance(item, dict) or item.get("id") is None:
                raise ValueError(f"invalid {collection_name} entry in TL schema JSON")

    if previous is None:
        return

    previous_keys = schema_object_keys(previous)
    current_keys = schema_object_keys(current)
    if not previous_keys:
        return

    removed = previous_keys - current_keys
    ratio = len(removed) / len(previous_keys)
    if ratio > 0.10:
        raise ValueError(
            "TL schema object safety guard triggered: "
            f"{len(removed)}/{len(previous_keys)} objects disappeared ({ratio:.1%})"
        )


def definition_keys(value: str) -> set[str]:
    keys: set[str] = set()
    for line in value.splitlines():
        line = line.strip()
        if not line or line.startswith("//") or line.startswith("---"):
            continue
        match = DEFINITION_RE.match(line)
        if match:
            name, constructor_id = match.groups()
            keys.add(f"{name}#{constructor_id or ''}")
    return keys


def validate_tl_text(previous: str | None, current: str, *, required_markers: tuple[str, ...]) -> None:
    if not current.strip():
        raise ValueError("TL schema response is empty")

    for marker in required_markers:
        if marker not in current:
            raise ValueError(f"TL schema response is missing required marker: {marker}")

    current_keys = definition_keys(current)
    if len(current_keys) < 5:
        raise ValueError("TL schema response contains too few definitions")

    if previous is None:
        return

    previous_keys = definition_keys(previous)
    if not previous_keys:
        return

    removed = previous_keys - current_keys
    ratio = len(removed) / len(previous_keys)
    if ratio > 0.10:
        raise ValueError(
            "TL schema safety guard triggered: "
            f"{len(removed)}/{len(previous_keys)} definitions disappeared ({ratio:.1%})"
        )


def read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def fetch_sources() -> tuple[str, dict[str, Any], str, dict[str, Any]]:
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        follow_redirects=True,
        headers={"User-Agent": "Telegram-Developer-Crawler/0.1"},
    ) as client:
        responses = await asyncio.gather(
            client.get(API_TL_URL),
            client.get(API_JSON_URL),
            client.get(MTPROTO_TL_URL),
            client.get(MTPROTO_JSON_URL),
        )
        for response in responses:
            response.raise_for_status()

        api_tl = normalize_tl(responses[0].text)
        api_json = responses[1].json()
        mtproto_tl = normalize_tl(responses[2].text)
        mtproto_json = responses[3].json()

    return api_tl, api_json, mtproto_tl, mtproto_json


def collect() -> None:
    api_tl, api_json, mtproto_tl, mtproto_json = asyncio.run(fetch_sources())

    api_json_path = DATA_ROOT / "api.json"
    api_tl_path = DATA_ROOT / "api.tl"
    mtproto_json_path = DATA_ROOT / "mtproto.json"
    mtproto_tl_path = DATA_ROOT / "mtproto.tl"

    validate_schema_json(read_json(api_json_path), api_json)
    validate_schema_json(read_json(mtproto_json_path), mtproto_json)

    validate_tl_text(
        read_text(api_tl_path),
        api_tl,
        required_markers=("---functions---",),
    )
    validate_tl_text(
        read_text(mtproto_tl_path),
        mtproto_tl,
        required_markers=("---functions---", "resPQ#"),
    )

    write_text(api_tl_path, api_tl)
    write_text(api_json_path, render_json(api_json))
    write_text(mtproto_tl_path, mtproto_tl)
    write_text(mtproto_json_path, render_json(mtproto_json))

    metadata = {
        "sources": {
            "api_tl": API_TL_URL,
            "api_json": API_JSON_URL,
            "mtproto_tl": MTPROTO_TL_URL,
            "mtproto_json": MTPROTO_JSON_URL,
        },
        "api": {
            "layer": api_json.get("layer"),
            "constructors": len(api_json.get("constructors", [])),
            "methods": len(api_json.get("methods", [])),
            "sha256_tl": sha256_text(api_tl),
            "sha256_json": sha256_text(render_json(api_json)),
        },
        "mtproto": {
            "constructors": len(mtproto_json.get("constructors", [])),
            "methods": len(mtproto_json.get("methods", [])),
            "sha256_tl": sha256_text(mtproto_tl),
            "sha256_json": sha256_text(render_json(mtproto_json)),
        },
        "safety": {
            "max_object_removal_ratio": 0.10,
        },
    }
    write_text(DATA_ROOT / "metadata.json", render_json(metadata))


def main() -> None:
    collect()


if __name__ == "__main__":
    main()
