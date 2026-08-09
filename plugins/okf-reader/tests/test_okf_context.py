#!/usr/bin/env python3
"""Tests for scripts/okf_context.py.

Run with: python3 -m unittest discover -s plugins/okf-reader/tests -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import okf_context  # noqa: E402


def write(root: Path, rel: str, content: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


MARKED = '---\nokf_version: "0.2"\n---\n\n# {title}\n'


class TmpProjectTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.root = Path(self._tmpdir.name).resolve()
        self._env = dict(os.environ)
        self.addCleanup(lambda: os.environ.clear() or os.environ.update(self._env))

    def set_option(self, key: str, value: str) -> None:
        os.environ[f"CLAUDE_PLUGIN_OPTION_{key.upper()}"] = value


class DiscoveryTests(TmpProjectTestCase):
    def test_marked_bundle_is_discovered(self):
        write(self.root, "spec/index.md", MARKED.format(title="Spec"))
        bundles = okf_context.discover_bundles(self.root)
        self.assertEqual([b["id"] for b in bundles], ["spec"])
        self.assertEqual(bundles[0]["description"], "Spec")
        self.assertEqual(bundles[0]["status"], "normative")

    def test_nested_index_inside_bundle_is_not_a_separate_bundle(self):
        write(self.root, "spec/index.md", MARKED.format(title="Spec"))
        write(self.root, "spec/tables/index.md", "no frontmatter, just navigation\n")
        bundles = okf_context.discover_bundles(self.root)
        self.assertEqual([b["id"] for b in bundles], ["spec"])

    def test_multiple_bundles_sorted_by_depth_then_name(self):
        write(self.root, "zzz/index.md", MARKED.format(title="Z"))
        write(self.root, "docs/adr/index.md", MARKED.format(title="ADR"))
        write(self.root, "aaa/index.md", MARKED.format(title="A"))
        bundles = okf_context.discover_bundles(self.root)
        self.assertEqual([b["id"] for b in bundles], ["aaa", "zzz", "docs/adr"])

    def test_node_modules_and_dotdirs_are_pruned(self):
        write(self.root, "node_modules/pkg/index.md", MARKED.format(title="Should not appear"))
        write(self.root, ".git/index.md", MARKED.format(title="Should not appear"))
        write(self.root, "spec/index.md", MARKED.format(title="Spec"))
        bundles = okf_context.discover_bundles(self.root)
        self.assertEqual([b["id"] for b in bundles], ["spec"])

    def test_cache_dir_is_pruned(self):
        write(self.root, ".okf/cache/vendored/index.md", MARKED.format(title="Vendored"))
        bundles = okf_context.discover_bundles(self.root)
        self.assertEqual(bundles, [])

    def test_depth_cap(self):
        write(self.root, "a/b/c/d/e/index.md", MARKED.format(title="Too deep"))
        bundles = okf_context.discover_bundles(self.root)
        self.assertEqual(bundles, [])

    def test_unmarked_index_is_not_discovered_by_walk(self):
        write(self.root, "spec/index.md", "# Unmarked\n\nno frontmatter.\n")
        write(self.root, "docs/adr/index.md", MARKED.format(title="ADR"))
        bundles = okf_context.discover_bundles(self.root)
        # only the marked bundle is found; the unmarked one is not promoted
        # via fallback because a marked bundle already exists.
        self.assertEqual([b["id"] for b in bundles], ["docs/adr"])

    def test_fallback_when_nothing_marked(self):
        write(self.root, "spec/index.md", "# Unmarked spec\n\nno frontmatter.\n")
        bundles = okf_context.discover_bundles(self.root)
        self.assertEqual([b["id"] for b in bundles], ["spec"])

    def test_empty_project_discovers_nothing(self):
        self.assertEqual(okf_context.discover_bundles(self.root), [])


class TrustedBundlesTests(TmpProjectTestCase):
    def test_relative_standards_bundle_resolves_against_hook_cwd(self):
        write(self.root, "standards/index.md", "# Standards\n")
        self.set_option("standards_bundle", "standards")
        bundle = okf_context.trusted_bundles()[0]
        self.assertEqual(okf_context.resolve(self.root, bundle), self.root / "standards")

    def test_relative_standards_bundle_does_not_use_process_cwd(self):
        write(self.root, "standards/index.md", "# Standards\n")
        self.set_option("standards_bundle", "standards")
        bundle = okf_context.trusted_bundles()[0]
        with tempfile.TemporaryDirectory() as other:
            self.assertIsNone(okf_context.resolve(Path(other).resolve(), bundle))


class ExternalBundlesTests(TmpProjectTestCase):
    def test_inside_project_path_is_rejected(self):
        write(self.root, "spec/index.md", MARKED.format(title="Spec"))
        write(
            self.root,
            "okf.json",
            json.dumps({"bundles": [{"id": "bad", "source": "./spec", "status": "normative"}]}),
        )
        bundle = okf_context.external_bundles(self.root)[0]
        self.assertIsNone(okf_context.resolve(self.root, bundle))

    def test_outside_project_absolute_path_resolves(self):
        with tempfile.TemporaryDirectory() as other:
            other_root = Path(other).resolve()
            write(other_root, "index.md", "# External\n")
            write(
                self.root,
                "okf.json",
                json.dumps(
                    {"bundles": [{"id": "external", "source": str(other_root), "status": "informative"}]}
                ),
            )
            bundle = okf_context.external_bundles(self.root)[0]
            resolved = okf_context.resolve(self.root, bundle)
            self.assertEqual(resolved, other_root)

    def test_remote_source_resolves_from_cache_dir_only_when_vendored(self):
        write(
            self.root,
            "okf.json",
            json.dumps(
                {"bundles": [{"id": "platform", "source": "github:acme/std", "status": "normative"}]}
            ),
        )
        bundle = okf_context.external_bundles(self.root)[0]
        self.assertIsNone(okf_context.resolve(self.root, bundle))

        write(self.root, ".okf/cache/platform/index.md", "# Vendored\n")
        self.assertIsNotNone(okf_context.resolve(self.root, bundle))

    def test_malformed_okf_json_is_ignored(self):
        write(self.root, "okf.json", "{not json")
        self.assertEqual(okf_context.external_bundles(self.root), [])

    def test_missing_okf_json_yields_no_external_bundles(self):
        self.assertEqual(okf_context.external_bundles(self.root), [])


class BuildContextTests(TmpProjectTestCase):
    def test_empty_project_produces_no_context(self):
        self.assertEqual(okf_context.build_context(self.root), "")

    def test_precedence_standards_then_discovered_then_external(self):
        self.set_option("standards_bundle", str(self.root / "standards"))
        write(self.root, "standards/index.md", "# Standards\n")
        write(self.root, "spec/index.md", MARKED.format(title="Spec"))
        with tempfile.TemporaryDirectory() as other:
            other_root = Path(other).resolve()
            write(other_root, "index.md", "# External\n")
            write(
                self.root,
                "okf.json",
                json.dumps(
                    {"bundles": [{"id": "external", "source": str(other_root), "status": "normative"}]}
                ),
            )
            context = okf_context.build_context(self.root)
        rows = [line for line in context.splitlines() if line.startswith("| `")]
        ids_in_order = [line.split("`")[1] for line in rows]
        self.assertEqual(ids_in_order, ["standards", "spec", "external"])
        self.assertIn("| `standards` | normative | 1 |", rows[0])
        self.assertIn("| `spec` | normative | 2 |", rows[1])
        self.assertIn("| `external` | normative | 3 |", rows[2])

    def test_informative_bundle_has_no_precedence_number(self):
        with tempfile.TemporaryDirectory() as other:
            other_root = Path(other).resolve()
            write(other_root, "index.md", "# External\n")
            write(
                self.root,
                "okf.json",
                json.dumps(
                    {"bundles": [{"id": "external", "source": str(other_root), "status": "informative"}]}
                ),
            )
            context = okf_context.build_context(self.root)
        self.assertIn("| `external` | informative | – |", context)


if __name__ == "__main__":
    unittest.main()
