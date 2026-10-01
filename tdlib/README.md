# TDLib schema

The crawler tracks the official TDLib API schema from the upstream `tdlib/td` repository.

## Source

- Repository: https://github.com/tdlib/td
- Schema: `td/generate/scheme/td_api.tl`
- Raw source: https://raw.githubusercontent.com/tdlib/td/master/td/generate/scheme/td_api.tl

## Data branch layout

- `tdlib/tl/td_api.tl` — normalized upstream TL source.
- `tdlib/tl/td_api.json` — deterministic structured index.
- `tdlib/tl/metadata.json` — upstream commit, counts, hashes and safety settings.

The data branch is the archive root, so these paths do not have an additional `data/` prefix.

## Safety

The collector rejects empty or very small schemas, duplicate definition names, and snapshots where more than 10% of previously known definitions disappear.

## Provenance

The TL file uses native `//` comments. The JSON index remains valid JSON with no injected crawler credit field.
