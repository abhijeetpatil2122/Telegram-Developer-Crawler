"""Telegram Rich Message notifications for the developer crawler."""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys

import httpx

API = "https://api.telegram.org/bot{}/{}"
DEFAULT_CHAT = "@botapinews"
TOTAL_STAGES = 7


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
            try:
                data = response.json()
            except ValueError:
                data = {"ok": False, "description": response.text}
    except httpx.HTTPError as exc:
        print(f"Telegram notification request failed: {exc}", file=sys.stderr)
        return None

    if not response.is_success or not data.get("ok"):
        print(
            f"Telegram API failed for {method}: "
            f"{data.get('description', response.text)}",
            file=sys.stderr,
        )
        return None
    return data["result"]


def rich_payload(html_text: str) -> str:
    """Serialize InputRichMessage using Telegram's native Rich HTML mode."""
    return json.dumps(
        {"html": html_text},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def status_html(
    progress: int,
    title: str,
    detail: str,
    stage: int | None = None,
    total_stages: int = TOTAL_STAGES,
    crawl_number: str = "",
    eta: str = "",
) -> str:
    progress = max(0, min(100, progress))
    total_stages = max(1, total_stages)
    stage = max(1, min(stage or 1, total_stages))
    crawl = f"  •  #{html.escape(str(crawl_number))}" if crawl_number else ""
    eta_html = f"  •  ETA <code>{html.escape(eta)}</code>" if eta else ""

    return (
        "<h2>⚙️ Telegram Developer Crawler"
        f"{crawl}</h2>"
        "<table compact striped>"
        "<tr><th>Task</th><th>Progress</th></tr>"
        f"<tr><td>{html.escape(title)}</td>"
        f"<td><b>{progress}%</b><br/>"
        f"Step <b>{stage}/{total_stages}</b>{eta_html}</td></tr>"
        "</table>"
        "<blockquote>"
        "<b>Current step</b><br/>"
        f"{html.escape(detail)}"
        "</blockquote>"
    )


def final_html(text: str, compare_url: str, commit_url: str) -> str:
    """Convert the classifier's HTML summary into a native Rich HTML post."""
    raw = html.unescape(text or "")
    raw = re.sub(r"<hr\s*/?>", "", raw, flags=re.I)
    raw = re.sub(r"</?(?:p|ul|li)>", lambda m: m.group(0), raw, flags=re.I)

    # The classifier already emits safe, intentionally formatted HTML. Strip
    # only tags which are not part of the Rich HTML vocabulary we use below.
    raw = re.sub(r"<h[1-6]>", "<h3>", raw, flags=re.I)
    raw = re.sub(r"</h[1-6]>", "</h3>", raw, flags=re.I)

    buttons = []
    if compare_url:
        buttons.append(
            f'<tg-button type="url" style="primary" url="{html.escape(compare_url, quote=True)}">Full Changelog</tg-button>'
        )
    if commit_url:
        buttons.append(
            f'<tg-button type="url" style="success" url="{html.escape(commit_url, quote=True)}">Snapshot Commit</tg-button>'
        )
    buttons.append(
        '<tg-button type="url" style="link" url="https://github.com/abhijeetpatil2122/Telegram-Developer-Crawler/tree/data">Data Snapshot</tg-button>'
    )

    return (
        "<h2>📣 Telegram Developer Update</h2>"
        "<p>New developer-facing changes were detected.</p>"
        "<details open><summary>Change summary</summary>"
        f"{raw}"
        "</details>"
        '<tg-button-row align="center">'
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
    parser.add_argument("--stage", type=int)
    parser.add_argument("--total-stages", type=int, default=TOTAL_STAGES)
    parser.add_argument("--crawl-number", default=os.environ.get("GITHUB_RUN_NUMBER", ""))
    parser.add_argument("--eta", default="")
    parser.add_argument("--compare-url", default="")
    parser.add_argument("--commit-url", default="")
    args = parser.parse_args()

    if args.action == "start":
        result = call(
            "sendRichMessage",
            rich_message=rich_payload(
                status_html(
                    args.progress or 5,
                    args.title or "🚀 Starting crawl",
                    args.detail or "Preparing Telegram developer data collectors.",
                    args.stage,
                    args.total_stages,
                    args.crawl_number,
                    args.eta,
                )
            ),
        )
        if result:
            print(result["message_id"])
        return 0

    if args.action == "notify":
        result = call(
            "sendRichMessage",
            rich_message=rich_payload(
                final_html(args.text, args.compare_url, args.commit_url)
            ),
        )
        return 0 if result is not None else 0

    if not args.message_id or not os.environ.get("TG_BOT_TOKEN"):
        return 0

    if args.action == "update":
        result = call(
            "editMessageText",
            message_id=args.message_id,
            rich_message=rich_payload(
                status_html(
                    args.progress,
                    args.title or "Updating",
                    args.detail,
                    args.stage,
                    args.total_stages,
                    args.crawl_number,
                    args.eta,
                )
            ),
        )
        return 0 if result is not None else 0

    result = call("deleteMessage", message_id=args.message_id)
    return 0 if result is not None else 0


if __name__ == "__main__":
    sys.exit(main())
