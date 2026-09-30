import datetime as dt
from types import SimpleNamespace

from crawler.mtproto_config import json_safe, normalize_app_config, normalize_config, normalize_premium_promo


def test_json_safe_serializes_datetime_values():
    value = {"created": dt.datetime(2026, 9, 30, 12, 34, 56)}
    assert json_safe(value) == {"created": "2026-09-30T12:34:56"}


def test_config_normalization_removes_volatile_fields():
    value = SimpleNamespace(
        to_dict=lambda: {
            "date": 123,
            "expires": 456,
            "dc_options": [{"id": 1}],
            "autologin_token": "secret",
            "test_mode": False,
        }
    )
    result = normalize_config(value)
    assert result["date"] == 0
    assert result["expires"] == 0
    assert result["dc_options"] == []
    assert result["autologin_token"] is None
    assert result["test_mode"] is False


def test_app_config_normalization_removes_volatile_fields():
    value = SimpleNamespace(
        to_dict=lambda: {
            "hash": 123,
            "ton_usd_rate": 123,
            "test": "stable",
        }
    )
    assert normalize_app_config(value) == {"hash": 0, "test": "stable"}


def test_premium_promo_normalization_removes_personal_and_volatile_fields():
    value = SimpleNamespace(
        to_dict=lambda: {
            "users": [{"id": 123}],
            "status_text": "real",
            "status_entities": [{"type": "bold"}],
            "period_options": [{"months": 12}],
            "videos": [],
        }
    )
    assert normalize_premium_promo(value) == {
        "users": [],
        "status_text": "crawler",
        "status_entities": [],
        "period_options": [],
        "videos": [],
    }


def test_default_test_dc_endpoints_use_telethon_compatible_port():
    from crawler.mtproto_config import DEFAULT_TEST_DC_ENDPOINTS

    assert {port for _, port in DEFAULT_TEST_DC_ENDPOINTS.values()} == {80}


def test_test_dc_endpoint_override(monkeypatch):
    from crawler.mtproto_config import load_test_endpoints

    monkeypatch.setenv(
        "TDC_TEST_DC_ENDPOINTS",
        '{"1-test":["1.1.1.1",443],"2-test":["2.2.2.2",80]}',
    )
    endpoints = load_test_endpoints()
    assert endpoints["1-test"] == ("1.1.1.1", 443)
    assert endpoints["2-test"] == ("2.2.2.2", 80)
    assert endpoints["3-test"] == ("149.154.175.117", 80)
