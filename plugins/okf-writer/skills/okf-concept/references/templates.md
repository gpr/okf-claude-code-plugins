# Templates

The `type: Template` concept contract, slug/norm rules, and the
new-type derivation this skill performs at authoring-procedure.md step 7.

## The `type: Template` contract

`templates/<slug>.md` is itself a conformant OKF concept — real `---`
frontmatter, `type: Template`. That frontmatter carries `title`,
`description`, `status: draft`, and `generated`, exactly like any other
concept.

The skeleton for the *target* type — the frontmatter and body a new
concept of that type should start from — lives in a fenced code block
inside the template's body. **It is never a second `---` block.**

This matters because every `.md` file that isn't `index.md` or `log.md`
is a concept. If a template opened with the target type's frontmatter
(`type: ADR`, ...), any OKF consumer — including this skill's own
type-vocabulary scan at authoring-procedure.md step 1 — would read the
template file itself as a real concept of that type. That would poison
the bundle's type vocabulary (a phantom ADR that is really a template)
and corrupt any index or count built from it. Step 1 of the procedure
guards against a bundle that already has this problem by excluding
`<root>/templates/` when collecting existing concept types — but a
template this skill writes must not create the problem in the first
place.

## `templates/index.md` is the type registry

Entries: `* [<canonical Type>](<slug>.md) - <one line>`. The link text is
the authoritative canonical spelling of `type` for that slug — not
derived from the filename (see reverse lookup, below).

## Slug and normalization rules

```
slug(s):  lowercase → replace each run of non-alphanumeric chars with "-" → trim "-"
norm(s):  slug(s), then drop a trailing "s" from the last token unless it ends in "ss"
```

| Input | `slug` (filename) | `norm` (matching key) |
|---|---|---|
| `ADR` | `adr` | `adr` |
| `ADRs` | `adrs` | `adr` |
| `BigQuery Table` | `bigquery-table` | `bigquery-table` |
| `API Endpoint` | `api-endpoint` | `api-endpoint` |
| `Attested Computation` | `attested-computation` | `attested-computation` |
| `Business Class` | `business-class` | `business-class` |

Acronym and camel-case rule: an intra-word capital never inserts a
hyphen. `BigQuery` → `bigquery`, not `big-query`. `ADR` → `adr`, not
`a-d-r`. Only characters that are literally non-alphanumeric become
separators.

**Filenames use `slug`; matching uses `norm`.** `templates/adrs.md` and
`templates/adr.md` would both match `norm = adr` — if both exist, that's
a pre-existing duplicate in the bundle, and the skill asks which to use
rather than picking.

## Reverse lookup: slug to canonical type

Not computed by un-slugging — casing is unrecoverable (`adr` cannot
yield `ADR`). Two authoritative sources, in order:

1. The link text of the entry in `templates/index.md`.
2. The `type:` value inside the template's skeleton fence — checked when
   the template is actually loaded, and it wins if the two disagree.

This is why authoring-procedure.md step 7 must write its
`templates/index.md` entry with the canonical type string as link text —
that entry is what makes future lookups exact-match without asking.

## Deriving a template from a concept

Runs only for a new type or a type that has no template yet, and only
*after* the concept is written — the template is derived from the file
that was actually produced, not invented ahead of it.

| Part of the written concept | In the derived template |
|---|---|
| `type` value | verbatim — it is what the template selects |
| `title`, `description` values | `<hint>` placeholders |
| `tags` | key kept with `[<tag>, <tag>]` if the concept used it; dropped otherwise |
| `resource` | key kept with `<uri hint>` if the concept used it; dropped otherwise |
| `status` | `draft` |
| `generated` | `{ by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }` |
| `sources` | dropped — provenance is per-concept |
| `verified`, `attester`, `executor.receipt` | never present |
| body headings | verbatim, in order |
| body prose under a heading | one `<what goes here>` line |
| body table | header row kept, data rows collapsed to one placeholder row |
| concrete links, footnotes, values | dropped |

## Worked example

Concept written first (`decisions/choose-duckdb.md`, full text in
`authoring-procedure.md`'s new-type example) produces this derived
template:

`````markdown
---
type: Template
title: ADR template
description: Skeleton for ADR concepts.
status: draft
generated: { by: claude-code/claude-sonnet-5, at: 2026-08-09T10:16:00Z }
---

Skeleton for `type: ADR` concepts. Copy the fence below into a new
file's frontmatter, then fill the body headings. Resolve every
`<placeholder>`.

```yaml
type: ADR
title: <the decision, stated as an action>
description: <one sentence recording what was decided and why>
tags: [<tag>, <tag>]
status: draft
generated: { by: claude-code/<model-id>, at: <RFC 3339 UTC, Z suffix> }
```

# Context

<what forced the decision>

# Decision

<the decision, one sentence, present tense>

# Consequences

- <what gets better>
- <what gets worse>
`````

Note what generalized: `title`/`description`/`tags` values became
placeholders, prose became one-line hints, the `generated` timestamp
became a format hint. Note what stayed: `type: ADR`, `status: draft`,
every heading, the heading order. Note what is absent: `sources`,
`verified`, any concrete link.

Then `templates/index.md` gains:

```markdown
* [ADR](adr.md) - Skeleton for ADR concepts.
```
