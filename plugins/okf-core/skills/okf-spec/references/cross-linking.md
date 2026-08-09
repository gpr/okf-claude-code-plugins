# Cross-linking and paths

Covers §6 of OKF v0.2.

## Links between concepts

Concepts MAY link to other concepts using standard markdown links. Two
forms are supported:

- **Absolute (bundle-relative):** begins with `/`, interpreted relative
  to the **bundle root** — not the filesystem root. This is the
  recommended form because it stays stable when documents move within
  their subdirectory.

  ```markdown
  See the [customers table](/tables/customers.md) for the join key.
  ```

- **Relative:** a standard markdown relative path.

  ```markdown
  See the [neighboring concept](./other.md).
  ```

A link from concept A to concept B asserts a relationship; the specific
kind (parent/child, references, joins-with, depends-on) is conveyed by
the surrounding prose, not the link itself. A consumer building a graph
view typically treats all links as directed edges of an untyped
relationship.

Consumers MUST tolerate broken links: a link whose target doesn't exist
in the bundle isn't malformed — it may represent not-yet-written
knowledge.

## Path-valued fields

`resource`, `sources[].resource`, `computation`, `executor.resource`, and
`attester.resource` each name a path or URI. (`sources[].resource` may
instead be a scope descriptor rather than a path — see
`trust-and-provenance.md`.) Each accepts:

- an absolute URL (`https://...`),
- a bundle-relative path beginning with `/`, or
- a relative path (`../computations/revenue.md`).

## The `references/` convention

A `references/` subdirectory conventionally mirrors external material,
run instructions, or code as first-class concepts within the bundle.
`sources`, `executor`, and `attester` entries commonly point into it
(e.g. `references/attesters/revenue.py`). It's a naming convention, not a
requirement.
