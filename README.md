# Telegram Developer Crawler

Developer-focused crawler for meaningful changes across Telegram's official developer surfaces.

## Architecture

- main: crawler code, source manifests, normalization, validation, tests and workflows.
- data: generated snapshots, credited change reports and Git history.
- Git history: the historical source of truth for exact changes.
- Telegram: temporary crawl progress and final change notifications.
- No database or Redis is required.

## Current collectors

1. MTProto configuration — production/test DC configuration and related global datasets
2. MTProto/TL schemas — official Telegram API and MTProto schemas
3. TDLib schema — official td_api.tl and structured definition index
4. Telegram Desktop schemas — official Desktop API and MTProto schemas
5. Telegram Android — stable/public-beta APK metadata/resources plus canonical main API and E2E schema extraction
6. 5C change classifier — semantic additions/changes/deletions across all generated modules
7. Telegram notifications — one temporary editable crawl-status message and one final change alert when data changes

## Provenance

Generated snapshots carry:

- TL: // auto-generated header with Copyright (C) 2026 Abhijeet Patil
- JSON: _crawler provenance metadata
- XML/Markdown: native comment-style provenance
- Change reports: every unified-diff hunk receives // Telegram Developer Crawler — Copyright (C) 2026 Abhijeet Patil

The credited diff is an attribution layer; the native GitHub commit/compare diff is left untouched.

## Notification lifecycle

1. Start one temporary crawl-status message.
2. Edit it as MTProto, TL, TDLib, Desktop, Android download and Android JADX stages progress.
3. If generated data is unchanged, delete the status message and send nothing.
4. If data changes, delete the status message, commit/push the data branch, then send one final changelog alert with the GitHub commit/compare links.

## Android output

For each channel:

- main_api.tl / main_api.json — developer-facing current main API schema, merging the official API with Android-specific current definitions.
- e2e.tl / e2e.json — separate official Telegram E2E schema.
- metadata.json — APK/version/build/package provenance.
- resources/ — selected deterministic Android resources.

See docs/modules/android/README.md for details.
