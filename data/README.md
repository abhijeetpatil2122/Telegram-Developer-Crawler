# Generated Telegram developer data

This directory is the generated snapshot store for the crawler.

The repository's main branch contains crawler code and source definitions. The data branch contains only this data/ tree and its Git history.

## MTProto server data

The first collector tracks these datasets:

### Per data center

- config.json — help.getConfig
- cdn-config.json — help.getCdnConfig
- countries-list.json — help.getCountriesList
- app-config.json — help.getAppConfig

These are stored under:

data/mtproto/config/{production,test}/dcN/

### Global user datasets

When TG_USER_SESSION is configured:

- available-reactions.json — messages.getAvailableReactions
- premium-promo.json — help.getPremiumPromo

These are stored under:

data/mtproto/config/global/

User-only datasets are intentionally normalized to remove account-specific or volatile fields before they enter Git history.

## Git history

Do not edit generated snapshots manually.

Every crawler run compares the newly generated snapshots with the previous data-branch version. Git history therefore acts as the historical change detector and evidence store.

The data branch is data-only by design; crawler source code, workflows, tests and source manifests belong on main.
