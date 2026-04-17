# Implementation plan: wiki subdirectories by category

Support organizing wiki pages into subdirectories based on their index
category. New pages go into the matching subdirectory, creating it if
needed. Backward compatible: flat wikis continue to work.

## Design decisions

- **Grouping logic:** subdirectories map to index categories (e.g.,
  `teams/`, `projects/`, `services/`, `people/`, `concepts/`).
- **Page placement:** new pages go into the subdirectory matching their
  index category, creating it if it doesn't exist.
- **Backward compatible:** all scripts and references must work with
  both flat wikis (no subdirectories) and organized wikis.
- **Link format:** relative paths from the page's location. A page in
  `teams/toolchain.md` links to `../services/test-console.md`. Pages
  in the root link to `teams/toolchain.md`.
- **Index, tags.md, glossary.md** stay in the wiki root and use paths
  relative to root (e.g., `teams/toolchain.md`).
- **Migration:** a dedicated command or script reorganizes an existing
  flat wiki into subdirectories, updating all links.

## Impact analysis

### Link regex (7 occurrences across 5 scripts)

Current regex: `[a-zA-Z0-9_-]+\.md` — matches only flat filenames.
New regex must match: `[a-zA-Z0-9_/-]+\.md` or a more permissive
pattern that captures `subdir/page.md` and `../subdir/page.md`.

Affected locations:

| File | Line(s) | Context |
|---|---|---|
| `wiki-check.py` | 117 | `build_link_graph` |
| `wiki-stats.py` | 48 | `gather_stats` link graph |
| `wiki-tags.py` | 106 | `get_page_connections` |
| `wiki-tags.py` | 190 | `build_link_graph` |
| `wiki-backlinks.py` | 47 | `build_link_graph_with_descriptions` |
| `wiki-backlinks.py` | 55 | connection entry regex |
| `wiki-log-filter.py` | 65 | source article filename regex |

### Page listing (5 scripts)

Currently `os.listdir(wiki_dir)` — flat only. Must become recursive
(`os.walk` or similar) to discover pages in subdirectories.

Affected functions:

- `wiki-check.py`: `list_pages()`
- `wiki-stats.py`: inline in `gather_stats()`
- `wiki-tags.py`: `load_wiki()`
- `wiki-backlinks.py`: inline in `find_missing_backlinks()`
- `wiki-log-filter.py`: `list_source_files()` (less affected — scans
  source dirs, not wiki)

### Page identity

Currently pages are identified by filename (`toolchain.md`). With
subdirectories, identity becomes a relative path from wiki root
(`teams/toolchain.md`). This affects:

- All dicts keyed by filename across all scripts
- `parse_index()` — link targets in index entries
- `build_title_map()` in `wiki-backlinks.py`
- Frontmatter `sources:` and `synthesis_sources:` lists
- Connection link targets in page body

### Index parsing

`parse_index()` in `wiki-check.py` and `wiki-tags.py` currently
extracts filenames from links like `](page.md)`. With subdirectories,
links become `](teams/page.md)` — the regex already captures this
(`\]\((.+?\.md)\)`) but downstream code assumes flat filenames.

### Generated artifacts

- **`tags.md`** — links must include subdirectory: `[Title](teams/page.md)`
- **`glossary.md`** — same
- **`tag-map.json`** — page keys become `teams/page.md`

### EXCLUDE_FILES

Currently `{"index.md", "tags.md", "glossary.md"}`. These stay in
the root. The exclude logic needs to compare against root-relative
paths, not bare filenames.

## Implementation sequence

| # | Step | Effort | Depends on |
|---|---|---|---|
| 1 | Shared utility: `list_pages()` with recursive walk | Small | — |
| 2 | Shared utility: updated link regex constant | Small | — |
| 3 | Update `wiki-check.py` | Medium | 1, 2 |
| 4 | Update `wiki-stats.py` | Small | 1, 2 |
| 5 | Update `wiki-tags.py` | Medium | 1, 2 |
| 6 | Update `wiki-backlinks.py` | Small | 1, 2 |
| 7 | Update `wiki-log-filter.py` | Small | — |
| 8 | Update `write_tag_artifacts()` — links with subdir | Small | 5 |
| 9 | Update `write_glossary_artifact()` — links with subdir | Small | 5 |
| 10 | Migration script or command | Medium | 1-9 |
| 11 | Update `references/wiki-ingest.md` — page placement logic | Small | — |
| 12 | Update `references/wiki-lint.md` | Small | — |
| 13 | Update `references/wiki-synthesize.md` | Small | — |
| 14 | Update `references/wiki-file.md` | Small | — |
| 15 | Update `SKILL.md` — structure description | Small | — |
| 16 | Update tests | Medium | 1-9 |
| 17 | End-to-end validation on existing wiki | Medium | All |

## Step 1-2: Shared utilities

Extract a shared `list_wiki_pages(wiki_dir)` that uses `os.walk` and
returns paths relative to `wiki_dir` (e.g., `teams/toolchain.md` or
`toolchain.md` for flat). Each script currently has its own inline
page listing — consolidate into one.

Define a shared link regex:
```python
WIKI_LINK_RE = r"\[.*?\]\(([a-zA-Z0-9_./-]+\.md)\)"
```

Decision: shared module (`scripts/wiki_common.py`) or duplicate the
constant in each script. A shared module is cleaner but adds an import
dependency. Since scripts are stdlib-only and invoked standalone,
a shared module that's importable from the same directory works.

## Step 3-6: Script updates

For each script:

1. Replace `os.listdir` page listing with `list_wiki_pages()`.
2. Replace hardcoded link regex with the shared constant.
3. Update all dict keys from `filename` to `relpath` (e.g.,
   `teams/toolchain.md`).
4. Update EXCLUDE_FILES check to compare against relative paths
   from wiki root (files in root only — `index.md`, not
   `teams/index.md`).
5. Test with both flat and subdirectory layouts.

### Link graph normalization

Pages in different subdirectories link to each other with relative
paths (`../services/test-console.md`). The link graph must normalize
these to wiki-root-relative paths. Given a page at
`teams/toolchain.md` with a link `](../services/test-console.md)`,
resolve to `services/test-console.md`.

```python
os.path.normpath(os.path.join(os.path.dirname(page_relpath), link_target))
```

## Step 10: Migration script

New script `scripts/wiki-organize.py` (or a flag on `wiki-check.py`):

1. Read `index.md` to get category → pages mapping.
2. For each category, compute a directory slug (e.g.,
   "Services and tools" → `services/`).
3. Move pages into subdirectories.
4. Update all internal links in all pages to use new relative paths.
5. Update `index.md`, `tags.md`, `glossary.md` links.
6. Report what was moved.

The category-to-directory slug mapping could be:
- Automatic: slugify the category name.
- Configurable: a mapping in `.meta/` or frontmatter.

Automatic is simpler. Edge case: what if a page is not in the index?
It stays in the root (orphan).

## Step 11-15: Reference file updates

### wiki-ingest.md

Page placement logic in step 5a:

1. Determine the page's category (from the reconciliation plan).
2. Check if a matching subdirectory exists in `<wiki-root>/`.
3. If yes, write to `<wiki-root>/category-slug/page-name.md`.
4. If no, create the subdirectory and write there.
5. Links to/from other pages use relative paths.

### wiki-lint.md, wiki-synthesize.md, wiki-file.md

Update script invocations and note that pages may live in
subdirectories. The scripts handle this transparently.

### SKILL.md

Update the wiki structure description to show subdirectories:

```
<wiki-root>/
├── index.md
├── tags.md
├── glossary.md
├── teams/
│   ├── toolchain.md
│   └── ...
├── projects/
│   └── ...
└── .meta/
```

## Backward compatibility

The key constraint: all scripts must work with **both** layouts.

- Flat wiki: `list_wiki_pages()` returns `["page.md", ...]`
- Organized wiki: returns `["teams/page.md", "services/other.md", ...]`
- Mixed (mid-migration): returns both flat and nested

The link resolution logic handles both: `page.md` (flat) and
`../category/page.md` (nested) both resolve correctly when normalized
against the page's own location.

## Risks

| Risk | Mitigation |
|---|---|
| Link breakage during migration | Migration script validates all links after moving; `wiki-check.py` catches broken links |
| Performance with deep nesting | Only one level of subdirectories (enforced by convention, not code) |
| Category name changes | Renaming a category in the index doesn't auto-rename the directory — document as manual step |
| Obsidian compatibility | Obsidian resolves wiki-links differently — test with Obsidian graph view |
| Pages in multiple categories | A page belongs to one category (the one in the index). If a page appears in multiple index categories, use the first one. |
