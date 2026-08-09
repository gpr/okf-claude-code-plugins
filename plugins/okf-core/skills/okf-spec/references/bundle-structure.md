# Bundle structure, index files, log files

Covers §3, §8, §9 of OKF v0.2.

## Layout

A bundle is a directory tree of markdown files. Directory structure is
independent of domain — organize concepts however makes sense for the
knowledge being captured.

```
path/to/bundle/
  index.md                      # Optional. Directory listing for progressive disclosure.
  log.md                        # Optional. Chronological history of updates.
  <concept>.md                  # A concept at the bundle root.
  <subdirectory>/               # Subdirectories organize concepts into groups.
    index.md
    <concept>.md
    <subdirectory>/
      ...
```

A bundle MAY be distributed as a git repository (recommended — history,
attribution, diffs), a tarball/zip archive, or a subdirectory within a
larger repository.

## Reserved filenames

`index.md` and `log.md` have defined meaning at any level of the
hierarchy and MUST NOT be used for concept documents. All other `.md`
files are concept documents.

Tags remain a first-class concept through the `tags` frontmatter field
(see `frontmatter.md`). There is no separate file format for aggregating
documents by tag — a consumer wanting a tag-browsing view synthesizes one
at consumption time by scanning frontmatter.

## `index.md`

MAY appear in any directory, including the bundle root. Enumerates the
directory's contents for progressive disclosure — letting a human or
agent see what's available before opening individual documents.

Index files contain no frontmatter, with one exception: a bundle-root
`index.md` MAY carry an `okf_version` key (see `conformance.md`). The
body uses one or more sections, each grouping concepts under a heading:

```markdown
# Section / Group Heading

* [Title 1](relative-url-1) - short description of item 1
* [Title 2](relative-url-2) - short description of item 2

# Another Section

* [Subdirectory](subdir/) - short description of the subdirectory
```

Entries SHOULD include the description from the linked concept's
frontmatter. Producers MAY generate `index.md` automatically; consumers
MAY synthesize one on the fly when none is present.

**When writing a concept:** if a directory has an `index.md`, add an
entry for the new concept there too — this is a post-write step agents
commonly forget.

## `log.md`

MAY appear at any level of the hierarchy to record the history of
changes to that scope. Flat list of date-grouped entries, newest first:

```markdown
# Directory Update Log

## 2026-05-22
* **Update**: Added a BigQuery table reference for [Customer Metrics](/tables/customer-metrics.md).
* **Creation**: Established the [Dataplex Playbook](/playbooks/dataplex.md).

## 2026-05-15
* **Initialization**: Created foundational directory structure.
```

Date headings MUST use ISO 8601 `YYYY-MM-DD` form. Log entries are prose;
the leading bold word (`**Update**`, `**Creation**`, `**Deprecation**`)
is a convention, not a requirement.

**When writing a concept:** if the bundle (or the directory) has a
`log.md`, append an entry for the change under today's date heading
(creating the heading if it doesn't exist).
