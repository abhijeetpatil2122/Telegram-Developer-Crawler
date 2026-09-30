"""Collect the official TDLib API schema from upstream TDLib.

Canonical source:
- https://github.com/tdlib/td/blob/master/td/generate/scheme/td_api.tl

The raw TL file is preserved exactly after line-ending normalization. A
deterministic structured index is generated from top-level TL definitions so
future diff classification can identify added/removed/modified classes and
functions without reparsing the whole file.
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
DATA_ROOT = ROOT / "data" / "tdlib" / "schema"

TDLIB_TL_URL = "https://raw.githubusercontent.com/tdlib/td/master/td/generate/scheme/td_api.tl"
TDLIB_COMMIT_URL = "https://api.github.com/repos/tdlib/td/commits/master"

DEFINITION_RE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9_.]*)"
    r"(?:#(?P<id>[0-9a-fA-F]+))?"
    r"(?P<body>.*?)"
    r"\s=\s(?P<result>[^;]+);\s*$"
)


def normalize_tl(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def render_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def parse_definitions(value: str) -> list[dict[str, Any]]:
    definitions: list[dict[str, Any]] = []
    section = "constructors"

    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("---functions---"):
            section = "functions"
            continue

        match = DEFINITION_RE.match(line)
        if not match:
            continue

        body = match.group("body").strip()
        definitions.append(
            {
                "kind": section,
                "name": match.group("name"),
                "id": match.group("id"),
                "params": body,
                "result": match.group("result").strip(),
                "source": line,
            }
        )

    return definitions


def definition_keys(definitions: list[dict[str, Any]]) -> set[str]:
    return {
        f"{item['kind']}:{item['name']}"
        for item in definitions
        if item.get("name")
    }


def validate_schema(previous: list[dict[str, Any]] | None, current: list[dict[str, Any]]) -> None:
    constructors = [item for item in current if item["kind"] == "constructors"]
    functions = [item for item in current if item["kind"] == "functions"]

    if len(constructors) < 100:
        raise ValueError(f"TDLib schema contains too few constructors: {len(constructors)}")
    if len(functions) < 100:
        raise ValueError(f"TDLib schema contains too few functions: {len(functions)}")

    names = [f"{item['kind']}:{item['name']}" for item in current]
    if len(names) != len(set(names)):
        raise ValueError("TDLib schema contains duplicate definition names")

    if previous is None:
        return

    old_keys = definition_keys(previous)
    new_keys = definition_keys(current)
    if not old_keys:
        return

    removed = old_keys - new_keys
    ratio = len(removed) / len(old_keys)
    if ratio > 0.10:
        raise ValueError(
            "TDLib schema safety guard triggered: "
            f"{len(removed)}/{len(old_keys)} definitions disappeared ({ratio:.1%})"
        )


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def fetch_sources() -> tuple[str, dict[str, Any]]:
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        follow_redirects=True,
        headers={"User-Agent": "Telegram-Developer-Crawler/0.1"},
    ) as client:
        schema_response, commit_response = await asyncio.gather(
            client.get(TDLIB_TL_URL),
            client.get(TDLIB_COMMIT_URL),
        )
        schema_response.raise_for_status()
        commit_response.raise_for_status()
        return schema_response.text, commit_response.json()


def collect() -> None:
    source, commit = asyncio.run(fetch_sources())
    source = normalize_tl(source)
    definitions = parse_definitions(source)

    previous_source = read_text(DATA_ROOT / "td_api.tl")
    previous_json = read_json(DATA_ROOT / "td_api.json")
    previous_definitions = (
        previous_json.get("definitions")
        if isinstance(previous_json, dict)
        else None
    )

    validate_schema(previous_definitions, definitions)

    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    (DATA_ROOT / "td_api.tl").write_text(source, encoding="utf-8")

    structured = {
        "source": TDLIB_TL_URL,
        "definitions": definitions,
    }
    structured_text = render_json(structured)
    (DATA_ROOT / "td_api.json").write_text(structured_text, encoding="utf-8")

    metadata = {
        "source": TDLIB_TL_URL,
        "source_repository": "https://github.com/tdlib/td",
        "source_path": "td/generate/scheme/td_api.tl",
        "upstream": {
            "branch": "master",
            "commit": commit.get("sha"),
            "commit_url": commit.get("html_url"),
            "message": (commit.get("commit") or {}).get("message", "").splitlines()[0],
        },
        "counts": {
            "constructors": sum(item["kind"] == "constructors" for item in definitions),
            "functions": sum(item["kind"] == "functions" for item in definitions),
            "total": len(definitions),
        },
        "sha256": {
            "tl": sha256_text(source),
            "json": sha256_text(structured_text),
        },
        "safety": {
            "max_definition_removal_ratio": 0.10,
        },
    }
    (DATA_ROOT / "metadata.json").write_text(render_json(metadata), encoding="utf-8")


def main() -> None:
    collect()


if __name__ == "__main__":
    main()
