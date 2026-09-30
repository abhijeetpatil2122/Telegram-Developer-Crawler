# Telegram Developer Crawler

Developer-focused crawler for meaningful changes across Telegram's official developer surfaces.

## Architecture

- `main`: crawler code, source manifests, normalization, validation and workflows.
- `data`: generated snapshots and historical observations.
- Git history: the source of truth for changes and diff links.
- Telegram: notification layer.

The design intentionally avoids a database or Redis. The generated `data` branch is the historical snapshot store.

## Current collectors

1. **MTProto configuration** — production/test DC configuration and related global datasets
2. **MTProto/TL schemas** — official Telegram API and MTProto schemas
3. **TDLib schema** — official TDLib API schema and structured definition index
4. **Telegram Desktop schemas** — official Desktop API and MTProto schemas
5. **Telegram Android client** — stable and public-beta APK metadata/resources (Stage 5A)

Roadmap next: Android TL extraction/comparison, iOS/desktop developer resources, Bot API/Mini Apps documentation, change classification, and Telegram alerts.

### Telegram Android client

Android is deliberately split into **stable** and **public beta** channels. Stage 5A tracks the direct APKs and deterministic resources separately. The next stage will extract the embedded `org.telegram.tgnet` TL schema from each APK.

See `docs/modules/android/README.md` for the module design.
