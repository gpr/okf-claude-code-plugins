# OKF essentials for authoring

Claude Code has no inter-plugin dependency mechanism, so `okf-writer` must
write conformant OKF v0.2 files without `okf-core` installed. This file is
the minimum needed to do that.

If the `okf-spec` skill is available, read it for anything this file
doesn't cover — trust tiers, `verified` semantics, Attested Computation
fields, conformance, v0.1 migration — and let it win on any disagreement.

## Concept documents

A concept is one markdown file: YAML `---` frontmatter, then a markdown
body. `type` is the only required frontmatter key. `type` values are
freeform — there is no central registry — and consumers MUST tolerate
unknown types gracefully.

## Writable frontmatter keys

| Key | Meaning |
|---|---|
| `type` | required; kind of concept, freeform |
| `title` | display name |
| `description` | one-sentence summary |
| `resource` | canonical URI of the underlying asset |
| `tags` | list of freeform labels |
| `status` | `draft \| stable \| deprecated`, default `stable` |
| `generated` | `{ by, at }` — who/when last wrote the content |
| `sources` | provenance list |
| `stale_after` | absolute date; concept is stale on/after it |

## Never written by this skill

`verified`, `attester`, `executor.receipt`, and the `computation` body of
an Attested Computation. This is house policy for these plugins, not OKF
normative text — don't quote it back as spec. These fields represent
confirmation or sanctioned logic that must come from a human or a
deterministic process, not from an agent.

## Actor and timestamp conventions

- `generated.by` is `claude-code/<model-id>`, e.g.
  `claude-code/claude-sonnet-5` — the model actually running, not a
  copied literal.
- `generated.at` is RFC 3339, UTC, with a `Z` suffix
  (`2026-08-09T14:30:00Z`).
- Date-only fields (`stale_after`, `usage_window`) are `YYYY-MM-DD`.

## `index.md`

Reserved at every level of the hierarchy; never a concept document.
Carries no frontmatter, except an optional `okf_version` key in the
bundle-root `index.md` only. Body is one or more sections, each an H1
heading grouping bullet links:

```markdown
# Section heading

* [Title](relative-url) - short description of the item

# Another section

* [Subdirectory](subdir/) - short description of the subdirectory
```

Separator between link text and description is ` - ` (space-hyphen-space).
Descriptions SHOULD come from the linked concept's frontmatter
`description`.

## `log.md`

Reserved at every level; never a concept document. Fixed H1
`# Directory Update Log`, then date-grouped entries, newest first, with
`## YYYY-MM-DD` headings (ISO 8601 — MUST). Entries are prose bulleted
with a bold lead word by convention (`**Creation**`, `**Update**`,
`**Deprecation**`):

```markdown
# Directory Update Log

## 2026-05-22
* **Update**: Added a BigQuery table reference for [Customer Metrics](/tables/customer-metrics.md).
* **Creation**: Established the [Dataplex Playbook](/playbooks/dataplex.md).

## 2026-05-15
* **Initialization**: Created foundational directory structure.
```

## Cross-links

A `/`-prefixed path is resolved against the *bundle root* and is the
recommended form. A plain relative path (`./other.md`) is also legal.
Broken links MUST be tolerated by consumers.

## Conventional body headings

Not required, but consistent across bundles: `# Schema`, `# Examples`,
`# Computation`. Favor structural markdown — headings, lists, tables,
fenced code blocks — over freeform prose.

## Attested Computation

Drafting one is covered standalone, without `okf-spec`, in
`authoring-procedure.md`'s "`type: Attested Computation`" section: write
`status: draft`, ask for the required `runtime`, never invent the
computation body, and never write `verified`, `attester`, or
`executor.receipt`. That section is self-contained — read it directly
rather than relying on this file for those fields.

## What this file omits

Trust tiers, the `human:` actor prefix, `usage_window`, source
credibility signals, the `verified`-as-list coercion rule, v0.1→v0.2
migration, and full Attested Computation field semantics (`parameters`
typing, `executor` shape, `attester` verdict codes) beyond what's needed
to draft one, above. These are read-only concerns for a creation skill —
read them from `okf-spec` when it's installed.
