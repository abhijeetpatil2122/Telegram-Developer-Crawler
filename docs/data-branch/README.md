# Telegram Developer Crawler — data archive

This branch is the **generated data archive** for [Telegram-Developer-Crawler](https://github.com/abhijeetpatil2122/Telegram-Developer-Crawler).

It is intentionally separate from the `main` branch so that consumers can inspect Telegram developer data without pulling the crawler implementation, tests, workflow files or source manifests.

## What this branch contains

The branch stores normalized snapshots collected from Telegram's developer-facing MTProto/runtime data sources.

Current module:

- **MTProto configuration**
  - `help.getConfig`
  - `help.getCountriesList`
  - `help.getAppConfig`
  - `help.getCdnConfig`
  - `messages.getAvailableReactions`
  - `help.getPremiumPromo`

The collector follows the access requirements of each method. Public/unauthenticated methods are collected with the crawler's API credentials, bot-only data uses the configured bot session, and user-only datasets are collected only when a `TG_USER_SESSION` is configured.

## Directory structure

```text
data/
└── mtproto/
    └── config/
        ├── global/
        ├── production/
        │   ├── dc1/
        │   ├── dc2/
        │   ├── dc3/
        │   ├── dc4/
        │   └── dc5/
        └── test/
            ├── dc1/
            ├── dc2/
            └── dc3/
```

The `test/` tree is present when the test-network API credentials are configured. The crawler has standard Telegram test DC endpoints built in and supports `TDC_TEST_DC_ENDPOINTS` as an override.

Read the README inside each module directory for its collection scope.

## How history works

Git history is the historical database for this project.

A scheduled/manual crawler run:

1. fetches the current Telegram data;
2. normalizes volatile or account-specific fields;
3. validates the new snapshot against the previous snapshot;
4. publishes changed data to this branch;
5. records the change as a Git commit.

This means a file's Git history and diff are the primary evidence for when a tracked value changed.

## Safety

The crawler has a structural guard that rejects a replacement snapshot when more than 10% of previously observed leaf paths disappear. This helps prevent an API/client failure from silently replacing a valid dataset with a partial response.

Generated JSON should not be edited manually. Changes to collection logic belong on `main`.

## Relationship to main

- `main` = crawler implementation, source definitions, tests and GitHub Actions.
- `data` = normalized generated snapshots and their Git history.

For implementation details, see the README on the `main` branch.
