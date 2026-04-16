---
name: wiki-kb
description: >
  Build and maintain a local, portable, markdown-based knowledge base.
  Use when the user wants to ingest documents into a wiki, check wiki health,
  synthesize emergent concepts, file ephemeral knowledge, or query the wiki.
  Trigger on: "ingest", "add to knowledge base", "build wiki", "lint",
  "check wiki", "synthesize", "find patterns", "file this", "add to wiki",
  "import from GitLab", "what is X?", "who owns Y?", "what team is Z on?"
license: Apache-2.0
compatibility: Requires Python 3.10+. All scripts are stdlib-only.
metadata:
  version: 1.0.0
  authors: [juanje]
  tags: [knowledge-base, wiki, markdown, local]
  repository: https://gitlab.com/juanjeojeda/wiki-kb
---

# wiki-kb

Transforms documents, conversations, and scattered team knowledge into an
interconnected wiki of atomic markdown pages. Plain files, no database, no
external service. Each engineer owns their local instance.

## Wiki root

Resolve the wiki root path in this order:

1. Explicit path from the user.
2. `WIKI_ROOT` in workspace config (`.env`, agent config, project settings).
3. Default: `./wiki/` relative to workspace root.

All scripts accept `--wiki-root <path>`.

## First-time setup

Create the directory, `.meta/`, a `.gitignore` (`.meta/` and `.staging/`),
`index.md` with `# Wiki`, and `.meta/log.md` with `# Wiki log`.

## Routing

Read the corresponding reference file **before** starting work.

| User intent | Reference file |
|---|---|
| "ingest", "add to knowledge base", "build wiki", "process documents" | `references/wiki-ingest.md` |
| "lint", "check wiki", "wiki health", "review the wiki" | `references/wiki-lint.md` |
| "synthesize", "find abstractions", "what concepts are missing" | `references/wiki-synthesize.md` |
| "file this", "add this to the wiki", "capture this" | `references/wiki-file.md` |
| "import from GitLab", "import repo", "ingest this URL" | `references/wiki-import.md` |
| Creating entity pages (glossary, service, team, project, person) | `references/wiki-entities.md` (load alongside the active operation) |

### Queries

For questions like "what is X?", "who owns Y?", "what team is Z on?":

1. Read both `<wiki-root>/index.md` and `<wiki-root>/tags.md` to find relevant pages. The index groups pages by category; the tag map groups them by concept — use both for better coverage.
2. Read the matching page(s) and answer from their content.
3. If navigation is insufficient, use `python3 scripts/wiki-tags.py --wiki-root <path> --search "keywords"` as fallback.

No reference file needed — the wiki's own structure supports direct lookup.

## Scripts

Stdlib-only Python scripts. All accept `--wiki-root <path>` and `--json`.

| Script | Purpose |
|---|---|
| `wiki-check.py` | Structural checks (orphans, ghosts, broken links, backlinks, frontmatter) |
| `wiki-stats.py` | Graph statistics (pages, connections, hubs) |
| `wiki-tags.py` | Tag management, synthesis heuristics, search, normalization |
| `wiki-backlinks.py` | Missing backlink extraction with batch splitting |
| `wiki-log-filter.py` | Skip already-processed files during ingestion |

Each reference file documents which scripts to use and when.
