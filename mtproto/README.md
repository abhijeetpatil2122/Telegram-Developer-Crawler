# MTProto data

This module contains developer-facing data collected through Telegram's MTProto and official TL-schema surfaces.

## Data branch layout

- `mtproto/configs/` — production/test `help.getConfig` snapshots.
- `mtproto/app-config/` — production/test `help.getAppConfig` snapshots.
- `mtproto/countries-list/` — production/test `help.getCountriesList` snapshots.
- `mtproto/global/` — global datasets such as CDN configuration, available reactions and Premium promo.
- `mtproto/tl/` — official API and MTProto TL/JSON schemas.

The `data` branch is the archive itself, so these paths are relative to the branch root; there is no extra `data/` directory.

Telegram distinguishes `help.getConfig` from `help.getAppConfig`: the former contains MTProto/server configuration, while the latter contains rapidly evolving client-specific application configuration.

## TL schema collection

The `mtproto/tl/` dataset is collected directly from Telegram's public schema endpoints:

- `core.telegram.org/schema` — current API TL schema.
- `core.telegram.org/schema/json` — current API TL schema in JSON.
- `core.telegram.org/schema/mtproto` — current MTProto TL schema.
- `core.telegram.org/schema/mtproto-json` — current MTProto TL schema in JSON.

The collector preserves both text and JSON representations and writes deterministic JSON formatting.

## Provenance

TL files use native `//` comments. JSON files remain valid, untouched JSON; no synthetic credit property is injected. Stage 5C adds attribution only to the separate credited diff artifact.
