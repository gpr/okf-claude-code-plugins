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
root and its reads are size-capped.

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
HARD_CAP = 10_000  # Claude Code spills additionalContext above this to a file
MAX_INDEX_BYTES = 256 * 1024  # refuse to read an implausible index.md

RULES = """\
## How to read OKF bundles

- A link starting with `/` is relative to **its own bundle's root**, not the
  filesystem: `/tables/orders.md` in a bundle at `spec/` means `spec/tables/orders.md`
- Traverse via `index.md` files; read concepts on demand, never preload a bundle
- To explore a bundle or find a concept by tag, type, description or title, use agent `okf-search`"""


def option(key: str, default: str = "") -> str:
    """Read a userConfig value, exported to hooks as CLAUDE_PLUGIN_OPTION_<KEY>."""
    return os.environ.get(f"CLAUDE_PLUGIN_OPTION_{key.upper()}", default).strip()


def budget() -> int:
    try:
        return max(500, min(HARD_CAP, int(float(option("context_budget", "9000")))))
    except ValueError:
        return 9000


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
    if index.stat().st_size > MAX_INDEX_BYTES:
        print(f"okf: {bundle_id}/index.md is implausibly large; ignored", file=sys.stderr)
        return None
    return root


def display(cwd: Path, root: Path) -> str:
    try:
        return str(root.relative_to(cwd.resolve()))
    except ValueError:
        return str(root)


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

    parts = [RULES]
    remaining = budget() - len(RULES)

    # Normative bundles are binding, so their index is inlined eagerly: you
    # cannot comply with a specification you do not know exists.
    for rank, (bundle, root) in enumerate(normative, start=1):
        rel = display(cwd, root)
        scope = "organization" if bundle.get("_trusted") else "project"
        header = (
            f"## Bundle `{bundle['id']}` - NORMATIVE ({scope}, precedence {rank}, at `{rel}/`)\n\n"
            "Its specifications are binding. Comply with them, or state explicitly "
            "why you cannot. On conflict, the lower precedence number wins.\n\n"
            "Root index:\n\n"
        )
        try:
            body = (root / "index.md").read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"okf: cannot read {rel}/index.md: {exc}", file=sys.stderr)
            continue
        chunk = header + body
        if len(chunk) > remaining:
            chunk = chunk[: max(remaining, 0)] + f"\n\n[truncated - read `{rel}/index.md` in full]"
        parts.append(chunk)
        remaining -= len(chunk)
        if remaining <= 0:
            break

    # Informative bundles get a pointer only. "Consult when relevant" is exactly
    # a lazy-load condition, so they cost ~15 tokens each at startup.
    if informative:
        lines = "\n".join(
            f"- `{b['id']}` at `{display(cwd, r)}/`"
            + (f" - {b['description']}" if b.get("description") else "")
            for b, r in informative
        )
        parts.append(
            "## Informative bundles\n\n"
            "Consult these when relevant. They are not binding and may be overridden "
            f"by normative bundles or by project code. Read their `index.md` on demand.\n\n{lines}"
        )

    return "\n\n".join(parts)


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