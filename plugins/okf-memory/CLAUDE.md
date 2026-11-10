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
- `bin/okf-memory-prune` — user-run: deletes memories whose source is gone
  and their `index.md` entries (dry run unless `--apply`)
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
- Only a full Read creates a memory, and only one `servable()` would show
  (it has outline entries; its generated part, Notes excluded, is at most
  `MAX_MEMORY_RATIO` of the source). Edit/Write/ranged Read refresh an
  existing one (`create=False`) and print nothing; an existing memory is
  refreshed even when no longer servable, so its notes stay current.
- Outline line numbers must match Read's: split with `outline.split_lines()`
  (`\n` only), never `str.splitlines()`, which also breaks on form feed and
  U+2028.
- `memory_root()` returns None unless `memory_dir` resolves to a
  subdirectory of the project root; every caller treats None as "inactive".
- Memory path keeps the source extension (`file.ext.md`) — changing it to
  `file.md` makes same-stem files collide.
- A memory write (create or regenerate, in `ensure_memory()`) also calls
  `record_in_bundle()`: upsert in the root `index.md`, entry in the root
  `log.md`, under `_BundleLock`. Serving a fresh memory writes nothing.
- `memory_path()` returns None for sources named `index`/`log` in any letter
  case: their memory would be a reserved OKF filename (case-insensitive on
  macOS/Windows).
- Generated files (`is_generated()`: `GENERATED_NAMES`, `GENERATED_DIRS`,
  `*.min.*`) get an outline built with `build_memory()` and served, but are
  never passed to `ensure_memory()`: nothing is written, nothing indexed.
- Nothing in a hook deletes a memory. Deletion lives only in
  `bin/okf-memory-prune`, under `_BundleLock`, and only touches files whose
  frontmatter `type` is `Source Memory`.
- `PRODUCER` (`okf-memory/<version>`) must follow `version` in
  `plugin.json`.
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

## Verifying in a live session

Unit tests feed synthetic payloads. Two assumptions only a real Claude Code
session can check: that Claude Code accepts `updatedToolOutput` for Read,
and that `PostToolUseFailure`'s `additionalContext` reaches the model.
After a Claude Code upgrade, or a change to the reply shape, check both
locally (cloud sessions don't load this repo's plugins):

1. Set `"pluginConfigs": {"okf-memory@okf-cc-plugins": {"max_bytes": "8000"}}`
   in `~/.claude/settings.json`, then start a session in this repo (or run
   `/reload-plugins`).
2. Ask Claude to Read `plugins/okf-memory/scripts/okf_memory.py` in full.
   Expected: the reply opens with `okf-memory: ... this result is its
   memory`, and `.memory/plugins/okf-memory/scripts/okf_memory.py.md`
   exists. If Claude sees the real file, the replacement was dropped.
3. Ask for a ranged Read (`offset`/`limit`) of the same file. Expected: real
   content.
4. Create a file over Read's own size cap and ask for a full Read. Expected:
   Read errors, and Claude still answers from the outline (that comes from
   `additionalContext`).
5. Edit the file from step 2, then Read it in full again. Expected: the
   outline shows the edit; the memory was regenerated.

## Tests

```
python3 -m unittest discover -s plugins/okf-memory/tests
```
