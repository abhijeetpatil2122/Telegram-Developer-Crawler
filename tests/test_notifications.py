from crawler.notifications import final_html, rich_payload, status_html
import json


def test_rich_payload_uses_html():
    payload = json.loads(rich_payload("<b>Hello</b>"))
    assert payload["html"] == "<b>Hello</b>"


def test_status_is_rich_html():
    html = status_html(80, "📱 Android clients", "Downloading Stable + Public Beta APKs.")
    assert html.startswith("<h2>⚙️ Telegram Developer Crawler</h2>")
    assert "<br/>" not in html
    assert "<h3>📱 Android clients</h3>" in html
    assert "80%" in html


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
