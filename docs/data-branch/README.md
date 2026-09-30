# Telegram Developer Crawler — data archive

This branch is the generated data archive for the Telegram Developer Crawler.

It is intentionally separate from `main` so consumers can inspect Telegram developer data without pulling crawler implementation, tests, workflow files or source manifests.

## Current modules

### MTProto

- `data/mtproto/config/` — runtime configuration snapshots.
- `data/mtproto/tl/` — official API and MTProto TL schemas, in text and JSON.

The MTProto configuration collector tracks:
- `help.getConfig`
- `help.getCountriesList`
- `help.getAppConfig`
- `help.getCdnConfig`
- `messages.getAvailableReactions`
- `help.getPremiumPromo`

The TL collector tracks:
- `https://core.telegram.org/schema`
- `https://core.telegram.org/schema/json`
- `https://core.telegram.org/schema/mtproto`
- `https://core.telegram.org/schema/mtproto-json`

## Directory structure

```text
data/
└── mtproto/
    ├── config/
    │   ├── global/
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
