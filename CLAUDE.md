# okf-claude-plugins

A Claude Code plugin marketplace for the Open Knowledge Format (OKF), not an
application. Each `plugins/<name>/` is an independently installable plugin;
`.claude-plugin/marketplace.json` is the index Claude Code reads to list them.

## Layout

```
.claude-plugin/marketplace.json     # marketplace manifest: name, owner, plugins[]
plugins/<name>/
  .claude-plugin/plugin.json        # plugin manifest: name, description, userConfig
  README.md                         # user-facing behaviour docs
```

Plugin internals vary by kind — this marketplace has both:

- **Hook-based** (`okf-reader`): `hooks/hooks.json`, `scripts/` (stdlib
  Python), `agents/`, `bin/` (CLI entry points), `tests/` (unittest),
  `examples/` (fixtures for the README).
- **Skill-only** (`okf-core`, `okf-writer`): `skills/<skill-name>/SKILL.md` +
  `references/*.md`, no hooks, scripts, or tests.

## Adding or renaming a plugin

A plugin's name and description live in three places that drift independently —
this repo has already broken this way once (`c61084e`, "repair marketplace
listing and hook portability"):

1. `plugins/<name>/.claude-plugin/plugin.json` — `name`, `description`
2. `.claude-plugin/marketplace.json` `plugins[]` entry — `name`,
   `source: "./plugins/<name>"`, `description` (must match plugin.json)
3. `README.md` plugin bullet list

Update all three together. Sanity-check both manifests still parse:

```
jq . .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json
```

## Shared conventions

- Hook and CLI scripts are Python 3 **stdlib only**. They run under whatever
  `python3` the user already has — no install step, no virtualenv, no
  dependency manifest. Do not add one.
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

## Adding a plugin

No CLAUDE.md exists yet for `okf-driven-dev` — it doesn't exist as a plugin
directory in this repository; it's named only in the root `README.md`'s
plugin list. Add a plugin-specific CLAUDE.md alongside its first
implementation, once there's something to describe.
