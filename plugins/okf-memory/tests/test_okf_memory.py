#!/usr/bin/env python3
"""Tests for scripts/okf_memory.py and scripts/outline.py.

Run with: python3 -m unittest discover -s plugins/okf-memory/tests -v
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import okf_memory  # noqa: E402
import outline  # noqa: E402


def write(root: Path, rel: str, content: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def big_python(n: int = 40) -> str:
    chunks = ['"""Module doc."""\nimport os\nfrom pathlib import Path\n\nLIMIT = 3\n']
    for i in range(n):
        body = "\n".join(f"    x{j} = {j} * {i}  # padding padding padding" for j in range(12))
        chunks.append(f'\ndef func_{i}(a: int, b: str = "x") -> int:\n    """Doc {i}."""\n{body}\n    return a\n')
    chunks.append("\nclass Thing(Base):\n    \"\"\"A thing.\"\"\"\n\n    def method(self):\n        pass\n")
    return "".join(chunks)


class TmpProjectTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.root = Path(self._tmpdir.name).resolve()
        self._env = dict(os.environ)
        self.addCleanup(lambda: os.environ.clear() or os.environ.update(self._env))
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.root)
        for key in ("MAX_BYTES", "MEMORY_DIR"):
            os.environ.pop(f"CLAUDE_PLUGIN_OPTION_{key}", None)

    def run_hook(self, payload: dict) -> tuple[str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), \
                unittest.mock.patch("sys.stdin", io.StringIO(json.dumps(payload))):
            okf_memory.main()
        return out.getvalue(), err.getvalue()

    def pre(self, path: Path, **tool_input) -> tuple[str, str]:
        """A Read of `path` as PostToolUse sees it: the tool already ran."""
        content = path.read_text(errors="replace")
        n = content.count("\n") + 1
        return self.run_hook({
            "hook_event_name": "PostToolUse", "tool_name": "Read", "cwd": str(self.root),
            "tool_input": {"file_path": str(path), **tool_input},
            "tool_response": {"type": "text", "file": {
                "filePath": str(path), "content": content,
                "numLines": n, "startLine": 1, "totalLines": n}},
        })

    def shown(self, out: str) -> str:
        """What Claude would see, from the hook's stdout."""
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PostToolUse")
        return hso["updatedToolOutput"]["file"]["content"]

    def post(self, tool: str, path: Path) -> tuple[str, str]:
        return self.run_hook({
            "hook_event_name": "PostToolUse", "tool_name": tool, "cwd": str(self.root),
            "tool_input": {"file_path": str(path)},
        })


class PreReadTests(TmpProjectTestCase):
    def test_small_file_passes_through_silently(self):
        src = write(self.root, "small.py", "x = 1\n")
        out, err = self.pre(src)
        self.assertEqual((out, err), ("", ""))
        self.assertFalse((self.root / ".memory").exists())

    def test_big_file_output_is_replaced_by_memory_and_memory_is_written(self):
        src = write(self.root, "pkg/mod.py", big_python())
        out, _ = self.pre(src)
        reason = self.shown(out)
        updated = json.loads(out)["hookSpecificOutput"]["updatedToolOutput"]
        self.assertEqual(updated["type"], "text")
        self.assertEqual(updated["file"]["filePath"], str(src))
        self.assertEqual(updated["file"]["numLines"], reason.count("\n") + 1)
        self.assertIn("def func_0(a: int, b: str='x') -> int", reason)
        self.assertIn("class Thing(Base)", reason)
        mem = self.root / ".memory/pkg/mod.py.md"
        self.assertTrue(mem.is_file())
        self.assertIn(mem.read_text(), reason)

    def test_ranged_read_is_never_intercepted(self):
        src = write(self.root, "mod.py", big_python())
        self.assertEqual(self.pre(src, offset=1, limit=50)[0], "")
        self.assertEqual(self.pre(src, limit=10)[0], "")
        self.assertEqual(self.pre(src, offset=0)[0], "")

    def test_outside_project_passes_through(self):
        with tempfile.TemporaryDirectory() as other:
            src = write(Path(other), "mod.py", big_python())
            self.assertEqual(self.pre(src)[0], "")

    def test_memory_dir_itself_is_not_intercepted(self):
        src = write(self.root, ".memory/huge.md", "# h\n" + "x" * 50000)
        self.assertEqual(self.pre(src)[0], "")

    def test_binary_passes_through(self):
        src = self.root / "blob.dat"
        src.write_bytes(b"\0\1\2" * 20000)
        self.assertEqual(self.pre(src)[0], "")

    def test_no_outline_means_no_interception(self):
        src = write(self.root, "data.unknownext", "plain text line\n" * 3000)
        self.assertEqual(self.pre(src)[0], "")

    def test_max_bytes_option_and_zero_disables(self):
        src = write(self.root, "mod.py", big_python())
        os.environ["CLAUDE_PLUGIN_OPTION_MAX_BYTES"] = "0"
        self.assertEqual(self.pre(src)[0], "")
        os.environ["CLAUDE_PLUGIN_OPTION_MAX_BYTES"] = str(src.stat().st_size + 1)
        self.assertEqual(self.pre(src)[0], "")

    def test_memory_dir_option(self):
        src = write(self.root, "mod.py", big_python())
        os.environ["CLAUDE_PLUGIN_OPTION_MEMORY_DIR"] = "kb/mem"
        self.assertNotEqual(self.pre(src)[0], "")
        self.assertTrue((self.root / "kb/mem/mod.py.md").is_file())

    def test_same_stem_different_ext_do_not_collide(self):
        a = write(self.root, "app.py", big_python())
        b = write(self.root, "app.js", "\n".join(f"export function f{i}(a) {{\n" + "  return a;\n" * 20 + "}" for i in range(120)))
        self.pre(a), self.pre(b)
        self.assertTrue((self.root / ".memory/app.py.md").is_file())
        self.assertTrue((self.root / ".memory/app.js.md").is_file())

    def test_stale_memory_is_regenerated_and_notes_survive(self):
        src = write(self.root, "mod.py", big_python())
        self.pre(src)
        mem = self.root / ".memory/mod.py.md"
        mem.write_text(mem.read_text().replace(
            okf_memory.NOTES_PLACEHOLDER, "# Notes\n\nfunc_3 is the hot path.\n"))
        src.write_text(big_python() + "\ndef added_later():\n    pass\n")
        reason = self.shown(self.pre(src)[0])
        self.assertIn("def added_later()", reason)
        self.assertIn("func_3 is the hot path.", reason)
        self.assertIn("func_3 is the hot path.", mem.read_text())

    def test_fresh_memory_is_served_as_is(self):
        src = write(self.root, "mod.py", big_python())
        self.pre(src)
        mem = self.root / ".memory/mod.py.md"
        mem.write_text(mem.read_text() + "\nhand edit\n")
        self.assertIn("hand edit", self.pre(src)[0])

    def test_unknown_output_shape_is_left_alone(self):
        src = write(self.root, "mod.py", big_python())
        for response in ({"type": "file_unchanged", "file": {"filePath": str(src)}},
                         "1\tplain string", None):
            out, _ = self.run_hook({
                "hook_event_name": "PostToolUse", "tool_name": "Read", "cwd": str(self.root),
                "tool_input": {"file_path": str(src)}, "tool_response": response})
            self.assertEqual(out, "")
        self.assertTrue((self.root / ".memory/mod.py.md").is_file())

    def test_failed_full_read_gets_memory_as_context(self):
        src = write(self.root, "mod.py", big_python())
        out, _ = self.run_hook({
            "hook_event_name": "PostToolUseFailure", "tool_name": "Read", "cwd": str(self.root),
            "tool_input": {"file_path": str(src)}, "error": "File content exceeds maximum"})
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PostToolUseFailure")
        self.assertIn("def func_0", hso["additionalContext"])

    def test_failed_ranged_read_gets_nothing(self):
        src = write(self.root, "mod.py", big_python())
        out, _ = self.run_hook({
            "hook_event_name": "PostToolUseFailure", "tool_name": "Read", "cwd": str(self.root),
            "tool_input": {"file_path": str(src), "offset": 5}, "error": "x"})
        self.assertEqual(out, "")

    def test_garbage_input_never_raises(self):
        for payload in ("not json", json.dumps({"hook_event_name": "PostToolUse", "tool_name": "Read",
                                                 "tool_input": {"file_path": 42}})):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err), \
                    unittest.mock.patch("sys.stdin", io.StringIO(payload)):
                okf_memory.main()
            self.assertEqual(out.getvalue(), "")


class PostToolTests(TmpProjectTestCase):
    def test_post_refreshes_existing_memory_after_edit(self):
        src = write(self.root, "mod.py", big_python())
        self.pre(src)
        src.write_text(big_python() + "\ndef edited():\n    pass\n")
        self.assertEqual(self.post("Edit", src), ("", ""))
        self.assertIn("def edited()", (self.root / ".memory/mod.py.md").read_text())

    def test_edit_write_and_ranged_read_never_create_a_memory(self):
        src = write(self.root, "mod.py", big_python())
        self.post("Write", src)
        self.post("Edit", src)
        self.pre(src, offset=1, limit=20)
        self.assertFalse((self.root / ".memory").exists())


class BundleTests(TmpProjectTestCase):
    """The memory dir is an OKF bundle: root index.md and log.md track every write."""

    def test_reply_points_at_grep_on_the_source(self):
        src = write(self.root, "pkg/mod.py", big_python())
        self.assertIn("use Grep on `pkg/mod.py`", self.shown(self.pre(src)[0]))

    def test_resource_and_source_resolve_from_the_concept(self):
        src = write(self.root, "pkg/sub/mod.py", big_python())
        self.pre(src)
        mem = self.root / ".memory/pkg/sub/mod.py.md"
        meta = okf_memory.read_frontmatter(mem.read_text())
        self.assertEqual(meta["resource"], "../../../pkg/sub/mod.py")
        self.assertEqual((mem.parent / meta["resource"]).resolve(), src)
        self.assertIn('resource: "../../../pkg/sub/mod.py"', meta["sources"])
        self.assertTrue(meta["generated"].startswith("{ by: okf-memory/"))

    def test_creation_writes_root_index_and_log(self):
        self.pre(write(self.root, "pkg/mod.py", big_python()))
        self.pre(write(self.root, "app.py", big_python()))
        index = (self.root / ".memory/index.md").read_text()
        self.assertTrue(index.startswith('---\nokf_version: "0.2"\n---\n\n# Source Memories\n'))
        n = big_python().count("\n")
        entries = [ln for ln in index.splitlines() if ln.startswith("* [")]
        self.assertEqual(entries, [
            f"* [app.py](app.py.md) - Structural outline of app.py (Python, {n} lines).",
            f"* [pkg/mod.py](pkg/mod.py.md) - Structural outline of pkg/mod.py (Python, {n} lines).",
        ])
        log = (self.root / ".memory/log.md").read_text().splitlines()
        self.assertEqual(log[0], "# Memory Update Log")
        self.assertRegex(log[2], r"^## \d{4}-\d{2}-\d{2}$")
        self.assertEqual(log[3:5], [
            "* **Creation**: Memory of the source file, [app.py](app.py.md).",
            "* **Creation**: Memory of the source file, [pkg/mod.py](pkg/mod.py.md).",
        ])

    def test_refresh_updates_index_entry_and_logs_once_per_day(self):
        src = write(self.root, "mod.py", big_python())
        self.pre(src)
        for i in range(3):
            src.write_text(big_python() + f"\ndef edit_{i}():\n    pass\n")
            self.post("Edit", src)
        index = (self.root / ".memory/index.md").read_text()
        self.assertEqual(index.count("](mod.py.md)"), 1)
        self.assertIn(f"(Python, {big_python().count(chr(10)) + 3} lines)", index)
        log = (self.root / ".memory/log.md").read_text()
        self.assertEqual(log.count("**Update**"), 1)
        self.assertEqual(log.count("**Creation**"), 1)
        self.assertLess(log.index("**Update**"), log.index("**Creation**"))

    def test_fresh_memory_served_again_does_not_touch_the_log(self):
        src = write(self.root, "mod.py", big_python())
        self.pre(src)
        log = self.root / ".memory/log.md"
        before = log.read_text()
        self.pre(src)
        self.assertEqual(log.read_text(), before)

    def test_existing_index_and_log_content_is_kept(self):
        write(self.root, ".memory/index.md", "# Hand-made\n\n* [Guide](guide.md) - mine\n")
        write(self.root, ".memory/log.md",
              "# Memory Update Log\n\n## 2000-01-01\n* **Initialization**: Created.\n")
        self.pre(write(self.root, "mod.py", big_python()))
        index = (self.root / ".memory/index.md").read_text()
        self.assertTrue(index.startswith("# Hand-made\n\n* [Guide](guide.md) - mine\n"))
        self.assertNotIn("okf_version", index)
        self.assertIn("# Source Memories\n\n* [mod.py](mod.py.md)", index)
        log = (self.root / ".memory/log.md").read_text()
        self.assertLess(log.index("**Creation**"), log.index("## 2000-01-01"))
        self.assertIn("* **Initialization**: Created.", log)

    def test_reserved_names_never_get_a_memory(self):
        for name in ("index", "log", "docs/index"):
            src = write(self.root, name, big_python())
            self.assertEqual(self.pre(src)[0], "")
        self.assertFalse((self.root / ".memory").exists())

    def test_link_is_url_quoted_and_label_escaped(self):
        self.pre(write(self.root, "my dir/a[1].py", big_python()))
        index = (self.root / ".memory/index.md").read_text()
        self.assertIn("* [my dir/a\\[1\\].py](my%20dir/a%5B1%5D.py.md) - ", index)


class OutlineTests(unittest.TestCase):
    def setUp(self) -> None:
        # Regex/stdlib strategies are tested without tree-sitter, whatever is installed.
        patcher = unittest.mock.patch.object(outline, "_language_pack", return_value=None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_python_tree_has_spans_signatures_and_nesting(self):
        _, entries = outline.outline(Path("m.py"), big_python(2))
        text = "\n".join(entries)
        self.assertIn("imports: os, pathlib", text)
        self.assertIn("LIMIT = …", text)
        self.assertRegex(text, r"L\d+-\d+: def func_1\(a: int, b: str='x'\) -> int  # Doc 1\.")
        self.assertRegex(text, r"L\d+-\d+:   def method\(self\)")

    def test_python_syntax_error_falls_back_to_scan(self):
        method, entries = outline.outline(Path("m.py"), "def ok():\n    pass\ndef broken(:\n")
        self.assertIn("declaration scan", method)
        self.assertEqual(len(entries), 2)

    def test_markdown_headings_skip_code_fences(self):
        md = "# Top\n\n```sh\n# not a heading\n```\n\n## Sub\n"
        _, entries = outline.outline(Path("x.md"), md)
        self.assertEqual(entries, ["L1: Top", "L7:   Sub"])

    def test_typescript_scan(self):
        ts = ("export interface Foo {\n  a: number;\n}\n"
              "export const f = async (x: number) => x;\n"
              "class Bar {\n  private baz(x: number): void {\n    if (x) {\n    }\n  }\n}\n")
        _, entries = outline.outline(Path("x.ts"), ts)
        self.assertEqual([e.split(":")[0] for e in entries], ["L1", "L4", "L5", "L6"])

    def test_json_key_tree(self):
        _, entries = outline.outline(Path("x.json"), json.dumps({"a": {"b": [1, 2]}, "c": "s"}))
        self.assertEqual(entries, ["$: object{2}", "  .a: object{1}", "    .a.b: array[2] of int", "  .c: string"])

    def test_minified_has_no_outline(self):
        method, entries = outline.outline(Path("x.js"), "var a=1;" * 2000)
        self.assertTrue(method.startswith("none"))
        self.assertEqual(entries, [])



class FakePack:
    """Stands in for tree_sitter_language_pack; records whether it was asked to parse."""

    def __init__(self, cached):
        self.cached, self.processed = cached, []

    def detect_language_from_path(self, path):
        return "typescript" if path.endswith(".ts") else None

    def downloaded_languages(self):
        return self.cached

    def ProcessConfig(self, **kw):
        return kw

    def process(self, text, config):
        self.processed.append(config["language"])
        span = lambda a, b: type("S", (), {"start_line": a, "end_line": b})()  # noqa: E731
        item = lambda kind, name, sig, a, b, children=(): type("I", (), dict(  # noqa: E731
            kind=type("K", (), {"type": kind})(), name=name, signature=sig, span=span(a, b),
            doc_comment=None, children=list(children)))()
        return type("R", (), {"structure": [
            item("Class", "Bar", "class Bar extends Baz", 2, 9,
                 [item("Method", "baz", "private baz(x: number): void", 4, 6)])]})()


class TreeSitterTests(unittest.TestCase):
    TS = "x;\n" * 10

    def test_cached_grammar_is_used_with_one_based_lines_and_nesting(self):
        pack = FakePack(["typescript"])
        with unittest.mock.patch.object(outline, "_language_pack", return_value=pack):
            method, entries = outline.outline(Path("x.ts"), self.TS)
        self.assertEqual(method, "syntax tree (tree-sitter, typescript)")
        self.assertEqual(entries, ["L3-10: class Bar extends Baz",
                                   "L5-7:   private baz(x: number): void"])

    def test_uncached_grammar_is_never_requested(self):
        pack = FakePack([])  # process() would download it: must not be called
        with unittest.mock.patch.object(outline, "_language_pack", return_value=pack):
            method, _ = outline.outline(Path("x.ts"), self.TS)
        self.assertEqual(pack.processed, [])
        self.assertIn("declaration scan", method)

    @unittest.skipUnless(outline._language_pack() and "go" in outline._language_pack().downloaded_languages(),
                         "tree-sitter-language-pack with a cached go grammar not installed")
    def test_real_tree_sitter_go(self):
        go = "package m\n\nfunc F(a int) error {\n\treturn nil\n}\n"
        method, entries = outline.outline(Path("m.go"), go)
        self.assertEqual(method, "syntax tree (tree-sitter, go)")
        self.assertEqual(entries, ["L3-5: func F(a int) error"])


if __name__ == "__main__":
    unittest.main()
