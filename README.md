# Telegram Developer Crawler

Developer-focused crawler for meaningful changes across Telegram's official developer surfaces.

## Architecture

- `main`: crawler code, source manifests, normalization, validation and workflows.
- `data`: generated snapshots and historical observations.
- Git history: the source of truth for changes and diff links.
- Telegram: notification layer.

The design intentionally avoids a database or Redis. The generated `data` branch is the historical snapshot store, following the same evidence-first model used by Telegram crawler projects such as MarshalX's crawler.

## First collector: MTProto configuration

The first collector observes:

- `help.getConfig`
- `help.getAppConfig`

For production:

1. Connect once to Telegram.
2. Call `help.getConfig`.
3. Discover the current production DC endpoints from Telegram's response.
4. Create a fresh in-memory MTProto session for each DC.
5. Collect `help.getConfig` and `help.getAppConfig` independently.

For test DCs, endpoints are supplied through `TDC_TEST_DC_ENDPOINTS` because the test network is separate from production.

Known volatile values are normalized before snapshots are written:

- `config.date`
- `config.expires`
- `config.dc_options`
- `app_config.ton_usd_rate`

A snapshot safety guard rejects a generated file when more than 10% of its previously observed leaf paths disappear. This prevents a broken extractor or partial response from silently replacing good historical data.

## Repository layout

```
main
├── crawler/              # collectors, normalization, validation
├── sources/              # source manifests and collector configuration
├── .github/workflows/    # scheduled collection and data-branch publishing
└── data/                 # local working tree for generated snapshots

data
└── data/                 # generated historical snapshots
```

The `data` branch is intentionally separate from `main`, so crawler code changes do not mix with generated observations.

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

## Credentials

Never commit a real `.env` file.

Local development uses:

```bash
cp .env.example .env
```

Then fill in the required values. The collector reads environment variables directly.

GitHub Actions will use repository secrets with the same names.

## Safety principles

- Prefer official sources.
- Preserve exact evidence and source URLs.
- Normalize volatile values before committing.
- Reject suspicious mass disappearance from extractors.
- Treat beta/client observations as observations, not official announcements.
- No database or Redis for the first version.
