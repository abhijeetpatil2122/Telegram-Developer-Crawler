# Telegram Desktop schemas

The crawler tracks the official Telegram Desktop TL schemas from the upstream telegramdesktop/tdesktop repository.

## Sources

- Repository: https://github.com/telegramdesktop/tdesktop
- API schema: Telegram/SourceFiles/mtproto/scheme/api.tl
- MTProto schema: Telegram/SourceFiles/mtproto/scheme/mtproto.tl
- Branch: dev

Telegram Desktop's developer guidance identifies these two files as its API schema files.

## Generated files

- schema/api.tl — normalized upstream Telegram API TL source.
- schema/api.json — deterministic structured index of API constructors and functions.
- schema/mtproto.tl — normalized upstream MTProto TL source.
- schema/mtproto.json — deterministic structured index of MTProto constructors and functions.
- schema/*-metadata.json — exact upstream commit, counts, hashes and safety settings.
- schema/metadata.json — module-level source and commit manifest.

The raw TL files remain canonical evidence and preserve upstream comments. Only line endings and the final newline are normalized.

## Safety

Each schema rejects:
- very small snapshots;
- duplicate definition names;
- snapshots where more than 10% of previously known definitions disappear.

The API and MTProto schemas are kept separate because they represent different schema layers used by Telegram Desktop.
