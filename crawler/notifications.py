"""Telegram Rich Message notification controller for crawler progress and changes."""
from __future__ import annotations

import argparse
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


def rich_payload(html: str) -> str:
    return json.dumps(
        {"html": html, "skip_entity_detection": False},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def status_html(text: str) -> str:
    return f"<b>⚙️ Telegram Developer Crawler</b><br/><br/>{text}"


def final_html(text: str, compare_url: str, commit_url: str) -> str:
    html = text or "<b>A new developer-data snapshot is available.</b>"
    buttons = []
    if compare_url:
        buttons.append(
            f'<tg-button type="url" style="primary" url="{compare_url}">Full Changelog</tg-button>'
        )
    if commit_url:
        buttons.append(
            f'<tg-button type="url" style="success" url="{commit_url}">Commit</tg-button>'
        )
    buttons.append(
        '<tg-button type="url" style="link" url="https://github.com/abhijeetpatil2122/Telegram-Developer-Crawler/tree/data">Data Snapshot</tg-button>'
    )
    return html + "<br/><br/><tg-button-row>" + "".join(buttons) + "</tg-button-row>"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "update", "delete", "notify"))
    parser.add_argument("--message-id")
    parser.add_argument("--text", default="")
    parser.add_argument("--compare-url", default="")
    parser.add_argument("--commit-url", default="")
    args = parser.parse_args()

    if args.action == "start":
        html = status_html(
            args.text
            or "🚀 <b>Starting crawl…</b><br/>Preparing Telegram developer data collectors."
        )
        result = call("sendRichMessage", rich_message=rich_payload(html))
        if result:
            print(result["message_id"])
        return 0

    if args.action == "notify":
        html = final_html(args.text, args.compare_url, args.commit_url)
        result = call("sendRichMessage", rich_message=rich_payload(html))
        return 0 if result is not None else 1

    if not args.message_id:
        return 0

    if args.action == "update":
        html = status_html(args.text)
        result = call(
            "editMessageText",
            message_id=args.message_id,
            rich_message=rich_payload(html),
        )
        return 0 if result is not None else 1

    result = call("deleteMessage", message_id=args.message_id)
    return 0 if result is not None else 1


if __name__ == "__main__":
    sys.exit(main())
