"""Classify generated data changes and render a credited Stage 5C changelog."""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import html
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from crawler.credits import credit_diff, with_markdown_credit

DATA_BRANCH = "data"
SNAPSHOT_ROOT = Path("data")
DEF_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9_.]+)#(?P<id>[0-9a-fA-F]+).*?=\s*(?P<rhs>[^;]+);\s*$"
)


def run(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], text=True, stderr=subprocess.DEVNULL
    )


def base_files(base: str) -> set[str]:
    """Return normalized archive paths from both current and legacy data layouts."""
    raw = run("ls-tree", "-r", "--name-only", base).splitlines()
    result = set()
    for path in raw:
        if path.startswith("data/"):
            result.add(path.removeprefix("data/"))
        elif path not in {"README.md", ".gitignore"}:
            result.add(path)
    return result


def current_files() -> set[str]:
    if not SNAPSHOT_ROOT.exists():
        return set()
    return {
        str(p.relative_to(SNAPSHOT_ROOT))
        for p in SNAPSHOT_ROOT.rglob("*")
        if p.is_file()
    }


def changed_files(base: str):
    old_files, new_files = base_files(base), current_files()
    for path in sorted(old_files | new_files):
        old_exists = path in old_files
        new_exists = path in new_files
        if old_exists and new_exists:
            status = "M"
        elif new_exists:
            status = "A"
        else:
            status = "D"
        yield status, path


def read_base(base: str, path: str) -> str | None:
    """Read a base snapshot, supporting the previous data/<path> layout."""
    for candidate in (path, f"data/{path}"):
        try:
            return run("show", f"{base}:{candidate}")
        except subprocess.CalledProcessError:
            pass
    return None


def read_current(path: str) -> str | None:
    p = SNAPSHOT_ROOT / path
    return p.read_text(encoding="utf-8") if p.exists() else None


def parse_tl(text: str | None) -> dict[str, str]:
    result = {}
    for line in (text or "").splitlines():
        m = DEF_RE.match(line)
        if m:
            result[f"{m.group('name')}#{m.group('id').lower()}"] = line.strip()
    return result


def flatten(value: Any, prefix=""):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
        return out
    if isinstance(value, list):
        out = {}
        for i, v in enumerate(value):
            out.update(flatten(v, f"{prefix}[{i}]"))
        return out
    return {prefix: value}


def parse_json(text):
    try:
        return json.loads(text) if text else None
    except json.JSONDecodeError:
        return None



NOTIFICATION_IGNORED_JSON_PATHS = {
    # APK identity/transport metadata is useful in the archive, but changing
    # hashes, CDN URLs and extraction hashes are not developer-facing changes.
    "TgAndroid/{channel}/metadata.json": {
        "artifact.sha256", "artifact.size", "resolved_url", "tl_extraction.sha256",
    },
    # Runtime MTProto values can change while the developer-facing config is
    # unchanged. Keep them in data, but suppress them from channel alerts.
    "mtproto/configs/{environment}/{dc}/config.json": {
        "date", "expires", "access_hash", "file_reference",
    },
    # Premium promo payloads contain Telegram media objects whose file
    # references/bytes rotate without changing the developer-facing promo.
    "mtproto/global/premium-promo.json": {
        "file_reference", "access_hash",
    },
}


def notification_ignored_paths(path: str) -> set[str]:
    for pattern, fields in NOTIFICATION_IGNORED_JSON_PATHS.items():
        regex = re.escape(pattern).replace(r"\{channel\}", r"[^/]+").replace(
            r"\{environment\}", r"[^/]+"
        ).replace(r"\{dc\}", r"[^/]+")
        if re.fullmatch(regex, path):
            return set(fields)
    return set()


def remove_json_paths(value: Any, ignored: set[str], prefix: str = "") -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else key
            # Ignore an explicitly configured field and nested occurrences of
            # volatile MTProto object fields such as file_reference.
            if path in ignored or key in {"__bytes__"} and "file_reference" in prefix:
                continue
            out[key] = remove_json_paths(item, ignored, path)
        return out
    if isinstance(value, list):
        return [remove_json_paths(item, ignored, f"{prefix}[{i}]") for i, item in enumerate(value)]
    return value


def semantic_json_for_notification(path: str, old_text: str | None, new_text: str | None):
    old, new = parse_json(old_text), parse_json(new_text)
    if old is None or new is None:
        return semantic_json(old_text, new_text)
    ignored = notification_ignored_paths(path)
    if ignored:
        old = remove_json_paths(old, ignored)
        new = remove_json_paths(new, ignored)
    return semantic_json(
        json.dumps(old, ensure_ascii=False, sort_keys=True),
        json.dumps(new, ensure_ascii=False, sort_keys=True),
    )


def semantic_json(old_text, new_text):
    old, new = parse_json(old_text), parse_json(new_text)
    if old is None or new is None:
        return [], [], []

    def schema_map(v):
        out = {}
        if not isinstance(v, dict):
            return out
        for kind, field in (("constructor", "constructors"), ("method", "methods")):
            items = v.get(field, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        name = item.get("predicate") or item.get("method") or item.get("name")
                        ident = item.get("id")
                        if name is not None and ident is not None:
                            out[f"{kind}:{ident}:{name}"] = item
        return out

    om, nm = schema_map(old), schema_map(new)
    if om or nm:
        keys = sorted(set(om) | set(nm))
        return (
            [k for k in keys if k not in om],
            [k for k in keys if k in om and k in nm and om[k] != nm[k]],
            [k for k in keys if k not in nm],
        )

    of, nf = flatten(old), flatten(new)
    keys = sorted(set(of) | set(nf))
    return (
        [k for k in keys if k not in of],
        [k for k in keys if k in of and k in nf and of[k] != nf[k]],
        [k for k in keys if k not in nf],
    )


def semantic_tl(old, new):
    o, n = parse_tl(old), parse_tl(new)
    keys = sorted(set(o) | set(n))
    return (
        [k for k in keys if k not in o],
        [k for k in keys if k in o and k in n and o[k] != n[k]],
        [k for k in keys if k not in n],
    )


def module_for(path):
    path = path.removeprefix("data/")
    if path.startswith(("mtproto/configs/", "mtproto/app-config/",
                        "mtproto/countries-list/", "mtproto/global/")):
        return "MTProto configuration"
    if path.startswith("mtproto/tl/"):
        return "MTProto/TL schema"
    if path.startswith("tdlib/tl/"):
        return "TDLib"
    if path.startswith("tdesktop/tl/"):
        return "Telegram Desktop"
    if path.startswith("TgAndroid/tl/stable/"):
        return "Android Stable"
    if path.startswith("TgAndroid/tl/beta/"):
        return "Android Preview"
    if path.startswith("TgAndroid/"):
        return "Android client"
    return "Other"


def classify(base):
    groups = {}
    for status, path in changed_files(base):
        old, new = read_base(base, path), read_current(path)
        if path.endswith(".tl"):
            a, c, d = semantic_tl(old, new)
        elif path.endswith(".json"):
            a, c, d = semantic_json_for_notification(path, old, new)
        else:
            ol, nl = set((old or "").splitlines()), set((new or "").splitlines())
            a, c, d = sorted(nl - ol), [], sorted(ol - nl)

        module = module_for(path)
        g = groups.setdefault(
            module, {"files": [], "additions": 0, "changes": 0, "deletions": 0}
        )
        entry = {
            "path": path,
            "status": status,
            "additions": a[:200],
            "changes": c[:200],
            "deletions": d[:200],
        }
        g["files"].append(entry)
        g["additions"] += len(a)
        g["changes"] += len(c)
        g["deletions"] += len(d)

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "groups": groups,
    }


def credited_unified_diff(base: str) -> str:
    chunks = []
    for status, path in changed_files(base):
        old = read_base(base, path) or ""
        new = read_current(path) or ""
        if old == new:
            continue
        diff = difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"data/{path} (previous)",
            tofile=f"data/{path} (current)",
            n=3,
        )
        chunks.append("".join(diff).rstrip("\n"))
    return credit_diff("\n".join(chunks))


def render_markdown(summary, base):
    lines = [
        "# Telegram Developer Crawler — Change Report",
        "",
        f"Base snapshot: {base}",
        "",
    ]
    for module, g in summary["groups"].items():
        lines += [f"## {module}", ""]
        for e in g["files"]:
            lines += [f"### {e['path']}", ""]
            for title, key in (
                ("Additions", "additions"),
                ("Changes", "changes"),
                ("Deletions", "deletions"),
            ):
                if e[key]:
                    lines.append(f"**{title}**")
                    lines += [f"- {x}" for x in e[key]]
                    lines.append("")
    diff = credited_unified_diff(base)
    lines += ["## Credited unified diff", "", "DIFF START", diff, "DIFF END"]
    return with_markdown_credit("\n".join(lines))


def android_info(channel):
    meta = parse_json(read_current(f"TgAndroid/{channel}/metadata.json")) or {}
    schema = parse_json(read_current(f"TgAndroid/tl/{channel}/main_api.json")) or {}
    android = meta.get("android", {}) if isinstance(meta, dict) else {}
    return android.get("version_name"), android.get("version_code"), schema.get("layer")


def android_previous_info(base, channel):
    meta = parse_json(read_base(base, f"TgAndroid/{channel}/metadata.json")) or {}
    schema = parse_json(read_base(base, f"TgAndroid/tl/{channel}/main_api.json")) or {}
    android = meta.get("android", {}) if isinstance(meta, dict) else {}
    return android.get("version_name"), android.get("version_code"), schema.get("layer")



def notification(summary, base):
    """Render only developer-meaningful changes; volatile metadata stays silent."""
    meaningful = []
    for module, group in summary["groups"].items():
        files = []
        for entry in group["files"]:
            old, new = read_base(base, entry["path"]), read_current(entry["path"])
            if entry["path"].endswith(".json"):
                added, changed, deleted = semantic_json_for_notification(entry["path"], old, new)
            elif entry["path"].endswith(".tl"):
                added, changed, deleted = semantic_tl(old, new)
            else:
                old_lines = set((old or "").splitlines())
                new_lines = set((new or "").splitlines())
                added, changed, deleted = sorted(new_lines - old_lines), [], sorted(old_lines - new_lines)
            if added or changed or deleted:
                files.append((entry, len(added), len(changed), len(deleted)))
        if files:
            meaningful.append((module, files))

    if not meaningful:
        return ""

    sections = [
        "<h2>📣 Developer data changed</h2>",
        "<p>A new Telegram developer-data snapshot contains meaningful changes.</p>",
    ]

    for module, files in meaningful:
        additions = sum(a for _, a, _, _ in files)
        changes = sum(c for _, _, c, _ in files)
        deletions = sum(d for _, _, _, d in files)
        sections.append(f"<h3>📦 {html.escape(module)}</h3>")
        items = [
            f"➕ Added: <b>{additions}</b>",
            f"✏️ Changed: <b>{changes}</b>",
            f"➖ Removed: <b>{deletions}</b>",
            f"📄 Files: <b>{len(files)}</b>",
        ]

        if module in ("Android Stable", "Android Preview"):
            channel = "stable" if module == "Android Stable" else "beta"
            version, build, layer = android_info(channel)
            old_version, old_build, _ = android_previous_info(base, channel)
            label = "Stable" if channel == "stable" else "Preview"
            if version:
                items.insert(
                    0,
                    f"📱 {label}: <code>{html.escape(str(version))}</code> "
                    f"• Build <code>{html.escape(str(build or '—'))}</code>",
                )
            if layer:
                items.insert(1 if version else 0, f"🧩 Layer: <code>{html.escape(str(layer))}</code>")
            if version and version == old_version and build != old_build:
                items.append("🏷️ <b>#Patch</b>")
            items.append(f"#Android #{label}")

        sections.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")

    return "<hr/>".join(sections)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default=DATA_BRANCH)
    p.add_argument("--output", required=True)
    p.add_argument("--json", required=True)
    p.add_argument("--notification")
    a = p.parse_args()

    s = classify(a.base)
    Path(a.output).write_text(render_markdown(s, a.base), encoding="utf-8")
    Path(a.json).write_text(
        json.dumps(s, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if a.notification:
        Path(a.notification).write_text(notification(s, a.base), encoding="utf-8")
    print(json.dumps({"files": sum(len(g["files"]) for g in s["groups"].values()),
                      "groups": list(s["groups"])}))


if __name__ == "__main__":
    main()
