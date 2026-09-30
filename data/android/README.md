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

The later TL extraction stage will decompile the APK's `org.telegram.tgnet` classes and produce a normalized TL schema for each channel independently. Stable-vs-Beta comparison will be added after both extraction pipelines are validated.

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

Stage 5B downloads each recorded APK into a temporary workspace, decompiles `org.telegram.tgnet` with a pinned JADX release, reconstructs TL constructors/methods from generated serialization code, and records the embedded layer. Only normalized `tl.tl`, structured `tl.json`, and extraction metadata are published; APKs and decompiled Java sources are never committed.

Safety checks require at least 500 constructors and 200 methods, reject duplicate definition keys, and reject historical definition loss above 10%. Stable and Public Beta are processed independently.
