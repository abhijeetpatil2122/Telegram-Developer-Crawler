"""Telegram Rich Message notification controller for crawler progress and changes."""
from __future__ import annotations

import argparse
import html
import json
import os
import sys

import httpx

API = "https://api.telegram.org/bot{}/{}"
DEFAULT_CHAT = "@botapinews"


def call(method: str, **payload):
    token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_ALERT_CHAT_ID") or DEFAULT_CHAT
    if not token:
        print("Telegram notification skipped: TG_BOT_TOKEN is not configured.", file=sys.stderr)
        return None
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                API.format(token, method),
                data={"chat_id": chat_id, **payload},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"Telegram notification request failed: {exc}", file=sys.stderr)
        return None

    data = response.json()
    if not data.get("ok"):
        print(f"Telegram notification failed: {data}", file=sys.stderr)
        return None
    return data["result"]


def rich_payload(html_content: str) -> str:
    # Rich HTML is intentionally used here: Telegram maps h*, p, ul/li,
    # hr and tg-button-row/tg-button to native Rich Message blocks.
    return json.dumps(
        {"html": html_content, "skip_entity_detection": False},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def status_html(progress: int, title: str, detail: str) -> str:
    progress = max(0, min(100, progress))
    filled = progress // 10
    bar = "▰" * filled + "▱" * (10 - filled)
    return (
        "<h2>⚙️ Telegram Developer Crawler</h2>"
        "<p><b>Workflow progress</b> "
        f"<code>{progress}%</code></p>"
        f"<p><code>{bar}</code></p>"
        "<hr/>"
        f"<h3>{html.escape(title)}</h3>"
        f"<p>{html.escape(detail)}</p>"
        "<p><i>Live crawl status • this message updates automatically.</i></p>"
    )


def final_html(text: str, compare_url: str, commit_url: str) -> str:
    # 5C produces trusted Rich HTML. Keep it as HTML instead of wrapping it
    # inside a plain paragraph so its headings/lists remain real blocks.
    content = text.strip() or "<p>A new developer-data snapshot is available.</p>"
    buttons = []
    if compare_url:
        buttons.append(
            f'<tg-button type="url" style="primary" url="{html.escape(compare_url, quote=True)}">'
            "Full Changelog</tg-button>"
        )
    if commit_url:
        buttons.append(
            f'<tg-button type="url" style="success" url="{html.escape(commit_url, quote=True)}">'
            "Commit</tg-button>"
        )
    buttons.append(
        '<tg-button type="url" style="link" '
        'url="https://github.com/abhijeetpatil2122/Telegram-Developer-Crawler/tree/data">'
        "Data Snapshot</tg-button>"
    )
    return (
        "<h2>🛠️ Telegram Developer Crawler</h2>"
        "<p><b>Developer data changed</b></p>"
        "<hr/>"
        f"{content}"
        "<hr/>"
        "<p><i>Generated automatically by Telegram Developer Crawler.</i></p>"
        "<tg-button-row>"
        + "".join(buttons)
        + "</tg-button-row>"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "update", "delete", "notify"))
    parser.add_argument("--message-id")
    parser.add_argument("--text", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--detail", default="")
    parser.add_argument("--progress", type=int, default=0)
    parser.add_argument("--compare-url", default="")
    parser.add_argument("--commit-url", default="")
    args = parser.parse_args()

    if args.action == "start":
        html_content = status_html(
            args.progress or 5,
            args.title or "Starting crawl",
            args.detail or "Preparing Telegram developer data collectors.",
        )
        result = call("sendRichMessage", rich_message=rich_payload(html_content))
        if result:
            print(result["message_id"])
        return 0

    if args.action == "notify":
        if not os.environ.get("TG_BOT_TOKEN"):
            return 0
        result = call(
            "sendRichMessage",
            rich_message=rich_payload(
                final_html(args.text, args.compare_url, args.commit_url)
            ),
        )
        return 0 if result is not None else 1

    if not args.message_id or not os.environ.get("TG_BOT_TOKEN"):
        return 0

    if args.action == "update":
        html_content = status_html(args.progress, args.title, args.detail)
        result = call(
            "editMessageText",
            message_id=args.message_id,
            rich_message=rich_payload(html_content),
        )
        return 0 if result is not None else 1

    result = call("deleteMessage", message_id=args.message_id)
    return 0 if result is not None else 1


if __name__ == "__main__":
    sys.exit(main())
