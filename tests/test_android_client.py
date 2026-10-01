from pathlib import Path
import hashlib

import pytest

from crawler.android_client import parse_apktool_version_info, parse_manifest, render_json, sha256_bytes


def test_render_json_is_deterministic():
    assert render_json({"b": 2, "a": 1}) == '{\n  "_crawler": {\n    "copyright": "Copyright (C) 2026 Abhijeet Patil",\n    "generated_by": "Telegram Developer Crawler"\n  },\n  "a": 1,\n  "b": 2\n}\n'


def test_sha256_is_stable():
    assert sha256_bytes(b"telegram") == hashlib.sha256(b"telegram").hexdigest()


def test_parse_manifest(tmp_path: Path):
    manifest = tmp_path / "AndroidManifest.xml"
    manifest.write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" '
        'package="org.telegram.messenger" android:versionName="12.10.4" '
        'android:versionCode="7094" />',
        encoding="utf-8",
    )
    assert parse_manifest(manifest) == {
        "package": "org.telegram.messenger",
        "version_name": "12.10.4",
        "version_code": 7094,
    }


def test_parse_manifest_falls_back_to_apktool_yml(tmp_path: Path):
    manifest = tmp_path / "AndroidManifest.xml"
    manifest.write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" />',
        encoding="utf-8",
    )
    yml = tmp_path / "apktool.yml"
    yml.write_text(
        "versionInfo:\n"
        "  versionCode: '7094'\n"
        "  versionName: 12.10.4\n",
        encoding="utf-8",
    )
    assert parse_manifest(
        manifest, yml, "org.telegram.messenger.beta"
    ) == {
        "package": "org.telegram.messenger.beta",
        "version_name": "12.10.4",
        "version_code": 7094,
    }


def test_parse_apktool_version_info(tmp_path: Path):
    yml = tmp_path / "apktool.yml"
    yml.write_text(
        "versionInfo:\n"
        "  versionCode: '7094'\n"
        "  versionName: 12.10.4\n",
        encoding="utf-8",
    )
    assert parse_apktool_version_info(yml) == ("12.10.4", 7094)


def test_parse_manifest_rejects_missing_version(tmp_path: Path):
    manifest = tmp_path / "AndroidManifest.xml"
    manifest.write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" '
        'package="org.telegram.messenger" />',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing package/version metadata"):
        parse_manifest(manifest)
