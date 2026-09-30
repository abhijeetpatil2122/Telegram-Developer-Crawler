# Telegram Developer Crawler

Developer-focused crawler for meaningful changes across Telegram's official developer surfaces.

## Architecture

- `main`: crawler code, source manifests, normalization, validation and workflows.
- `data`: generated snapshots and historical observations.
- Git history: the source of truth for changes and diff links.
- Telegram: notification layer.

The design intentionally avoids a database or Redis. The generated `data` branch is the historical snapshot store, following the same evidence-first model used by Telegram crawler projects such as MarshalX's crawler.

## First collector: MTProto configuration

The first collector observes the MTProto server configuration surface, following the server-data approach used by MarshalX's Telegram crawler.

Per production/test DC:

- `help.getConfig` — core MTProto/server configuration and DC options
- `help.getCdnConfig` — CDN public-key configuration
- `help.getCountriesList` — country names, ISO codes and phone-code patterns
- `help.getAppConfig` — rapidly changing graphical-client configuration

Globally, when an authorized user StringSession is configured:

- `messages.getAvailableReactions` — available reaction metadata and animations
- `help.getPremiumPromo` — Premium promotion configuration

Telegram documents `getConfig` and `getAppConfig` as runtime configuration sources; `getCdnConfig` and `getCountriesList` are additional server/client configuration datasets tracked by the crawler. The latter two user-only datasets require a user session. citeturn1search6turn1search1turn1search0turn4search3turn1search9

For production:

1. Connect once to Telegram.
2. Call `help.getConfig`.
3. Discover the current production DC endpoints from Telegram's response.
4. Create a fresh in-memory MTProto session for each DC.
5. Collect the four per-DC datasets independently.
6. If `TG_USER_SESSION` is configured, collect the two user-only datasets into the global snapshot.

For test DCs, endpoints and separate test-network credentials are optional because the test network is separate from production.

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

Then fill in the values. The MTProto configuration collector requires `TG_API_ID` and `TG_API_HASH`. It connects without logging in, which allows `help.getConfig` and `help.getAppConfig` to be collected without using a bot account. `TG_BOT_TOKEN` is optional and is reserved for the future Telegram alerting layer.

Test collection additionally requires `TG_TEST_API_ID`, `TG_TEST_API_HASH`, and `TDC_TEST_DC_ENDPOINTS`. `TG_TEST_BOT_TOKEN` is optional and reserved for future bot-based collectors or alerts.

GitHub Actions reads these secrets from the `appConfig` environment.

## Safety principles

- Prefer official sources.
- Preserve exact evidence and source URLs.
- Normalize volatile values before committing.
- Reject suspicious mass disappearance from extractors.
- Treat beta/client observations as observations, not official announcements.
- No database or Redis for the first version.
