# Generated Telegram developer data

This directory is the generated snapshot tree published by the crawler.

The repository's **main** branch contains crawler code, source definitions, tests and workflow configuration. The **data** branch is the historical archive of generated snapshots.

## Directory layout

- `mtproto/` — MTProto/API runtime data.
- `mtproto/config/` — configuration datasets collected from Telegram.
- `mtproto/config/global/` — global datasets that are not stored once per production DC.
- `mtproto/config/production/` — production DC snapshots.
- `mtproto/config/test/` — test-network DC snapshots, when test credentials and endpoints are configured.

Each logical folder contains its own README describing the datasets stored there.

## Snapshot rules

Generated JSON files are normalized before they enter Git history. Volatile, account-specific or transport-specific fields are removed or neutralized where appropriate so that Git changes represent meaningful Telegram data changes rather than timestamps, hashes or session-specific values.

Before replacing an existing snapshot, the crawler applies a structural safety guard. A snapshot is rejected if more than 10% of previously observed leaf paths disappear.

## History

The data branch is intentionally used as the historical snapshot store. A crawler run writes a new commit only when generated data changes.

Do not edit generated JSON snapshots manually. Changes should come from the crawler on the main branch.

## Authentication

Some datasets are public and can be collected with the API ID/hash. Other datasets require the corresponding Telegram authorization:

- Bot-only global data uses `TG_BOT_TOKEN`.
- User-only global data uses `TG_USER_SESSION`.

A user StringSession is a credential and must never be committed to this repository or included in generated data.
