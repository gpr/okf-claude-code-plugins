# okf-claude-plugins

A Claude Code plugin marketplace for the Open Knowledge Format (OKF), not an
application. Each `plugins/<name>/` is an independently installable plugin;
`.claude-plugin/marketplace.json` is the index Claude Code reads to list them.

## Layout

```
.claude-plugin/marketplace.json     # marketplace manifest: name, owner, plugins[]
docs/                                # guides for users consuming the marketplace, not a plugin's own docs
plugins/<name>/
  .claude-plugin/plugin.json        # plugin manifest: name, description, userConfig
  README.md                         # user-facing behaviour docs
```

Plugin internals vary by kind — this marketplace has both:

- **Hook-based** (`okf-reader`, `okf-memory`): `hooks/hooks.json`, `scripts/`
  (Python), `bin/` (CLI entry points), `tests/` (unittest), `examples/`
  (fixtures for the README).
- **Skill-only** (`okf-core`, `okf-writer`): `skills/<skill-name>/SKILL.md` +
  `references/*.md` (+ `assets/` and `evals/` for `okf-writer`'s
  `okf-type-library`, which ships ready-made template files), no hooks,
  scripts, or tests. `okf-core` also ships `agents/` (the `okf-search`
  agent).

## Adding or renaming a plugin

A plugin's name and description live in three places that drift independently —
this repo has already broken this way once (`c61084e`, "repair marketplace
listing and hook portability"):

1. `plugins/<name>/.claude-plugin/plugin.json` — `name`, `description`
2. `.claude-plugin/marketplace.json` `plugins[]` entry — `name`,
   `source: "./plugins/<name>"`, `description` (must match plugin.json)
3. `README.md` plugins table (the "What it does" cell)

Update all three together. Sanity-check both manifests still parse:

```
jq . .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json
```

## Shared conventions

- Hook and CLI scripts are Python 3 and run under whatever `python3` the user
  already has. They must **work on the stdlib alone**: a third-party library
  (e.g. tree-sitter in `okf-memory`) is an optional, lazily imported
  enhancement with a stdlib fallback, installed only by an explicit user-run
  setup command (`plugins/okf-memory/bin/okf-memory-setup`), never by a hook.
  No virtualenv, no dependency manifest the plugin needs before it works.
- Reference in-plugin files from `hooks.json` via `${CLAUDE_PLUGIN_ROOT}`,
  never a relative path (see `plugins/okf-reader/hooks/hooks.json`).
- Hook invariants for every plugin here: never touch the network; never raise
  (a broken hook must not break session startup); emit nothing when there is
  nothing to say, so projects that don't use OKF pay zero tokens.
- User-facing configuration goes through `userConfig` in `plugin.json`, read
  in the script from `CLAUDE_PLUGIN_OPTION_<KEY>`.

## Commands

Run from the repo root:

```
python3 -m unittest discover -s plugins/okf-reader/tests   # tests
python3 plugins/okf-reader/bin/okf-reader-preview .         # what the hook would inject
python3 -m unittest discover -s plugins/okf-memory/tests   # okf-memory tests
```

## Working in this repo

With okf-reader active, this repo self-discovers
`plugins/okf-reader/examples/spec/index.md` (it declares `okf_version`) and
injects it as a normative bundle. That's a fixture demonstrating
auto-discovery for `README.md`'s docs, not a spec governing this repo —
ignore it. Don't strip its frontmatter to silence the injection: the
`okf_version` discovery mechanism itself is covered by
`tests/test_okf_context.py` (via synthetic tmp-dir fixtures, not this file
directly), so doing so breaks the worked example without touching any test.

This repo enables its own `okf-memory` plugin (`.claude/settings.json`,
marketplace registered from `.` so the hook runs the working-tree code). A
full `Read` of a file over `max_bytes` returns its memory (outline with source
line numbers), not the content; use a ranged `Read` (`offset`/`limit`) or
`Grep` for real lines. Memories land in `.memory/`, which is gitignored.
Changes to `plugins/okf-memory/` take effect at the next session or
`/reload-plugins`.

`max_bytes` can't be set here: Claude Code reads `pluginConfigs` only from
user or managed settings. At the 20 KB default almost no file in this repo
qualifies, so to exercise the plugin while working on it, lower it in
`~/.claude/settings.json`:
`"pluginConfigs": {"okf-memory@okf-cc-plugins": {"max_bytes": "8000"}}`.

## Adding a plugin

No CLAUDE.md exists yet for `okf-driven-dev` — it doesn't exist as a plugin
directory in this repository; it's named only in the root `README.md`'s
plugin list. Add a plugin-specific CLAUDE.md alongside its first
implementation, once there's something to describe.
