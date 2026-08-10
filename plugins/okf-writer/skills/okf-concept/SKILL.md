---
name: okf-concept
description: Authoring workflow for Open Knowledge Format (OKF) v0.2 concept documents — identify the type, apply the matching templates/<type>.md skeleton, write the concept, then derive a new template if the type is new and update index.md and log.md. Use when asked to "create a concept", "add a concept", "new OKF document", "add an ADR", "add a playbook", "document this table in the bundle", "add a metric/runbook/reference to the knowledge bundle", "start an OKF bundle", or when a question involves templates/index.md, deriving or reusing a concept template, choosing a type value, concept filenames and slugs, where a new concept file belongs, index.md entries, or log.md update entries.
---

# OKF Concept

Creates OKF v0.2 concept documents: identifies the `type`, reuses or derives
its `templates/<type>.md` skeleton, writes the concept, and keeps
`index.md`/`log.md` current.

## What this does

Given a request naming a concept to add, this skill finds the bundle, works
out whether the requested type already exists, fills in (or invents) a
skeleton, writes one file, and updates the bookkeeping files a bundle
depends on for discovery — the two steps `bundle-structure.md` calls out as
"commonly forgotten": adding the concept to its directory's `index.md`, and
logging the change.

## Procedure

Steps 1–6 write nothing. Full detail for every step is in
`references/authoring-procedure.md` — read it before writing files.

1. **Find the bundle root.** Use okf-reader's injected bundle table if
   present; otherwise find directories whose `index.md` declares
   `okf_version`. Zero found, more than one found and ambiguous, or the
   sole candidate is the trusted (`standards_bundle`) bundle: ask.
2. **Read the type vocabulary.** `<root>/templates/index.md` is the
   registry — link text is the canonical `type`, link target is
   `templates/<slug>.md`. Add the `type:` values of existing concepts
   outside `templates/`.
3. **Identify the `type`.** Compare `norm(requested)` against each known
   type. Exact match: reuse the bundle's spelling, no question. Acronym
   or containment near-match: ask existing-vs-new. No match: new type.
4. **Load the skeleton** from `templates/<slug>.md` — its body fence
   becomes the new frontmatter, its headings become the new body. No
   template: invent the skeleton and mark the run new-template.
5. **Choose directory and filename.** Follow existing concepts of this
   type; else `<root>/<plural-slug>/`; else `<root>/`. Filename is
   `slug(title).md`; if that slugs to `index` or `log`, ask for a
   different title instead. Never overwrite.
6. **Confirm once.** Show root, type (existing or new), path, title,
   description, and whether a template will be derived.
7. **Write the concept.** Set `type`, `title`, `description`,
   `status: draft`, `generated`. Resolve or delete every
   `<placeholder>`; delete headings with nothing under them.
8. **New type only — derive `templates/<slug>.md` afterwards.** The type
   value and the headings stay; values and prose become placeholders.
   Its own frontmatter is `type: Template`; the skeleton is a fenced
   code block in the body, never a second `---` block. Add its entry
   to `templates/index.md`.
9. **Update indexes.** The concept's own directory `index.md` (create if
   missing); the parent chain only when a directory is new. Entries are
   `* [Title](relative-path) - description`, description copied from the
   concept's frontmatter.
10. **Append to the bundle-root `log.md`.** Create with
    `# Directory Update Log` if absent. Today's `## YYYY-MM-DD` heading
    goes directly under the H1, above older dates. One `**Creation**`
    bullet for the concept, one more for a derived template, both with
    `/`-rooted links.

Then report every file written and confirm no `<placeholder>` survived.

## Ask vs. decide

| Decide silently | Must ask |
|---|---|
| Slug mechanics, index/log formatting, insertion position | Which bundle, when more than one is found and the request is ambiguous, or when the sole candidate is the trusted bundle |
| Which frontmatter keys to include | Existing-vs-new on an acronym/containment hit |
| Which template headings to keep or drop | Target directory when no precedent exists |
| The date/timestamp values | Overwriting or editing an existing file, or a filename that would collide with a reserved name |

## Never written by this skill

`verified`, `attester`, `executor.receipt`, and the `computation` body of
an Attested Computation. These are house policy for these plugins, not
OKF normative text — they represent human or deterministic-process
confirmation. An Attested Computation is still drafted, not refused: see
`references/authoring-procedure.md`.

## Task → reference

| Task | Read |
|---|---|
| Any step of the authoring procedure, in full | `references/authoring-procedure.md` |
| The `type: Template` contract, slug/norm rules, deriving a template | `references/templates.md` |
| Format rules with `okf-core` not installed | `references/okf-essentials.md` |

Read the matching reference before writing files. Paths are relative to
this skill's directory.

## Scope

`okf-concept` covers authoring workflow only. Format semantics (frontmatter
fields, trust tiers, conformance) belong to `okf-spec` (`okf-core`), read
via `references/okf-essentials.md` when that skill isn't installed and
deferred to when it is. Bundle discovery, precedence, and `okf.json` belong
to `okf-reader`.
