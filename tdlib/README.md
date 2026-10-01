# TDLib schema

The crawler tracks the official TDLib API schema from the upstream `tdlib/td` repository.

## Source

- Repository: https://github.com/tdlib/td
- Schema: `td/generate/scheme/td_api.tl`
- Raw source: https://raw.githubusercontent.com/tdlib/td/master/td/generate/scheme/td_api.tl

## Generated files

- `schema/td_api.tl` — normalized upstream TL source.
- `schema/td_api.json` — deterministic structured index of top-level constructors and functions.
- `schema/metadata.json` — upstream commit, counts, hashes and safety settings.

The upstream commit is recorded so every snapshot can be tied to an exact TDLib repository state.

## Safety

The collector rejects:
- empty/very small schemas;
- duplicate definition names;
- snapshots where more than 10% of previously known definitions disappear.

The raw TL remains the canonical evidence. The generated JSON is an index for future schema-aware diff classification.
