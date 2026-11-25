---
name: okf-concept
description: Authoring workflow for Open Knowledge Format (OKF) v0.3 concept documents — identify the type, apply the matching templates/<type>.md skeleton, write the concept, then derive a new template if the type is new and update index.md and log.md; also retire, rename, or move a concept. Use when asked to "create a concept", "add a concept", "new OKF document", "add an ADR", "add a playbook", "document this table in the bundle", "add a metric/runbook/reference to the knowledge bundle", "start an OKF bundle", "deprecate/retire/rename/move this concept", or when a question involves templates/index.md, deriving or reusing a concept template, choosing a type value, concept filenames and slugs, where a new concept file belongs, index.md entries, or log.md update entries.
---

# OKF Concept

Creates OKF v0.3 concept documents: identifies the `type`, reuses or derives
its `templates/<type>.md` skeleton, writes the concept, and keeps
`index.md`/`log.md` current.

## What this does

Given a request naming a concept to add, this skill finds the bundle, works
out whether the requested type already exists, fills in (or invents) a
skeleton, writes one file, and updates the bookkeeping files a bundle
depends on for discovery — the two steps most often forgotten: adding the
concept to its directory's `index.md`, and logging the change.

## Procedure

Step numbers match `references/authoring-procedure.md` — read it before
writing files. Steps 1–6 read and decide only; every write comes after
the confirm at step 6.

1. **Find the bundle root.** Use okf-reader's injected bundle table if
   present; otherwise scan for directories whose `index.md` declares
   `okf_version`, with okf-reader's depth and skip rules. Zero found,
   more than one found and ambiguous, or the sole candidate is the
   trusted (`standards_bundle`) bundle: ask.
2. **Read the type vocabulary.** `<root>/templates/index.md` is the
   registry — link text is the canonical `type`, link target is
   `templates/<slug>.md`. Add the `type:` values of existing concepts
   outside `templates/`.
3. **Identify the `type`.** Compare `norm(requested)` against each known
   type; the first pass with a hit decides. Exact match: reuse the
   bundle's spelling, no question. Acronym or containment near-match:
   ask existing-vs-new (one question, even with several hits). No match:
   new type.
4. **Choose the skeleton source** — decide only, write nothing. In
   order: the type's template; else, if the type is in use with no
   template, derive from its newest concept (mark new-template); else,
   if `okf-type-library` catalogs it, plan to install that one template
   (mark catalog-install, not new-template); else invent it (mark
   new-template).
5. **Choose directory and filename.** User-named directory; else follow
   existing concepts of this type; else `<root>/<plural-slug>/` in a
   foldered bundle of 5+ concepts; else `<root>/`. The last two are
   flagged *no precedent* at the confirm. Filename is `slug(title).md`;
   if that slugs to `index` or `log`, ask for a different title
   instead. Never overwrite.
6. **Confirm once.** Show root, type (existing or new), path (flagged if
   no precedent), title, description, and the skeleton source.
7. **Write the concept.** On catalog-install, first install the one
   template via `okf-type-library`'s single-type mode. Set `type`,
   `title`, `description`, `status: draft`, `generated` (quoted
   `"claude-code/<model>"` and `"<YYYY-MM-DDTHH:MM:SSZ>"`). Record
   `sources` with footnotes keyed by source `id` for what you drew from;
   write nothing a source doesn't support. Resolve or delete every
   `<placeholder>`; delete headings with nothing under them.
8. **New template only — derive `templates/<slug>.md` afterwards.** The
   type value and the headings stay; values and prose become
   placeholders. Its own frontmatter is `type: Template`; the skeleton
   is a fenced code block in the body, never a second `---` block. Add
   its entry to `templates/index.md`, back-filling the index if it is
   new.
9. **Update indexes.** The concept's own directory `index.md` (create if
   missing); the parent chain only when a directory is new. Entries are
   `* [Title](relative-path) - description`, description copied from the
   concept's frontmatter. Only the bundle-root `index.md` has frontmatter
   (a new one gets `okf_version: "0.3"`, `title`, `description`); keep an
   existing one's frontmatter as it is.
10. **Append to the bundle-root `log.md`.** Create with
    `# Directory Update Log` if absent, never with frontmatter. Today's
    `## YYYY-MM-DD` heading goes directly under the H1, above older dates.
    One `**Creation**` bullet for the concept, one more for a derived
    template, both with links relative to the bundle root.
11. **Self-check, validate, and report** every file written, unsourced
    facts, and concepts needing re-verification; run `okf-generate`'s
    validator when that skill is available.

## Ask vs. decide

| Decide silently | Must ask |
|---|---|
| Slug mechanics, index/log formatting, insertion position | Which bundle, when more than one is found and the request is ambiguous, or when the sole candidate is the trusted bundle |
| Which frontmatter keys to include | Existing-vs-new on an acronym/containment hit |
| Which template headings to keep or drop | Target directory when no precedent exists — shown at the confirm, flagged |
| The `generated` timestamp | Overwriting or editing an existing file, or a filename that would collide with a reserved name |
| | A `stale_after` date — only from a review cycle the user or a source states; never guessed |

## Trust fields

House policy for these plugins, aligned with `okf-generate` — not OKF
normative text:

- Never add `verified` to content written in the same run. Record a
  `human:<id>` verification only when that person confirmed the content,
  asked for it, and stated their id; never infer an id from git config.
- Never write or edit the computation of an Attested Computation. Copy it
  verbatim from a sanctioned source, or write no Attested Computation and
  report the gap.
- Write `executor` / `attester` only when the files they point at exist.

See `references/authoring-procedure.md`'s Attested Computation and
"Updating, retiring, moving" sections.

## Task → reference

| Task | Read |
|---|---|
| Any step of the authoring procedure, in full | `references/authoring-procedure.md` |
| The `type: Template` contract, slug/norm rules, deriving a template | `references/templates.md` |
| Retire, rename, move, or update a concept; record a verification | `references/authoring-procedure.md` — "Updating, retiring, moving" |
| OKF v0.3 format rules (links, paths, `sources`, root `index.md`, `log.md`) | `references/okf-essentials.md` |

Read the matching reference before writing files. Paths are relative to
this skill's directory.

## Scope

`okf-concept` covers authoring workflow only. Format semantics (frontmatter
fields, trust tiers, conformance) belong to `okf-core` — its
`okf-generate` and `okf-spec` skills — read via
`references/okf-essentials.md` when those aren't installed and deferred
to when they are. Bootstrapping a bundle from external sources (schemas,
docs), migrating an older bundle, and answering from a bundle are
`okf-generate`'s and `okf-consume`'s jobs. Bundle discovery, precedence, and `okf.json` belong
to `okf-reader`. Seeding a bundle with a starter set of types, before any
concept of those types exists, belongs to `okf-type-library` (same plugin).
