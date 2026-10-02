from crawler.notifications import final_html, rich_payload, status_html
import json


def test_rich_payload_uses_html():
    payload = json.loads(rich_payload("<b>Hello</b>"))
    assert payload["html"] == "<b>Hello</b>"


def test_status_is_rich_html_without_progress_bar():
    html = status_html(
        "📱 Android clients",
        "Downloading Stable + Public Beta APKs.",
        6,
        7,
        "42",
        "~1–2 min",
    )
    assert html.startswith("<h2>⚙️ Telegram Developer Crawler")
    assert "<h3>📱 Android clients</h3>" in html
    assert "Downloading Stable + Public Beta APKs." in html
    assert "Stage <b>6/7</b>" in html
    assert "#42" in html
    assert "~1–2 min" in html
    assert "<blockquote>" in html
    assert "<table" not in html
    assert "▰" not in html
    assert "▱" not in html
    assert "%" not in html


def test_final_contains_rich_buttons():
    html = final_html(
        "<b>Developer data changed</b>",
        "https://github.com/example/compare/a...b",
        "https://github.com/example/commit/b",
    )
    assert '<tg-button-row align="center">' in html
    assert 'type="url"' in html
    assert "Full Changelog" in html
    assert "Snapshot Commit" in html
    assert "Data Snapshot" in html


def test_status_supports_stage_counter():
    html = status_html("📐 Official TL schemas", "Collecting API + MTProto schemas.", 3, 7)
    assert "3/7" in html
    assert "%" not in html


def test_final_uses_expandable_rich_blocks():
    html = final_html("<h3>📦 MTProto</h3><ul><li>Added: <b>2</b></li></ul>", "", "")
    assert '<tg-button-row align="center">' in html
    assert "<h3>📦 MTProto</h3>" in html


def test_status_includes_crawl_number_and_eta():
    html = status_html(
        "🛠️ Android schema extraction",
        "Extracting Stable + Preview schemas.",
        7,
        7,
        "42",
        "~3–4 min",
    )
    assert "#42" in html
    assert "~3–4 min" in html
    assert "%" not in html
