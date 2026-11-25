# OKF essentials for authoring

Claude Code has no inter-plugin dependency mechanism, so `okf-writer` must
write conformant OKF v0.3 files without `okf-core` installed. This file is
the minimum needed to do that.

If `okf-core` is installed, its `okf-generate` skill (the official OKF
producer skill) and `okf-spec` (the vendored v0.3 `SPEC.md`) are the format
authority: read them for anything this file doesn't cover — migration,
validation, recording a verification, full Attested Computation semantics —
and let them win on any disagreement about the format. This skill's own
workflow rules (one confirm, never overwrite, `status: draft`, templates and
the type registry) still apply on top.

## Concepts and other files

- A **concept** is a `.md` file, not named `index.md` or `log.md`, whose
  YAML frontmatter has a non-empty `type`. `type` is the only required key;
  values are freeform, with no central registry.
- A `.md` file without frontmatter or without `type` (`README.md`,
  `AGENTS.md`) is **not a concept**. Consumers skip it.
- A file not ending in `.md` is an asset. Paths with a part starting with
  `.` are not part of the bundle.
- `index.md` and `log.md` are reserved at every level and never concepts,
  whatever frontmatter they hold.

## Frontmatter syntax

- The file starts with a line that is exactly `---`; the frontmatter ends at
  the next line that is exactly `---`. It must parse as a YAML mapping.
- Never repeat a key. Use no custom YAML tags.
- Quote timestamps, actors, and values that look like numbers or booleans.
  Inside a `{ ... }` flow mapping a value with a comma must be quoted.
- When editing a file, keep keys you don't know and don't rewrite values
  you didn't change.

## Writable frontmatter keys

| Key | Meaning |
|---|---|
| `type` | required; kind of concept, freeform |
| `title` | display name |
| `description` | one sentence |
| `resource` | canonical URI of the underlying asset (a path field) |
| `tags` | a YAML list, e.g. `[sales, orders]`; a scalar is one tag, so `tags: a, b` is the single tag `a, b` |
| `status` | `draft \| stable \| deprecated`; absent = `stable`; any other value means "not current" to consumers |
| `superseded_by` | path of the replacement; only with `status: deprecated` |
| `generated` | `{ by, at }` — who made the content, and when it last changed in meaning |
| `sources` | provenance entries, below |
| `usage_window` | `{ from, to }` period for `sources[].usage_count` |
| `stale_after` | instant on/after which the concept needs a re-check; only from a known review cycle — never guess one |

Producer-specific keys are allowed anywhere; name them
`x-<producer>-<name>` (e.g. `x-acme-owner`).

## Provenance: `sources` and footnotes

```yaml
sources:
  - id: rev-policy                       # stable key; required when the body cites it
    resource: https://wiki.acme/finance/revenue   # REQUIRED: URL, /path in the bundle, or a scope descriptor
    title: Revenue recognition policy
    author: "team:finance-fpa"           # an actor, below
```

- Add `author`, `usage_count`, or `last_modified` only with the real value;
  every `usage_count` needs a `usage_window`.
- Cite one claim with a footnote whose label is a `sources[].id`:
  `Revenue excludes tax.[^rev-policy]` and
  `[^rev-policy]: Revenue recognition policy`. Never numbered labels such as
  `[^1]`, and no `# Citations` list in the body.
- Write only what a source supports. Don't invent columns, URLs, owners,
  numbers, or review dates.

## Actors and timestamps

- An actor is `<producer>/<version>` for a tool or agent, or
  `<scheme>:<id>` with `human:`, `team:`, or `process:`. Only `human:` gives
  the human-reviewed trust tier.
- `generated.by` for content this skill writes is `"claude-code/<model-id>"`,
  e.g. `"claude-code/claude-opus-5"` — the model actually running, not a
  copied literal.
- Timestamps are RFC 3339 with an offset, or a date. House style: quoted,
  UTC, `Z` suffix. `generated.at` is a date-time
  (`"2026-08-09T14:30:00Z"`); `stale_after` and the other timestamp keys may
  be a date (`"2026-12-31"`, meaning 00:00 UTC).
- Set `generated` on each concept you create or change in meaning. A fix to
  format, whitespace, or links keeps the existing `generated` value.

## Trust fields (house policy, aligned with okf-generate)

This is house policy for these plugins, not OKF normative text — don't quote
it back as spec.

- **`verified`**: never add an entry to content written in the same run.
  Add `{ by: "human:<id>", at: "<now>" }` only when that person confirmed
  the content, asked for it to be recorded, and stated their id. Never infer
  an id from git config or a login name. Keep every existing entry.
- A `verified` event counts only if its `at` is not older than
  `generated.at`. So a change in meaning (a new `generated.at`) silently
  drops a concept to unverified until it is re-verified — tell the user.
- **Attested Computation computation**: never write or edit it. Copy it
  verbatim from a sanctioned source (an approved SQL file, a dbt model, a
  query from its owner) and cite that source.
- **`executor`, `attester`**: write them only when the file they point at
  exists. Otherwise omit the field and say in the body that the computation
  cannot be attested yet.

## Links and paths

A link target or path field value resolves three ways:

1. A value with a scheme (`https:`) is an absolute URL.
2. A value starting with `/` resolves from the bundle root.
3. Anything else resolves from the directory of the file that contains it.

Both in-bundle forms are valid. House style, matching okf-generate:

- **Body links** (concepts, `index.md`, `log.md`) are relative to the file —
  `../tables/orders.md` — because that form also renders correctly on GitHub
  when the bundle is a subdirectory of a repository.
- **Path fields** (`resource`, `sources[].resource`, `computation`,
  `executor.resource`, `attester.resource`, `superseded_by`) start with `/`:
  `/references/attesters/sql-equality.py`. A bare `references/...` would
  resolve from the file's own directory.
- Percent-encode spaces (`my%20concept.md`). Paths are case-sensitive; never
  create two paths that differ only by case.
- Link once per section, not from headings or code, and only to concepts
  that exist or that you create in this run. Consumers tolerate broken
  links, but a link to nothing helps no reader.

## `index.md`

Reserved; never a concept. A **subdirectory** `index.md` has no
frontmatter. The **bundle-root** `index.md` may carry bundle metadata, and
when you create one it gets:

```markdown
---
okf_version: "0.3"
title: <Bundle name>
description: <One sentence — the scope of the bundle and when to use it.>
license: <SPDX expression — only when known; else omit the line>
---
```

When editing a root `index.md`, keep its existing frontmatter as it is.

The body is one or more sections, each a heading grouping bullet links (H1
headings, as in the spec's example):

```markdown
# Section heading

* [Title](relative-url) - short description of the item

# Another section

* [Subdirectory](subdir/) - short description of the subdirectory
```

Separator between link text and description is ` - ` (space-hyphen-space).
Descriptions come from the linked concept's frontmatter `description`.

## `log.md`

Reserved at every level; never a concept; **no frontmatter**. A flat list
of date-grouped entries, newest first, under `## YYYY-MM-DD` headings (the
one MUST). This skill uses the spec's H1 `# Directory Update Log` when it
creates a log; an existing log's H1 is left as it is. Entries are prose
bulleted with a bold lead word by convention (`**Creation**`, `**Update**`,
`**Deprecation**`), with links relative to the log file:

```markdown
# Directory Update Log

## 2026-05-22
* **Update**: Added a BigQuery table reference for [Customer Metrics](tables/customer-metrics.md).
* **Creation**: Established the [Dataplex Playbook](playbooks/dataplex.md).

## 2026-05-15
* **Initialization**: Created foundational directory structure.
```

## Conventional body headings

Not required, but consistent across bundles: `# Schema`, `# Examples`,
`# Computation`. Favor structural markdown — headings, lists, tables,
fenced code blocks — over freeform prose. The body dialect is CommonMark
with GFM tables and `[^label]` footnotes; don't rely on other extensions
(`[[wikilinks]]` are not links in OKF).

## Attested Computation

Covered standalone in `authoring-procedure.md`'s "`type: Attested
Computation`" section. That section is self-contained — read it directly.

## Retire, move, rename

Covered in `authoring-procedure.md`'s "Updating, retiring, moving"
section: keep the file, set `status: deprecated` and `superseded_by`, and
leave a short deprecated stub at an old path.

## What this file omits

Trust-tier computation for readers, source credibility weighing, conflict
resolution, migrating an older bundle, and running the validator. Those
belong to `okf-core`'s `okf-consume` and `okf-generate` skills.
