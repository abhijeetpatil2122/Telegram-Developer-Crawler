# Telegram Developer Crawler — data archive

This branch contains generated Telegram developer snapshots. Git history is the historical source of truth for changes; no change-report directory is stored in the data branch.

## Current layout

- `mtproto/configs/` — production/test MTProto configuration snapshots.
- `mtproto/app-config/` — production/test application configuration.
- `mtproto/countries-list/` — production/test country lists.
- `mtproto/global/` — global MTProto datasets.
- `mtproto/tl/` — official API and MTProto TL/JSON schemas.
- `tdlib/tl/` — TDLib schema.
- `tdesktop/tl/` — Telegram Desktop API and MTProto schemas.
- `TgAndroid/` — Android Stable/Preview APK metadata and selected resources.
- `TgAndroid/tl/` — canonical Android Stable/Preview main API and E2E schemas.

## Provenance

- TL files use native `//` comments.
- XML files use native XML comments.
- Markdown files use native HTML comments.
- JSON snapshots remain untouched valid JSON; they contain no injected crawler credit field.
- Credited diffs are generated separately by Stage 5C and are not committed into this branch.

## History and diffs

Git history and GitHub compare views remain the canonical source for exact snapshot changes. Stage 5C classifies additions, changes and deletions before the final Telegram notification; its credited diff is an attribution layer and never modifies generated source files.
