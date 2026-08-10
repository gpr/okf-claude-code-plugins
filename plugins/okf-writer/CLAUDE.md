# okf-writer

Skill-only plugin: no hooks, no `userConfig`, no scripts, no tests. Ships
two skills:

- `okf-concept` — the authoring workflow for OKF v0.2 concept documents:
  identify the type, apply or derive its `templates/<type>.md` skeleton,
  write the concept, then keep `index.md` and `log.md` in sync.
- `okf-type-library` — a starter catalog of 16 ready-made
  `templates/<type>.md` files, installed as a chosen subset before any
  concept of those types exists.

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
- `skills/okf-type-library/SKILL.md` — the catalog table, presets, and the
  install procedure outline
- `skills/okf-type-library/references/catalog.md` — full job description,
  disambiguation, and `norm()` non-collision proof for each of the 16 types
- `skills/okf-type-library/references/install-procedure.md` — the install
  procedure in full: bundle-root resolution (mirrors `okf-concept`'s, see
  below), selection, write, index/log updates
- `skills/okf-type-library/references/traceability.md` — the link graph,
  the `# Traceability` heading convention, directory hints
- `skills/okf-type-library/assets/templates/*.md` — the 16 ready-made
  `type: Template` files themselves, one per catalog entry

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
- `okf-concept` and `okf-type-library` are split by verb and cardinality,
  not by keyword avoidance alone: `okf-concept` owns "create"/"add" one
  concept now; `okf-type-library` owns "seed"/"install"/"scaffold" a set
  of types before any concept of them exists. Both mention "template" —
  that overlap is fine because the verbs and plurality disambiguate.

## The template/concept boundary

A `templates/<type>.md` file's own frontmatter is always `type: Template`.
The target type's skeleton lives in a fenced code block in the body, never
as a second `---` block. If a template opened with the target type's
frontmatter, any OKF consumer (including this skill's own type-vocabulary
scan in step 1) would index it as a real concept of that type. Step 1 of
the procedure also explicitly excludes `<root>/templates/` when collecting
existing concept types from the bundle, for the same reason.

`okf-type-library`'s 16 `assets/templates/*.md` files are the physical
embodiment of this same invariant, checked with:

```
for f in plugins/okf-writer/skills/okf-type-library/assets/templates/*.md; do
  [ "$(grep -c '^---$' "$f")" = 2 ] || echo "SECOND FRONTMATTER BLOCK: $f"
  grep -q '^type: Template$' "$f" || echo "NOT type Template: $f"
done
```

## Assets are copies, not `cp`

`okf-type-library` installs its 16 `assets/templates/*.md` files by
Reading each one and Writing it to `<bundle>/templates/<slug>.md` with a
single line rewritten — the `generated:` timestamp, which must carry the
running model and the actual time and so can never be a plain file copy.
Every other byte is transcribed unchanged, never recomposed. This is
deliberate: transcribing rather than composing frontmatter makes the
`type: Template` invariant above impossible to violate at install time.
`${CLAUDE_PLUGIN_ROOT}` is not used — it appears only in `okf-reader`'s
`hooks.json`, never in a skill, and Read/Write already resolve
`assets/templates/*.md` relative to the skill directory the same way
`references/*.md` does. The assets carry `type: Template`, never
`okf_version`, and `assets/templates/` has no `index.md` of its own, so
`okf-reader` never auto-discovers them as a bundle — the same trap the
"No test suite" section below already covers for `examples/`.

## Bundle-root resolution is stated twice

`okf-concept/references/authoring-procedure.md` §Step 0 and
`okf-type-library/references/install-procedure.md` §Step 1 both restate
the same bundle-root resolution logic, deliberately not cross-referenced
across skill directories — each skill's docs state "paths are relative
to this skill's directory," and `okf-concept`'s file is 369 lines to
`okf-type-library`'s 20-line restatement. If the two disagree,
`okf-concept`'s is authoritative (the longer form). Change both together.

## No test suite

Unlike `okf-reader`, there's no `tests/` here — a skill's content isn't
executable code to unit-test. Verify changes by reading the skill against
[OKF SPEC.md v0.2](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md)
and by the manual walkthrough in `README.md`'s parent plan / this plugin's
verification steps — a throwaway bundle **outside** this repo, never a
fixture under `plugins/okf-writer/examples/`: an `okf_version` marker there
would be auto-discovered by `okf-reader` in this repo and change its
documented token budget (see `plugins/okf-reader/CLAUDE.md`). The same
applies to `okf-type-library`'s eval fixtures — build them under
`$TMPDIR`, never under `plugins/`.

## Manifest sync

Same three-place rule as the rest of this repo (root `CLAUDE.md`
"Adding or renaming a plugin"): `plugin.json` `name`/`description`,
`marketplace.json`'s `plugins[]` entry, and the root `README.md` bullet.
Sanity-check with:

```
jq . .claude-plugin/marketplace.json plugins/*/.claude-plugin/plugin.json
```

Adding `okf-type-library` did **not** trigger this rule — the plugin's
`name` and `description` are unchanged. It did require editing two things
people conflate with this rule but which it doesn't cover: the root
README's **"Ships" column** (a different cell from the description) and
the root CLAUDE.md **Layout block**, which claimed no plugin here ships
`assets/`.
