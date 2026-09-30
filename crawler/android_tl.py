"""Extract Telegram TL schema from Android Stable/Public Beta APKs (Module 5B).

The APK itself is never committed. JADX decompiles the Android tgnet package into
temporary Java sources; this module reconstructs TL definitions from the generated
serialization/deserialization methods and publishes only normalized TL/JSON metadata.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "android"
JADX_URL = os.environ.get(
    "ANDROID_JADX_URL",
    "https://github.com/skylot/jadx/releases/download/v1.5.6/jadx-1.5.6.zip",
)
PACKAGE_PREFIX = "org.telegram.tgnet"
MAX_REMOVAL_RATIO = 0.10
MIN_CONSTRUCTORS = 500
MIN_METHODS = 200

TYPE_READERS = {
    "readInt32": "int",
    "readInt64": "long",
    "readDouble": "double",
    "readString": "string",
    "readByteBuffer": "bytes",
    "readByteArray": "bytes",
    "readBool": "Bool",
}



LAYER_SUFFIX_RE = re.compile(r"^(?P<base>.+?)(?:_layer_?(?P<layer>\\d+)|_old\\d*|_(?P<legacy>\\d{3,}))$")


def canonical_name(raw: str) -> tuple[str, int | None, bool]:
    """Convert JADX Android TL class names to canonical TL names.

    Returns (name, embedded_layer, is_historical). Android keeps many old
    generated classes alongside the current schema. Those classes are useful
    to the decompiler but must not leak into the developer-facing scheme.
    """
    name = raw.rsplit(".", 1)[-1]
    if name.startswith("TL_"):
        name = name[3:]

    embedded_layer: int | None = None
    historical = False
    match = LAYER_SUFFIX_RE.match(name)
    if match:
        name = match.group("base")
        if match.group("layer"):
            embedded_layer = int(match.group("layer"))
            historical = True
        elif match.group("legacy"):
            embedded_layer = int(match.group("legacy"))
            historical = True
        else:
            historical = True

    if "_old" in name.lower():
        name = re.sub(r"_old\\d*$", "", name, flags=re.IGNORECASE)
        historical = True

    # Java uses underscores to encode TL namespaces, e.g.
    # TL_auth_authorization -> auth.authorization. Do not split ordinary
    # camelCase TL names, which are already canonical.
    if "_" in name:
        parts = [p for p in name.split("_") if p]
        if len(parts) >= 2:
            name = parts[0].lower() + "." + "_".join(parts[1:])

    return name, embedded_layer, historical


def canonical_type(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return raw
    if raw.startswith("Vector<") and raw.endswith(">"):
        return f"Vector<{canonical_type(raw[7:-1])}>"
    if raw.startswith("flags."):
        prefix, typ = raw.split("?", 1) if "?" in raw else (raw, "")
        return f"{prefix}?{canonical_type(typ)}" if typ else prefix
    if raw in {"#", "int", "long", "double", "string", "bytes", "Bool", "true", "int128", "int256"}:
        return raw
    name, _, _ = canonical_name(raw)
    return name


def canonicalize_definition(item: dict[str, Any], current_layer: int | None) -> dict[str, Any] | None:
    name, embedded_layer, historical = canonical_name(item["name"])
    if historical and (embedded_layer is None or current_layer is None or embedded_layer < current_layer):
        return None
    if embedded_layer is not None and current_layer is not None and embedded_layer != current_layer:
        return None

    result = dict(item)
    result["name"] = name
    if result["kind"] == "constructor":
        result["type"] = canonical_type(str(result["type"]))
    else:
        result["result"] = canonical_type(str(result["result"]))
    result["params"] = [
        {"name": p["name"], "type": canonical_type(p["type"])}
        for p in result.get("params", [])
    ]
    return result

CLASS_RE = re.compile(
    r"(?:public\s+)?(?:static\s+)?(?:final\s+)?class\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)(?:\s+extends\s+(?P<extends>[A-Za-z0-9_.$<>]+))?"
)
CONSTRUCTOR_RE = re.compile(r"\bconstructor\s*=\s*(?P<id>-?0x[0-9a-fA-F]+|-?\d+)\s*;")
LAYER_PATTERNS = (
    re.compile(r"\b(?:this\.)?layer\s*=\s*(?P<value>\d+)\s*;"),
    re.compile(r"\b(?:static\s+)?(?:final\s+)?(?:int|long)\s+LAYER\s*=\s*(?P<value>\d+)\s*;"),
    re.compile(r"\bcurrentLayer\s*=\s*(?P<value>\d+)\s*;"),
    re.compile(r"\bgetLayer\s*\([^)]*\)\s*\{\s*return\s+(?P<value>\d+)\s*;"),
)

RETURN_TL_RE = re.compile(r"return\s+([A-Za-z0-9_.$]+)\.TLdeserialize\s*\(")
RETURN_READ_RE = re.compile(r"return\s+stream\.([A-Za-z0-9_]+)\s*\(")
ASSIGN_TL_RE = re.compile(
    r"(?P<field>[A-Za-z_$][\w$]*)\s*=\s*(?:\([^)]+\)\s*)?"
    r"(?P<type>[A-Za-z0-9_.$]+)\.TLdeserialize\s*\("
)
ASSIGN_READ_RE = re.compile(
    r"(?P<field>[A-Za-z_$][\w$]*)\s*=\s*stream\.(?P<reader>[A-Za-z0-9_]+)\s*\("
)
ASSIGN_VECTOR_RE = re.compile(
    r"(?P<field>[A-Za-z_$][\w$]*)\s*=\s*(?:\([^)]+\)\s*)?"
    r"Vector(?:Legacy)?\.(?:deserialize|deserializeVector)\s*\("
)
CAST_VECTOR_RE = re.compile(
    r"\((?P<type>[A-Za-z0-9_.$<>]+)\)\s*Vector(?:Legacy)?\."
)
FLAG_IF_RE = re.compile(r"\(flags\s*&\s*(?P<mask>0x[0-9a-fA-F]+|\d+)\)\s*!=\s*0")

FIELD_RE = re.compile(
    r"(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?"
    r"(?P<type>[A-Za-z0-9_.$<>\[\]]+)\s+(?P<name>[A-Za-z_$][\w$]*)\s*;"
)
WRITE_RE = re.compile(
    r"stream\.(?P<writer>writeInt32|writeInt64|writeDouble|writeString|"
    r"writeByteBuffer|writeByteArray|writeBool)\s*\(\s*(?P<field>[A-Za-z_$][\w$]*)"
)
OBJECT_WRITE_RE = re.compile(
    r"(?P<field>[A-Za-z_$][\w$]*)\.serializeToStream\s*\(\s*stream"
)

def render_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_tl(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip() + "\n"


def definition_key(item: dict[str, Any], default_kind: str | None = None) -> str:
    kind = item.get("kind") or default_kind
    if not kind:
        raise ValueError("definition is missing kind")
    return f"{kind}:{item['id']}:{item['name']}"


def leaf_paths(value: Any, prefix: str = "") -> set[str]:
    if isinstance(value, dict):
        out: set[str] = set()
        for k, v in value.items():
            p = f"{prefix}.{k}" if prefix else str(k)
            out.update(leaf_paths(v, p))
        return out
    if isinstance(value, list):
        out: set[str] = set()
        for i, v in enumerate(value):
            out.update(leaf_paths(v, f"{prefix}[{i}]"))
        return out
    return {prefix or "$"}


def validate_definition_safety(previous: Any, current: list[dict[str, Any]]) -> None:
    if not previous:
        return
    old = {
        definition_key(x, "constructor")
        for x in previous.get("constructors", [])
    }
    old.update(
        definition_key(x, "method")
        for x in previous.get("methods", [])
    )
    new = {definition_key(x) for x in current}
    if not old:
        return
    ratio = len(old - new) / len(old)
    if ratio > MAX_REMOVAL_RATIO:
        raise ValueError(
            f"Android TL safety guard triggered: {len(old-new)}/{len(old)} "
            f"definitions disappeared ({ratio:.1%})"
        )


def balanced_block(text: str, brace_start: int) -> str:
    depth = 0
    in_string = False
    quote = ""
    escape = False
    for i in range(brace_start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
            continue
        if ch in ('"', "'"):
            in_string = True
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[brace_start + 1:i]
    raise ValueError("unbalanced Java block")


def extract_method_body(text: str, method: str) -> str | None:
    match = re.search(rf"\b{re.escape(method)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return None
    brace = text.find("{", match.start())
    return balanced_block(text, brace)


def mask_to_bit(mask: str) -> int:
    value = int(mask, 0)
    if value <= 0 or value & (value - 1):
        return -1
    return value.bit_length() - 1


def parse_params(read_body: str) -> list[dict[str, str]]:
    params: list[dict[str, str]] = []
    seen: set[str] = set()

    # The flags integer itself is a TL flags field.
    if re.search(r"\bflags\s*=\s*stream\.readInt32\s*\(", read_body):
        params.append({"name": "flags", "type": "#"})
        seen.add("flags")

    lines = read_body.splitlines()
    active_bit: int | None = None
    for line in lines:
        flag = FLAG_IF_RE.search(line)
        if flag:
            active_bit = mask_to_bit(flag.group("mask"))
        tl = ASSIGN_TL_RE.search(line)
        read = ASSIGN_READ_RE.search(line)
        vector = ASSIGN_VECTOR_RE.search(line)
        if tl:
            name = tl.group("field")
            typ = tl.group("type").split(".")[-1]
        elif read:
            name = read.group("field")
            typ = TYPE_READERS.get(read.group("reader"))
            if typ is None:
                continue
        elif vector:
            name = vector.group("field")
            cast = CAST_VECTOR_RE.search(line)
            typ = f"Vector<{cast.group('type').split('.')[-1] if cast else 'Object'}>"
        else:
            continue
        if name in seen:
            continue
        if active_bit is not None and active_bit >= 0:
            typ = f"flags.{active_bit}?{typ}"
        params.append({"name": name, "type": typ})
        seen.add(name)
        # One-line if blocks are common in generated code.
        if "}" in line:
            active_bit = None

    return params


def parse_method_params(class_body: str) -> list[dict[str, str]]:
    fields = {m.group("name"): m.group("type") for m in FIELD_RE.finditer(class_body)}
    body = extract_method_body(class_body, "serializeToStream") or ""
    params: list[dict[str, str]] = []
    seen: set[str] = set()
    active_bit: int | None = None

    for line in body.splitlines():
        flag = FLAG_IF_RE.search(line)
        if flag:
            active_bit = mask_to_bit(flag.group("mask"))

        match = WRITE_RE.search(line)
        if match:
            field = match.group("field")
            if field not in fields or field == "constructor" or field in seen:
                if "}" in line:
                    active_bit = None
                continue
            writer = match.group("writer")
            type_map = {
                "writeInt32": "# " if field == "flags" else "int",
                "writeInt64": "long",
                "writeDouble": "double",
                "writeString": "string",
                "writeByteBuffer": "bytes",
                "writeByteArray": "bytes",
                "writeBool": "Bool",
            }
            typ = type_map[writer].strip()
            if field == "flags":
                typ = "#"
            elif active_bit is not None and active_bit >= 0:
                typ = f"flags.{active_bit}?{typ}"
            params.append({"name": field, "type": typ})
            seen.add(field)

        obj = OBJECT_WRITE_RE.search(line)
        if obj:
            field = obj.group("field")
            if field in fields and field not in seen:
                typ = fields[field].split(".")[-1]
                if active_bit is not None and active_bit >= 0:
                    typ = f"flags.{active_bit}?{typ}"
                params.append({"name": field, "type": typ})
                seen.add(field)

        if "}" in line:
            active_bit = None

    return params

def infer_return_type(body: str) -> str | None:
    match = RETURN_TL_RE.search(body)
    if match:
        return match.group(1).split(".")[-1]
    match = RETURN_READ_RE.search(body)
    if match:
        return TYPE_READERS.get(match.group(1))
    return None


def extract_layer_from_java(text: str, source_name: str = "") -> int | None:
    """Extract the Android API layer from JADX output."""
    preferred = Path(source_name).name == "TLRPC.java"
    candidates: list[tuple[tuple[int, int], int]] = []
    for index, pattern in enumerate(LAYER_PATTERNS):
        match = pattern.search(text)
        if match:
            value = int(match.group("value"))
            if 200 <= value <= 400:
                candidates.append(((0 if preferred else 1, index), value))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def parse_java_source(text: str, source_name: str) -> tuple[list[dict[str, Any]], int | None]:
    definitions: list[dict[str, Any]] = []
    layer = extract_layer_from_java(text, source_name)

    for match in CLASS_RE.finditer(text):
        name = match.group("name")
        extends = match.group("extends") or ""
        # The TLRPC/TL_* container classes themselves can contain generated
        # nested classes. Only classes with an extends clause can be TL objects. Restrict the
        # search to this class body so an outer container class cannot steal the
        # constructor of its first nested TL class.
        brace = text.find("{", match.end())
        if not extends or brace < 0:
            continue
        try:
            body = balanced_block(text, brace)
        except ValueError:
            continue
        constructor = CONSTRUCTOR_RE.search(body)
        if not constructor:
            continue
        cid = int(constructor.group("id"), 0)
        is_method = (
            "deserializeResponse(" in body or "deserializeResponseT(" in body
        )
        read_body = (
            extract_method_body(body, "readParams")
            or extract_method_body(body, "readParamsT")
            or ""
        )
        if is_method and not read_body:
            read_body = extract_method_body(body, "serializeToStream") or ""
        params = parse_method_params(body) if is_method else parse_params(read_body)
        if is_method:
            response_body = (
                extract_method_body(body, "deserializeResponse")
                or extract_method_body(body, "deserializeResponseT")
                or ""
            )
            result = infer_return_type(response_body)
            if not result:
                continue
            definitions.append({
                "kind": "method",
                "name": name,
                "id": cid,
                "result": result,
                "params": params,
                "source": source_name,
            })
        else:
            extends = match.group("extends") or ""
            result = extends.split(".")[-1].split("<")[0]
            if not result or result in {"TLObject", "TLMethod"}:
                continue
            definitions.append({
                "kind": "constructor",
                "name": name,
                "id": cid,
                "type": result,
                "params": params,
                "source": source_name,
            })
    return definitions, layer


def to_tl(definitions: list[dict[str, Any]], layer: int | None) -> str:
    constructors = [x for x in definitions if x["kind"] == "constructor"]
    methods = [x for x in definitions if x["kind"] == "method"]
    lines = [
        "///////////////////////////////",
        "// Telegram Android API",
        "///////////////////////////////",
        "",
        "// This file is auto-generated by Telegram Developer Crawler",
        "",
        "---types---",
    ]
    for item in sorted(constructors, key=lambda x: (x["name"], x["id"])):
        params = " ".join(f"{p['name']}:{p['type']}" for p in item["params"])
        suffix = f" {params}" if params else ""
        lines.append(f"{item['name']}#{item['id'] & 0xffffffff:08x}{suffix} = {item['type']};")
    lines.extend(["", "---functions---"])
    for item in sorted(methods, key=lambda x: (x["name"], x["id"])):
        params = " ".join(f"{p['name']}:{p['type']}" for p in item["params"])
        suffix = f" {params}" if params else ""
        lines.append(f"{item['name']}#{item['id'] & 0xffffffff:08x}{suffix} = {item['result']};")
    lines.extend(["", f"// LAYER {layer if layer is not None else 'UNKNOWN'}"])
    return normalize_tl("\n".join(lines))


def find_previous(channel: str) -> dict[str, Any] | None:
    path = DATA_ROOT / channel / "tl.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def download_file(url: str, destination: Path, attempts: int = 5) -> None:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with httpx.Client(timeout=180.0, follow_redirects=True) as client:
                with client.stream(
                    "GET",
                    url,
                    params={"tdcNoCache": os.urandom(8).hex()} if "telegram.org/dl/" in url else None,
                    headers={"User-Agent": "Telegram-Developer-Crawler/0.1"},
                ) as r:
                    if r.status_code >= 500:
                        r.raise_for_status()
                    r.raise_for_status()
                    with destination.open("wb") as f:
                        for chunk in r.iter_bytes():
                            f.write(chunk)
            return
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code < 500 or attempt == attempts:
                raise
            last_error = exc
        except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError) as exc:
            if attempt == attempts:
                raise
            last_error = exc
        import time
        time.sleep(min(2 ** (attempt - 1), 8))
    raise RuntimeError(f"download failed: {last_error}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_jadx(jadx_bin: Path, apk: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(jadx_bin), "-r", "-j", str(max(1, min(os.cpu_count() or 2, 4))),
        "--no-imports", "--show-bad-code", "--no-inline-anonymous",
        "--comments-level", "none",
        "-d", str(output), str(apk),
    ]
    process = subprocess.run(cmd, text=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=1200, check=False)
    if process.returncode != 0:
        # JADX may return nonzero when unrelated classes fail to decompile.
        # The reference extractor continues and validates the extracted TL set.
        if not output.exists() or not any(output.rglob("TLRPC*.java")):
            raise RuntimeError(
                f"jadx failed ({process.returncode}) without usable tgnet output:\n"
                f"{process.stdout[-6000:]}"
            )


def extract_channel(channel: str, jadx_bin: Path) -> dict[str, Any]:
    metadata_path = DATA_ROOT / channel / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    apk_url = metadata["source_url"]
    with tempfile.TemporaryDirectory(prefix=f"tdc-android-tl-{channel}-") as temp:
        root = Path(temp)
        apk = root / "app.apk"
        sources = root / "jadx"
        download_file(apk_url, apk)
        actual_sha256 = sha256_file(apk)
        expected_sha256 = metadata["artifact"]["sha256"]
        if actual_sha256 != expected_sha256:
            raise RuntimeError(
                f"{channel} APK changed between Module 5A and 5B: "
                f"expected {expected_sha256}, got {actual_sha256}"
            )
        run_jadx(jadx_bin, apk, sources)

        package_root = sources / "sources" / Path(*PACKAGE_PREFIX.split("."))
        if not package_root.exists():
            # JADX may place sources directly under the output directory.
            package_root = sources / Path(*PACKAGE_PREFIX.split("."))
        java_files = sorted(package_root.rglob("*.java")) if package_root.exists() else []
        if not java_files:
            raise RuntimeError(f"JADX produced no {PACKAGE_PREFIX} Java sources")

        definitions: list[dict[str, Any]] = []
        layer: int | None = None
        for java_file in java_files:
            parsed, found_layer = parse_java_source(
                java_file.read_text(encoding="utf-8", errors="replace"),
                java_file.relative_to(sources).as_posix(),
            )
            definitions.extend(parsed)
            if layer is None and found_layer is not None:
                layer = found_layer

    # The Android package contains historical TL classes for compatibility.
    # Canonicalize only after the layer has been discovered so _layerNNN/_old
    # classes can be filtered consistently against the current layer.
    canonical_candidates: list[tuple[dict[str, Any], bool]] = []
    for definition in definitions:
        canonical = canonicalize_definition(definition, layer)
        if canonical is None:
            continue
        _, _, historical = canonical_name(definition["name"])
        canonical_candidates.append((canonical, historical))

    # If Android ships both a canonical class and a generated historical
    # _layerNNN/_old variant with the same TL name, prefer the canonical class.
    by_name: dict[tuple[str, str], list[tuple[dict[str, Any], bool]]] = {}
    for item, historical in canonical_candidates:
        by_name.setdefault((item["kind"], item["name"]), []).append((item, historical))

    canonical_definitions: list[dict[str, Any]] = []
    for key, candidates in by_name.items():
        candidates.sort(key=lambda pair: (pair[1], pair[0]["id"]))
        chosen = candidates[0][0]
        if any(item["id"] != chosen["id"] for item, _ in candidates[1:]):
            raise ValueError(f"Android TL canonicalization found conflicting IDs for {key[1]}")
        canonical_definitions.append(chosen)

    names = [definition_key(x) for x in canonical_definitions]
    if len(names) != len(set(names)):
        raise ValueError("Android TL canonicalization produced duplicate definition keys")

    definitions = canonical_definitions
    constructors = [x for x in definitions if x["kind"] == "constructor"]
    methods = [x for x in definitions if x["kind"] == "method"]
    if len(constructors) < MIN_CONSTRUCTORS or len(methods) < MIN_METHODS:
        raise ValueError(
            f"Android TL extraction is implausibly small: "
            f"{len(constructors)} constructors, {len(methods)} methods"
        )

    previous = find_previous(channel)
    validate_definition_safety(previous, definitions)

    tl = to_tl(definitions, layer)
    payload = {
        "layer": layer,
        "constructors": constructors,
        "methods": methods,
        "counts": {
            "constructors": len(constructors),
            "methods": len(methods),
            "total": len(definitions),
        },
        "sha256": {"tl": sha256_text(tl)},
        "safety": {"max_definition_removal_ratio": MAX_REMOVAL_RATIO},
        "source": {
            "apk": metadata["resolved_url"],
            "apk_sha256": metadata["artifact"]["sha256"],
            "package": metadata["android"]["package"],
            "version_name": metadata["android"]["version_name"],
            "version_code": metadata["android"]["version_code"],
            "jadx": JADX_URL,
        },
    }
    output = DATA_ROOT / channel
    output.mkdir(parents=True, exist_ok=True)
    (output / "tl.tl").write_text(tl, encoding="utf-8")
    (output / "tl.json").write_text(render_json(payload), encoding="utf-8")
    metadata["tl_extraction"] = {
        "stage": "5B",
        "layer": layer,
        "counts": payload["counts"],
        "tl": "tl.tl",
        "json": "tl.json",
        "sha256": payload["sha256"]["tl"],
        "jadx": JADX_URL,
        "target_package": PACKAGE_PREFIX,
    }
    metadata_path.write_text(render_json(metadata), encoding="utf-8")
    return payload


def collect() -> None:
    with tempfile.TemporaryDirectory(prefix="tdc-jadx-") as temp:
        root = Path(temp)
        archive = root / "jadx.zip"
        download_file(JADX_URL, archive)
        unpack = root / "jadx"
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(unpack)
        bins = [
            path for path in unpack.rglob("jadx")
            if path.is_file() and path.parent.name == "bin"
        ] + [
            path for path in unpack.rglob("jadx.bat")
            if path.is_file() and path.parent.name == "bin"
        ]
        if not bins:
            raise RuntimeError("JADX archive contains no executable bin/jadx")
        jadx_bin = bins[0]
        if jadx_bin.suffix != ".bat":
            jadx_bin.chmod(0o755)

        results = {channel: extract_channel(channel, jadx_bin) for channel in ("stable", "beta")}

    combined = {
        "stage": "5B",
        "channels": {
            channel: {
                "layer": result["layer"],
                "counts": result["counts"],
                "tl": f"{channel}/tl.tl",
                "json": f"{channel}/tl.json",
                "sha256": result["sha256"]["tl"],
            }
            for channel, result in results.items()
        },
        "source": {"package": PACKAGE_PREFIX, "jadx": JADX_URL},
        "safety": {"max_definition_removal_ratio": MAX_REMOVAL_RATIO},
    }
    (DATA_ROOT / "metadata.json").write_text(render_json(combined), encoding="utf-8")


if __name__ == "__main__":
    collect()
