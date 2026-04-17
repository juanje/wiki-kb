# Wiki organize

## When to use

Triggered by "organize wiki", "move pages into folders", "reorganize
into subdirectories", "group pages by category", or when the user
explicitly requests restructuring the wiki layout.

Use this to **migrate existing root-level pages** into category
subdirectories. Wikis that grew before subdirectory support was added,
or new wikis where early pages landed in root, accumulate pages that
should be in subdirectories. This script moves them and updates all
links in one pass.

## Prerequisites

- The wiki must have an `index.md` with `## Category` headings and
  page entries. The script derives subdirectory names from these
  categories.
- Pages not listed in the index stay in the root (orphans).

## Procedure

### 1. Dry-run — preview the plan

```bash
python3 <skill-dir>/scripts/wiki-organize.py --wiki-root <path>
```

Show the output to the user. It lists:
- Which pages move to which subdirectory.
- Which pages stay in root (orphans or uncategorized).
- Total moves planned.

### 2. Get user approval

Present the plan and **wait for confirmation** before proceeding.
The user may want to:
- Rename categories in `index.md` first (the directory slug comes
  from the category name).
- Exclude certain categories from organization.
- Handle orphan pages first (run lint to add them to the index).

### 3. Execute the migration

```bash
python3 <skill-dir>/scripts/wiki-organize.py --wiki-root <path> --apply
```

The script:
1. Creates subdirectories for each category (slugified names).
2. Moves pages into their category's subdirectory.
3. Updates all internal links across all pages to use relative paths.
4. Updates links in `index.md`, `tags.md`, and `glossary.md`.

### 4. Verify

Run structural checks to confirm no links broke:

```bash
python3 <skill-dir>/scripts/wiki-check.py --wiki-root <path>
```

Fix any issues found.

### 5. Regenerate artifacts

```bash
python3 <skill-dir>/scripts/wiki-tags.py --wiki-root <path> --map --glossary --save
```

### 6. Git commit

```bash
git add <wiki-root>/ && git commit -m "wiki: organize into subdirectories by category"
```

## After migration

New pages created by ingest or file operations are always placed in
their category subdirectory — no further migration needed.

## Reverting

The migration is reversible via git: `git checkout HEAD~1 -- <wiki-root>/`.
