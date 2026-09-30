# MTProto data

This module contains developer-facing data collected through Telegram's MTProto and official TL-schema surfaces.

## Current submodules

- `config/` — runtime server/client configuration and related datasets.
- `tl/` — official MTProto/API TL schemas in text and machine-readable JSON form.

## TL schema collection

The `tl/` dataset is collected directly from Telegram's public schema endpoints:

- `https://core.telegram.org/schema` — current API TL schema.
- `https://core.telegram.org/schema/json` — current API TL schema in JSON.
- `https://core.telegram.org/schema/mtproto` — current MTProto TL schema.
- `https://core.telegram.org/schema/mtproto-json` — current MTProto TL schema in JSON.

The collector preserves both text and JSON representations and writes deterministic JSON formatting. The API layer is read from the source JSON rather than hard-coded.

Before publication, the collector checks that the schema is structurally valid and rejects a replacement when more than 10% of previously observed schema objects/definitions disappear. This is intended to catch partial downloads or broken extraction.

## Configuration collection

The configuration collector uses Telethon to call the relevant MTProto methods. Production DC endpoints are discovered from `help.getConfig`; test-network endpoints use Telegram's standard test DC endpoints with the same application API credentials; an optional environment override can replace those endpoints.

Data is normalized before publication and protected by the snapshot safety guard.

## Future MTProto modules

Additional MTProto datasets can be added here when they provide useful developer-facing change signals. New collectors should document their source, authentication requirement, normalization rules and output path before being enabled.
