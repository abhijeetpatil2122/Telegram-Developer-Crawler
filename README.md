# Telegram Developer Crawler

Developer-focused crawler for meaningful changes across Telegram's official developer surfaces.

## Architecture

- **main** — crawler code, source manifests, normalization, validation, tests and workflows.
- **data** — generated snapshots and Git history.
- **Git history** — historical source of truth for exact snapshot changes.
- **Telegram** — temporary Rich Message crawl progress and final Rich Message change notifications.
- **No database or Redis** is required.

## Current collectors

1. MTProto configuration — production/test DC configuration and related global datasets.
2. MTProto/TL schemas — official Telegram API and MTProto schemas.
3. TDLib schema — official `td_api.tl` and structured definition index.
4. Telegram Desktop schemas — official Desktop API and MTProto schemas.
5. Telegram Android — Stable/Public Beta APK metadata/resources plus canonical main API and E2E extraction.
6. Change classification — semantic additions/changes/deletions across every generated module.
7. Notifications — Rich Message crawl status plus final Rich Message changelog.

## Data branch layout

The `data` branch is an archive root, not a nested `data/` directory:

`mtproto/configs/` · `mtproto/tl/` · `tdlib/tl/` · `tdesktop/tl/` · `TgAndroid/tl/`

## Provenance

Generated source artifacts use comment-safe provenance:

- TL: native `//` header with Copyright (C) 2026 Abhijeet Patil.
- XML: native XML comment.
- Markdown: native HTML comment.
- JSON: untouched valid JSON; no synthetic credit property.
- Credited diff: each unified-diff hunk receives `// Telegram Developer Crawler — Copyright (C) 2026 Abhijeet Patil`.

The credited diff is an attribution artifact and never modifies the extracted source files.

## Notification lifecycle

The crawler uses one editable Telegram Rich Message for live crawl status. It is updated through the collection stages and removed after publication.

Stage 5C separately classifies the generated snapshot into semantic additions, changes and deletions. Snapshot-only noise does not produce a final channel alert. The notification comparison ignores known volatile/generated metadata such as Android APK/TL hashes, CDN resolution URLs, and MTProto runtime date/expires fields while keeping those values intact in the data archive.

This separation is intentional: the data branch records the complete crawl; the Telegram channel reports developer-meaningful changes. Final alerts include the Rich Message changelog, GitHub compare/commit buttons, and module-specific Android version/build/layer information when applicable.

## Android output

For each channel:

- `main_api.tl/json` — developer-facing current main API schema.
- `e2e.tl/json` — separate official Telegram E2E schema.
- `metadata.json` — APK/version/build/package provenance.
- `resources/` — selected deterministic Android resources.

See `docs/modules/android/README.md` for details.
