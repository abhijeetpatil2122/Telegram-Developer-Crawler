# Telegram Developer Crawler — data archive

This branch is the generated data archive for the Telegram Developer Crawler.

It is intentionally separate from main so consumers can inspect Telegram developer data without pulling crawler implementation, tests, workflow files or source manifests.

## Current modules

### MTProto

- data/mtproto/config/ — help.getConfig server/MTProto configuration.
- data/mtproto/app-config/ — help.getAppConfig client-specific application configuration.
- data/mtproto/countries-list/ — help.getCountriesList country metadata.
- data/mtproto/global/ — global datasets.
- data/mtproto/tl/ — official API and MTProto TL schemas.

### TDLib

- data/tdlib/schema/ — official tdlib/td td_api.tl, structured JSON index and provenance metadata.

### Telegram Desktop

- data/tdesktop/schema/ — official telegramdesktop/tdesktop api.tl and mtproto.tl, structured JSON indexes and provenance metadata.
- api.tl and mtproto.tl are kept separate because they represent different schema layers used by Telegram Desktop.

## Directory structure

```text
data/
├── mtproto/
│   ├── config/
│   ├── app-config/
│   ├── countries-list/
│   ├── global/
│   └── tl/
├── tdlib/
│   └── schema/
└── tdesktop/
    └── schema/
        ├── api.tl
        ├── api.json
        ├── api-metadata.json
        ├── mtproto.tl
        ├── mtproto.json
        ├── mtproto-metadata.json
        └── metadata.json
```

The data branch is generated. Do not edit snapshots manually; changes to collection logic belong on main.

## How history works

Git history is the historical database for this project.

A scheduled/manual crawler run:
1. fetches current Telegram data;
2. normalizes deterministic fields;
3. validates the new snapshot against the previous snapshot;
4. publishes changed data to this branch;
5. records the change as a Git commit.

A schema change can therefore be inspected through the exact file diff and commit history.

## Safety

The collectors use structural guards to reject suspicious mass disappearance from a source. Schema collectors currently apply a 10% maximum disappearance threshold.

## Relationship to main

- main = crawler implementation, source definitions, tests and GitHub Actions.
- data = normalized generated snapshots and Git history.
