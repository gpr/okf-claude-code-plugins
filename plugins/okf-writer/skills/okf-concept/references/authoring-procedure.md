# Authoring procedure

The full form of `SKILL.md`'s 10-step outline. Read `templates.md` before
step 3 or step 7; read `okf-essentials.md` if `okf-spec` isn't installed.

## Step 0 — Locate the bundle root

1. If the session context already contains an okf-reader "OKF bundles"
   table, its paths are the candidate set. Read the table; do not re-scan.
2. Otherwise: candidates are directories containing an `index.md` whose
   frontmatter declares `okf_version`. Search downward from the working
   directory and check each ancestor directory up to the repository root.
3. Resolve:
   - **0 candidates** — ask the user: name an existing bundle directory,
     or a path at which to start a new one. Never invent a root.
   - **1 candidate** — use it, unless it is the trusted bundle (below),
     which always asks.
   - **N candidates** — if the request names a path inside exactly one,
     use that one; otherwise ask which.
4. A directory the user names explicitly is the bundle root even without
   an `okf_version` marker — the marker is a discovery aid, not a
   conformance requirement.
5. In okf-reader's injected table, the row with `Bundle` id `standards`
   is the organization's trusted bundle (from the `standards_bundle`
   userConfig, deployed via user or managed settings — a cloned
   repository cannot supply or override it). Never treat it as a write
   target without asking first, even when it is the only candidate:
   confirm the user actually intends to add a concept to the
   organization's shared standards, not just their own project.

## Step 1 — Read the bundle's type vocabulary

1. Read `<root>/templates/index.md`.
   - Present — each entry's link text is the canonical `type` string,
     each link target is `templates/<slug>.md`. This file is the
     bundle's type registry.
   - Absent but `templates/` exists — list `templates/*.md` and read the
     `type:` inside each one's skeleton fence (see `templates.md`).
   - `templates/` absent entirely — the registry is empty; every request
     takes the new-type path, and `templates/` plus `templates/index.md`
     get created at step 7.
2. Also collect types already in use: the `type:` frontmatter values of
   concepts under `<root>`, **excluding `<root>/templates/`**. A bundle
   can predate this skill and have types with no template.
3. Known types = union of steps 1 and 2, each stored as
   `{canonical string, normalized key}` (normalization in `templates.md`).

## Step 2 — Identify the `type`

This is the crux. Extract a proposed type string from the request (the
noun the user names: "an ADR", "a playbook", "a BigQuery table"). If the
request names no type at all, infer one from the content and confirm it
at step 5.

Match `norm(proposed)` against each known type's normalized key, in order:

| Pass | Rule | Action |
|---|---|---|
| 1. Exact | `norm(proposed) == norm(known)` | **Existing type.** Adopt the bundle's canonical spelling verbatim — not the user's. No question. |
| 2. Acronym | initials of the hyphen-separated tokens of one key equal the other key (`adr` ↔ `architecture-decision-record`) | **Ask.** |
| 3. Containment | one key's token list is a contiguous sub-sequence of the other's (`table` ⊂ `bigquery-table`) | **Ask.** |
| 4. No hit | — | **New type.** Confirm the exact string at step 5. |

Passes 2 and 3 never auto-merge and never auto-create. The question is a
single binary: *"Use the existing type `BigQuery Table`, or create a new
type `Table`?"* A wrong merge silently mislabels the concept; a wrong
split silently forks the vocabulary; both are cheap to prevent and
expensive to unwind.

Normalization handles casing and plurals inside pass 1 — `Playbooks`,
`playbook`, `PLAYBOOK` all hit exactly and ask nothing.

Casing for a genuinely new type: Title Case each word, preserving any
all-caps token and any intra-word capital the user typed (`ADR`, `SLO`,
`BigQuery Table`, `API Endpoint`).

## Step 3 — Load the skeleton

- Template exists — read `templates/<slug>.md`. Its own frontmatter
  (`type: Template`) is discarded. Its body's fenced code block becomes
  the new concept's frontmatter; the headings after the fence become the
  body.
- Template missing, but the `okf-type-library` skill catalogs this type —
  install that single template from its catalog (never a preset; that
  skill's selection step is skipped when it is invoked this way),
  register it in `templates/index.md`, log it, then load its fence. The
  run is **not** marked new-template: step 7 would otherwise overwrite a
  hand-vetted catalog template with one generalized from a single
  concept.
- Type exists but the template does not — derive the skeleton from the
  most recently modified existing concept of that type, and mark the run
  **new-template** so step 7 still runs.
- New type — the skeleton is invented from the type's conventional shape
  (an ADR gets Context/Decision/Consequences; a table gets `# Schema`;
  see `okf-essentials.md`'s conventional headings) and step 7 turns it
  into a template.

## Step 4 — Choose directory and filename

Directory, first rule that fires:

1. Concepts of this type already exist — the directory holding the
   plurality of them.
2. The user named a directory — that one.
3. The bundle has 5 or more concepts and is already foldered —
   `<root>/<plural-slug>/` (`playbooks/`, `tables/`, `decisions/`).
4. Otherwise — `<root>/`.

`templates/` never receives anything but `type: Template` files.

Filename: `slug(title) + ".md"`, no singularization. If this produces
`index` or `log` — the two reserved names — stop and ask for a different
title before writing; `<dir>/index.md` and `<dir>/log.md` are never
concept documents, and step 8/9 would otherwise treat the file as the
directory's index or the bundle's log instead of a concept. A collision
with any other existing file stops the run and asks; never overwrite. If
the existing file carries a `verified` entry, refuse outright — this is
a creation skill, not an editor.

## Step 5 — Single confirm point

Present, in one message, before any write: bundle root, `type` (marked
*existing* or *new*), target path, `title`, `description`, and whether a
template will be derived.

| Decide silently | Must ask |
|---|---|
| Slug mechanics, index/log formatting, insertion position | Which bundle, when step 0 leaves more than one candidate (including the trusted bundle as sole candidate) |
| Which frontmatter keys to include | Existing-vs-new on an acronym/containment hit |
| Which template headings to keep or drop | Target directory when no precedent exists |
| The date/timestamp values | Overwriting or editing an existing file, or a filename that would collide with a reserved name |

## Step 6 — Write the concept

Frontmatter written: `type` (canonical spelling), `title`, `description`,
`status: draft`, `generated: { by: claude-code/<running model id>,
at: <RFC 3339 UTC with Z> }`. Add `tags` if the bundle uses tags;
`resource` if the concept names a real asset URI; `sources` if the
content came from a citable artifact.

Never written: `verified`, `attester`, `executor.receipt`. Omitted unless
the user supplies a value: `stale_after`, `usage_window`.

`status: draft` is written explicitly rather than relying on the OKF
default of `stable` — agent-authored, human-unconfirmed content is a
draft, and the explicit key makes that visible to a reader who doesn't
know the default.

`generated.by` uses the *running* model's id, read at runtime. Examples
in this skill's docs show `claude-code/claude-sonnet-5`; that literal is
never copied verbatim into an output file — substitute the actual model.

Placeholders in a skeleton are `<lowercase hint in angle brackets>`.
Every one is resolved or its line deleted before the file is written. A
heading with nothing to say under it is deleted, not left empty. Step 10
greps the written file for unresolved `<…>`.

## Step 7 — New type: derive `templates/<slug>.md` after the concept

Runs only when the run was marked new-type or new-template. Reads the
just-written concept back and generalizes it. Full derivation table and a
complete worked example are in `templates.md`.

Once written, add `* [<canonical Type>](<slug>.md) - Skeleton for <Type>
concepts.` to `templates/index.md`, creating it with H1 `# Templates` if
absent; and if `templates/` itself is new, link it from the bundle-root
`index.md`.

## Step 8 — `index.md` updates

Scope: the concept's own directory, the parent chain only when a
directory is new, and `templates/index.md` when a template was derived.
A fully recursive "every ancestor lists every descendant" is not done —
the spec doesn't ask for it and it duplicates every entry at every level.

Concept's own directory:

- **Exists** — insert `* [<title>](<filename>.md) - <description>` into
  the H1 section whose heading normalizes to the concept's type (singular
  or plural); else the first section; else append a new
  `# <Type, plural>` section. If the section's existing entries are
  already sorted by link text, insert alphabetically; otherwise append.
  Separator exactly ` - `. Description copied verbatim from the concept's
  frontmatter.
- **Missing** — create it. H1 is the directory name in Title Case (bundle
  root: the bundle's name). No frontmatter — except a bundle-root
  `index.md` being created from nothing, which gets `okf_version: "0.2"`.
- **New directory** — add `* [<Dir Title>](<dir>/) - <one line>` to the
  parent's `index.md`, creating that parent index the same way, recursing
  to the bundle root.

Link form: `index.md` entries are **relative to that index's directory**
(a bare filename for a sibling). Bundle-root-relative `/`-paths are used
in concept bodies and in `log.md`.

## Step 9 — `log.md` at the bundle root

1. Read `<root>/log.md`; create with H1 `# Directory Update Log` if
   absent.
2. Today's `## YYYY-MM-DD` heading: if present, append bullets at the end
   of its block; if absent, insert it immediately after the H1, above all
   existing date headings (newest first).
3. Bullets, bundle-root-relative links:
   - `* **Creation**: Added the [<title>](/<path>.md) <type> concept.`
   - plus, when a template was derived:
     `* **Creation**: Derived the [<Type> template](/templates/<slug>.md) from it.`
4. Bundle-root `log.md` only — not a directory-local `log.md`, even if
   the target directory maintains one. OKF permits a `log.md` at any
   level and `bundle-structure.md` says to append to a directory-local
   one when present; this skill deliberately narrows that to the
   bundle root, as one predictable place to check for the history of
   every concept this skill writes. This is house policy for this
   skill, not an OKF requirement — a bundle that relies on a
   directory-local log for that directory's history won't see this
   skill's entries there.

## Step 10 — Self-check and report

- List every file written or edited.
- Grep each written file for unresolved `<…>` placeholder text (the one
  exception: the Attested Computation TODO line, see below).
- Every new `.md` outside `index.md`/`log.md` has `type` in its
  frontmatter.
- A derived template has an entry in `templates/index.md`.
- No file was written with `verified`, `attester`, or `executor.receipt`.

## `type: Attested Computation`

Draft, do not refuse. `okf-spec`'s house rules explicitly permit an agent
to propose `runtime`, `parameters`, `computation`, and `executor` on a
brand-new draft with no `verified` entry, precisely so this case works.

1. Write `status: draft`. Never write `verified`, `attester`, or
   `executor.receipt`.
2. `runtime` is required — ask for it if the request doesn't supply it.
3. The skill does not invent the computation. Either the user supplies
   the SQL/code (paste it verbatim, don't rewrite it), or the
   `# Computation` section is written as an explicit
   `TODO: paste the sanctioned computation — an agent must not author this.`
   This is the one permitted exception to step 6's
   no-unresolved-placeholders rule, and step 10's self-check whitelists it.
4. The log entry notes the computation is pending human authorship.
5. A derived `templates/attested-computation.md` carries a placeholder
   computation only — never a real one, and never an `attester` key.
6. If the target file already exists with a `verified` entry, stop
   (already covered by step 4's general refusal). This is also why this
   skill needs no separate rule for okf-spec's extended restriction —
   once an Attested Computation carries `verified`, changing `runtime`,
   the `computation` path, or `executor.resource` requires the same
   human confirmation as `verified` itself. This skill only ever
   creates new files; step 4's blanket refusal to touch any file with a
   `verified` entry already makes that restriction unreachable here.

## Worked example: existing type

Before — `templates/` holds only `playbook.md`; `playbooks/` holds
`freshness-alert.md`.

```
demo/
  index.md
  log.md
  templates/
    index.md                  * [Playbook](playbook.md) - Skeleton for Playbook concepts.
    playbook.md                type: Template
  playbooks/
    index.md
    freshness-alert.md         type: Playbook
```

Request: "add a playbook for rotating the on-call pager".
`norm("playbook")` hits pass 1 — existing type, canonical spelling
`Playbook`, no template work.

After:

```
demo/
  index.md                    unchanged
  log.md                      + 1 bullet
  templates/                  unchanged
  playbooks/
    index.md                  + 1 entry
    freshness-alert.md
    rotate-on-call-pager.md   NEW
```

`playbooks/index.md`:

```markdown
# Playbooks

* [Data freshness alert](freshness-alert.md) - Steps to triage a freshness alert on the orders pipeline.
* [Rotate the on-call pager](rotate-on-call-pager.md) - Steps to hand the on-call pager to the next rotation.
```

`log.md`:

```markdown
# Directory Update Log

## 2026-08-09
* **Creation**: Added the [Rotate the on-call pager](/playbooks/rotate-on-call-pager.md) Playbook concept.
```

## Worked example: new type

Request against the tree above: "add an ADR recording why we chose
DuckDB". `norm("ADR") = adr`; known norms `{playbook}`; no exact, no
acronym expansion, no containment — new type. Confirmed at step 5 as
`ADR`, target `decisions/choose-duckdb.md`.

After:

```
demo/
  index.md                    + * [Decisions](decisions/) - Architecture decision records.
  log.md                      + 2 bullets
  templates/
    index.md                  + * [ADR](adr.md) - Skeleton for ADR concepts.
    adr.md                    NEW   (written second)
    playbook.md
  decisions/
    index.md                  NEW
    choose-duckdb.md          NEW   (written first)
  playbooks/...               unchanged
```

`decisions/choose-duckdb.md` — written first:

```markdown
---
type: ADR
title: Use DuckDB for local analytics
description: Records the decision to run local analytical queries on DuckDB instead of SQLite.
tags: [architecture, analytics]
status: draft
generated: { by: claude-code/claude-sonnet-5, at: 2026-08-09T10:15:00Z }
---

# Context

Local analytics run on SQLite. Scans over the event tables are
row-oriented and dominate the runtime of every ad-hoc query.

# Decision

Adopt DuckDB for all local analytical queries. SQLite stays for
transactional state.

# Consequences

- Columnar scans replace row scans on the hot path.
- One more binary to vendor and keep current.
```

See `templates.md` for the derived `templates/adr.md` this produces.

`decisions/index.md` (new):

```markdown
# Decisions

* [Use DuckDB for local analytics](choose-duckdb.md) - Records the decision to run local analytical queries on DuckDB instead of SQLite.
```

`log.md`:

```markdown
# Directory Update Log

## 2026-08-09
* **Creation**: Added the [Rotate the on-call pager](/playbooks/rotate-on-call-pager.md) Playbook concept.
* **Creation**: Added the [Use DuckDB for local analytics](/decisions/choose-duckdb.md) ADR concept.
* **Creation**: Derived the [ADR template](/templates/adr.md) from it.
```
