# Telegram Developer Crawler

Developer-focused crawler for tracking meaningful changes across Telegram's official developer surfaces.

The project follows a Git-based snapshot model inspired by the architecture of MarshalX's Telegram crawler:

- `main` contains crawler code, source definitions, normalizers, filters, and workflows.
- `data` contains generated snapshots and historical observations.
- Git commits provide the change history and diff URLs used by alerts.

## Planned sources

- Bot API and Mini Apps documentation
- MTProto / TL schemas
- TDLib schemas
- Telegram Desktop schemas
- Android stable and beta client signals
- iOS stable and beta client signals
- Desktop/macOS client signals
- MTProto production and test configuration
- Selected developer-relevant Telegram resources

## Design principles

1. Prefer official Telegram sources.
2. Preserve evidence and link alerts back to exact snapshots/diffs.
3. Normalize volatile values before committing.
4. Treat client/beta observations as observations, not official announcements.
5. Guard against broken crawls and accidental mass deletions.
6. Keep the first version Git-native: no database or Redis.

## Branches

### main

The crawler and its configuration.

### data

Generated snapshots. This branch is the project's historical data store.

## Status

Initial repository bootstrap. Collectors will be added incrementally, starting with the repository/data model and MTProto configuration collector.
