from crawler.notifications import final_html, rich_payload, status_html
import json


def test_rich_payload_uses_html():
    payload = json.loads(rich_payload("<b>Hello</b>"))
    assert payload["html"] == "<b>Hello</b>"
    assert payload["skip_entity_detection"] is False


def test_status_is_rich_html():
    html = status_html("📱 <b>Downloading Android</b>")
    assert html.startswith("<b>⚙️ Telegram Developer Crawler</b>")
    assert "<br/>" not in html
    assert "<b>Downloading Android</b>" in html


def test_final_contains_rich_buttons():
    html = final_html(
        "<b>Developer data changed</b>",
        "https://github.com/example/compare/a...b",
        "https://github.com/example/commit/b",
    )
    assert "<tg-button-row>" in html
    assert 'type="url"' in html
    assert "Full Changelog" in html
    assert "Commit" in html
    assert "Data Snapshot" in html
