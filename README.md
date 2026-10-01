# Telegram Developer Crawler — data archive

This branch is the generated Telegram developer snapshot archive. Git history is the historical source of truth for exact changes. No `changes/` directory is stored.

## Root layout

- `mtproto/configs/` — MTProto production/test configuration snapshots.
- `mtproto/app-config/` — application configuration snapshots.
- `mtproto/countries-list/` — country lists.
- `mtproto/global/` — global MTProto datasets.
- `mtproto/tl/` — official API and MTProto TL/JSON schemas.
- `tdlib/tl/` — TDLib schema.
- `tdesktop/tl/` — Telegram Desktop API and MTProto schemas.
- `TgAndroid/` — Android Stable/Preview metadata and selected resources.
- `TgAndroid/tl/` — Android Stable/Preview main API and E2E schemas.

The archive intentionally does **not** use `data/data/`, `android/`, or a generated `changes/` directory.

## Provenance

- TL files use native `//` comments.
- XML files use native XML comments.
- Markdown files use native HTML comments.
- JSON snapshots remain valid JSON and contain no injected crawler credit property.
- Stage 5C credited diffs are generated outside the data archive and are not committed as `changes/`.

## History and notifications

Git history and GitHub compare views are canonical for exact snapshot changes. Stage 5C classifies semantic additions, changes and deletions for every module, then the notification controller publishes the final Rich Message with changelog and commit buttons.
