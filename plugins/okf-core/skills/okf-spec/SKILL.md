---
name: okf-spec
description: Format reference for the Open Knowledge Format (OKF) v0.3 — bundles of markdown concept documents with YAML frontmatter — plus this plugin set's house rules for writing it. Use when a question is about what an OKF field, file, or rule means (type, sources, generated, verified, status, superseded_by, stale_after, runtime, parameters, computation, executor, attester, okf_version, license, x- extension keys), reserved index.md/log.md files, which .md files are concepts, link and path resolution, trust tiers, actor strings, conformance, versioning, or Attested Computation semantics; or when working in a directory whose index.md declares okf_version and you need the spec text. To produce, migrate, repair, validate, or record a verification, use okf-generate; to answer from a bundle, use okf-consume.
---

# OKF Spec

Source: [`references/SPEC.md`](references/SPEC.md), OKF v0.3, vendored
verbatim from
[open-knowledge-format/open-knowledge-format](https://github.com/open-knowledge-format/open-knowledge-format/blob/main/SPEC.md)
(see `UPSTREAM.md` at the plugin root). It is the normative text; this file is
an index into it plus house rules.

## Which skill

| Task | Use |
|---|---|
| Write, generate, enrich, migrate, repair, or validate a bundle; record a verification | `okf-generate` |
| Answer a question from a bundle; report trust, freshness, attestation | `okf-consume` |
| "What does this field / file / rule mean?" | this skill → the SPEC section below |

## What OKF is

A **bundle** is a directory tree of markdown files. Its root is marked by a
bundle-root `index.md` with frontmatter (§2, §8.1). Inside it (§3.2):

- A **concept** is a `.md` file, not named `index.md` or `log.md`, whose
  frontmatter has a non-empty `type`. Its **concept ID** is its path within
  the bundle without `.md`.
- A `.md` file without frontmatter or without `type` (`README.md`,
  `AGENTS.md`, `SKILL.md`) is **not a concept**. Consumers skip it; it does
  not affect conformance.
- A file not ending in `.md` is an **asset** (images, attester code).
- Names starting with `.` are not part of the bundle; symlinks leaving the
  root are not followed.
- `index.md` and `log.md` are reserved at every level and are never
  concepts, whatever frontmatter they hold. Only the **bundle-root**
  `index.md` may have frontmatter (`okf_version`, `title`, `description`,
  `license`, extension keys); subdirectory `index.md` and every `log.md`
  have none.

A path in a link or a path field resolves three ways (§6): a URI scheme is an
absolute URL; a leading `/` resolves from the bundle root; anything else
resolves from the directory of the file that contains it. A value resolving
outside the bundle root is external — never read it from disk.

## Field cheat sheet

An index, not the specification: read the cited section before answering a
field question.

| Key | Applies to | Meaning | SPEC |
|---|---|---|---|
| `type` | concept | required; freeform kind; consumers accept unknown types | §4.1 |
| `title`, `description` | concept | display name; one-sentence summary | §4.1 |
| `resource` | concept | canonical URI of the underlying asset (path field) | §4.1, §6.2 |
| `tags` | concept | YAML list; a scalar is one tag, never split at commas | §4.1, §11.2 |
| `sources` | concept | provenance entries: `resource` (required), `id`, `title`, `author` (actor), `usage_count`, `last_modified` | §5.1 |
| `usage_window` | concept | `{ from, to }` period for `usage_count` | §5.1 |
| `generated` | concept | `{ by, at }`: last *meaningful* change; `by` required | §5.2 |
| `verified` | concept | list of `{ by, at }` (both required); bare mapping = one item; tier counts only events with `at >= generated.at` | §5.2, §5.3 |
| `status` | concept | `draft \| stable \| deprecated`; absent = `stable`; any other value = not current | §5.4 |
| `superseded_by` | deprecated concept | path of the replacement | §5.4 |
| `stale_after` | concept | instant; stale when `now >= stale_after`; unparseable = never fresh | §5.5 |
| `runtime` | Attested Computation | required; defines what `parameters` mean | §10.2 |
| `parameters` | Attested Computation | `{ name, type, required }`; `name`, `type` required; `required` defaults to `false` | §10.2 |
| `computation` | Attested Computation | path to the computation file, instead of a fenced block | §10.3 |
| `executor` | Attested Computation | `{ resource, receipt }`: run instructions, and the fields a run returns | §10.2 |
| `attester` | Attested Computation | `{ resource }`: deterministic (no-LLM) code returning `{ ok, reason }` | §10.2, §10.5 |
| `okf_version`, `title`, `description`, `license` | bundle-root `index.md` | bundle metadata; `okf_version` quoted, e.g. `"0.3"` | §8.1 |
| `x-<producer>-<name>` | anywhere | extension keys; consumers never reject unknown keys | §4.1 |

Timestamps (`generated.at`, `verified[].at`, `stale_after`,
`sources[].last_modified`, `usage_window.from`/`to`) are RFC 3339 date-times
with an offset, or a full date meaning 00:00 UTC that day (§5).

## SPEC.md section index

`references/SPEC.md` is about 54 KB. Read the line range you need with
`Read` (`offset`/`limit`) or `Grep`, not the whole file.

| Lines | Section |
|---|---|
| 13–47 | §1 Motivation, goals, non-goals |
| 48–73 | §2 Terminology |
| 74–119 | §3 Bundle structure; §3.1 reserved filenames; §3.2 concepts, assets, other files |
| 120–237 | §4 Concept documents: frontmatter syntax, §4.1 fields and extensions, §4.2 body, §4.3–4.4 examples |
| 238–372 | §5 Provenance, trust, lifecycle: timestamps, §5.1 `sources`, §5.2 `generated`/`verified`, §5.3 trust tiers, §5.4 `status`/`superseded_by`, §5.5 `stale_after` |
| 373–420 | §6 Links and paths: resolution, §6.1 links, §6.2 path fields, §6.3 `references/`, §6.4 bundle graph |
| 421–439 | §7 Actor convention |
| 440–482 | §8 Index files; §8.1 bundle metadata |
| 483–503 | §9 Log files |
| 504–649 | §10 Attested computations |
| 650–694 | §11 Conformance; §11.2 consumer rules |
| 695–725 | §12 Versioning; §12.1 older bundles; §12.2 deferred |
| 726–766 | §13 Changes from v0.2 |
| 767–928 | Appendix A: worked example (income statement) |
| 929–943 | Appendix B: changes from v0.1 to v0.2 |

## House rules

House policy for this plugin set, not OKF normative text — don't quote it
back as spec. It only fills in what SPEC.md and `okf-generate` leave open;
where they speak, they win.

- **Actor literal.** For content Claude Code writes, `generated.by` is
  `"claude-code/<model-id>"` (e.g. `"claude-code/claude-opus-5"`) — the
  `<tool>/<model>` form `okf-generate` rule 3 asks for, pinned so bundles
  written by these plugins stay consistent.
- **Timestamps.** Write every timestamp quoted, in UTC with a `Z` suffix.
  Use the date-time form (`"2026-08-09T14:30:00Z"`) for `generated.at` and
  `verified[].at`; the other timestamp keys may be a date (`"2026-12-31"`).
- **Trust fields** follow `okf-generate` rules 4 and 5, restated so they are
  not lost:
  - Never add a `verified` entry to content generated in the same run. Add a
    `human:<id>` entry only when that person confirmed the content, asked for
    it to be recorded, and stated their id; never infer an id from git
    config or a login name.
  - Never write or edit the computation of an Attested Computation. Copy it
    exactly from a sanctioned source and cite it. Without one, describe the
    metric, write no Attested Computation, and report the gap. An unreviewed
    query the user explicitly wants kept is a `type: Reference` with
    `status: draft`, never linked as a computation.
  - Set `executor.resource` / `attester.resource` only to files that exist.
    Otherwise omit the field and say the computation is not attestable yet.
- **Other versions.** If a bundle's root `index.md` declares an
  `okf_version` other than `0.3`, or none, say so. Read it best-effort with
  the §12.1 fallbacks (SPEC lines 695–725), and offer migration through
  `okf-generate` rather than silently rewriting it.

## Scope

`okf-spec` covers format semantics. Bundle discovery, precedence, and
`okf.json` are `okf-reader`'s job; concept authoring workflow, templates,
and type libraries are `okf-writer`'s.
