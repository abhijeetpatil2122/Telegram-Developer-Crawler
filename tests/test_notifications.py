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
    assert "What is happening?" in html
    assert "<table compact striped>" in html
    assert "<blockquote>" in html


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
    html = status_html(35, "📐 Official TL schemas", "Collecting API + MTProto schemas.", 3, 7)
    assert "3/7" in html
    assert "35%" in html


def test_final_uses_expandable_rich_blocks():
    html = final_html("<h3>📦 MTProto</h3><ul><li>Added: <b>2</b></li></ul>", "", "")
    assert "<details open>" in html
    assert "<h3>📦 MTProto</h3>" in html


def test_status_includes_crawl_number_and_eta():
    html = status_html(
        90,
        "🛠️ Android schema extraction",
        "Extracting Stable + Preview schemas.",
        7,
        7,
        "42",
        "~3–4 min",
    )
    assert "#42" in html
    assert "~3–4 min" in html
    assert "90%" in html
