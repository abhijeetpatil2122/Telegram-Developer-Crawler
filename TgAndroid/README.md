# Telegram Android client

Module 5 tracks the official Telegram Android client in two independent channels:

- **Stable** — direct APK from https://telegram.org/dl/android/apk.
- **Public Beta** — direct APK from https://telegram.org/dl/android/apk-public-beta.

## Data branch layout

The data branch is the archive root:

- `TgAndroid/` — Stable/Preview APK metadata and selected resources.
- `TgAndroid/tl/stable/` — Stable `main_api.tl/json` and `e2e.tl/json`.
- `TgAndroid/tl/beta/` — Preview `main_api.tl/json` and `e2e.tl/json`.

There is no `data/` prefix on the data branch.

## Stage 5A

The first stage downloads both APKs independently and records resolved URL, APK size and SHA-256, package name, version name/code, Apktool provenance and selected deterministic resources. APK bytes are temporary and are never committed.

## Stage 5B

JADX extracts `org.telegram.tgnet`. Historical/duplicate Android classes are canonicalized into developer-facing TL definitions. `main_api.tl` merges the official API base with current Android-specific definitions; `e2e.tl` is maintained separately from the official Telegram E2E schema.

Safety checks reject unexpectedly small schemas, duplicate definition keys and excessive historical definition loss.

## Stage 5C and notifications

Stage 5C compares Stable/Preview and every other generated module semantically, classifying additions, changes and deletions. The final notification reports all changed modules. A temporary Rich Message status is edited through the crawl stages and removed after publication.

Generated TL/XML/Markdown artifacts use native comment-style provenance. JSON artifacts remain untouched valid JSON.
