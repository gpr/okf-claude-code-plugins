# Validating a bundle

No single spec section — see the note on severity below.

The spec's conformance rule (`conformance.md`, §11) is permissive: a
consumer MUST NOT reject a bundle for missing optional fields, unknown
types, broken links, or missing `index.md`. That rule constrains what a
*consumer* may refuse to load — it is not a statement that everything is
equally fine. "Validate this bundle" is a request for a review, and a
review needs severities. Use the three buckets below. Report and
propose fixes; never silently normalize a bundle while "validating" it —
an agent that rewrites `status` or stamps a `generated` block during
validation has gone beyond what was asked.

## Spec violation (bundle is non-conformant)

- A non-reserved `.md` file with no parseable YAML frontmatter block.
- A frontmatter block with a missing or empty `type` field.
- `index.md` or `log.md` used as a concept document (has a `type` field,
  or content that isn't the §8/§9 structure).
- A non-root `index.md` carrying frontmatter other than nothing, or a
  root `index.md` carrying frontmatter keys other than `okf_version`.
- `runtime` missing on a `type: Attested Computation` concept.
- A `log.md` date heading not in ISO 8601 `YYYY-MM-DD` form.

## Advisory (conformant, but worth flagging)

- Missing recommended fields (`title`, `description`) on a concept
  that's clearly resource-bound or user-facing.
- A cross-link (bundle-relative or relative) whose target doesn't exist
  in the bundle.
- `stale_after` in the past (`today >= stale_after`).
- `status: deprecated` still linked from non-deprecated concepts.
- A path-valued field (`resource`, `sources[].resource`, `computation`,
  `executor.resource`, `attester.resource`) that doesn't resolve.
- A footnote label in the body with no matching `sources[].id`.
- An Attested Computation with no `attester` (can't be checked
  mechanically) or no `verified` entry.

## Not an issue

- Unknown `type` values.
- Unknown extra frontmatter keys.
- A directory with no `index.md`.
- Absent trust, provenance, or lifecycle families entirely — a concept
  with only `type` is fully conformant.

## Check order

1. Walk the tree; for every non-reserved `.md`, parse frontmatter and
   check the spec-violation bucket first.
2. For `index.md`/`log.md` files present, check their structure against
   `bundle-structure.md`.
3. For each concept, check the advisory bucket: recommended fields,
   `stale_after`, path-valued fields, footnote/`sources` consistency.
4. For `type: Attested Computation` concepts, additionally check
   `attested-computation.md`'s contract fields are complete and
   internally consistent (e.g. every footnote label has a `sources[].id`,
   `parameters` entries have `name`/`type`/`required`).
5. Summarize: violations first (blocking), then advisories, then a count
   of concepts with no trust/provenance frontmatter (informational, not
   a problem).

## Grep-able patterns

- Missing `type`: frontmatter block present but no `^type:` line.
- Reserved-name misuse: `index.md`/`log.md` files containing `^type:`.
- Bare `verified` mapping (legal, but confirm it's read as one-element
  list downstream, not iterated as a raw string).
- `stale_after: <date>` — compare against today's date.
- Footnote labels: `\[\^([\w-]+)\]` in the body vs `sources[].id` in
  frontmatter.
