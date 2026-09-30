from types import SimpleNamespace

from crawler.mtproto_config import normalize_app_config, normalize_config


def test_config_normalization_removes_volatile_fields():
    value = SimpleNamespace(
        to_dict=lambda: {
            "date": 123,
            "expires": 456,
            "dc_options": [{"id": 1}],
            "test_mode": False,
        }
    )
    result = normalize_config(value)
    assert result["date"] == 0
    assert result["expires"] == 0
    assert result["dc_options"] == []
    assert result["test_mode"] is False


def test_app_config_normalization_removes_exchange_rate():
    value = SimpleNamespace(
        to_dict=lambda: {
            "ton_usd_rate": 123,
            "test": "stable",
        }
    )
    assert normalize_app_config(value) == {"test": "stable"}
