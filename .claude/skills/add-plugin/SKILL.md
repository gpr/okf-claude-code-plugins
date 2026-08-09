---
name: add-plugin
description: This skill should be used when the user asks to "add a plugin", "create a new plugin", "scaffold a plugin", "add okf-writer", "add okf-driven-dev", or wants to add an entry to this repository's marketplace. Scaffolds a new plugin under plugins/<name>/ and syncs its name and description across plugin.json, marketplace.json, and README.md — the three sites that must agree per the root CLAUDE.md.
disable-model-invocation: true
---

# Add Plugin

Scaffold a new plugin in the `okf-cc-plugins` marketplace and keep its name
and description in sync across the three sites that must agree: this repo has
already broken from letting them drift once (see `c61084e`, "repair
marketplace listing and hook portability").

## Before starting

Ask for (or infer from context) two things if not already given:

1. **Plugin name** — kebab-case, matches the eventual `plugins/<name>/`
   directory.
2. **One-sentence description** — this exact string is written to all three
   sites verbatim; do not paraphrase between them.

Check the plugin does not already exist: `ls plugins/` and grep
`.claude-plugin/marketplace.json` for the name.

## Steps

### 1. Choose a layout

This marketplace has two plugin shapes today (see root `CLAUDE.md` §Layout).
Pick the one that matches what the plugin does, or ask the user:

- **Hook-based** (`okf-reader` is the model): needs to run code on a Claude
  Code event. Layout:
  ```
  plugins/<name>/
    .claude-plugin/plugin.json
    README.md
    hooks/hooks.json
    scripts/            # stdlib Python invoked by hooks
    agents/              # optional
    bin/                 # optional CLI entry points
    tests/                # optional unittest
  ```
- **Skill-only** (`okf-core` is the model): ships packaged knowledge/workflow
  only, no runtime code. Layout:
  ```
  plugins/<name>/
    .claude-plugin/plugin.json
    README.md
    skills/<skill-name>/SKILL.md
    skills/<skill-name>/references/*.md
  ```

For a genuinely new shape, use `plugin-dev:create-plugin` for the scaffolding
mechanics, then continue at step 2 below for the marketplace-specific wiring
it does not know about.

### 2. Write `plugins/<name>/.claude-plugin/plugin.json`

```json
{
  "name": "<name>",
  "description": "<description>",
  "version": "0.1.0",
  "displayName": "<Display Name>",
  "author": {
    "name": "Gregory Romé",
    "email": "gregory.rome@gmail.com",
    "url": "https://github.com/gpr"
  }
}
```

Add a `userConfig` block only if the plugin takes user-facing configuration
(see `okf-reader`'s `plugin.json` for the pattern: `type`, `title`,
`description`, `required`/`default`).

### 3. Add the marketplace entry

Append to `plugins[]` in `.claude-plugin/marketplace.json`, at the repo root:

```json
{
  "name": "<name>",
  "source": "./plugins/<name>",
  "description": "<description>"
}
```

`name` and `description` must be byte-identical to `plugin.json`. `source`
must be exactly `./plugins/<name>`.

### 4. Update the README bullet list

Add one bullet to the plugin list in root `README.md`, matching the existing
style (`` `name`: description``). If `<name>` is `okf-writer` or
`okf-driven-dev`, a bullet already exists there as a forward reference —
replace it rather than duplicating.

### 5. Add a plugin CLAUDE.md once there is something to describe

Per root `CLAUDE.md` §"Adding a plugin": do not add
`plugins/<name>/CLAUDE.md` at scaffold time if the plugin has no
implementation yet. Add it alongside the first real implementation, following
the shape of `plugins/okf-reader/CLAUDE.md` (hook-based: file map, invariants,
how to add a `userConfig` key, token budget, test command) or
`plugins/okf-core/CLAUDE.md` (skill-only: file map, scope boundary, how to
edit `SKILL.md`, note there's no test suite).

## Verify

Both manifests must still parse and agree:

```bash
jq . .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json
```

Then check parity explicitly (this is what the manifest-parity `PostToolUse`
hook in `.claude/settings.json` runs automatically on every edit to a
`.claude-plugin/*.json` file — expect no output when everything matches):

```bash
jq -r --slurpfile mk .claude-plugin/marketplace.json '
  .name as $n | .description as $d |
  ($mk[0].plugins[] | select(.name==$n)) as $e |
  if   $e == null            then "MISSING in marketplace: \($n)"
  elif $e.description != $d  then "DESC DRIFT: \($n)"
  elif $e.source != "./plugins/\($n)" then "SOURCE DRIFT: \($n)"
  else empty end' plugins/*/.claude-plugin/plugin.json
```

For a hook-based plugin, also confirm the hook fires without raising:

```bash
python3 -m unittest discover -s plugins/<name>/tests   # if tests/ exists
```

## Scope

This skill only wires a plugin into the marketplace's structural conventions.
It does not design the plugin's actual functionality (hooks logic, skill
content) — that is the user's call, made explicitly per root `CLAUDE.md`'s
"Ask first on big decisions" (architecture, interfaces) and "No speculative
features" (do not scaffold `okf-writer` or `okf-driven-dev`'s internals
unprompted, only the shell once asked).
