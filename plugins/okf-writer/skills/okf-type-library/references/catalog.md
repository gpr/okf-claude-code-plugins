# Catalog

The 16 types this skill can install, their jobs, and how they avoid
colliding with each other or with `okf-concept`'s type-matching rules
(`okf-concept/references/templates.md`'s `slug`/`norm`).

## The 16

| Canonical `type` | slug | `norm` | one-liner (= each asset's own `description`) |
|---|---|---|---|
| `Specification` | `specification` | `specification` | What one capability should do, before it is built. |
| `Requirement` | `requirement` | `requirement` | One testable statement with a fit criterion. |
| `Plan Item` | `plan-item` | `plan-item` | One unit of implementation work and its done-condition. |
| `ADR` | `adr` | `adr` | One architectural decision, its forces, and its cost. |
| `Technology` | `technology` | `technology` | A technology committed to, and where it applies. |
| `Dependency` | `dependency` | `dependency` | One pinned third-party artifact, version and licence. |
| `Component` | `component` | `component` | One unit of the system, its responsibility and boundary. |
| `Interface` | `interface` | `interface` | One contract between components, with its guarantees. |
| `Test Plan` | `test-plan` | `test-plan` | How something gets proven, and what evidence counts. |
| `Risk` | `risk` | `risk` | What could go wrong, how bad, and who watches it. |
| `Playbook` | `playbook` | `playbook` | A repeatable procedure a human runs. |
| `Environment` | `environment` | `environment` | One place the system runs and what differs there. |
| `Postmortem` | `postmortem` | `postmortem` | What broke, what it cost, what changed as a result. |
| `Convention` | `convention` | `convention` | A rule a newcomer would otherwise get wrong. |
| `Glossary Term` | `glossary-term` | `glossary-term` | One term this project uses in a specific way. |
| `Attested Computation` | `attested-computation` | `attested-computation` | A sanctioned computation, drafted for human attestation. |

Each asset's own frontmatter `description:` is byte-identical to its
one-liner above, and the installer copies that same string into the
type's `templates/index.md` entry (install procedure step 6) — one
source of truth instead of two strings that drift. (Templates that
`okf-concept` derives use a fixed `Skeleton for <Type> concepts.` line
instead; the two kinds of entry can sit in one index.)

## Why none of these 16 collide

`okf-concept`'s type-matching (`references/templates.md` in the
`okf-concept` skill) has three ways two type strings can be treated as
the same or as an ask-worthy near-miss:

1. **Exact `norm()` match** — none share a `norm` key. No key ends in
   `s` or `ies`, so `norm()`'s singularizing never changes one of them,
   let alone merges two.
2. **Acronym match** (initials of one key's tokens equal another key) —
   no initialism of a multi-token key equals another key in the table:
   `plan-item` → `pi`, `test-plan` → `tp`, `glossary-term` → `gt`,
   `attested-computation` → `ac`. None of `pi`, `tp`, `gt`, `ac`, `adr`
   collide.
3. **Containment match** (one key's token list is a contiguous
   sub-sequence of another's) — checked pairwise; the only near-miss
   worth naming is `plan-item` vs `test-plan`, and `[plan, item]` is not
   a sub-sequence of `[test, plan]` in either direction, so it doesn't
   fire.

If you add a 17th type later, re-run this check before adding it to the
table.

## Known, deliberate surprise

Installing both `Plan Item` and `Test Plan` means a bare request like
"add a plan" hits both in `okf-concept` step 3's containment pass:
`[plan]` is a contiguous sub-sequence of `[plan, item]` and of
`[test, plan]`. The two catalog keys don't collide with each other; the
request is just ambiguous. `okf-concept` asks one question listing both
plus the new-type option. This is correct behaviour, not a bug in this
catalog: name the type ("a plan item for the migration", "a test plan
for the migration") to skip the question.

## Keeping the confusable types distinct

**Specification vs Requirement vs Plan Item** — the spec-driven-dev
spine most likely to blur:

- **Specification** — a whole capability, described from outside,
  before it is built. Prose plus acceptance conditions. One per
  capability.
- **Requirement** — one atomic statement the system must satisfy, with
  a fit criterion (`The system shall <observable behaviour>.`). Many
  per Specification. If you can't say how you'd measure it passing,
  it isn't a Requirement yet.
- **Plan Item** — one unit of work that changes files: steps and a
  done-condition. Answers "who does what next", not "what should be
  true".

**Technology vs Dependency** — the stack-choice pair:

- **Technology** — the category-level choice and its blast radius (we
  use Postgres; here's where it applies and what it costs to operate).
  One per choice.
- **Dependency** — the concrete pinned artifact
  (`psycopg[binary]==3.2.1`, MIT, declared in `uv.lock`). Many per
  Technology.

## Documented deviations from `okf-concept`'s defaults

- **`stale_after` pre-wired.** `okf-concept` step 7 omits `stale_after`
  unless the user supplies a value. `Dependency` and `Risk` are the
  only two skeletons that carry it as a placeholder line — a pin with
  no revisit date and a risk with no review date are exactly the
  failure modes those two types exist to prevent. The placeholder is
  still filled-or-deleted like any other, so `okf-concept`'s mechanical
  rule holds; only the *presence* of the line as a prompt differs.
- **`Attested Computation` carries no `executor` key at all**, even
  though `okf-spec`'s house rules permit an agent to propose `executor`
  on a fresh draft with no `verified` entry. `executor.receipt` is
  never agent-written under any circumstance, and showing the parent
  `executor:` key in a template invites filling the whole block. Add
  `executor` by hand once a real one exists.

## Preset membership

See `SKILL.md` for the preset table. `Glossary Term` and
`Attested Computation` are in no preset — install them by explicit name
or via `all`. `Attested Computation` deliberately never widens with a
preset: it is the one type in this catalog where a wrong template is a
policy violation (an agent-authored computation body), not a style
problem.
