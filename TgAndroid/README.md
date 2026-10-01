# Telegram Android client

Module 5 tracks the official Telegram Android client in two independent channels:

- **Stable** — direct APK from `https://telegram.org/dl/android/apk`.
- **Public Beta** — direct APK from `https://telegram.org/dl/android/apk-public-beta`.

Telegram's Android distribution supports reproducible builds, and the official site documents that the direct-download Android APK is built from the published open-source client. The crawler therefore preserves APK provenance and deterministic extracted evidence rather than committing the APK itself.

## Stage 5A

The first stage downloads both APKs independently and records:

- resolved download URL;
- APK size and SHA-256;
- Android package name;
- version name and version code;
- Apktool provenance;
- `res/values/strings.xml`;
- `res/values/public.xml`.

The APK itself is temporary and is never committed to the data branch.

## Why Stable and Beta are separate

Stable and Public Beta are different observations. A Beta snapshot must never overwrite Stable, and a failed Beta extraction must not affect the Stable snapshot.

Stage 5B produces the normalized TL schema for each channel independently. Stable-vs-Beta comparison belongs to Stage 5C and will consume these canonical snapshots.

## Safety

Stage 5A refuses to publish an artifact when:

- the HTTP request fails;
- the downloaded file is suspiciously small;
- the response is not an APK/ZIP;
- Apktool fails;
- required manifest/resource files are missing;
- version metadata cannot be parsed.

No APK bytes are stored in Git.

## Module 5B — Android TL extraction

Stage 5B downloads each recorded APK into a temporary workspace, decompiles `org.telegram.tgnet` with a pinned JADX release, reconstructs TL constructors/methods from generated serialization code, and records the embedded layer. The raw Android Java class names are then canonicalized into a developer-facing TL scheme: `TL_` prefixes are removed, namespace separators become `.`, historical `_layerNNN`/`_old` classes are filtered, type references are normalized, and the output uses the standard `---types---` / `---functions---` layout with a `// LAYER N` footer. The developer-facing outputs are `main_api.tl`, `main_api.json`, `e2e.tl`, `e2e.json`, and extraction metadata; APKs and decompiled Java sources are never committed. `main_api.tl` is the Android-derived main API schema and `e2e.tl` is the official end-to-end schema kept as a separate usable input.

Safety checks require at least 500 constructors and 200 methods, reject duplicate definition keys, and reject historical definition loss above 10%. Stable and Public Beta are processed independently.


## Provenance and notifications

Generated artifacts carry Telegram Developer Crawler provenance. The crawler can also maintain one temporary Telegram status message during a run (download → decompile → extract → validate); it is removed when the run finishes without a data change. Change announcements will be produced by the later Stable/Beta diff classifier.
