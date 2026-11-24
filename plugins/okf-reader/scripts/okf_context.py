#!/usr/bin/env python3
"""SessionStart hook: inject OKF bundle context into a Claude Code session.

Bundles come from three places:

  * `userConfig` (`CLAUDE_PLUGIN_OPTION_*`) - machine or organization scope.
    Claude Code reads `pluginConfigs` only from user, `--settings` and managed
    settings, never from the workspace, so a cloned repository cannot supply
    these. Suitable for org-wide normative standards.
  * Auto-discovery - project scope, version-controlled, needs no declaration.
    Any directory under the project root whose `index.md` frontmatter
    declares `okf_version` (OKF SPEC §8.1: only a bundle-root `index.md` may
    carry frontmatter) is treated as a bundle root. This is how a repository's own
    knowledge is found: it lives in the tree, so it is discovered from the
    tree.
  * `okf.json` at the project root - project scope, version-controlled,
    external only. It exists to name what discovery cannot see: bundles
    outside the project root, and remote sources (`github:`, `https:`, ...)
    vendored into a cache directory. It is untrusted, since it ships with the
    repository, but its paths are not confined: an entry may point anywhere
    on disk. A bundle already inside the project is discovered automatically
    and must not be re-declared here - such an entry is ignored with a
    warning, so there is exactly one source of truth per bundle.

The hook only lists bundles and points at their `index.md`; it never reads
bundle content, so there is nothing to size-cap.

Design constraints:
  * Never touches the network. Remote bundles must be vendored into the cache
    directory by an explicit sync step.
  * Silent no-op when no bundle is present, so non-OKF projects pay nothing.
  * Never raises. A broken hook must not break session startup.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

CONFIG = "okf.json"

# Auto-discovery: how deep to walk below the project root, and what to skip.
MAX_DEPTH = 4
PRUNE_DIRS = {"node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target", "vendor"}
FALLBACK_DIRS = ["spec", "docs/okf", "knowledge"]

RULES = """\
## How to read OKF bundles

- A link starting with `/` is relative to **its own bundle's root**, not the
  filesystem: `/tables/orders.md` in a bundle at `spec/` means `spec/tables/orders.md`.
  Other links resolve from the linking file's directory; never read outside the bundle
- Concepts are `.md` files with a frontmatter `type`; `index.md` and `log.md` never are
- Traverse via `index.md` files; read concepts on demand, never preload a bundle
- To find a concept by tag, type, description or title, use agent `okf-search` if it is
  available (it ships with okf-core), passing it the bundle table below"""


def option(key: str, default: str = "") -> str:
    """Read a userConfig value, exported to hooks as CLAUDE_PLUGIN_OPTION_<KEY>."""
    return os.environ.get(f"CLAUDE_PLUGIN_OPTION_{key.upper()}", default).strip()


def trusted_bundles() -> list[dict]:
    """Bundles from user or managed settings. A repository cannot inject these."""
    path = option("standards_bundle")
    if not path:
        return []
    return [
        {
            "id": "standards",
            "source": path,
            "status": "normative",
            "_trusted": True,
            "description": "Organization standards",
        }
    ]


NULLS = {"", "~", "null", "Null", "NULL"}


def _scalar(value: str) -> str:
    """Read a one-line YAML scalar as a string.

    Double-quoted values honour backslash escapes, single-quoted ones `''`.
    Unquoted values lose a trailing ` #` comment. A value that is only a
    comment (YAML null) or a block-scalar indicator (`|`, `>-`, ...) whose
    text sits on later lines returns "", so callers fall back.
    """
    value = value.strip()
    if value.startswith('"'):
        i = 1
        while i < len(value) and value[i] != '"':
            i += 2 if value[i] == "\\" else 1
        try:
            return json.loads(value[: i + 1])
        except ValueError:
            return value[1:i]
    if value.startswith("'"):
        out, i = [], 1
        while i < len(value):
            if value[i] == "'":
                if value[i + 1 : i + 2] == "'":
                    out.append("'")
                    i += 2
                    continue
                break
            out.append(value[i])
            i += 1
        return "".join(out)
    if value.startswith("#") or re.fullmatch(r"[|>][-+0-9]*", value):
        return ""
    return value.split(" #", 1)[0].strip()


def read_index_meta(index: Path) -> dict | None:
    """Parse an `index.md`'s frontmatter, if it declares `okf_version`.

    Per SPEC §8.1, only a bundle-root `index.md` may carry frontmatter, with
    the keys `okf_version`, `title`, `description` and `license` (plus
    extension keys). A file whose frontmatter has no non-null `okf_version`
    (§11.2: null or empty equals absent) is not treated as a bundle root;
    returns None. Only top-level `key: value` lines are read, so a nested
    key under an extension mapping can't mark a bundle.

    The returned `description` is what an agent reads to pick a bundle:
    frontmatter `description`, else frontmatter `title`, else the body's
    first `# ` heading.
    """
    try:
        lines = index.read_text(encoding="utf-8").lstrip("\ufeff").splitlines()
    except (OSError, UnicodeDecodeError):
        return None

    if not lines or lines[0].strip() != "---":
        return None

    meta: dict[str, str] = {}
    body_start = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body_start = i + 1
            break
        if line[:1] in (" ", "\t", "#", "-") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = _scalar(value)

    if body_start is None or meta.get("okf_version", "") in NULLS:
        return None

    heading = ""
    in_fence = False
    for line in lines[body_start:]:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("# "):
            heading = stripped[2:].strip()
            break

    meta["description"] = next(
        (v for v in (meta.get("description", ""), meta.get("title", ""), heading) if v not in NULLS),
        "",
    )
    return meta


def discover_bundles(cwd: Path) -> list[dict]:
    """Walk the project tree for bundle roots marked with `okf_version`.

    A hit prunes its own subtree: nested `index.md` files inside a bundle are
    navigation, not further bundle roots. Falls back to a fixed list of
    conventional directories when nothing is marked, so bundles predating the
    `okf_version` key are still found.
    """
    cache_dir = (cwd / option("cache_dir", ".okf/cache")).resolve()
    root = cwd.resolve()
    found: list[dict] = []

    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        depth = len(current.relative_to(root).parts)

        dirnames[:] = [
            d
            for d in dirnames
            if not (d.startswith(".") and d != ".okf")
            and d not in PRUNE_DIRS
            and (current / d) != cache_dir
        ]
        if depth >= MAX_DEPTH:
            dirnames[:] = []

        if "index.md" not in filenames:
            continue

        meta = read_index_meta(current / "index.md")
        if meta is None:
            continue

        rel = current.relative_to(root)
        bundle_id = str(rel).replace(os.sep, "/") if rel.parts else root.name
        source = f"./{bundle_id}" if rel.parts else "."
        found.append(
            {
                "id": bundle_id,
                "source": source,
                "status": "normative",
                "description": meta["description"],
                "_discovered": True,
            }
        )
        dirnames[:] = []  # this subtree belongs to the bundle just found

    if found:
        found.sort(key=lambda b: (b["id"].count("/"), b["id"]))
        return found

    for candidate in FALLBACK_DIRS:
        if (root / candidate / "index.md").is_file():
            found.append(
                {
                    "id": candidate,
                    "source": f"./{candidate}",
                    "status": "normative",
                    "description": "",
                    "_discovered": True,
                }
            )
    return found


def external_bundles(cwd: Path) -> list[dict]:
    """Bundles declared by the repository for sources discovery cannot see:
    directories outside the project root, and remote sources. Untrusted input."""
    cfg = cwd / CONFIG
    if not cfg.is_file():
        return []
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"okf: ignoring {CONFIG}: {exc}", file=sys.stderr)
        return []
    bundles = data.get("bundles", [])
    return [b for b in bundles if isinstance(b, dict)] if isinstance(bundles, list) else []


def resolve(cwd: Path, bundle: dict) -> Path | None:
    """Map a declaration to a local directory holding `index.md`. Never fetches.

    `standards_bundle` and auto-discovered sources resolve as given - the
    former is trusted, the latter was just found inside the project. A path
    declared in `okf.json` resolves as written too, since the file exists to
    name bundles *outside* the project root - but if it resolves back inside
    the project it is rejected: that bundle is already found by
    auto-discovery, and honoring the declaration here would create two
    sources of truth for it. A non-path source (`github:`, `https:`, ...)
    always maps to the vendored cache directory.
    """
    source = str(bundle.get("source", ""))
    bundle_id = str(bundle.get("id", ""))
    if not source or not bundle_id:
        return None

    is_local = bundle.get("_trusted") or bundle.get("_discovered")
    is_path = is_local or source.startswith((".", "/", "~"))

    if is_path:
        root = Path(source).expanduser()
        if not root.is_absolute():
            root = cwd / root
    else:  # github:, https:, anything else -> vendored cache only
        root = cwd / option("cache_dir", ".okf/cache") / bundle_id

    try:
        root = root.resolve()
    except OSError:
        return None

    if is_path and not is_local:
        try:
            root.relative_to(cwd.resolve())
        except ValueError:
            pass  # outside the project: expected for an external declaration
        else:
            print(
                f"okf: bundle {bundle_id!r} is inside the project; local bundles "
                f"are auto-discovered - remove it from {CONFIG}",
                file=sys.stderr,
            )
            return None

    index = root / "index.md"
    if not index.is_file():
        if not bundle.get("_discovered"):
            reason = (
                f"remote sources must be vendored into {option('cache_dir', '.okf/cache')}/"
                if not is_path
                else f"no index.md at {root}"
            )
            print(f"okf: bundle {bundle_id!r} unavailable ({reason})", file=sys.stderr)
        return None
    return root


def display(cwd: Path, root: Path) -> str:
    try:
        return str(root.relative_to(cwd.resolve()))
    except ValueError:
        return str(root)


def cell(value: str) -> str:
    """Escape a value for a markdown table cell. Descriptions come from an
    untrusted okf.json and must not be able to break the table's shape."""
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def build_context(cwd: Path) -> str:
    # Precedence: an organization constraint outranks the project's own
    # knowledge, which in turn outranks what the project imports.
    declared = trusted_bundles() + discover_bundles(cwd) + external_bundles(cwd)

    normative: list[tuple[dict, Path]] = []
    informative: list[tuple[dict, Path]] = []
    seen_roots: set[Path] = set()
    for bundle in declared:
        root = resolve(cwd, bundle)  # emits its own warning on failure
        if root is None:
            continue
        if root in seen_roots:
            continue
        seen_roots.add(root)
        target = normative if bundle.get("status") == "normative" else informative
        target.append((bundle, root))

    if not normative and not informative:
        return ""

    rows = [
        f"| `{cell(bundle['id'])}` | normative | {rank} | `{cell(display(cwd, root))}/index.md` | {cell(bundle.get('description', ''))} |"
        for rank, (bundle, root) in enumerate(normative, start=1)
    ] + [
        f"| `{cell(bundle['id'])}` | informative | – | `{cell(display(cwd, root))}/index.md` | {cell(bundle.get('description', ''))} |"
        for bundle, root in informative
    ]

    table = (
        "## OKF knowledge bundles\n\n"
        "Normative bundles are binding: comply with them, or state explicitly why "
        "you cannot. On conflict, the lower precedence number wins. Informative "
        "bundles are advisory and may be overridden by normative bundles or by "
        "project code. Read an index only when you need it.\n\n"
        "| Bundle | Type | Prec | Index | Description |\n"
        "|---|---|---|---|---|\n" + "\n".join(rows)
    )

    return "\n\n".join([RULES, table])


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        cwd = Path(payload.get("cwd") or ".")
        # The same script serves SessionStart and SubagentStart, so echo back
        # whichever event actually fired.
        event = payload.get("hook_event_name") or "SessionStart"
        context = build_context(cwd)
        if not context:
            return  # no bundle: emit nothing, cost nothing
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": event,
                        "additionalContext": context,
                    }
                }
            )
        )
    except Exception as exc:  # never break session startup
        print(f"okf: hook failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
