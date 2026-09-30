# MTProto data

This folder contains runtime data collected through Telegram's MTProto API.

The module is designed to track developer-relevant server and client configuration that can change independently of the static TL schema.

## Current submodule

- `config/` — configuration and related server datasets.

The README inside `config/` documents the individual datasets and authentication scope.

## Collection model

The crawler uses Telethon to call the relevant MTProto methods. Production DC endpoints are discovered from `help.getConfig`; test-network endpoints are explicitly configured through the crawler environment.

Data is normalized before publication and protected by the snapshot safety guard.

## Future MTProto modules

Additional MTProto datasets can be added here when they provide useful developer-facing change signals. New collectors should document their source method, authentication requirement, normalization rules and output path before being enabled.
