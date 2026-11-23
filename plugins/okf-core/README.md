# OKF Core

Shared knowledge of the [Open Knowledge Format (OKF)](https://github.com/open-knowledge-format/open-knowledge-format/blob/main/SPEC.md)
v0.3 for OKF plugins.

Ships three skills:

- `okf-generate` and `okf-consume` — the official OKF agent skills, vendored
  verbatim from the
  [OKF repository](https://github.com/open-knowledge-format/open-knowledge-format)
  (Apache-2.0; pinned commit in [`UPSTREAM.md`](UPSTREAM.md)).
  `okf-generate` writes, migrates, repairs, and validates bundles and records
  verifications; `okf-consume` answers from a bundle and reports provenance,
  trust tier, freshness, and attestation.
- `okf-spec` — the format reference: the vendored v0.3 `SPEC.md` with a
  section index, a field cheat sheet, and this plugin set's house rules
  (actor literal, timestamp form, trust-field policy). See
  `skills/okf-spec/SKILL.md`.

Also ships one agent, `okf-search`: it locates concepts across a project's
bundles and returns concept IDs with verbatim quotes, never paraphrase, plus
each concept's status, trust tier, and freshness. With `okf-reader`
installed, its injected session context points Claude at this agent; without
it, the agent finds bundle roots itself (a root `index.md` with frontmatter).

## Optional scripts

`okf-generate/scripts/validate.py` and `okf-consume/scripts/scan.py` need
Python 3.9+ and PyYAML (`pip install pyyaml`). They are optional: without
them the skills fall back to checking the rules by hand. No hook runs them.

## Don't also install upstream `okf`

The OKF repository publishes the same two skills as its own plugin, `okf`.
Installing both gives Claude two copies of `okf-generate` and `okf-consume`
competing for the same requests; install one or the other.

## Scope

`okf-core` covers format semantics and generic produce/consume procedures.
It does not cover:

- Bundle discovery, precedence, or `okf.json` — that's `okf-reader`.
- Concept authoring workflow, templates, and type libraries — that's
  `okf-writer`.

Claude Code has no inter-plugin dependency mechanism. `okf-writer` and
`okf-driven-dev` expect `okf-core` to be installed alongside them for
format-accurate output, but must still function without it.
