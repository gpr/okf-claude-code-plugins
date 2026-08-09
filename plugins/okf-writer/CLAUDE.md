# okf-writer

Skill-only plugin: no hooks, no `userConfig`, no scripts, no tests. Ships one
skill, `okf-concept` — the authoring workflow for OKF v0.2 concept
documents: identify the type, apply or derive its `templates/<type>.md`
skeleton, write the concept, then keep `index.md` and `log.md` in sync.
User-facing scope is in `README.md`; this file covers what breaks when you
edit it.

## File map

- `skills/okf-concept/SKILL.md` — frontmatter `description` (the trigger
  phrase Claude matches to decide when to load this skill) plus the 10-step
  procedure outline and the ask-vs-decide table
- `skills/okf-concept/references/authoring-procedure.md` — the procedure in
  full: bundle-root resolution, type matching, directory/filename rules,
  frontmatter fill rules, index/log insertion, Attested Computation, the
  worked before/after trees
- `skills/okf-concept/references/templates.md` — the `type: Template`
  concept contract, slug/norm rules, reverse lookup, derivation
- `skills/okf-concept/references/okf-essentials.md` — minimal standalone
  format restatement; defers to `okf-spec` when it's installed

## Scope boundary

`okf-concept` covers authoring workflow only:

- Format semantics (frontmatter fields, trust tiers, conformance) →
  `okf-core`'s job. `okf-essentials.md` restates only the byte-level rules
  needed to emit conformant files; it does not duplicate `okf-spec`.
- Bundle discovery, precedence, `okf.json` → `okf-reader`'s job. Step 0 of
  the procedure uses okf-reader's injected bundle table when present, but
  falls back to its own `okf_version` scan so it still works alone.

Claude Code has no inter-plugin dependency mechanism, so nothing enforces
co-installation. **Never reference a path under `plugins/okf-core/`** —
`okf-writer` must function without `okf-core` installed. Where the skill
needs to defer to `okf-spec`, it names the *skill*, never a file path.

## Editing `SKILL.md`

- The frontmatter `description` is the only thing that decides whether this
  skill loads at all. It's deliberately keyword-dense (literal trigger
  phrases like "add an ADR", "new OKF document"; literal filenames like
  `templates/index.md`). Trim a keyword only if you've confirmed nothing
  depends on matching it.
- It deliberately excludes `okf-spec`'s trigger keywords (`frontmatter`,
  `verified`, `stale_after`, `attester`) so the two skills don't compete for
  the same prompts.
- Keep `SKILL.md` a short index. New authoritative content is a new or
  extended `references/*.md`, linked from `SKILL.md` — not inlined into it.

## The template/concept boundary

A `templates/<type>.md` file's own frontmatter is always `type: Template`.
The target type's skeleton lives in a fenced code block in the body, never
as a second `---` block. If a template opened with the target type's
frontmatter, any OKF consumer (including this skill's own type-vocabulary
scan in step 1) would index it as a real concept of that type. Step 1 of
the procedure also explicitly excludes `<root>/templates/` when collecting
existing concept types from the bundle, for the same reason.

## No test suite

Unlike `okf-reader`, there's no `tests/` here — a skill's content isn't
executable code to unit-test. Verify changes by reading the skill against
[OKF SPEC.md v0.2](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md)
and by the manual walkthrough in `README.md`'s parent plan / this plugin's
verification steps — a throwaway bundle **outside** this repo, never a
fixture under `plugins/okf-writer/examples/`: an `okf_version` marker there
would be auto-discovered by `okf-reader` in this repo and change its
documented token budget (see `plugins/okf-reader/CLAUDE.md`).

## Manifest sync

Same three-place rule as the rest of this repo (root `CLAUDE.md`
"Adding or renaming a plugin"): `plugin.json` `name`/`description`,
`marketplace.json`'s `plugins[]` entry, and the root `README.md` bullet.
Sanity-check with:

```
jq . .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json
```
