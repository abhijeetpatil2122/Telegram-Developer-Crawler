# Telegram Developer Crawler — data archive

This branch contains generated Telegram developer snapshots and their Git history.

## Current modules

- MTProto configuration: config, app-config, countries-list and global datasets.
- MTProto/TL: official API and MTProto schemas.
- TDLib: official td_api.tl and structured JSON.
- Telegram Desktop: official API and MTProto schemas.
- Android Stable: APK metadata/resources plus main API and E2E schemas.
- Android Preview: APK metadata/resources plus main API and E2E schemas.
- changes/: credited Stage 5C change reports generated only when a snapshot changes.

## History and diffs

Git history is the historical database. Each crawler run compares the generated snapshot against the previous data commit before publishing.

Stage 5C classifies changes as additions, changes and deletions by module. The generated change report contains a unified diff whose every hunk is annotated with the crawler provenance marker.

The GitHub commit and compare URLs remain the canonical, unmodified source diff. The credited report is an additional attribution artifact and does not rewrite GitHub's native diff.

## Generated-file provenance

Generated artifacts carry Telegram Developer Crawler provenance and Copyright (C) 2026 Abhijeet Patil.

TL snapshots use a // file header. JSON snapshots remain untouched valid JSON because JSON has no standard comment syntax; provenance is carried by crawler documentation and credited change reports. XML/Markdown artifacts use their native comment syntax.

## Directory structure

data/
├── mtproto/
│   ├── config/
│   ├── app-config/
│   ├── countries-list/
│   ├── global/
│   └── tl/
├── tdlib/schema/
├── tdesktop/schema/
└── android/
    ├── stable/
    ├── beta/
    └── metadata.json

The crawler also writes data/changes/<timestamp>-change-report.md when a run changes generated data.
