#!/usr/bin/env python3
"""Read hooks: serve a file's memory instead of the whole file when it is big.

PreToolUse(Read)
    A full (un-ranged) Read of a project file larger than `max_bytes` is
    denied, and the deny reason - which Claude sees as the tool result -
    carries the file's memory: an OKF concept at
    `<memory_dir>/<path/to/file.ext>.md` holding a structural outline with
    line numbers. The memory is generated when missing and regenerated when
    the source hash no longer matches, so a stale outline (wrong line
    numbers) is never served. Claude then reads only the ranges it needs.

    Never intercepted: ranged reads (`offset` or `limit` set - this is the
    escape hatch, including for a deliberate full read), files at or under
    the limit, binary files, files outside the project root, files inside the
    memory dir, and files whose memory would not be meaningfully smaller than
    the file itself.

PostToolUse(Read|Edit|Write|MultiEdit)
    Refreshes an existing memory whose source changed. Never creates one:
    memories are created lazily, on the first oversized read.

A memory's `# Notes` section is hand-written (by people or by Claude) and is
preserved verbatim across regeneration; everything above it is generated.

Design constraints (shared with every hook in this marketplace):
  * No network.
  * Never raises: any failure means "allow the Read", never "block it".
  * Silent when there is nothing to say.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import outline as outline_mod  # noqa: E402

DEFAULT_MAX_BYTES = 20000
DEFAULT_MEMORY_DIR = ".memory"
# Serve the memory only when it is at most this fraction of the source size.
MAX_MEMORY_RATIO = 0.5
NOTES_HEADING = "# Notes"
NOTES_PLACEHOLDER = (
    f"{NOTES_HEADING}\n\n"
    "<!-- Hand-written. Everything from this heading down survives regeneration. -->\n"
)
BINARY_EXTS = {
    "png", "jpg", "jpeg", "gif", "webp", "bmp", "ico", "svgz", "pdf", "ipynb",
    "zip", "gz", "tgz", "bz2", "xz", "7z", "jar", "war", "whl", "so", "dylib",
    "dll", "exe", "bin", "o", "a", "class", "pyc", "wasm", "mp3", "mp4", "mov",
    "wav", "ogg", "woff", "woff2", "ttf", "otf", "sqlite", "db", "parquet",
}
SKIP_DIRS = {".git", ".hg", ".svn"}


def option(key: str, default: str = "") -> str:
    """Read a userConfig value, exported to hooks as CLAUDE_PLUGIN_OPTION_<KEY>."""
    return os.environ.get(f"CLAUDE_PLUGIN_OPTION_{key.upper()}", default).strip()


def max_bytes() -> int:
    try:
        return int(float(option("max_bytes", str(DEFAULT_MAX_BYTES))))
    except ValueError:
        return DEFAULT_MAX_BYTES


def project_root(payload: dict) -> Path:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or "."
    return Path(root).expanduser().resolve()


def memory_root(root: Path) -> Path:
    return (root / (option("memory_dir", DEFAULT_MEMORY_DIR) or DEFAULT_MEMORY_DIR)).resolve()


def memory_path(root: Path, source: Path) -> Path | None:
    """`<memory_dir>/<rel/path/file.ext>.md`, or None when `source` is out of scope.

    The source extension is kept (`app.py.md`, not `app.md`) so `app.py` and
    `app.js` in the same directory never share a memory.
    """
    try:
        rel = source.relative_to(root)
    except ValueError:
        return None  # outside the project: nowhere to keep its memory
    mem_root = memory_root(root)
    if source == mem_root or mem_root in source.parents:
        return None  # never take memories of memories
    if SKIP_DIRS & set(rel.parts):
        return None
    return mem_root / rel.parent / (rel.name + ".md")


def resolve_source(payload: dict, root: Path) -> Path | None:
    raw = (payload.get("tool_input") or {}).get("file_path")
    if not raw or not isinstance(raw, str):
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path(payload.get("cwd") or root) / path
    path = path.resolve()
    return path if path.is_file() else None


def is_binary(path: Path, head: bytes) -> bool:
    return path.suffix.lower().lstrip(".") in BINARY_EXTS or b"\0" in head[:8192]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_frontmatter(text: str) -> dict:
    """Flat `key: value` frontmatter only - enough for the keys this hook writes."""
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    meta = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith(" "):
            meta[key.strip()] = value.strip().strip('"')
    return meta


def notes_section(existing: str) -> str:
    for marker in (f"\n{NOTES_HEADING}\n", f"\n{NOTES_HEADING}\r\n"):
        idx = existing.find(marker)
        if idx >= 0:
            return existing[idx + 1:]
    return NOTES_PLACEHOLDER


def _yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)  # a JSON string is a valid YAML scalar


def build_memory(rel: str, source: Path, data: bytes, notes: str) -> str:
    text = data.decode("utf-8", errors="replace")
    n_lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
    lang = outline_mod.language(source)
    method, entries = outline_mod.outline(source, text)
    dropped = max(0, len(entries) - outline_mod.MAX_ENTRIES)
    entries = entries[: outline_mod.MAX_ENTRIES]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    parts = [
        "---",
        "type: Source Memory",
        f"title: {_yaml_str(rel)}",
        f"description: {_yaml_str(f'Structural outline of {rel} ({lang}, {n_lines} lines).')}",
        f"resource: {_yaml_str(rel)}",
        "tags: [okf-memory]",
        f"generated: {{ by: okf-memory, at: {now} }}",
        f"source_sha256: {sha256(data)}",
        f"source_bytes: {len(data)}",
        f"source_lines: {n_lines}",
        f"outline_entries: {len(entries)}",
        "---",
        "",
        "# Outline",
        "",
        f"Language: {lang}. Method: {method}. Line numbers are 1-based.",
        "",
    ]
    if entries:
        parts += ["```text", *entries, "```"]
        if dropped:
            parts += ["", f"… {dropped} more entries omitted; use Grep on the source."]
    else:
        parts.append("No outline available for this file; use Grep, or Read with offset/limit.")
    parts.append("")
    return "\n".join(parts) + "\n" + notes


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def ensure_memory(root: Path, source: Path, mem: Path, data: bytes, create: bool) -> str | None:
    """Return up-to-date memory text, (re)writing it if missing or stale.

    With `create=False`, a missing memory stays missing and None is returned.
    """
    existing = mem.read_text(encoding="utf-8", errors="replace") if mem.is_file() else None
    if existing is None and not create:
        return None
    if existing is not None and read_frontmatter(existing).get("source_sha256") == sha256(data):
        return existing
    rel = source.relative_to(root).as_posix()
    content = build_memory(rel, source, data, notes_section(existing or ""))
    write_atomic(mem, content)
    return content


def pre_read(payload: dict) -> dict | None:
    tool_input = payload.get("tool_input") or {}
    if tool_input.get("offset") is not None or tool_input.get("limit") is not None:
        return None  # ranged read: the reader already knows what it wants
    root = project_root(payload)
    source = resolve_source(payload, root)
    if source is None:
        return None
    mem = memory_path(root, source)
    if mem is None:
        return None
    size = source.stat().st_size
    limit = max_bytes()
    if limit <= 0 or size <= limit:
        return None
    data = source.read_bytes()
    if is_binary(source, data):
        return None
    content = ensure_memory(root, source, mem, data, create=True)
    if not content or read_frontmatter(content).get("outline_entries", "0") == "0":
        return None  # no structure to navigate by: the deny would only add a round trip
    if len(content.encode("utf-8")) > size * MAX_MEMORY_RATIO:
        return None  # the memory would not save enough to justify a round trip
    rel = source.relative_to(root).as_posix()
    mem_rel = mem.relative_to(root).as_posix() if root in mem.parents else str(mem)
    reason = (
        f"okf-memory: `{rel}` is {size:,} bytes, over the {limit:,}-byte full-read limit, "
        f"so its memory (`{mem_rel}`) is served instead of the file.\n"
        "Read only the ranges you need with Read `offset`/`limit` - ranged reads are never "
        "intercepted (a ranged read also covers the whole file when you really need it). "
        f"Durable facts about this file can be added under `{NOTES_HEADING}` in the memory; "
        "that section survives regeneration.\n\n"
        f"{content}"
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def post_tool(payload: dict) -> None:
    root = project_root(payload)
    source = resolve_source(payload, root)
    if source is None:
        return
    mem = memory_path(root, source)
    if mem is None or not mem.is_file():
        return
    data = source.read_bytes()
    if is_binary(source, data):
        return
    ensure_memory(root, source, mem, data, create=False)


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        event = payload.get("hook_event_name")
        if event == "PreToolUse" and payload.get("tool_name") == "Read":
            out = pre_read(payload)
            if out:
                print(json.dumps(out))
        elif event == "PostToolUse":
            post_tool(payload)
    except Exception as exc:  # a broken hook must fail open: let the Read through
        print(f"okf-memory: hook failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
