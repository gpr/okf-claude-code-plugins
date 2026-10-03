# OKF Writer

Authors [Open Knowledge Format (OKF)](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md)
concept documents.

Ships two skills, `okf-concept` and `okf-type-library`.

`okf-concept`: given a request like "add an ADR recording
why we chose DuckDB" or "add a playbook for rotating the on-call pager", it

1. finds the bundle root and identifies the concept `type` from the request,
   reusing an existing type's spelling when one matches;
2. picks a skeleton: the type's `templates/<type>.md` if it has one; else
   one derived from the bundle's existing concepts of that type; else,
   for a type new to the bundle, the matching `okf-type-library` catalog
   template; else an invented one;
3. confirms once, before writing anything;
4. writes the concept (installing the catalog template first, if that
   was the choice);
5. if it had no template to start from, derives `templates/<type>.md`
   from the concept it just wrote, and registers it in
   `templates/index.md`;
6. updates the concept's directory `index.md` (and its parent, if the
   directory is new) and appends an entry to the bundle-root `log.md`.

See `skills/okf-concept/SKILL.md`.

## Templates are concepts

`templates/<type>.md` files are themselves conformant OKF concepts —
`type: Template` frontmatter, with the target type's skeleton held in a
fenced code block in the body, never as a second frontmatter block. This
keeps a bundle's `templates/` directory spec-conformant instead of seeding it
with fake ADRs or Metrics.

## Starting from a catalog

`okf-type-library` ships 16 ready-made type templates — Specification,
Requirement, Plan Item, ADR, Technology, Dependency, and ten more. Ask it
to "set up the types for spec-driven development" and it installs the
five that matter for that workflow, registers them in
`templates/index.md`, and logs the change. It installs a subset, never
all 16 at once: an unused type sitting in the registry biases every
later `okf-concept` run toward it. See
`skills/okf-type-library/SKILL.md`.

## What it never writes

`verified`, `attester`, `executor.receipt`, and the `computation` body of an
Attested Computation — these represent confirmation or sanctioned logic that
must come from a human or a deterministic process, not from an agent.

## Standalone

Claude Code has no inter-plugin dependency mechanism. `okf-writer` restates
the minimum OKF byte-level rules it needs and works without `okf-core`
installed — see `skills/okf-concept/references/okf-essentials.md`. When
`okf-spec` (from `okf-core`) is available, it takes precedence on anything
`okf-essentials.md` doesn't cover.
