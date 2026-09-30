# MTProto configuration archive

This folder contains the normalized configuration datasets collected by the MTProto configuration collector.

Telegram documents `help.getConfig` as the current configuration, including data-center configuration. `help.getAppConfig` provides rapidly evolving client-specific configuration. The crawler keeps these related datasets together while separating global data from per-DC data.

## Directory layout

- `global/` — datasets collected once for the crawler's global scope.
- `production/` — production Telegram DC snapshots.
- `test/` — optional Telegram test-network DC snapshots.

## Per-DC datasets

Production/test DC folders contain:

- `config.json` — `help.getConfig`
- `countries-list.json` — `help.getCountriesList`
- `app-config.json` — `help.getAppConfig`

## Global datasets

The `global/` directory contains:

- `cdn-config.json` — `help.getCdnConfig`, collected with bot authorization.
- `available-reactions.json` — `messages.getAvailableReactions`, collected only when `TG_USER_SESSION` is configured.
- `premium-promo.json` — `help.getPremiumPromo`, collected only when `TG_USER_SESSION` is configured.

User-only datasets are normalized to remove account-specific or volatile response fields before entering Git history.

## Snapshot behavior

The crawler removes or neutralizes fields that would otherwise create noise, such as timestamps, hashes, DC option lists and account/session-specific values where applicable.

Existing snapshots are protected by a maximum 10% leaf-path removal threshold. A suspiciously incomplete replacement is rejected rather than published.

## Source of truth

The crawler implementation and source manifest live on `main`. This branch contains only generated output and its Git history.
