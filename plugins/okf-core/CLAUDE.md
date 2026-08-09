# okf-core

Skill-only plugin: no hooks, no `userConfig`, no scripts, no tests. Ships one
skill, `okf-spec` — the authoritative reference for OKF v0.2 format semantics
(bundle structure, frontmatter, trust/provenance, cross-linking, Attested
Computation, conformance). User-facing scope is in `README.md`; this file
covers what breaks when you edit it.

## File map

- `skills/okf-spec/SKILL.md` — frontmatter `description` (the trigger phrase
  Claude matches to decide when to load this skill) plus the top-level
  invariants and house rules
- `skills/okf-spec/references/*.md` (8 files) — one topic each, loaded only
  when `SKILL.md` routes to them (progressive disclosure)

## Scope boundary

`okf-spec` covers format semantics only:

- Bundle discovery, precedence, `okf.json` → `okf-reader`'s job, not this
  plugin's. Don't duplicate discovery rules here.
- Authoring workflow → `okf-writer`'s job (not yet built).

`okf-writer` and `okf-driven-dev` are expected to work alongside `okf-core`
but must still function without it — Claude Code has no inter-plugin
dependency mechanism, so nothing enforces co-installation. Don't have another
plugin's hook or script reference a file under `plugins/okf-core/` directly;
it may not be installed.

## Editing `SKILL.md`

- The frontmatter `description` is the only thing that decides whether this
  skill loads at all. It's deliberately keyword-dense (literal frontmatter
  keys like `stale_after`, `executor`, `attester`; literal trigger phrases
  like "creating, editing, validating"). Trim a keyword only if you've
  confirmed nothing depends on matching it.
- Keep `SKILL.md` a short index. New authoritative content is a new or
  extended `references/*.md`, linked from `SKILL.md` — not inlined into it.
- The "Rules for this agent" section is house policy for this plugin set, not
  OKF spec text. Keep that distinction explicit in wording; don't let house
  policy get quoted back as if it were normative SPEC.md content.

## No test suite

Unlike `okf-reader`, there's no `tests/` here — a skill's content isn't
executable code to unit-test. Verify changes by reading the skill against
[OKF SPEC.md v0.2](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md),
the source `SKILL.md` cites.
