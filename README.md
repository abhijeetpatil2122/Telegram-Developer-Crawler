# Telegram Developer Crawler

Developer-focused crawler for meaningful changes across Telegram's official developer surfaces.

## Architecture

- `main`: crawler code, source manifests, normalization, validation and workflows.
- `data`: generated snapshots and historical observations.
- Git history: the source of truth for changes and diff links.
- Telegram: notification layer.

The design intentionally avoids a database or Redis. The generated `data` branch is the historical snapshot store.

## Current collectors

1. **MTProto configuration** — production/test DC configuration and related global datasets
2. **MTProto/TL schemas** — official Telegram API and MTProto schemas
3. **TDLib schema** — official TDLib API schema and structured definition index

The roadmap continues with Telegram Desktop schemas, Android/iOS/desktop developer resources, Bot API/Mini Apps documentation, change classification, and Telegram alerts.

### TDLib schema

The crawler tracks the official TDLib schema from:
- `https://github.com/tdlib/td`
- `td/generate/scheme/td_api.tl`

The raw normalized TL source and a deterministic structured definition index are stored under `data/tdlib/schema/`. Metadata records the upstream TDLib commit used for the snapshot.

### MTProto configuration

Data is separated by dataset: `config/` for `help.getConfig`, `app-config/` for `help.getAppConfig`, `countries-list/` for `help.getCountriesList`, and `global/` for DC-independent datasets.

Per production/test DC:
- `help.getConfig`
- `help.getCountriesList`
- `help.getAppConfig`

Global datasets:
- `help.getCdnConfig`
- `messages.getAvailableReactions` (user session)
- `help.getPremiumPromo` (user session)

Production endpoints are discovered from `help.getConfig`. Test DCs use Telegram's standard test-network endpoints with the **same application `api_id/api_hash`**; `TDC_TEST_DC_ENDPOINTS` is an optional override.

### MTProto/TL schemas

The crawler collects the official API and MTProto TL schemas from:
- `https://core.telegram.org/schema`
- `https://core.telegram.org/schema/json`
- `https://core.telegram.org/schema/mtproto`
- `https://core.telegram.org/schema/mtproto-json`

Both the human-readable TL form and JSON form are stored under `data/mtproto/tl/`. The API layer is read from the live schema instead of hard-coded.

## Credentials

Never commit a real `.env` file.

The MTProto configuration collector uses:
- `TG_API_ID`
- `TG_API_HASH`
- `TG_BOT_TOKEN`
- optional `TG_USER_SESSION`
- optional `TDC_TEST_DC_ENDPOINTS`

**There are no separate `TG_TEST_API_ID` or `TG_TEST_API_HASH` credentials.** Production and test DC collection use the same application API credentials, while test DCs use the separate Telegram test network.

GitHub Actions reads these secrets from the `appConfig` environment.

## Safety principles

- Prefer official sources.
- Preserve exact evidence and source URLs.
- Normalize volatile values before committing.
- Reject suspicious mass disappearance from extractors.
- Treat beta/client observations as observations, not official announcements.
- No database or Redis for the first version.
