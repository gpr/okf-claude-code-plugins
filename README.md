# OKF Claude Code Plugins

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin%20marketplace-5A45FF)](https://docs.anthropic.com/en/docs/claude-code)
[![Python](https://img.shields.io/badge/python-3%20stdlib%20only-3776AB?logo=python&logoColor=white)](#requirements)

A Claude Code plugin marketplace for the [Open Knowledge Format](#what-is-okf)
(OKF) — plugins that let Claude Code read and write a project's markdown
knowledge base as a first-class citizen instead of ignoring it.

## What is OKF?

OKF is a directory of markdown files with YAML frontmatter: no schema
registry, no central authority, no required tooling. A **bundle** is the
unit of distribution; a **concept** is one markdown file within it, the unit
of knowledge. A minimal bundle looks like:

```
spec/
├── index.md          # bundle root — links to every concept, no frontmatter except okf_version
├── log.md             # dated changelog, newest entry first
├── adr-0001-database.md   # a concept
└── templates/
    ├── index.md
    └── adr.md          # a concept template, itself a conformant concept
```

A directory becomes a bundle root the moment its `index.md` declares a
version:

```markdown
---
okf_version: "0.2"
---

# Product spec
```

These plugins target **OKF v0.2**. Full format:
[SPEC.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).
Further reading:
[How the Open Knowledge Format can improve data sharing](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing) and
[OKF v0.2 adds trust signals](https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals).

## Why

Project knowledge — ADRs, specs, runbooks, constraints — usually lives in
markdown that nobody loads into context. These plugins make that knowledge
discoverable to Claude Code without paying for it on every session:
`okf-reader` injects bundle *locations*, never bundle content, so a project
that doesn't use OKF pays zero tokens.

## Install

```
/plugin marketplace add gpr/okf-claude-code-plugins
/plugin install okf-core@okf-cc-plugins
/plugin install okf-reader@okf-cc-plugins
/plugin install okf-writer@okf-cc-plugins
```

Plugins are independent — install only what you need. `okf-core` is
recommended alongside `okf-writer` for format-accurate output, but
`okf-writer` works standalone; Claude Code has no inter-plugin dependency
mechanism.

### Requirements

- Claude Code
- `python3` on `PATH` — `okf-reader` only, for its `SessionStart` hook

Hook and CLI scripts are Python 3 stdlib only: no install step, no
virtualenv, no dependency manifest.

## Plugins

| Plugin | What it does | Ships |
|---|---|---|
| [`okf-core`](plugins/okf-core) | Shared Open Knowledge Format (OKF) knowledge for OKF plugins. | skill `okf-spec` |
| [`okf-reader`](plugins/okf-reader) | Loads OKF knowledge bundles into Claude Code sessions, lazily and by declared authority. | `SessionStart` hook, agent `okf-search`, `bin/okf-reader-preview` |
| [`okf-writer`](plugins/okf-writer) | Authors Open Knowledge Format (OKF) concept documents and keeps templates, indexes, and logs in sync. | skills `okf-concept`, `okf-type-library` |

## How okf-reader finds bundles

Three sources, in precedence order:

1. **Organization standards** (`standards_bundle` userConfig) — deployed via
   managed settings, so a cloned repository cannot override it.
2. **Auto-discovery** — any directory whose `index.md` declares
   `okf_version`. Walks up to 4 levels below the project root, skips
   dotdirs (except `.okf`), `node_modules`, `venv`, `dist`, `build`,
   `target`, `vendor`, and the vendored cache directory. Falls back to a
   fixed list of conventional locations (`spec/`, `docs/okf/`,
   `knowledge/`) for bundles that predate the marker.
3. **`okf.json`** at the project root — for bundles discovery can't see:
   remote sources vendored into a cache directory, and directories outside
   the project root.

The hook never touches the network, and it never raises — a broken hook
must not break session startup. See
[`plugins/okf-reader/README.md`](plugins/okf-reader/README.md) for the full
precedence and conflict rules.

## Quick start

1. In a project, create `spec/index.md`:

   ```markdown
   ---
   okf_version: "0.2"
   ---

   # Product spec
   ```

2. Restart Claude Code (or `/clear`) so `okf-reader`'s `SessionStart` hook
   picks it up.
3. Ask Claude to "add an ADR recording why we chose DuckDB." With
   `okf-writer` installed, it writes the concept and keeps `index.md` and
   `log.md` in sync.

## Roadmap

- `okf-driven-dev` — spec-driven development workflow built on OKF. Not yet
  implemented: no plugin directory, no marketplace entry, cannot be
  installed.

## Development

```
plugins/<name>/.claude-plugin/plugin.json   # plugin manifest
plugins/<name>/README.md                    # user-facing docs
plugins/<name>/skills|hooks|agents|bin/...  # plugin internals, vary by kind
.claude-plugin/marketplace.json             # marketplace index
```

```
# run okf-reader's test suite (19 cases)
python3 -m unittest discover -s plugins/okf-reader/tests

# preview what the okf-reader hook would inject for a project
python3 plugins/okf-reader/bin/okf-reader-preview .

# sanity-check both manifests still parse
jq . .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json
```

A plugin's name and description live in three places that drift
independently: `plugin.json`, the `marketplace.json` entry, and this
README's plugin table. Update all three together — a `PostToolUse` hook
guards this on edit, and this repo has already broken that way once
(`c61084e`, "repair marketplace listing and hook portability").

Commits follow [Conventional Commits](https://www.conventionalcommits.org/).

## License

[MIT](LICENSE)
