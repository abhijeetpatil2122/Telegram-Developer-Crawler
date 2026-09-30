# Generated Telegram developer data

This branch is the generated data archive for Telegram-Developer-Crawler.

The root of this branch intentionally contains only the data/ directory. Crawler code, workflows, tests and source manifests live on the main branch.

## MTProto server datasets

Per data center:

- config.json — help.getConfig
- cdn-config.json — help.getCdnConfig
- countries-list.json — help.getCountriesList
- app-config.json — help.getAppConfig

Stored under data/mtproto/config/{production,test}/dcN/.

When the optional TG_USER_SESSION is configured on the main-branch workflow, the user-only datasets are also collected:

- available-reactions.json — messages.getAvailableReactions
- premium-promo.json — help.getPremiumPromo

Stored under data/mtproto/config/global/.

## Change detection

This branch is the historical snapshot store. Each generated file is committed only when its normalized content changes, so Git history provides the change timeline and exact diffs.

Do not edit this branch manually. Generated data is published by the crawler workflow from main.
