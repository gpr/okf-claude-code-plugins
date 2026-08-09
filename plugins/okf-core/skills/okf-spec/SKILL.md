---
name: okf-spec
description: Authoritative reference for the Open Knowledge Format (OKF) v0.2 — bundles of markdown concept documents with YAML frontmatter. Use when creating, editing, validating, reviewing, or migrating OKF bundles or concept documents, when working in a directory whose index.md declares okf_version, or when a question involves OKF frontmatter keys (type, sources, generated, verified, status, stale_after, runtime, parameters, executor, attester), reserved index.md/log.md files, trust tiers, actor strings, cross-links, conformance, or Attested Computation.
---

# OKF Spec

Source: [OKF SPEC.md v0.2](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md).

## What OKF is

OKF is a directory of markdown files with YAML frontmatter: no schema
registry, no central authority, no required tooling. A **bundle** is the
unit of distribution; a **concept** is one markdown file within it, the
unit of knowledge. A concept's ID is its path within the bundle with the
`.md` suffix removed.

## Invariants (spec MUST)

- `type` is the only always-required frontmatter key. A concept carrying
  just `type` is fully conformant (§11).
- `index.md` and `log.md` are reserved at every level of the hierarchy —
  never use them as concept documents.
- `index.md` carries no frontmatter, except an optional `okf_version` in
  the bundle-root `index.md` only.
- Consumers MUST NOT reject a bundle for: unknown `type` values, unknown
  extra frontmatter keys, broken cross-links, a missing `index.md`, or
  missing optional fields (§11).
- A bare `verified: { by, at }` mapping MUST be treated as a one-element
  list (§5.2).
- The `human:` actor prefix is mandatory for hand-authored or
  human-confirmed content — trust tiers key off it (§5.3, §7).
- An agent MAY supply values for declared `parameters` on an Attested
  Computation but MUST NOT author or edit the sanctioned computation
  itself (§10.3).

## Rules for this agent

These are house policy for this plugin set, not OKF normative text —
don't quote them back as spec.

- **Agent-writable:** `type`, `title`, `description`, `resource`, `tags`,
  `sources`, `generated`, `status`, `stale_after`, and values for declared
  `parameters`. When drafting a brand-new Attested Computation concept
  (`status: draft`, no `verified` entry yet), an agent MAY also propose
  `runtime`, `parameters`, `computation`, and `executor` — the concept
  stays unverified until a human confirms it.
- **Never agent-written:** `verified` (any entry), `attester`,
  `executor.receipt`, and the `computation` body of an Attested
  Computation. On an Attested Computation that already carries a
  `verified` entry, this extends to `runtime`, the `computation` path,
  and `executor.resource` too — changing any of these redefines what
  "sanctioned" means, so it requires the same human/process confirmation
  as `verified` itself, not a silent agent edit. These fields represent
  confirmation or sanctioned logic that must come from a human or a
  deterministic process, not from this agent.
- **Actor literal:** for agent-authored concepts, `generated.by` is
  `claude-code/<model-id>` (e.g. `claude-code/claude-opus-5`). §7 only
  defines the grammar `<producer>/<version>`; this pins the literal so
  bundles written by these plugins stay internally consistent.
- **Timestamps:** `generated.at` and `verified[].at` are RFC 3339, UTC,
  with a `Z` suffix (`2026-08-09T14:30:00Z`). Date-only fields
  (`stale_after`, `sources[].last_modified`, `usage_window`) are
  `YYYY-MM-DD`.
- If a bundle's `index.md` declares an `okf_version` other than `0.2`,
  say so explicitly and read `references/conformance.md` before assuming
  field semantics — v0.1 renamed or dropped some fields (§13).

## Field cheat sheet

| Key | Applies to | Meaning | Reference |
|---|---|---|---|
| `type` | any concept | required; kind of concept, freeform | `frontmatter.md` |
| `title` | any concept | display name | `frontmatter.md` |
| `description` | any concept | one-sentence summary | `frontmatter.md` |
| `resource` | any concept | canonical URI of the underlying asset | `frontmatter.md` |
| `tags` | any concept | list of freeform labels | `frontmatter.md` |
| `sources` | any concept | provenance list + credibility signals | `trust-and-provenance.md` |
| `usage_window` | any concept | `{from, to}` framing `sources[].usage_count` | `trust-and-provenance.md` |
| `generated` | any concept | `{by, at}` — who/when last wrote the content | `trust-and-provenance.md` |
| `verified` | any concept | list of `{by, at}` confirmation events | `trust-and-provenance.md` |
| `status` | any concept | `draft \| stable \| deprecated`, default `stable` | `trust-and-provenance.md` |
| `stale_after` | any concept | absolute date; stale on/after it | `trust-and-provenance.md` |
| `runtime` | Attested Computation | required; how to run it (`bigquery`, `dbt`, ...) | `attested-computation.md` |
| `parameters` | Attested Computation | typed named holes: `{name, type, required}` | `attested-computation.md` |
| `computation` | Attested Computation | path to computation file, instead of inline fence | `attested-computation.md` |
| `executor` | Attested Computation | `{resource, receipt}` — how it's run and what proves it | `attested-computation.md` |
| `attester` | Attested Computation | deterministic (no-LLM) verdict code | `attested-computation.md` |
| `okf_version` | bundle-root `index.md` only | declared spec version, e.g. `"0.2"` | `conformance.md` |

## Smallest legal concept

```markdown
---
type: Playbook
---

# Notes

Anything goes here — `type` is the only required key.
```

## Bundle-root `index.md`

```markdown
---
okf_version: "0.2"
---

# Bundle

* [Some concept](some-concept.md) - short description.
```

## Task → reference

| Task | Read |
|---|---|
| Adding or editing a concept document | `references/frontmatter.md` |
| Laying out a new bundle, `index.md`, `log.md` | `references/bundle-structure.md` |
| Linking between concepts, path-valued fields | `references/cross-linking.md` |
| Citing sources, provenance, trust tiers, `status` | `references/trust-and-provenance.md` |
| Recording a change to a bundle | `references/bundle-structure.md` |
| After adding a concept, linking it from `index.md` | `references/bundle-structure.md` |
| Anything with `runtime`, `computation`, `executor`, `attester` | `references/attested-computation.md` |
| Validating or reviewing a bundle | `references/validation-checklist.md` |
| `okf_version` isn't `0.2`, or migrating from v0.1 | `references/conformance.md` |
| Need a complete file to copy | `references/worked-example.md` |

Read the matching reference before answering. Do not answer OKF field
questions from the cheat sheet above — it is an index, not a
specification. Read at most two references for one task. Paths are
relative to this skill's directory.

## Scope

`okf-spec` covers format semantics only. Bundle discovery, precedence,
and `okf.json` are `okf-reader`'s job. Authoring workflow is
`okf-writer`'s job.
