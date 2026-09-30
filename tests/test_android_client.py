from pathlib import Path
import hashlib

import pytest

from crawler.android_client import parse_manifest, render_json, sha256_bytes


def test_render_json_is_deterministic():
    assert render_json({"b": 2, "a": 1}) == '{\n  "a": 1,\n  "b": 2\n}\n'


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


def test_parse_manifest_rejects_missing_version(tmp_path: Path):
    manifest = tmp_path / "AndroidManifest.xml"
    manifest.write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" '
        'package="org.telegram.messenger" />',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing package/version metadata"):
        parse_manifest(manifest)
