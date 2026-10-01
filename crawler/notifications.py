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
            if not response.is_success:
                print(
                    f"Telegram API HTTP {response.status_code} for {method}: "
                    f"{data.get('description', response.text)}",
                    file=sys.stderr,
                )
                return None
    except httpx.HTTPError as exc:
        print(f"Telegram notification request failed: {exc}", file=sys.stderr)
        return None

    if not data.get("ok"):
        print(f"Telegram notification failed: {data}", file=sys.stderr)
        return None
    return data["result"]


def rich_payload(html_content: str) -> str:
    """Build InputRichMessage JSON using Telegram Rich HTML block syntax."""
    return json.dumps(
        {"html": html_content},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _progress_bar(progress: int) -> str:
    progress = max(0, min(100, progress))
    filled = progress // 10
    return "▰" * filled + "▱" * (10 - filled)


def status_html(
    progress: int,
    title: str,
    detail: str,
    stage: int | None = None,
    total_stages: int = TOTAL_STAGES,
) -> str:
    """Render a compact live status using native Rich block HTML."""
    progress = max(0, min(100, progress))
    stage = stage if stage is not None else 1
    total_stages = max(1, total_stages)
    stage = max(1, min(stage, total_stages))

    stage_label = f"Stage {stage}/{total_stages}"
    bar = _progress_bar(progress)

    return (
        "<h2>⚙️ Telegram Developer Crawler</h2>"
        "<p><b>Live crawl progress</b></p>"
        "<table compact striped>"
        "<tr><td><b>Progress</b></td><td><code>"
        f"{progress}%"
        "</code></td></tr>"
        "<tr><td><b>Stage</b></td><td><code>"
        f"{stage_label}"
        "</code></td></tr>"
        "<tr><td><b>Status</b></td><td><code>"
        f"{html.escape(bar)}"
        "</code></td></tr>"
        "</table>"
        "<hr/>"
        f"<h3>{html.escape(title)}</h3>"
        f"<blockquote>{html.escape(detail)}</blockquote>"
        "<details>"
        "<summary>Backend activity</summary>"
        "<ul>"
        "<li>Collecting official Telegram developer sources</li>"
        "<li>Normalizing and validating generated snapshots</li>"
        "<li>Comparing the new snapshot with the <code>data</code> archive</li>"
        "</ul>"
        "</details>"
        "<footer>Live status • this message updates automatically.</footer>"
    )


def status_fallback_html(progress: int, title: str, detail: str) -> str:
    """Safe legacy Bot API HTML fallback."""
    progress = max(0, min(100, progress))
    bar = _progress_bar(progress)
    return (
        "<b>⚙️ Telegram Developer Crawler</b>\n"
        f"<b>Progress:</b> <code>{progress}%</code> <code>{bar}</code>\n\n"
        f"<b>{html.escape(title)}</b>\n"
        f"{html.escape(detail)}\n\n"
        "<i>Live crawl status • this message updates automatically.</i>"
    )


def final_html(text: str, compare_url: str, commit_url: str) -> str:
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
        "<blockquote expandable>"
        "The crawler found changes in one or more Telegram developer data sources. "
        "Expand this section for the generated 5C classification."
        "</blockquote>"
        "<hr/>"
        "<h3>🔎 Change summary</h3>"
        "<details open>"
        "<summary>Semantic 5C report</summary>"
        f"{content}"
        "</details>"
        '<tg-button-row align="center">'
        + "".join(buttons)
        + "</tg-button-row>"
        "<footer>Generated automatically by Telegram Developer Crawler.</footer>"
    )


def final_fallback_html(text: str, compare_url: str, commit_url: str) -> str:
    """Safe legacy-HTML fallback for a Rich API rejection."""
    plain = html.unescape(text or "").replace("<", "").replace(">", "").strip()
    lines = ["<b>🛠️ Telegram Developer Crawler</b>", "", "<b>Developer data changed</b>"]
    if plain:
        lines += ["", plain]
    if compare_url:
        lines += ["", f'<a href="{html.escape(compare_url, quote=True)}">Full Changelog</a>']
    if commit_url:
        lines += [f'<a href="{html.escape(commit_url, quote=True)}">Commit</a>']
    lines += [
        '<a href="https://github.com/abhijeetpatil2122/Telegram-Developer-Crawler/tree/data">'
        "Data Snapshot</a>"
    ]
    return "\n".join(lines)


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
    parser.add_argument("--compare-url", default="")
    parser.add_argument("--commit-url", default="")
    args = parser.parse_args()

    if args.action == "start":
        progress = args.progress or 5
        title = args.title or "Starting crawl"
        detail = args.detail or "Preparing Telegram developer data collectors."
        result = call(
            "sendRichMessage",
            rich_message=rich_payload(
                status_html(progress, title, detail, args.stage, args.total_stages)
            ),
        )
        if result:
            print(result["message_id"])
            return 0

        fallback = call(
            "sendMessage",
            text=status_fallback_html(progress, title, detail),
            parse_mode="HTML",
            disable_web_page_preview="true",
        )
        if fallback:
            print(fallback["message_id"])
        return 0

    if args.action == "notify":
        if not os.environ.get("TG_BOT_TOKEN"):
            return 0
        rich_result = call(
            "sendRichMessage",
            rich_message=rich_payload(
                final_html(args.text, args.compare_url, args.commit_url)
            ),
        )
        if rich_result is not None:
            return 0

        fallback = call(
            "sendMessage",
            text=final_fallback_html(args.text, args.compare_url, args.commit_url),
            parse_mode="HTML",
            disable_web_page_preview="true",
        )
        return 0 if fallback is not None else 1

    if not args.message_id or not os.environ.get("TG_BOT_TOKEN"):
        return 0

    if args.action == "update":
        progress = args.progress
        title = args.title or "Updating"
        detail = args.detail
        rich_result = call(
            "editMessageText",
            message_id=args.message_id,
            rich_message=rich_payload(
                status_html(progress, title, detail, args.stage, args.total_stages)
            ),
        )
        if rich_result is not None:
            return 0

        fallback = call(
            "editMessageText",
            message_id=args.message_id,
            text=status_fallback_html(progress, title, detail),
            parse_mode="HTML",
            disable_web_page_preview="true",
        )
        return 0 if fallback is not None else 1

    result = call("deleteMessage", message_id=args.message_id)
    return 0 if result is not None else 1


if __name__ == "__main__":
    sys.exit(main())
