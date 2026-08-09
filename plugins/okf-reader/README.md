# okf-reader

Loads [OKF](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md)
knowledge bundles into a Claude Code session at startup, lazily: the hook
only ever prints bundle locations and points at each bundle's `index.md`. It
never reads bundle content.

## Where bundles come from

Three sources, in precedence order:

1. **Organization standards** (`standards_bundle` userConfig) - deployed via
   user or managed settings, so a cloned repository cannot override it.
2. **Auto-discovery** - any directory under the project root whose
   `index.md` declares `okf_version` in its frontmatter (OKF SPEC §12, the
   only place frontmatter is permitted in an `index.md`) is a bundle root.
   No declaration file needed:

   ```markdown
   ---
   okf_version: "0.2"
   ---

   # Product spec
   ```

   Discovery walks up to 4 levels below the project root, skips dotdirs
   (except `.okf`), `node_modules`, `venv`, `dist`, `build`, `target`,
   `vendor`, and the vendored cache directory, and stops descending into a
   bundle once found - nested `index.md` files inside it are navigation, not
   further bundle roots. All discovered bundles are normative.

   If nothing in the tree declares `okf_version`, the hook falls back to a
   fixed list of conventional locations (`spec/`, `docs/okf/`, `knowledge/`)
   and accepts a bare `index.md` there, for bundles that predate the marker.

3. **`okf.json`** at the project root - for bundles discovery cannot see:
   remote sources (`github:`, `https:`, ...) vendored into a cache directory,
   and directories outside the project root. See `examples/okf.json`.

   `okf.json` is untrusted (it ships with the repository), but its paths are
   not confined to the project: an entry may point anywhere on disk. If an
   entry resolves *inside* the project, it's rejected with a warning -
   that bundle is already found by auto-discovery, and the file exists
   precisely for what discovery can't reach.

Precedence: standards, then discovered bundles (shallowest path first, then
alphabetically), then `okf.json` entries in array order. On a normative
conflict, the lower precedence number wins.

## Remote bundles

The hook never touches the network. A `github:` or `https:` source in
`okf.json` must be vendored into the cache directory (`.okf/cache/<id>` by
default, configurable via the `cache_dir` userConfig) by a separate sync
step before it will resolve.

## Preview

```
bin/okf-reader-preview [PROJECT] [--standards DIR] [--cache-dir DIR] [--raw]
```

Prints what the hook would inject for a given project without starting
Claude Code. Exits 1 when nothing resolves, so it's usable in CI as a check
that a project's bundles still resolve.
