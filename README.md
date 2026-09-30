# Telegram Developer Crawler

Developer-focused crawler for meaningful changes across Telegram's official developer surfaces.

## Architecture

- `main`: crawler code, source manifests, normalization, validation and workflows.
- `data`: generated snapshots and historical observations.
- Git history: the source of truth for changes and diff links.
- Telegram: notification layer.

## First collector

The initial collector observes MTProto configuration through:

- `help.getConfig`
- `help.getAppConfig`

It keeps separate production/test DC snapshots and removes known volatile values before writing JSON.

The collector uses a fresh in-memory MTProto session per DC. Credentials are supplied through environment variables and are never committed.

## Planned collectors

1. MTProto configuration
2. MTProto/TL schemas
3. TDLib schemas
4. Telegram Desktop schemas
5. Android stable/beta schema and developer resources
6. iOS stable/beta developer resources
7. Desktop/macOS developer resources
8. Bot API and Mini Apps documentation
9. Diff classification and Telegram alerts

## Safety principles

- Prefer official sources.
- Preserve exact evidence and source URLs.
- Normalize volatile values before committing.
- Reject suspicious mass disappearance from extractors.
- Treat beta/client observations as observations, not official announcements.
- No database or Redis for the first version.
