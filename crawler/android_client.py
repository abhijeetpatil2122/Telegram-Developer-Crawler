"""Collect Telegram Android stable and public-beta APK resources.

Module 5A deliberately stops at APK/resource evidence. TL extraction is added
as a separate stage so a decompiler failure can never publish a bad schema.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import httpx

from crawler.credits import add_json_credit, with_tl_credit

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "android"
APKTOOL_URL = os.environ.get(
    "ANDROID_APKTOOL_URL",
    "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.12.1.jar",
)
SOURCES = {
    "stable": "https://telegram.org/dl/android/apk",
    "beta": "https://telegram.org/dl/android/apk-public-beta",
}
EXPECTED_PACKAGES = {
    "stable": "org.telegram.messenger.web",
    "beta": "org.telegram.messenger.beta",
}
ANDROID_NS = "http://schemas.android.com/apk/res/android"
USER_AGENT = "Telegram-Developer-Crawler/0.1"
RETRYABLE_HTTPX_ERRORS = (httpx.ProtocolError, httpx.TimeoutException, httpx.NetworkError)


def render_json(value: Any) -> str:
    return json.dumps(add_json_credit(value) if isinstance(value, dict) else value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_apktool_version_info(apktool_yml: Path) -> tuple[str | None, int | None]:
    text = apktool_yml.read_text(encoding="utf-8")
    name_match = re.search(r"(?m)^\s*versionName:\s*['\"]?([^'\"\n]+)", text)
    code_match = re.search(r"(?m)^\s*versionCode:\s*['\"]?([0-9]+)", text)
    version_name = name_match.group(1).strip() if name_match else None
    version_code = int(code_match.group(1)) if code_match else None
    return version_name, version_code


def parse_manifest(
    manifest: Path,
    apktool_yml: Path | None = None,
    expected_package: str | None = None,
) -> dict[str, Any]:
    root = ET.parse(manifest).getroot()
    package = root.attrib.get("package")
    version_name = root.attrib.get(f"{{{ANDROID_NS}}}versionName")
    version_code = root.attrib.get(f"{{{ANDROID_NS}}}versionCode")

    if apktool_yml and apktool_yml.exists():
        yml_name, yml_code = parse_apktool_version_info(apktool_yml)
        version_name = version_name or yml_name
        version_code = version_code or (str(yml_code) if yml_code is not None else None)

    package = package or expected_package
    if not package or not version_name or not version_code:
        raise ValueError("decoded Android metadata is missing package/version metadata")

    try:
        code = int(version_code, 0)
    except ValueError as exc:
        raise ValueError(f"invalid Android versionCode: {version_code}") from exc
    if code <= 0:
        raise ValueError(f"Android versionCode must be positive: {code}")
    return {
        "package": package,
        "version_name": version_name,
        "version_code": code,
    }


def validate_resources(decoded_root: Path) -> None:
    required = [
        decoded_root / "AndroidManifest.xml",
        decoded_root / "apktool.yml",
        decoded_root / "res" / "values" / "strings.xml",
        decoded_root / "res" / "values" / "public.xml",
    ]
    missing = [str(path.relative_to(decoded_root)) for path in required if not path.exists()]
    if missing:
        raise ValueError(f"apktool output is missing required Android resources: {', '.join(missing)}")


def run_apktool(apktool_jar: Path, apk_path: Path, output_dir: Path) -> None:
    process = subprocess.run(
        ["java", "-jar", str(apktool_jar), "d", "-s", "-f", str(apk_path), "-o", str(output_dir)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=600,
        check=False,
    )
    if process.returncode != 0:
        tail = process.stdout[-4000:]
        raise RuntimeError(f"apktool failed with exit code {process.returncode}:\n{tail}")


async def download(
    client: httpx.AsyncClient,
    url: str,
    destination: Path,
    *,
    attempts: int = 5,
) -> tuple[str, bytes]:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        cache_buster = uuid.uuid4().hex
        try:
            async with client.stream(
                "GET",
                url,
                params={"tdcNoCache": cache_buster},
                follow_redirects=True,
            ) as response:
                response.raise_for_status()
                final_url = str(response.url).split("?")[0]
                expected = response.headers.get("content-length")
                chunks: list[bytes] = []
                async for chunk in response.aiter_bytes():
                    chunks.append(chunk)
                content = b"".join(chunks)

            if expected and expected.isdigit() and len(content) != int(expected):
                raise httpx.RemoteProtocolError(
                    f"incomplete body: received {len(content)} bytes, expected {expected}"
                )
            if len(content) < 1024 * 1024:
                raise ValueError(f"downloaded artifact is suspiciously small: {len(content)} bytes")
            if not content.startswith(b"PK"):
                raise ValueError("downloaded Android artifact is not a ZIP/APK")
            destination.write_bytes(content)
            return final_url, content
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code < 500:
                raise
            last_error = exc
            if attempt == attempts:
                raise
            await asyncio.sleep(min(2 ** (attempt - 1), 8))
        except RETRYABLE_HTTPX_ERRORS as exc:
            last_error = exc
            if attempt == attempts:
                raise
            await asyncio.sleep(min(2 ** (attempt - 1), 8))
        except ValueError:
            raise
    raise RuntimeError(f"download failed: {last_error}")


async def collect_one(
    client: httpx.AsyncClient,
    apktool_jar: Path,
    channel: str,
    source_url: str,
    work_root: Path,
) -> dict[str, Any]:
    apk_path = work_root / f"{channel}.apk"
    decoded = work_root / f"{channel}-decoded"
    final_url, apk = await download(client, source_url, apk_path)
    run_apktool(apktool_jar, apk_path, decoded)
    validate_resources(decoded)
    manifest = parse_manifest(
        decoded / "AndroidManifest.xml",
        decoded / "apktool.yml",
        EXPECTED_PACKAGES[channel],
    )

    output = DATA_ROOT / channel
    output.mkdir(parents=True, exist_ok=True)
    resources = output / "resources"
    if resources.exists():
        shutil.rmtree(resources)
    shutil.copytree(decoded / "res" / "values", resources)
    for path in resources.iterdir():
        if path.name not in {"strings.xml", "public.xml"}:
            path.unlink()

    metadata = {
        "channel": channel,
        "source_url": source_url,
        "resolved_url": final_url,
        "artifact": {
            "filename": apk_path.name,
            "size": len(apk),
            "sha256": sha256_bytes(apk),
        },
        "android": manifest,
        "extractor": {
            "tool": "apktool",
            "mode": "-s",
            "apktool_url": APKTOOL_URL,
        },
        "scope": [
            "AndroidManifest.xml metadata",
            "res/values/strings.xml",
            "res/values/public.xml",
        ],
    }
    (output / "metadata.json").write_text(render_json(metadata), encoding="utf-8")
    return metadata


async def collect_async() -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tdc-android-") as temp:
        work_root = Path(temp)
        apktool_jar = work_root / "apktool.jar"
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=30.0),
            headers={"User-Agent": USER_AGENT},
        ) as client:
            await download(client, APKTOOL_URL, apktool_jar)
            results = await asyncio.gather(
                *(
                    collect_one(client, apktool_jar, channel, url, work_root)
                    for channel, url in SOURCES.items()
                )
            )
    combined = {
        "sources": SOURCES,
        "channels": {
            item["channel"]: {
                "version_name": item["android"]["version_name"],
                "version_code": item["android"]["version_code"],
                "package": item["android"]["package"],
                "sha256": item["artifact"]["sha256"],
                "metadata": f"{item['channel']}/metadata.json",
                "resources": f"{item['channel']}/resources/",
            }
            for item in results
        },
        "stage": "5A",
    }
    (DATA_ROOT / "metadata.json").write_text(render_json(combined), encoding="utf-8")


def collect() -> None:
    asyncio.run(collect_async())


if __name__ == "__main__":
    collect()
