# Wiring the OKF plugins into your project's CLAUDE.md

`okf-reader`, `okf-core`, and `okf-writer` give Claude Code the machinery to
read and write a markdown knowledge base. None of them read your project's
`CLAUDE.md`, and none of them tell Claude *when* to consult the bundle or
*when* to update it — that policy has to come from you. This guide gives you
a copy-paste `CLAUDE.md` block for a spec-first workflow, the bundle layout
it assumes, and how to debug it when the pieces don't line up.

## 1. What the plugins do, and what they don't

- `okf-reader`'s `SessionStart` hook injects bundle **locations** — never
  content — at startup, `/clear`, or `/compact`. Roughly 214 tokens for a
  one-bundle project, exactly zero for a project with no bundle.
- A directory becomes a bundle the moment its `index.md` declares
  `okf_version` in YAML frontmatter. That single key is the entire discovery
  contract.
- The skills (`okf-spec` from `okf-core`; `okf-concept` and
  `okf-type-library` from `okf-writer`) are **triggered by natural language,
  not slash commands** — none of these plugins ship a `commands/` directory.
  You ask for what you want ("add an ADR for X") and the matching skill
  loads.
- Nothing here reads `CLAUDE.md`. Bundle *locations* land in context
  automatically; what Claude *does* with them — read before proposing, write
  before implementing, update after — is a policy only you can set. That's
  what the rest of this guide sets up.

## 2. The block

Paste this into your project's `CLAUDE.md`. It assumes the layout in
[§3](#3-layout) and the bootstrap in [§4](#4-bootstrap).

````markdown
## Knowledge base

This project's knowledge lives in the OKF bundle at `spec/` — specifications,
decisions, conventions, plans. `okf-reader` injects the bundle's *location*
at session start, never its content: read `spec/index.md` and traverse from
there, on demand.

A link starting with `/` inside the bundle is relative to `spec/`, not the
filesystem: `/decisions/0001-duckdb.md` means `spec/decisions/0001-duckdb.md`.

To find which concepts apply to a question, use the `okf-search` agent.

## Spec-first (non-negotiable)

No code change without a corresponding concept in `spec/`.

1. Find the concept covering the change (`okf-search`).
2. If none exists, write it first — "add a Specification for X" — and stop
   for approval before touching code.
3. Implement against the concept; cite its path in the commit body.
4. If the implementation contradicts the concept, update the concept in the
   same change. Never leave code and spec disagreeing.

`spec/conventions/` is binding: each concept there is a rule this project
does not break. Read it before proposing an approach in its area.

## Keeping the bundle in sync

Before reporting a behaviour change done:

- update the affected concept, and the directory `index.md` if you added a file
- append an entry to `spec/log.md`
- prefer asking `okf-concept` to do this ("add an ADR recording …") over
  hand-writing frontmatter — it keeps `templates/`, `index.md` and `log.md`
  consistent

Never write `verified`, `attester`, `executor.receipt`, or a real
`computation` body: those require a human or a deterministic process.
````

**Don't copy spec content into `CLAUDE.md`.** Keep `CLAUDE.md` a pointer and
a policy; the knowledge itself lives in the bundle and loads on demand.
Pasting concepts in duplicates the token cost `okf-reader` exists to avoid,
and creates a second copy that goes stale the first time one side changes
without the other.

**On "non-negotiable":** an unqualified gate will also fire on a typo fix or
a no-op refactor, where writing a Specification first is pure overhead. If
that becomes a problem, loosen it deliberately — for example, append to
step 1: *"Skip this gate for typo fixes, formatting, and refactors with no
observable behaviour change."* Do that as a conscious edit, not by deleting
the block the first time it's inconvenient.

## 3. Layout

```
spec/
├── index.md            # bundle root — okf_version: "0.2", links to everything
├── log.md               # dated changelog, newest first
├── conventions/         # binding project rules — type: Convention
├── specifications/      # type: Specification — the unit spec-first gates on
├── requirements/        # type: Requirement
├── plan-items/          # type: Plan Item
├── decisions/           # type: ADR (not adrs/ — this is the one named exception)
├── test-plans/          # type: Test Plan
└── templates/
    ├── index.md          # the type registry: link text = type name, target = skeleton
    └── <slug>.md          # type: Template, one per type in use
```

**Why Specification is the gate.** Its shipped skeleton
(`okf-type-library`'s `assets/templates/specification.md`) is built to be
written *before* code exists: `# Problem` (what's blocked today), `# Scope`
(In / Out), `# Behaviour` (observable from outside, explicitly "no
implementation detail"), `# Acceptance` (conditions an implementation either
meets or doesn't), `# Open questions`. Its one-line description is "What one
capability should do, before it is built" — that's the spec-first rule,
verbatim, as a template.

The `spec-driven` preset (installed in [§4](#4-bootstrap)) also installs
Requirement, Plan Item, ADR, and Test Plan, wired into a traceability spine:

```
Specification ──specifies──▶ Requirement ──delivered by──▶ Plan Item
```

Use those for finer decomposition if you want it. The gate in §2 only
requires the Specification — keeping it to one concept is what keeps the
rule cheap enough to actually follow.

**If you're coming from a `constitution.md`-style workflow:** OKF has no
literal "constitution" concept. The nearest fit is `spec/conventions/`,
using the `Convention` type — "a rule a newcomer would otherwise get wrong,"
with `# Rule` / `# Why` / `# Examples` / `# Enforcement` headings. It's
project-scoped and versioned with the rest of the bundle. For rules that
must hold across *every* project in an org — not just this one — see
`standards_bundle` below.

**Org-wide rules.** `okf-reader` supports one normative bundle a cloned
repository cannot override, via the `standards_bundle` plugin option,
deployed through user or managed settings:

```json
{
  "pluginConfigs": {
    "okf-reader@okf-cc-plugins": {
      "standards_bundle": "/path/to/org/standards"
    }
  }
}
```

It's injected as bundle id `standards` at precedence 1 — ahead of anything
auto-discovered in the project. Both `okf-concept` and `okf-type-library`
refuse to write into a `standards` bundle without asking first.

## 4. Bootstrap

1. Create `spec/index.md`:

   ```markdown
   ---
   okf_version: "0.2"
   ---

   # Product spec
   ```

2. Ask Claude: *"set up the concept types for spec-driven development."*
   `okf-type-library` installs the `spec-driven` preset (Specification,
   Requirement, Plan Item, ADR, Test Plan) into `spec/templates/`.
3. Ask Claude: *"install a template for Convention."* `Convention` isn't in
   the `spec-driven` preset installed in step 2 (it ships with `stack`
   instead — Technology, Dependency, Convention), so it needs naming
   explicitly if you want `spec/conventions/` as described in §3.
4. Paste the [§2](#2-the-block) block into `CLAUDE.md`, then **restart
   Claude Code (or `/clear`)** so `okf-reader`'s `SessionStart` hook picks up
   the new bundle.

## 5. The day-to-day loop

A worked example, end to end:

1. You ask: "add caching to the search endpoint."
2. Claude runs `okf-search` for concepts related to search or caching. None
   exist.
3. Per the §2 gate, Claude proposes a Specification first — "add a
   Specification for search-result caching" — and stops for your approval
   before writing any code.
4. You approve (possibly after editing `# Scope` or `# Acceptance`).
   `okf-concept` writes `spec/specifications/search-result-caching.md` and
   updates `spec/specifications/index.md` — creating that directory and
   linking it from the bundle-root `spec/index.md`, since this is the first
   Specification — then appends to `spec/log.md`.
5. Claude implements against the concept's `# Acceptance` bullets — they
   double as the change's done-criteria, so the gate isn't pure ceremony.
6. Before reporting done, Claude updates the concept if the implementation
   diverged from what was specified, and appends the closing entry to
   `spec/log.md`.

## 6. Troubleshooting

| Symptom | Cause |
|---|---|
| No bundle table injected at all | The hook only fires on `startup`, `/clear`, or `/compact` — restart or `/clear` after creating a bundle |
| Bundle inside a monorepo isn't found | Discovery caps at 4 levels below the project root; a marker at `a/b/c/d/e/index.md` is out of reach |
| Only one of several bundles is found | A discovered bundle prunes its own subtree — a nested `index.md` is treated as navigation within that bundle, not a second root |
| `spec/` stopped being found after adding a bundle elsewhere | Unmarked `index.md` at `spec/`, `docs/okf/`, or `knowledge/` is only accepted as a fallback when *nothing* in the tree declares `okf_version` — one marked bundle anywhere disables it |
| An `okf.json` entry warns on startup and never appears | Bundles inside the project root are rejected there by design — they're already auto-discovered; rely on the `okf_version` marker instead |

To see exactly what the hook would inject for a project, run:

```
python3 plugins/okf-reader/bin/okf-reader-preview .
```

It exits 1 when nothing resolves, so it also works as a CI check that your
bundle still resolves after a refactor.
