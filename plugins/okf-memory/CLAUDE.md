# okf-memory

PostToolUse / PostToolUseFailure hooks that replace what Claude sees from an
oversized full `Read` with a per-file memory (OKF concept, structural outline
with source line numbers). User-facing behaviour is in `README.md`; this file
covers what breaks when you edit the implementation.

## File map

- `scripts/okf_memory.py` — the hook; dispatches on `hook_event_name` via
  `HANDLERS`
- `scripts/outline.py` — outline strategies: Python `ast`, Markdown headings,
  JSON key tree, tree-sitter (`tree-sitter-language-pack`, optional), regex
  declaration scan for everything in `LANGS`
- `hooks/hooks.json` — `PostToolUse(Read|Edit|Write|MultiEdit)` and
  `PostToolUseFailure(Read)`
- `bin/okf-memory-preview` — simulates PostToolUse after a full read
- `bin/okf-memory-setup` — installs tree-sitter + grammars; the only network
  access in this plugin, and only when a user runs it
- `tests/test_okf_memory.py` — `unittest`; tree-sitter cases use a fake pack,
  plus one real-grammar case that skips when the package is absent

## Invariants

- **Fail open.** `main()` catches `Exception`; any failure prints nothing, so
  Claude sees the tool's own result.
- `replaced_read_output()` only rewrites the `{"type": "text", "file":
  {"content": str}}` shape and keeps every other key. Never synthesize a
  Read output from scratch — Claude Code silently drops a value that does not
  match the tool schema.
- Ranged reads (`offset`/`limit` not None) are never replaced. That is the
  only way Claude can get a big file's real content.
- Stale memories are never served: `ensure_memory()` compares
  `source_sha256` before returning existing content.
- Everything from `NOTES_HEADING` down is preserved verbatim on regeneration
  (`notes_section()`). Don't change the heading text without migrating it.
- Only a full Read creates a memory; Edit/Write/ranged Read refresh an
  existing one (`create=False`) and print nothing.
- Memory path keeps the source extension (`file.ext.md`) — changing it to
  `file.md` makes same-stem files collide.
- **No network in hooks.** `_tree_sitter()` must check
  `downloaded_languages()` before `process()`: the pack downloads a missing
  grammar on demand. `test_uncached_grammar_is_never_requested` guards it.
- tree-sitter is optional: every code path must work when `_language_pack()`
  returns None. It is imported lazily (~45 ms), only when an outline is built.

## Adding a language

tree-sitter: add the grammar name to `DEFAULT_LANGUAGES` in
`bin/okf-memory-setup` (detection comes from the pack). Regex fallback: add
an entry to `LANGS` (ext → name, patterns, flags) in `outline.py`, and an
`_ALIASES` row for extra extensions. Add a case in `OutlineTests`.

## Adding a `userConfig` key

1. `userConfig` in `.claude-plugin/plugin.json`
2. `option("<key>", default)` in `okf_memory.py`
3. A flag in `bin/okf-memory-preview`

## Tests

```
python3 -m unittest discover -s plugins/okf-memory/tests
```
