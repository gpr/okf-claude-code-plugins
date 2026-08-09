# okf-reader

SessionStart hook that lists a project's OKF knowledge bundles and points at
each bundle's `index.md`; it never reads bundle content. User-facing behaviour
(bundle sources, precedence, discovery rules) is documented in `README.md` —
this file covers what breaks when you edit the implementation.

## File map

- `scripts/okf_context.py` — the hook itself
- `hooks/hooks.json` — registers it on `SessionStart`
- `bin/okf-reader-preview` — subprocess wrapper around the hook; exits 1 on
  empty output, so it doubles as a CI check that a project's bundles resolve
- `agents/okf-search.md` — haiku search agent named in the hook's injected
  `RULES` text
- `examples/` — `okf.json` is referenced directly by `README.md`; `spec/` is a
  standalone fixture demonstrating the `okf_version` marker (mirrors the
  inline example in `README.md`'s Auto-discovery section but isn't itself
  linked from it)
- `tests/test_okf_context.py` — stdlib `unittest`, 19 cases

## Invariants in `scripts/okf_context.py`

An edit must not violate any of these:

- `main()` catches `Exception` and writes to stderr. Never let one escape —
  session startup depends on it.
- No network, anywhere. A non-path source (`github:`, `https:`, ...) resolves
  **only** from the vendored cache dir (the `else` branch in `resolve()`).
- `build_context()` returns `""` when nothing resolves, and `main()` then
  prints nothing. This is the whole "non-OKF projects pay nothing" guarantee —
  don't make it print anything for the empty case.
- Only bundle *locations* are emitted, never content. There's no size cap
  because there's nothing to cap — don't add bundle-content reading without
  revisiting that.
- `okf.json` is untrusted (it ships with the cloned repo). Every value that
  lands in the markdown table goes through `cell()`. A path in `okf.json` that
  resolves inside the project root is rejected in `resolve()` — that bundle is
  already auto-discovered, and honoring the external declaration too would
  create two sources of truth for it.
- Precedence is fixed in `build_context()`: trusted (`standards_bundle`) →
  discovered (auto-discovery) → external (`okf.json`). Don't reorder without
  updating `README.md` and
  `test_precedence_standards_then_discovered_then_external`.

## Adding a `userConfig` key

Three edits, all required:

1. `userConfig` block in `.claude-plugin/plugin.json`
2. `option("<key>", default)` read in `okf_context.py`
3. A matching flag in `bin/okf-reader-preview` (see how `--standards` and
   `--cache-dir` map to `CLAUDE_PLUGIN_OPTION_STANDARDS_BUNDLE` /
   `CLAUDE_PLUGIN_OPTION_CACHE_DIR`)

The default must be repeated identically at every `option()` call site —
`cache_dir`'s default (`.okf/cache`) currently appears at three.

## Token budget

The injected block is prepended to every session in a project with a resolved
bundle. `bin/okf-reader-preview` prints its char and approximate token count
(~214 tokens on this repo) — check it after changing `RULES` or the table
layout in `build_context()`.

## Tests

```
python3 -m unittest discover -s plugins/okf-reader/tests
```

Run from the repo root. `TmpProjectTestCase` builds a throwaway project tree
per test and restores `os.environ` on cleanup. Add a case there for any new
discovery or resolution branch.
