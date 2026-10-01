# Telegram Desktop schemas

The crawler tracks the official Telegram Desktop TL schemas from the upstream `telegramdesktop/tdesktop` repository.

## Sources

- Repository: https://github.com/telegramdesktop/tdesktop
- API schema: `Telegram/SourceFiles/mtproto/scheme/api.tl`
- MTProto schema: `Telegram/SourceFiles/mtproto/scheme/mtproto.tl`
- Branch: `dev`

## Data branch layout

- `tdesktop/tl/api.tl` — normalized API TL source.
- `tdesktop/tl/api.json` — deterministic API constructor/function index.
- `tdesktop/tl/mtproto.tl` — normalized MTProto TL source.
- `tdesktop/tl/mtproto.json` — deterministic MTProto constructor/function index.
- `tdesktop/tl/*-metadata.json` — exact upstream commit, counts, hashes and safety settings.
- `tdesktop/tl/metadata.json` — module-level source manifest.

The data branch is the archive root, so there is no additional `data/` prefix.

## Provenance

TL files use native `//` comments. JSON files remain valid JSON and contain no injected crawler credit field.
