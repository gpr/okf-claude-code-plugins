# Conformance, versioning, and v0.1 → v0.2 migration

Covers §11, §12, §13 of OKF v0.2.

## Conformance

A bundle is conformant with OKF v0.2 if:

1. Every non-reserved `.md` file in the tree contains a parseable YAML
   frontmatter block.
2. Every frontmatter block contains a non-empty `type` field.
3. Every reserved filename (`index.md`, `log.md`) follows the structure
   in `bundle-structure.md` when present.

When the trust, lifecycle, provenance, or computation families are
present, producers SHOULD follow the conventions in
`trust-and-provenance.md` / `attested-computation.md`, and consumers:

- MUST treat a bare `verified` mapping as a one-element list.
- MUST NOT reject a concept for missing any optional family.
- SHOULD derive trust tiers and staleness only from the fields specified
  in the spec, and SHOULD surface, not silently drop, a failing
  attestation.

Consumers SHOULD treat all other constraints as soft guidance. In
particular, consumers MUST NOT reject a bundle because of: missing
optional frontmatter fields, unknown `type` values, unknown additional
frontmatter keys, broken cross-links, or missing `index.md` files.

This permissive stance means "conformant" and "clean" are different
questions — for the latter, see `validation-checklist.md`.

## Versioning

OKF revisions are versioned `<major>.<minor>`:

- A **minor** bump introduces backward-compatible additions (new
  optional fields, new conventional section headings).
- A **major** bump may make breaking changes (renaming required fields,
  changing reserved filenames).

Bundles MAY declare the version they target with `okf_version: "0.2"` in
a bundle-root `index.md` frontmatter block — the only place frontmatter
is permitted in an `index.md`. Consumers that don't understand the
declared version SHOULD attempt best-effort consumption rather than
refusing the bundle.

## Changes from v0.1

v0.2 supersedes v0.1. Two changes are breaking; the rest are additive. A
v0.1 bundle is consumable by a v0.2 consumer under the fallbacks noted
here.

**Breaking:**

- `timestamp` is superseded by `generated.at`. A concept's last content
  change is now `generated: {by, at}`. Consumers MAY fall back to a
  legacy `timestamp` when `generated` is absent.
- The body `# Citations` list is superseded by `sources` in frontmatter.
  Consumers SHOULD read `sources` and MAY still parse a legacy
  `# Citations` body list for v0.1 documents.

**Additive** (absence yields a plain v0.1 concept):

- New frontmatter families: `sources` with its credibility signals
  (`author`, `usage_count`, `last_modified`) and the `usage_window`
  sibling; `generated`, `verified`; `status`, `stale_after`.
- New concept type `Attested Computation` and its keys `runtime`,
  `parameters`, `computation`, `executor`, `attester`.
- New conventional body heading `# Computation`.
- The actor convention for `generated.by` and `verified[].by`.

Everything else (bundle structure, reserved filenames, the required
`type`, recommended `title`/`description`/`resource`/`tags`,
cross-linking, index files, log files, permissive conformance) carries
forward unchanged.

## Migrating a concept

1. Rename `timestamp` → `generated: { by: <actor>, at: <same datetime> }`.
   If the original author is unknown, use a `process:` or
   `reference_agent/` actor that reflects how the migration ran — never
   fabricate a `human:` actor.
2. Convert a body `# Citations` list into `sources` entries (`resource`
   per line, `id` synthesized if footnote attribution is added later).
3. Leave `verified`, `status`, `stale_after` absent unless there's a real
   basis to set them — do not invent verification history.
4. See `worked-example.md` for a full v0.1 → v0.2 diff of one concept.
