# Authoring procedure

The full form of `SKILL.md`'s 11-step outline; step numbers here match
it. Read `templates.md` before step 3 or step 8; read `okf-essentials.md`
for the OKF v0.3 format rules (with `okf-core` installed, its
`okf-generate` skill is the format authority — see that file).
Changing, retiring, or moving an existing concept is a separate path:
"Updating, retiring, moving" below.

Steps 1–6 read and decide; they write nothing. Every write happens after
the single confirm at step 6, so a "no" there leaves the bundle untouched.

## Step 1 — Locate the bundle root

1. If the session context already contains an okf-reader "OKF bundles"
   table, its paths are the candidate set. Read the table; do not re-scan.
2. Otherwise, scan the way okf-reader does, so both plugins see the same
   bundles: candidates are directories containing an `index.md` whose
   frontmatter declares `okf_version`, at most 4 levels below the project
   (repository) root, skipping dot-directories (except `.okf`),
   `node_modules`, `venv`, `.venv`, `__pycache__`, `dist`, `build`,
   `target`, `vendor`, and the vendored cache (`.okf/cache`). If none
   declares `okf_version`, fall back to whichever of `spec/`, `docs/okf/`,
   `knowledge/` has an `index.md`.
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

## Step 2 — Read the bundle's type vocabulary

1. Read `<root>/templates/index.md`.
   - Present — each entry's link text is the canonical `type` string,
     each link target is `templates/<slug>.md`. This file is the
     bundle's type registry.
   - Absent but `templates/` exists — list `templates/*.md` and read the
     `type:` inside each one's skeleton fence (see `templates.md`).
   - `templates/` absent entirely — the registry is empty.
2. Also collect types already in use: the `type:` frontmatter values of
   concepts under `<root>`, **excluding `<root>/templates/`**. Only
   concepts count: skip `index.md` and `log.md` (the root `index.md` has
   frontmatter but is never a concept), `.md` files with no frontmatter or
   no `type` (`README.md`, `AGENTS.md`), and paths with a part starting
   with `.`. A bundle can predate this skill and have types with no
   template.
3. Known types = union of 1 and 2, each stored as
   `{canonical string, normalized key, has template?}` (normalization in
   `templates.md`).

## Step 3 — Identify the `type`

This is the crux. Extract a proposed type string from the request (the
noun the user names: "an ADR", "a playbook", "a BigQuery table"). If the
request names no type at all, infer one from the content and confirm it
at step 6.

Match `norm(proposed)` against each known type's normalized key. Run the
passes in order; the first pass that hits anything decides.

| Pass | Rule | Action |
|---|---|---|
| 1. Exact | `norm(proposed) == norm(known)` | **Existing type.** Adopt the bundle's canonical spelling verbatim — not the user's. No question. |
| 2. Acronym | initials of the hyphen-separated tokens of one key equal the other key (`adr` ↔ `architecture-decision-record`) | **Ask.** |
| 3. Containment | one key's token list is a contiguous sub-sequence of the other's (`table` ⊂ `bigquery-table`) | **Ask.** |
| 4. No hit | — | **New type.** Confirm the exact string at step 6. |

Passes 2 and 3 never auto-merge and never auto-create. With one hit, the
question is a single binary: *"Use the existing type `BigQuery Table`, or
create a new type `Table`?"* With several hits in the same pass (`plan`
is contained in both `plan-item` and `test-plan`), ask one question that
lists every hit plus the new-type option. A wrong merge silently
mislabels the concept; a wrong split silently forks the vocabulary; both
are cheap to prevent and expensive to unwind.

Normalization handles casing and plurals inside pass 1 — `Playbooks`,
`playbook`, `PLAYBOOK` all hit exactly and ask nothing, and so do
`Dependencies` and `Dependency`.

Casing for a genuinely new type: Title Case each word, preserving any
all-caps token and any intra-word capital the user typed (`ADR`, `SLO`,
`BigQuery Table`, `API Endpoint`).

## Step 4 — Choose the skeleton source

Decide only; nothing is installed or written yet. First case that
applies:

1. **The type has a template** — the skeleton is `templates/<slug>.md`.
2. **The type is in use in the bundle but has no template** — the
   skeleton is derived from the most recently modified existing concept
   of that type. Mark the run **new-template**, so step 8 captures the
   bundle's own shape as its template. The bundle's existing concepts
   win over the catalog: they are the convention this bundle already
   follows.
3. **The type is new to the bundle, and the `okf-type-library` skill
   (same plugin) catalogs it** — match `norm()` against its catalog
   table. Mark the run **catalog-install**: step 7 installs that one
   template first. The run is **not** new-template — step 8 would
   otherwise replace a hand-vetted catalog template with one generalized
   from a single concept.
4. **Otherwise** — the skeleton is invented from the type's conventional
   shape (a table gets `# Schema`; a metric gets a definition; see
   `okf-essentials.md`'s conventional headings). Mark the run
   **new-template**.

## Step 5 — Choose directory and filename

Directory, first rule that fires:

1. The user named a directory — that one.
2. Concepts of this type already exist — the directory holding the
   plurality of them.
3. The bundle has 5 or more concepts and is already foldered —
   `<root>/<plural-slug>/`, where `<plural-slug>` is the slug of the
   type's English plural (`playbooks/`, `adrs/`, `technologies/`,
   `bigquery-tables/`).
4. Otherwise — `<root>/`.

Rules 3 and 4 have no precedent to follow. The directory they produce is
a proposal: step 6 shows it marked *no precedent* so the user can
redirect it before anything is written.

`templates/` never receives anything but `type: Template` files.

Filename: `slug(title) + ".md"`, no singularization, no shortening —
pick a short title if a short filename is wanted. If this produces
`index` or `log` — the two reserved names — stop and ask for a different
title before writing; `<dir>/index.md` and `<dir>/log.md` are never
concept documents, and steps 9–10 would otherwise treat the file as the
directory's index or the bundle's log instead of a concept. A collision
with any other existing file stops the run and asks; never overwrite. If
the existing file carries a `verified` entry, refuse outright — this
path creates; editing an existing concept is "Updating, retiring,
moving" below, and only on an explicit request.

## Step 6 — Single confirm point

Present, in one message, before any write: bundle root, `type` (marked
*existing* or *new*), target path (marked *no precedent* when step 5
rule 3 or 4 chose it), `title`, `description`, and the skeleton source —
existing template, catalog install, or a template to be derived.

| Decide silently | Must ask |
|---|---|
| Slug mechanics, index/log formatting, insertion position | Which bundle, when step 1 leaves more than one candidate (including the trusted bundle as sole candidate) |
| Which frontmatter keys to include | Existing-vs-new on an acronym/containment hit |
| Which template headings to keep or drop | Target directory when no precedent exists — shown at this confirm, marked *no precedent* |
| The `generated` timestamp | Overwriting or editing an existing file, or a filename that would collide with a reserved name |
| | A `stale_after` date — only from a review cycle the user or a source states; never guessed |

## Step 7 — Write the concept

**Catalog install first.** If step 4 marked the run catalog-install,
install that one template with `okf-type-library`'s single-type mode
(see that skill's install procedure). It writes `templates/<slug>.md`,
its `templates/index.md` entry, the bundle-root link to `templates/` if
`templates/` is new, and its own `log.md` bullet. Then load the skeleton
from the installed file.

**Loading a skeleton from a template:** its own frontmatter
(`type: Template`) is discarded. Its body's fenced code block becomes the
new concept's frontmatter; the headings after the fence become the body.

Frontmatter written: `type` (canonical spelling), `title`, `description`,
`status: draft`, `generated: { by: "claude-code/<running model id>",
at: "<now, YYYY-MM-DDTHH:MM:SSZ>" }` — both values quoted. Add `tags` (a
YAML list) if the bundle uses tags; `resource` if the concept names a real
asset URI.

Write only what a source supports — the user's request, files you read,
documentation you were given. When the content came from a citable
artifact, record it in `sources`:

- each entry has a stable `id` and the required `resource` (a URL, a
  `/`-rooted path in the bundle, or a scope descriptor), plus a `title`;
- list the concept's own `resource` as a source when the content came
  from it;
- `author` (an actor such as `"team:payments"`), `usage_count` (with a
  `usage_window`), and `last_modified` only with real values;
- cite a specific claim with a footnote whose label is the source's `id`
  — `[^adr-0007]` defined as `[^adr-0007]: ADR 0007` — never `[^1]`.

Tell the user, at step 11, which facts you could not source; omit them
rather than invent them.

Never written on this path: `verified` (content written in this run is
never verified by it — see `okf-essentials.md`'s trust fields). Omitted
unless the user supplies a value: `usage_window`, and `stale_after`,
which needs a known review or refresh cycle — never guess a date. Write
`executor` / `attester` only as the Attested Computation section allows.
All path fields (`resource`, `sources[].resource`, `computation`,
`executor.resource`, `attester.resource`, `superseded_by`) that point into
the bundle start with `/`.

`status: draft` is written explicitly rather than relying on the OKF
default of `stable` — agent-authored, human-unconfirmed content is a
draft, and the explicit key makes that visible to a reader who doesn't
know the default.

`generated.by` uses the *running* model's id, read at runtime. Examples
in this skill's docs show `claude-code/claude-opus-5`; that literal is
illustrative and never copied verbatim into an output file — substitute
the actual model.

Placeholders in a skeleton are `<lowercase hint in angle brackets>`.
Every one is resolved or its line deleted before the file is written. A
heading with nothing to say under it is deleted, not left empty. Step 11
greps the written file for unresolved `<…>`.

A skeleton's link placeholders (e.g. a `# Traceability` bullet
`[<adr title>](../adrs/<slug>.md)`) assume the concept sits one level
below the bundle root. Recompute each path relative to where *this*
concept is written and where its target actually is, and delete a bullet
whose target concept doesn't exist.

## Step 8 — New template only: derive `templates/<slug>.md` after the concept

Runs only when step 4 marked the run new-template. Reads the
just-written concept back and generalizes it. Full derivation table and a
complete worked example are in `templates.md`.

Once written, add `* [<canonical Type>](<slug>.md) - Skeleton for <Type>
concepts.` to `templates/index.md`. If that index doesn't exist yet,
create it with H1 `# Templates`, and **back-fill** an entry for every
`templates/*.md` already present, reading each canonical spelling from
its fence `type:` — step 2 stops scanning `templates/*.md` once an index
exists, so skipping the back-fill hides those templates from every later
run. If `templates/` itself is new, link it from the bundle-root
`index.md`.

## Step 9 — `index.md` updates

Scope: the concept's own directory, the parent chain only when a
directory is new, and `templates/index.md` when a template was derived
(step 8) or installed (step 7). A fully recursive "every ancestor lists
every descendant" is not done — the spec doesn't ask for it and it
duplicates every entry at every level.

Concept's own directory:

- **Exists** — insert `* [<title>](<filename>.md) - <description>` into
  the section whose heading normalizes to the concept's type (singular
  or plural); else the first section; else append a new
  `# <Type, plural>` section. If the section's existing entries are
  already sorted by link text, insert alphabetically; otherwise append.
  Separator exactly ` - `. Description copied verbatim from the concept's
  frontmatter.
- **Missing** — create it. H1 is the directory name in Title Case (bundle
  root: the bundle's name). No frontmatter — except a bundle-root
  `index.md` being created from nothing, which gets `okf_version: "0.3"`,
  a `title` (the bundle's name), a one-sentence `description` of the
  bundle's scope and when to use it, and `license` only when the user
  gave one (see `okf-essentials.md`). When editing an existing root
  `index.md`, keep its frontmatter byte for byte; never add frontmatter to
  a subdirectory `index.md`.
- **New directory** — add `* [<Dir Title>](<dir>/) - <one line>` to the
  parent's `index.md`, creating that parent index the same way, recursing
  to the bundle root.

Link form: every body link — `index.md` entries, concept bodies, and
`log.md` bullets — is **relative to the file that contains it** (a bare
filename for a sibling, `../adrs/choose-duckdb.md` across directories).
That form resolves the same under OKF and on GitHub when the bundle is a
subdirectory of a repository; a `/`-rooted link is valid OKF but breaks
on GitHub there. Only frontmatter path fields use `/`.

## Step 10 — `log.md` at the bundle root

1. Read `<root>/log.md`; create with H1 `# Directory Update Log` if
   absent. `log.md` never has frontmatter.
2. Today's `## YYYY-MM-DD` heading: if present, append bullets at the end
   of its block; if absent, insert it immediately after the H1, above all
   existing date headings (newest first). No blank line between the
   heading and its first bullet.
3. Bullets, links relative to the bundle root (where `log.md` sits):
   - `* **Creation**: Added the [<title>](<path>.md) <type> concept.`
   - plus, when a template was derived:
     `* **Creation**: Derived the [<Type> template](templates/<slug>.md) from it.`
   - a catalog install (step 7) has already logged its own bullet.
4. Bundle-root `log.md` only — not a directory-local `log.md`, even if
   the target directory maintains one. OKF permits a `log.md` at any
   level, recording changes in its own scope (SPEC §9); this skill
   deliberately narrows that to the bundle root, as one predictable place to check for the history of
   every concept this skill writes. This is house policy for this
   skill, not an OKF requirement — a bundle that relies on a
   directory-local log for that directory's history won't see this
   skill's entries there.

## Step 11 — Self-check, validate, and report

Self-check:

- Grep each written concept for unresolved `<…>` placeholder text. A
  derived template keeps its placeholders inside its fence and body —
  only its own frontmatter must be placeholder-free.
- Every new `.md` outside `index.md`/`log.md` has `type` in its
  frontmatter, and `generated.at` is a quoted date-time.
- No subdirectory `index.md` and no `log.md` has frontmatter; a root
  `index.md` this run created has `okf_version: "0.3"`, `title`, and
  `description`.
- Every footnote label equals a `sources[].id`; every in-bundle path
  field starts with `/`.
- A derived or installed template has an entry in `templates/index.md`.
- No written concept has a `verified:` key (this path never writes one),
  and no `executor`/`attester` points at a file that doesn't exist.

Validate: if the `okf-generate` skill (from `okf-core`) is available,
follow its "Validate" step on the bundle root — it ships a validator
script that needs PyYAML. Fix errors; fix warnings or say why you kept
them (a template's Traceability bullets pointing at concepts that don't
exist yet are expected). If it isn't available, the self-check above is
the validation.

Report: every file written or edited; concepts written as `draft`;
concepts that now need a new verification (their meaning changed after a
`verified` entry); facts you could not source; the validation result.

## `type: Attested Computation`

An Attested Computation holds a *sanctioned* computation (OKF §10). This
skill never writes or edits that computation — not even as a draft —
because a consumer would then attest a query an agent wrote.

1. **Ask for the sanctioned source** before step 6: an approved SQL file,
   a dbt model, or a query from its owner. Copy it verbatim into exactly
   one fenced block under `# Computation`, or, for a long or generated
   one, set `computation: "/<path to the file>"` and put no fenced block
   there. Cite the source in `sources` and with a footnote.
2. **No sanctioned source** — write no Attested Computation. Describe the
   value in a concept of its own type (e.g. `Metric`) without a
   computation, and report the gap at step 11. If the user explicitly
   wants an unreviewed query kept, store it as `type: Reference` with
   `status: draft`, and never link it as a computation.
3. `runtime` is required for the type — ask for it if the request doesn't
   supply it. `parameters` entries are `{ name, type, required }`: `name`
   and `type` required, `required` defaults to `false`; common types are
   `string`, `integer`, `number`, `boolean`, `date`, `timestamp`.
4. `executor` (`resource`, plus `receipt`: the fields a run returns, e.g.
   `[job_id, executed_sql, result]`) and `attester` (`resource`:
   deterministic code returning `{ ok, reason }`) are written only when
   the files they point at exist, with `/`-rooted paths. Otherwise omit
   them and state in the body that the computation cannot be attested
   yet.
5. Write `status: draft`, never `verified`. A derived
   `templates/attested-computation.md` carries a placeholder computation
   only. In practice step 4 installs the catalog's template instead,
   since `okf-type-library` catalogs this type.

## Updating, retiring, moving

Only on an explicit request to change, retire, rename, or move an
existing concept. Show the planned change at a single confirm, as in step
6, before writing.

- **Update.** Change only what the request and its sources support; keep
  every other line as it is, including unknown keys, human-written text,
  and every `verified` entry. Set a new `generated` only for a change in
  meaning; a fix to format, whitespace, or links keeps it. If the concept
  had a `verified` entry and its meaning changed, tell the user it now
  reads as unverified until someone re-verifies it.
- **Record a verification** only when a person confirmed the content,
  asked for it to be recorded, and stated their id:
  append `{ by: "human:<id>", at: "<now>" }` to `verified`. Never infer the
  id from git config or a login name.
- **Retire.** Keep the file with its definition and `verified` history;
  set `status: deprecated`; set `superseded_by: "/<path>.md"` when a
  replacement exists; state the reason in the body. Log a
  `**Deprecation**` bullet.
- **Move or rename.** Write the concept at the new path keeping its
  `generated` and `verified` values (a move doesn't change meaning). Leave
  a short concept at the old path with the same `type`, `status:
  deprecated`, `superseded_by` set to the new path, and one line linking
  to it. Update both directories' `index.md` entries and log the move.

Migrating a whole bundle from OKF v0.1 or v0.2 is `okf-generate`'s job
(its migration reference); hand off to it if it is installed, otherwise
tell the user what would change.

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
    freshness-alert.md         type: Playbook, title "Freshness alert"
```

Request: "add a playbook for rotating the on-call pager".
`norm("playbook")` hits pass 1 — existing type, canonical spelling
`Playbook`; step 4 case 1, the existing template; step 5 rule 2, the
`playbooks/` precedent. Title `Rotate on-call pager` slugs to
`rotate-on-call-pager.md`.

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

* [Freshness alert](freshness-alert.md) - Steps to triage a freshness alert on the orders pipeline.
* [Rotate on-call pager](rotate-on-call-pager.md) - Steps to hand the on-call pager to the next rotation.
```

`log.md`:

```markdown
# Directory Update Log

## 2026-08-09
* **Creation**: Added the [Rotate on-call pager](playbooks/rotate-on-call-pager.md) Playbook concept.
```

## Worked example: new type, derived template

Request against the tree above: "add a metric for weekly active users,
in `metrics/`". `norm("metric") = metric`; known norms `{playbook}`; no
exact, no acronym, no containment — new type. `Metric` isn't in the
`okf-type-library` catalog, so step 4 case 4: invent the skeleton, mark
new-template. Step 5 rule 1: the user named `metrics/`. Confirmed at
step 6 as `Metric` (*new*), target `metrics/weekly-active-users.md`,
template to be derived.

After:

```
demo/
  index.md                    + * [Metrics](metrics/) - Product and business metrics.
  log.md                      + 2 bullets
  templates/
    index.md                  + * [Metric](metric.md) - Skeleton for Metric concepts.
    metric.md                 NEW   (written second)
    playbook.md
  metrics/
    index.md                  NEW
    weekly-active-users.md    NEW   (written first)
  playbooks/...               unchanged
```

`metrics/weekly-active-users.md` — written first:

```markdown
---
type: Metric
title: Weekly active users
description: Distinct users with at least one session in a trailing seven-day window.
tags: [product, engagement]
status: draft
generated: { by: "claude-code/claude-opus-5", at: "2026-08-09T10:15:00Z" }
---

# Definition

A user is active if they start at least one session in the seven days
ending at the reporting date, UTC.

# Computation notes

Counts distinct `user_id` over the sessions table. Bots and internal
accounts are excluded.

# Caveats

- Not comparable with the earlier definition, which counted logins.
```

See `templates.md` for the derived `templates/metric.md` this produces.

`metrics/index.md` (new):

```markdown
# Metrics

* [Weekly active users](weekly-active-users.md) - Distinct users with at least one session in a trailing seven-day window.
```

`log.md`:

```markdown
# Directory Update Log

## 2026-08-09
* **Creation**: Added the [Rotate on-call pager](playbooks/rotate-on-call-pager.md) Playbook concept.
* **Creation**: Added the [Weekly active users](metrics/weekly-active-users.md) Metric concept.
* **Creation**: Derived the [Metric template](templates/metric.md) from it.
```

## Worked example: catalogued type

Request against the same tree: "add an ADR recording why we chose
DuckDB". `ADR` is new to the bundle, and `okf-type-library` catalogs it
— step 4 case 3, catalog-install, not new-template. No ADR precedent and
fewer than 5 concepts, so step 5 rule 4 proposes `<root>/choose-duckdb.md`
(title `Choose DuckDB`), marked *no precedent* at step 6; the user may
redirect it, e.g. to `adrs/`. After the confirm, step 7 installs
`templates/adr.md` from the catalog (with its own `templates/index.md`
entry and log bullet), loads its fence, and writes the concept. Step 8
does not run.
