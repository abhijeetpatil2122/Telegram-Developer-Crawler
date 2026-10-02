"""Compact Telegram Rich Message notifications for the developer crawler."""
from __future__ import annotations

import argparse
import html
import json
import re
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


def rich_payload(blocks: list[dict]) -> str:
    """Serialize explicit InputRichMessage blocks."""
    return json.dumps(
        {"blocks": blocks},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _progress_bar(progress: int, width: int = 10) -> str:
    progress = max(0, min(100, progress))
    filled = round(progress / 100 * width)
    return "▰" * filled + "▱" * (width - filled)


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "text": text}


def _heading(text: str, size: int = 4) -> dict:
    return {"type": "heading", "size": size, "text": text}


def _blockquote(text: str) -> dict:
    return {"type": "blockquote", "blocks": [_paragraph(text)]}


def _button(text: str, url: str, style: str = "primary") -> dict:
    return {"text": text, "style": style, "url": url}


def status_blocks(
    progress: int,
    title: str,
    detail: str,
    stage: int | None = None,
    total_stages: int = TOTAL_STAGES,
    crawl_number: str = "",
    eta: str = "",
) -> list[dict]:
    progress = max(0, min(100, progress))
    stage = max(1, min(stage or 1, max(1, total_stages)))
    total_stages = max(1, total_stages)

    header = "⚙️ Telegram Developer Crawler"
    if crawl_number:
        header += f"  •  #{crawl_number}"

    blocks = [
        _heading(header, 4),
        _paragraph(
            f"<b>{progress}%</b>  <code>{_progress_bar(progress)}</code>  "
            f"•  Step <b>{stage}/{total_stages}</b>"
            + (f"  •  ETA <code>{html.escape(eta)}</code>" if eta else "")
        ),
        _heading(title, 5),
        _blockquote(detail),
    ]
    return blocks


def final_blocks(text: str, compare_url: str, commit_url: str) -> list[dict]:
    """Build a compact permanent change post from the classifier's HTML summary."""
    raw = html.unescape(text or "")
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    raw = re.sub(r"</(?:p|li|h[1-6])>", "\n", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", "", raw)
    lines = [html.unescape(x).strip() for x in raw.splitlines() if x.strip()]

    blocks = [
        _heading("📣 Telegram Developer Update", 4),
        _paragraph("New developer-facing changes were detected."),
    ]

    current: list[str] = []
    for line in lines:
        if line.startswith(("📦 ", "📱 ", "🧩 ")):
            if current:
                blocks.append({"type": "list", "items": [
                    {"blocks": [_paragraph(item)]} for item in current
                ]})
                current = []
            blocks.append(_heading(line, 5))
        elif line.startswith((
            "➕ ", "✏️ ", "➖ ", "📄 ", "🏷️ ", "#Android", "#Stable", "#Preview"
        )):
            current.append(line)
        elif line not in {
            "📣 Developer data changed",
            "A new Telegram developer-data snapshot contains meaningful changes.",
        }:
            current.append(line)

    if current:
        blocks.append({"type": "list", "items": [
            {"blocks": [_paragraph(item)]} for item in current
        ]})

    buttons = []
    if compare_url:
        buttons.append(_button("Full Changelog", compare_url, "primary"))
    if commit_url:
        buttons.append(_button("Snapshot Commit", commit_url, "success"))
    buttons.append(
        _button(
            "Data Snapshot",
            "https://github.com/abhijeetpatil2122/Telegram-Developer-Crawler/tree/data",
            "link",
        )
    )
    blocks.append({"type": "buttons", "align": "center", "buttons": buttons})
    return blocks


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
                status_blocks(
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
                final_blocks(args.text, args.compare_url, args.commit_url)
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
                status_blocks(
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
