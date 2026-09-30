# Telegram Developer Crawler — data archive

This branch is the generated data archive for the Telegram Developer Crawler.

It is intentionally separate from `main` so consumers can inspect Telegram developer data without pulling crawler implementation, tests, workflow files or source manifests.

## Current modules

### MTProto

The MTProto data is split by dataset so server configuration, client application configuration, country metadata, global datasets, and TL schemas do not get mixed together.

- `data/mtproto/config/` — `help.getConfig` server/MTProto configuration.
- `data/mtproto/app-config/` — `help.getAppConfig` client-specific application configuration.
- `data/mtproto/countries-list/` — `help.getCountriesList` country metadata.
- `data/mtproto/global/` — global datasets such as CDN configuration, available reactions and Premium promo.
- `data/mtproto/tl/` — official API and MTProto TL schemas, in text and JSON.

Telegram documents `help.getConfig` as MTProto/server configuration and `help.getAppConfig` as rapidly evolving client-specific configuration, so they are intentionally stored as separate categories. citeturn1search0turn1search2

## Directory structure

```text
data/
└── mtproto/
    ├── config/
    │   ├── production/
    │   │   ├── dc1/
    │   │   ├── dc2/
    │   │   ├── dc3/
    │   │   ├── dc4/
    │   │   └── dc5/
    │   └── test/
    │       ├── dc1/
    │       ├── dc2/
    │       └── dc3/
    ├── app-config/
    │   ├── production/
    │   │   ├── dc1/
    │   │   ├── dc2/
    │   │   ├── dc3/
    │   │   ├── dc4/
    │   │   └── dc5/
    │   └── test/
    │       ├── dc1/
    │       ├── dc2/
    │       └── dc3/
    ├── countries-list/
    │   ├── production/
    │   └── test/
    ├── global/
    │   ├── available-reactions.json
    │   ├── cdn-config.json
    │   └── premium-promo.json
    └── tl/
        ├── api.json
        ├── api.tl
        ├── metadata.json
        ├── mtproto.json
        └── mtproto.tl
```

The `data` branch is generated. Do not edit snapshots manually; changes to collection logic belong on `main`.

## How history works

Git history is the historical database for this project.

A scheduled/manual crawler run:
1. fetches current Telegram data;
2. normalizes deterministic/volatile fields;
3. validates the new snapshot against the previous snapshot;
4. publishes changed data to this branch;
5. records the change as a Git commit.

A schema change can therefore be inspected through the exact file diff and commit history.

## Safety

The collectors use structural guards to reject suspicious mass disappearance from a source. The TL collector applies a 10% maximum disappearance threshold for schema objects/definitions.

## Relationship to main

- `main` = crawler implementation, source definitions, tests and GitHub Actions.
- `data` = normalized generated snapshots and Git history.
