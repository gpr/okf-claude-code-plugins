---
name: okf-type-library
description: Starter catalog of 16 ready-made Open Knowledge Format (OKF) concept type templates — Specification, Requirement, Plan Item, ADR, Technology, Dependency, Component, Interface, Test Plan, Risk, Playbook, Environment, Postmortem, Convention, Glossary Term, Attested Computation — installed as a chosen subset into a bundle's templates/ directory, pre-wired for traceability. Use when asked to "seed a bundle with starter templates", "set up the concept types for spec-driven development", "scaffold the type vocabulary", "bootstrap OKF for SDD", "install a template for X", "what concept types should this bundle have", when the request names several types at once, or when a question involves the type catalog, a preset of types, or how Specification, Requirement, Plan Item, ADR, Technology and Dependency link to each other.
---

# OKF Type Library

Installs a chosen subset of 16 ready-made OKF concept type templates
into a bundle's `templates/` directory, before any concept of those
types exists. Complements `okf-concept`, which authors one concept at a
time and derives a template only after the fact.

## What this does

Given a request naming a workflow ("spec-driven development") or
specific types ("Technology and Dependency"), this skill picks a subset
of its 16-type catalog, confirms once, then copies each one's asset into
the bundle's `templates/` — filling only the `generated` timestamp —
and registers each in `templates/index.md` and the bundle-root `log.md`.
It never installs all 16 unasked: an unused type in the registry biases
every later `okf-concept` run toward it.

## The catalog

| Type | slug | Job |
|---|---|---|
| Specification | `specification` | What one capability should do, before it is built. |
| Requirement | `requirement` | One testable statement with a fit criterion. |
| Plan Item | `plan-item` | One unit of implementation work and its done-condition. |
| ADR | `adr` | One architectural decision, its forces, and its cost. |
| Technology | `technology` | A technology committed to, and where it applies. |
| Dependency | `dependency` | One pinned third-party artifact, version and licence. |
| Component | `component` | One unit of the system, its responsibility and boundary. |
| Interface | `interface` | One contract between components, with its guarantees. |
| Test Plan | `test-plan` | How something gets proven, and what evidence counts. |
| Risk | `risk` | What could go wrong, how bad, and who watches it. |
| Playbook | `playbook` | A repeatable procedure a human runs. |
| Environment | `environment` | One place the system runs and what differs there. |
| Postmortem | `postmortem` | What broke, what it cost, what changed as a result. |
| Convention | `convention` | A rule a newcomer would otherwise get wrong. |
| Glossary Term | `glossary-term` | One term this project uses in a specific way. |
| Attested Computation | `attested-computation` | A sanctioned computation, drafted for human attestation. |

Full jobs, disambiguation between confusable pairs, and the
non-collision proof: `references/catalog.md`.

## Presets

| Preset | Triggered by | Types |
|---|---|---|
| `spec-driven` | "spec-driven development", "SDD", "spec first" | Specification, Requirement, Plan Item, ADR, Test Plan |
| `architecture` | "architecture", "system design", "design docs" | ADR, Component, Interface, Technology, Dependency |
| `delivery` | "planning", "roadmap", "sprint", "track the work" | Plan Item, Requirement, Risk, Test Plan |
| `operations` | "runbooks", "on-call", "SRE", "incidents", "ops" | Playbook, Environment, Postmortem, Risk |
| `stack` | "tech stack", "dependencies", "vendors", "licences" | Technology, Dependency, Convention |
| `minimal` | default when intent is vague | Specification, ADR, Plan Item |
| `all` | only on "all", "everything", "the full catalog" | all 16 |

`Glossary Term` and `Attested Computation` are in no preset — install by
explicit name or `all` only.

## Procedure

Full detail in `references/install-procedure.md` — read it before
writing files.

1. **Find the bundle root.** Same resolution as `okf-concept`: use
   okf-reader's injected table if present, else scan for `index.md`
   declaring `okf_version`. Ambiguous or trusted-bundle-only: ask.
2. **Read the existing registry** — `templates/index.md`, or
   `templates/*.md` if no index, plus `type:` values already in use.
3. **Select.** Named types win over a preset; a preset phrase wins over
   the vague-intent default (`minimal`); drop anything already in the
   registry as `skip, already exists`.
4. **Confirm once** — bundle root, preset and trigger, each type with
   target path and new/skip status, plus `templates/index.md` and
   `log.md` updates.
5. **Write.** Read each asset from `assets/templates/<slug>.md`,
   replace its single `generated:` line with the running model and now,
   transcribe everything else, write to `<root>/templates/<slug>.md`.
   Never overwrite.
6. **Update `templates/index.md`** — back-fill entries for any
   pre-existing `templates/*.md` files if the index didn't exist yet
   (skipping this hides them from `okf-concept`).
7. **Update the bundle-root `index.md`** if `templates/` is new.
8. **Append to the bundle-root `log.md`** — one `**Creation**` bullet
   per installed template.

Then report every file written and every type skipped, and confirm no
`<placeholder>` survived in any written file's own frontmatter.

## Ask vs. decide

| Decide silently | Must ask |
|---|---|
| Which preset a phrase maps to, slug mechanics, index/log formatting | Which bundle, when more than one is found and ambiguous, or the sole candidate is the trusted bundle |
| Insertion position, back-fill entries | Whether to widen beyond a matched preset or named types |
| The `generated` timestamp | Overwriting an existing template (never — always skip and report) |

## Never written by this skill

`verified`, `attester`, `executor` (any form), and a real computation
body for Attested Computation — every asset ships without them, and the
installer only ever transcribes the asset's own bytes plus a fresh
`generated` timestamp.

## Traceability

The 5 requested types plus Test Plan form a spine
(`Specification → Requirement → Plan Item → ADR → Technology →
Dependency`) pre-wired with a `# Traceability` heading in every
skeleton. Full graph and the `/decisions/` directory-hint exception:
`references/traceability.md`.

## Task → reference

| Task | Read |
|---|---|
| Any step of the install procedure, in full | `references/install-procedure.md` |
| Type jobs, disambiguation, non-collision proof, preset detail | `references/catalog.md` |
| The link graph, heading convention, directory hints | `references/traceability.md` |

Paths are relative to this skill's directory.

## Scope

`okf-type-library` seeds `templates/` with a starter set, before any
concept of those types exists. Writing one concept at a time, choosing
its type, and deriving a template from it after the fact is
`okf-concept`'s job (same plugin) — this skill installs a template that
`okf-concept` then loads on its next matching run. Format semantics
(frontmatter fields, trust tiers, conformance) belong to `okf-spec`
(`okf-core`). Bundle discovery, precedence, and `okf.json` belong to
`okf-reader`.
