# OKF Core

Shared knowledge of the [Open Knowledge Format (OKF)](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md)
for OKF plugins.

Ships one skill, `okf-spec`: the authoritative reference for OKF v0.2 format
semantics — bundle structure, frontmatter fields, provenance and trust,
cross-linking, Attested Computation, and conformance. See
`skills/okf-spec/SKILL.md`.

Also ships one agent, `okf-search`: it locates concepts across a project's
bundles and returns concept IDs with verbatim quotes, never paraphrase. With
`okf-reader` installed, its injected session context points Claude at this
agent; without it, the agent finds bundle roots by their `okf_version`
marker.

`okf-spec` covers format semantics only. It does not cover:

- Bundle discovery, precedence, or `okf.json` — that's `okf-reader`.
- Authoring workflow — that's `okf-writer`.

Claude Code has no inter-plugin dependency mechanism. `okf-writer` and
`okf-driven-dev` expect `okf-core` to be installed alongside them for
format-accurate output, but must still function without it.
