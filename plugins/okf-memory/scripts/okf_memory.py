#!/usr/bin/env python3
"""Read hooks: show Claude a file's memory instead of a big file's content.

PostToolUse(Read)
    After a full (un-ranged) Read of a project file larger than `max_bytes`,
    the result Claude sees is replaced (`updatedToolOutput`) by the file's
    memory: an OKF concept at `<memory_dir>/<path/to/file.ext>.md` holding a
    structural outline with source line numbers. The Read itself ran, so it
    still counts as "read" for Edit; Claude then reads only the ranges it
    needs. The memory is generated when missing and regenerated when the
    source hash no longer matches, so a stale outline is never served.

    Never replaced: ranged reads (`offset` or `limit` set - the escape hatch,
    including for a deliberate full read), files at or under the limit,
    binary files, files outside the project root, files inside the memory
    dir, files no outline could be built for, and files whose memory would
    not be meaningfully smaller than the file itself.

PostToolUseFailure(Read)
    A full Read that failed - usually a file over Read's own size cap - gets
    the memory attached as `additionalContext` next to the error.

PostToolUse(Edit|Write|MultiEdit), and ranged Reads
    Refresh an existing memory whose source changed. Never create one.

The memory dir is an OKF bundle: every time a memory is created or
regenerated, the bundle-root `index.md` gets an entry for it (created with
`okf_version` when missing) and the bundle-root `log.md` an entry under
today's date.

A memory's `# Notes` section is hand-written (by people or by Claude) and is
preserved verbatim across regeneration; everything above it is generated.

Design constraints (shared with every hook in this marketplace):
  * No network. tree-sitter grammars are used only if already cached.
  * Never raises: any failure means Claude sees the tool's own result.
  * Silent when there is nothing to say.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

try:
    import fcntl
except ImportError:  # Windows: index/log updates go unlocked
    fcntl = None

sys.path.insert(0, str(Path(__file__).resolve().parent))

import outline as outline_mod  # noqa: E402

PRODUCER = "okf-memory/0.1.0"  # OKF actor `<producer>/<version>`; keep in step with plugin.json
OKF_VERSION = "0.2"
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
# `<name>.md` is reserved at every level of an OKF bundle, so a source with
# one of these exact names cannot have a memory.
RESERVED_STEMS = {"index", "log"}
INDEX_HEADING = "# Source Memories"
LOG_HEADING = "# Memory Update Log"
LOCK_NAME = ".okf-memory.lock"
DATE_HEADING = re.compile(r"^## \d{4}-\d{2}-\d{2}\s*$")


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
    if SKIP_DIRS & set(rel.parts) or rel.name in RESERVED_STEMS:
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


def build_memory(rel: str, source: Path, mem: Path, data: bytes, notes: str) -> str:
    text = data.decode("utf-8", errors="replace")
    n_lines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
    lang = outline_mod.language(source)
    method, entries = outline_mod.outline(source, text)
    dropped = max(0, len(entries) - outline_mod.MAX_ENTRIES)
    entries = entries[: outline_mod.MAX_ENTRIES]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Relative to the concept itself, so the path resolves as OKF §6 reads it.
    link = Path(os.path.relpath(source, mem.parent)).as_posix()

    parts = [
        "---",
        "type: Source Memory",
        f"title: {_yaml_str(rel)}",
        f"description: {_yaml_str(f'Structural outline of {rel} ({lang}, {n_lines} lines).')}",
        f"resource: {_yaml_str(link)}",
        "tags: [okf-memory]",
        f"sources: [{{ id: source, resource: {_yaml_str(link)}, title: {_yaml_str(rel)} }}]",
        f"generated: {{ by: {PRODUCER}, at: {now} }}",
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


class _BundleLock:
    """Serialize read-modify-write of `index.md`/`log.md` across parallel hooks."""

    def __init__(self, mem_root: Path):
        self.path = mem_root / LOCK_NAME
        self.fh = None

    def __enter__(self):
        if fcntl is not None:
            self.fh = open(self.path, "a")
            fcntl.flock(self.fh, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        if self.fh is not None:
            fcntl.flock(self.fh, fcntl.LOCK_UN)
            self.fh.close()


def _md_link(mem_root: Path, mem: Path, title: str) -> str:
    target = quote(mem.relative_to(mem_root).as_posix(), safe="/")
    label = title.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    return f"[{label}]({target})"


def update_index(mem_root: Path, mem: Path, title: str, description: str) -> None:
    """Upsert the memory's entry in the bundle-root `index.md`.

    Only the lines of the `INDEX_HEADING` section that start with `* [` are
    rewritten (sorted by link); everything else in the file is kept.
    """
    link = _md_link(mem_root, mem, title)
    target = link[link.rindex("](") :]  # "](path)" - the upsert key
    entry = f"* {link} - {description}"
    index = mem_root / "index.md"
    text = index.read_text(encoding="utf-8") if index.is_file() else (
        f'---\nokf_version: "{OKF_VERSION}"\n---\n\n{INDEX_HEADING}\n\n'
    )
    lines = text.splitlines()
    try:
        start = lines.index(INDEX_HEADING)
    except ValueError:
        lines += ([""] if lines and lines[-1] else []) + [INDEX_HEADING, ""]
        start = len(lines) - 2
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("# ")), len(lines))
    section = lines[start + 1 : end]
    entries = [ln for ln in section if ln.startswith("* [") and target not in ln] + [entry]
    entries.sort(key=lambda ln: ln[ln.find("](") :])
    others = [ln for ln in section if not ln.startswith("* [") and ln.strip()]
    body = [""] + others + ([""] if others else []) + entries + [""]
    lines[start + 1 : end] = body
    write_atomic(index, "\n".join(lines).rstrip("\n") + "\n")


def update_log(mem_root: Path, mem: Path, title: str, created: bool) -> None:
    """Add an entry for the memory under today's date in the bundle-root `log.md`.

    Newest first, as OKF §9 lays it out. An identical entry already under
    today's heading is not repeated, so a file edited ten times in a day logs
    one update.
    """
    link = _md_link(mem_root, mem, title)
    entry = (f"* **Creation**: Memory of the source file, {link}." if created
             else f"* **Update**: Regenerated {link} after its source file changed.")
    today = datetime.now(timezone.utc).strftime("## %Y-%m-%d")
    log = mem_root / "log.md"
    text = log.read_text(encoding="utf-8") if log.is_file() else f"{LOG_HEADING}\n"
    lines = text.splitlines()
    first = next((i for i, ln in enumerate(lines) if DATE_HEADING.match(ln)), None)
    if first is not None and lines[first].strip() == today:
        end = next((i for i in range(first + 1, len(lines)) if lines[i].startswith("#")), len(lines))
        if entry in lines[first + 1 : end]:
            return
        lines.insert(first + 1, entry)
    else:
        at = first if first is not None else len(lines)
        block = [today, entry, ""]
        if at == len(lines) and lines and lines[-1]:
            block.insert(0, "")
        lines[at:at] = block
    write_atomic(log, "\n".join(lines).rstrip("\n") + "\n")


def record_in_bundle(mem_root: Path, mem: Path, content: str, created: bool) -> None:
    meta = read_frontmatter(content)
    title = meta.get("title") or mem.name[:-3]
    with _BundleLock(mem_root):
        update_index(mem_root, mem, title, meta.get("description", ""))
        update_log(mem_root, mem, title, created)


def ensure_memory(root: Path, source: Path, mem: Path, data: bytes, create: bool) -> str | None:
    """Return up-to-date memory text, (re)writing it if missing or stale.

    With `create=False`, a missing memory stays missing and None is returned.
    A write also records the memory in the bundle's root `index.md`/`log.md`.
    """
    existing = mem.read_text(encoding="utf-8", errors="replace") if mem.is_file() else None
    if existing is None and not create:
        return None
    if existing is not None and read_frontmatter(existing).get("source_sha256") == sha256(data):
        return existing
    rel = source.relative_to(root).as_posix()
    content = build_memory(rel, source, mem, data, notes_section(existing or ""))
    write_atomic(mem, content)
    record_in_bundle(memory_root(root), mem, content, created=existing is None)
    return content


def is_full_read(payload: dict) -> bool:
    tool_input = payload.get("tool_input") or {}
    return tool_input.get("offset") is None and tool_input.get("limit") is None


def memory_for(payload: dict) -> str | None:
    """The text to show Claude instead of a full Read, or None to leave it alone.

    Creates or refreshes the memory as a side effect.
    """
    if payload.get("tool_name") != "Read" or not is_full_read(payload):
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
        return None  # no structure to navigate by: the full content is the better answer
    if len(content.encode("utf-8")) > size * MAX_MEMORY_RATIO:
        return None  # the memory would not save enough to be worth the indirection
    rel = source.relative_to(root).as_posix()
    mem_rel = mem.relative_to(root).as_posix() if root in mem.parents else str(mem)
    return (
        f"okf-memory: `{rel}` is {size:,} bytes, over the {limit:,}-byte full-read limit, "
        f"so this result is its memory (`{mem_rel}`), not the file content.\n"
        "The `L<n>` entries below are line numbers in the source file; any line-number "
        "margin around this text belongs to the memory itself. Read the ranges you need "
        "with Read `offset`/`limit` - ranged reads always return real content (use one "
        "spanning the whole file when you truly need all of it). "
        f"To find what the outline does not show (a string, a call site, a constant), "
        f"use Grep on `{rel}` with line numbers, then Read only the range around the match. "
        f"Durable facts about this file can be added under `{NOTES_HEADING}` in the memory; "
        "that section survives regeneration.\n\n"
        f"{content}"
    )


def replaced_read_output(tool_response, text: str) -> dict | None:
    """Copy of Read's structured output with the file content swapped for `text`.

    Read returns `{"type": "text", "file": {"content", "numLines", "startLine",
    "totalLines", ...}}`. Only that shape is rewritten: anything else (an image,
    `file_unchanged`, a future schema) is left alone, and Claude Code ignores an
    `updatedToolOutput` that does not match the tool's schema anyway - either
    way the failure mode is "Claude sees the real file", never a broken result.
    """
    if not isinstance(tool_response, dict) or tool_response.get("type") != "text":
        return None
    file = tool_response.get("file")
    if not isinstance(file, dict) or not isinstance(file.get("content"), str):
        return None
    n_lines = text.count("\n") + 1
    new_file = dict(file, content=text, numLines=n_lines, startLine=1, totalLines=n_lines)
    return dict(tool_response, file=new_file)


def post_tool(payload: dict) -> dict | None:
    text = memory_for(payload)
    if text is not None:
        updated = replaced_read_output(payload.get("tool_response"), text)
        if updated is not None:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "updatedToolOutput": updated,
                }
            }
        return None
    # Not a substitution: keep an existing memory current (Edit/Write, ranged Read).
    root = project_root(payload)
    source = resolve_source(payload, root)
    if source is None:
        return None
    mem = memory_path(root, source)
    if mem is None or not mem.is_file():
        return None
    data = source.read_bytes()
    if not is_binary(source, data):
        ensure_memory(root, source, mem, data, create=False)
    return None


def post_failure(payload: dict) -> dict | None:
    """A full Read that failed (typically: file over Read's own size/token cap).

    That is exactly the file a memory helps most with, so attach it as context
    next to the error.
    """
    text = memory_for(payload)
    if text is None:
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUseFailure",
            "additionalContext": text,
        }
    }


HANDLERS = {"PostToolUse": post_tool, "PostToolUseFailure": post_failure}


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        handler = HANDLERS.get(payload.get("hook_event_name"))
        out = handler(payload) if handler else None
        if out:
            print(json.dumps(out))
    except Exception as exc:  # fail open: Claude gets the tool's own result
        print(f"okf-memory: hook failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
