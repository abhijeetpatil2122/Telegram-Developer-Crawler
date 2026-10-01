"""Telegram notification controller for crawler progress and final changes."""
from __future__ import annotations
import argparse
import html
import os
import sys
import httpx

API="https://api.telegram.org/bot{}/{}"

def call(method: str, **payload):
    token=os.environ.get("TG_BOT_TOKEN")
    chat_id=os.environ.get("TG_ALERT_CHAT_ID")
    if not token or not chat_id: return None
    try:
        with httpx.Client(timeout=20.0) as client:
            response=client.post(API.format(token,method),data={"chat_id":chat_id,**payload})
    except httpx.HTTPError as exc:
        print(f"Telegram notification request failed: {exc}", file=sys.stderr)
        return None
        response.raise_for_status()
        data=response.json()
    if not data.get("ok"):
        print(f"Telegram notification failed: {data}", file=sys.stderr)
        return None
    return data["result"]

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("start","update","delete","notify"))
    parser.add_argument("--message-id")
    parser.add_argument("--text",default="")
    parser.add_argument("--compare-url",default="")
    parser.add_argument("--commit-url",default="")
    args=parser.parse_args()

    if args.action=="start":
        result=call("sendMessage",text=args.text or "⚙️ Telegram Developer Crawler\n\nStarting crawl…")
        if result: print(result["message_id"])
        return 0
    if args.action=="notify":
        text=args.text or "🛠️ Telegram Developer Crawler\n\nA new developer-data snapshot is available."
        if args.compare_url: text += f"\n\n🔗 Full Changelog: {args.compare_url}"
        if args.commit_url: text += f"\n🧾 Commit / Diff: {args.commit_url}"
        call("sendMessage",text=text,parse_mode="HTML",disable_web_page_preview=False)
        return 0
    if not args.message_id: return 0
    if args.action=="update":
        call("editMessageText",message_id=args.message_id,text=args.text)
    else:
        call("deleteMessage",message_id=args.message_id)
    return 0

if __name__=="__main__":
    sys.exit(main())
