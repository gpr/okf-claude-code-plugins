#!/usr/bin/env python3
"""SessionStart hook: inject OKF bundle context into a Claude Code session.

Bundles come from two places, deliberately:

  * `userConfig` (`CLAUDE_PLUGIN_OPTION_*`) - machine or organization scope.
    Claude Code reads `pluginConfigs` only from user, `--settings` and managed
    settings, never from the workspace, so a cloned repository cannot supply
    these. Suitable for org-wide normative standards.
  * `okf.json` at the project root - project scope, version-controlled, shared
    with the team. Untrusted: it ships with the repository.

Because the project file is untrusted, its paths are confined to the project
root. The hook only lists bundles and points at their `index.md`; it never
reads bundle content, so there is nothing to size-cap.

Design constraints:
  * Never touches the network. Remote bundles must be vendored into the cache
    directory by an explicit sync step.
  * Silent no-op when no bundle is present, so non-OKF projects pay nothing.
  * Never raises. A broken hook must not break session startup.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CONFIG = "okf.json"

RULES = """\
## How to read OKF bundles

- A link starting with `/` is relative to **its own bundle's root**, not the
  filesystem: `/tables/orders.md` in a bundle at `spec/` means `spec/tables/orders.md`
- Traverse via `index.md` files; read concepts on demand, never preload a bundle
- To explore a bundle or find a concept by tag, type, description or title, use agent `okf-search`"""


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


def project_bundles(cwd: Path) -> list[dict]:
    """Bundles declared by the repository. Untrusted input."""
    cfg = cwd / CONFIG
    if not cfg.is_file():
        if (cwd / "spec" / "index.md").is_file():
            return [{"id": "spec", "source": "./spec", "status": "normative"}]
        return []
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"okf: ignoring {CONFIG}: {exc}", file=sys.stderr)
        return []
    bundles = data.get("bundles", [])
    return [b for b in bundles if isinstance(b, dict)] if isinstance(bundles, list) else []


def resolve(cwd: Path, bundle: dict) -> Path | None:
    """Map a declaration to a local directory holding `index.md`.

    Never fetches. Untrusted declarations are confined to the project root so a
    cloned repository cannot point the hook at arbitrary files on disk.
    """
    source = str(bundle.get("source", ""))
    bundle_id = str(bundle.get("id", ""))
    if not source or not bundle_id:
        return None

    if bundle.get("_trusted"):
        root = Path(source).expanduser()
    elif source.startswith((".", "/")):
        root = cwd / source
    else:  # github:, https:, anything else -> vendored cache only
        root = cwd / option("cache_dir", ".okf/cache") / bundle_id

    try:
        root = root.resolve()
    except OSError:
        return None

    if not bundle.get("_trusted"):
        try:
            root.relative_to(cwd.resolve())
        except ValueError:
            print(
                f"okf: bundle {bundle_id!r} resolves outside the project; ignored",
                file=sys.stderr,
            )
            return None

    index = root / "index.md"
    if not index.is_file():
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
    # Trusted bundles first: an organization constraint must outrank a repository.
    declared = trusted_bundles() + project_bundles(cwd)

    normative: list[tuple[dict, Path]] = []
    informative: list[tuple[dict, Path]] = []
    for bundle in declared:
        root = resolve(cwd, bundle)
        if root is None:
            print(
                f"okf: bundle {bundle.get('id')!r} unavailable "
                f"(remote sources must be vendored into {option('cache_dir', '.okf/cache')}/)",
                file=sys.stderr,
            )
            continue
        target = normative if bundle.get("status") == "normative" else informative
        target.append((bundle, root))

    if not normative and not informative:
        return ""

    rows = [
        f"| `{cell(bundle['id'])}` | normative | {rank} | `{display(cwd, root)}/index.md` | {cell(bundle.get('description', ''))} |"
        for rank, (bundle, root) in enumerate(normative, start=1)
    ] + [
        f"| `{cell(bundle['id'])}` | informative | – | `{display(cwd, root)}/index.md` | {cell(bundle.get('description', ''))} |"
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