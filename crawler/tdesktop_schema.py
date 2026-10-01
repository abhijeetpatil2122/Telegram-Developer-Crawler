"""Collect official Telegram Desktop TL schemas."""
from __future__ import annotations
import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import Any
import httpx

from crawler.credits import add_json_credit, with_tl_credit

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "tdesktop" / "schema"
BASE = "https://raw.githubusercontent.com/telegramdesktop/tdesktop/dev/Telegram/SourceFiles/mtproto/scheme"
COMMIT_URL = "https://api.github.com/repos/telegramdesktop/tdesktop/commits/dev"
SOURCES = {"api": f"{BASE}/api.tl", "mtproto": f"{BASE}/mtproto.tl"}

DEFINITION_RE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9_.]*)(?:#(?P<id>[0-9a-fA-F]+))?"
    r"(?P<body>.*?)\s=\s(?P<result>[^;]+);\s*$"
)

def normalize_tl(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"

def render_json(value: Any) -> str:
    return json.dumps(add_json_credit(value) if isinstance(value, dict) else value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"

def parse_definitions(value: str) -> list[dict[str, Any]]:
    result, section = [], "constructors"
    for raw in value.splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("---functions---"):
            section = "functions"
            continue
        if line.startswith("---types---"):
            section = "constructors"
            continue
        match = DEFINITION_RE.match(line)
        if match:
            result.append({
                "kind": section,
                "name": match.group("name"),
                "id": match.group("id"),
                "params": match.group("body").strip(),
                "result": match.group("result").strip(),
                "source": line,
            })
    return result

def definition_keys(items: list[dict[str, Any]]) -> set[str]:
    return {f"{x['kind']}:{x['name']}" for x in items if x.get("name")}

def validate_schema(previous, current, label: str) -> None:
    constructors = [x for x in current if x["kind"] == "constructors"]
    functions = [x for x in current if x["kind"] == "functions"]
    minimums = {"api": (500, 200), "mtproto": (20, 5)}
    min_c, min_f = minimums[label]
    if len(constructors) < min_c:
        raise ValueError(f"Telegram Desktop {label}.tl contains too few constructors: {len(constructors)}")
    if len(functions) < min_f:
        raise ValueError(f"Telegram Desktop {label}.tl contains too few functions: {len(functions)}")
    keys = [f"{x['kind']}:{x['name']}" for x in current]
    if len(keys) != len(set(keys)):
        raise ValueError(f"Telegram Desktop {label}.tl contains duplicate definition names")
    if previous is None:
        return
    old, new = definition_keys(previous), definition_keys(current)
    if not old:
        return
    removed = old - new
    ratio = len(removed) / len(old)
    if ratio > 0.10:
        raise ValueError(f"Telegram Desktop {label}.tl safety guard triggered: {len(removed)}/{len(old)} definitions disappeared ({ratio:.1%})")

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

async def fetch_sources():
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), follow_redirects=True, headers={"User-Agent": "Telegram-Developer-Crawler/0.1"}) as client:
        responses = await asyncio.gather(*(client.get(url) for url in SOURCES.values()), client.get(COMMIT_URL))
        for response in responses:
            response.raise_for_status()
        names = list(SOURCES)
        return {name: normalize_tl(responses[i].text) for i, name in enumerate(names)}, responses[-1].json()

def collect() -> None:
    sources, commit = asyncio.run(fetch_sources())
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    for label, source in sources.items():
        definitions = parse_definitions(source)
        previous_json = read_json(DATA_ROOT / f"{label}.json")
        previous = previous_json.get("definitions") if isinstance(previous_json, dict) else None
        validate_schema(previous, definitions, label)
        (DATA_ROOT / f"{label}.tl").write_text(with_tl_credit(source), encoding="utf-8")
        structured = {"source": SOURCES[label], "definitions": definitions}
        structured_text = render_json(structured)
        (DATA_ROOT / f"{label}.json").write_text(structured_text, encoding="utf-8")
        metadata = {
            "source": SOURCES[label],
            "source_repository": "https://github.com/telegramdesktop/tdesktop",
            "source_path": f"Telegram/SourceFiles/mtproto/scheme/{label}.tl",
            "upstream": {
                "branch": "dev",
                "commit": commit.get("sha"),
                "commit_url": commit.get("html_url"),
                "message": (commit.get("commit") or {}).get("message", "").splitlines()[0],
            },
            "counts": {
                "constructors": sum(x["kind"] == "constructors" for x in definitions),
                "functions": sum(x["kind"] == "functions" for x in definitions),
                "total": len(definitions),
            },
            "sha256": {"tl": sha256_text(with_tl_credit(source)), "json": sha256_text(structured_text)},
            "safety": {"max_definition_removal_ratio": 0.10},
        }
        (DATA_ROOT / f"{label}-metadata.json").write_text(render_json(metadata), encoding="utf-8")
    combined = {
        "source_repository": "https://github.com/telegramdesktop/tdesktop",
        "branch": "dev",
        "commit": commit.get("sha"),
        "commit_url": commit.get("html_url"),
        "schemas": {label: {"tl": f"{label}.tl", "json": f"{label}.json", "metadata": f"{label}-metadata.json"} for label in SOURCES},
    }
    (DATA_ROOT / "metadata.json").write_text(render_json(combined), encoding="utf-8")

if __name__ == "__main__":
    collect()
