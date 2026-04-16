# wiki-kb

An [Agent Skill](https://agentskills.io/specification) that builds and maintains a local, portable, markdown-based knowledge base. Plain files, no database, no external service.

## What it does

Transforms documents, conversations, and scattered team knowledge into an interconnected wiki of atomic markdown pages with four operations:

| Operation | Purpose |
|---|---|
| **Ingest** | Process documents into atomic wiki pages with frontmatter, backlinks, and index |
| **Lint** | Health checks: orphans, broken links, missing backlinks, thin pages; includes fix mode |
| **Synthesize** | Discover emergent concepts via tag clustering, co-occurrence, and cross-topic bridges |
| **File** | Capture ephemeral knowledge (conversations, quick notes) into the wiki on demand |

Plus **Import** (GitLab repos, URLs) and structured **entity types** (glossary, service, team, project, person).

## Quick start

1. Add the skill to your agent's skill directory.
2. Tell your agent: *"ingest `path/to/document.md` into the wiki"*.
3. The agent reads `SKILL.md`, routes to the right reference, and executes the pipeline.

The wiki defaults to `./wiki/` in your workspace. Override with an explicit path or a `WIKI_ROOT` variable.

## Requirements

- Python 3.10+
- Any AI coding agent that supports the [Agent Skills spec](https://agentskills.io/specification) (Claude Code, Cursor, Windsurf, etc.)

No external Python dependencies. All scripts are stdlib-only.

## Structure

```
wiki-kb/
├── SKILL.md                  # Router (75 lines)
├── references/
│   ├── wiki-ingest.md        # Full ingest procedure
│   ├── wiki-lint.md          # Health checks and fix mode
│   ├── wiki-synthesize.md    # Concept synthesis
│   ├── wiki-file.md          # Ephemeral capture
│   ├── wiki-entities.md      # Entity type templates
│   └── wiki-import.md        # Import from GitLab/URLs
└── scripts/
    ├── wiki-check.py         # Structural checks
    ├── wiki-stats.py         # Graph statistics
    ├── wiki-tags.py          # Tag management, search, synthesis heuristics
    ├── wiki-backlinks.py     # Missing backlink extraction
    └── wiki-log-filter.py    # Skip already-processed files
```

## Scripts

All scripts accept `--wiki-root <path>` and `--json`. Run from the skill directory:

```bash
python3 scripts/wiki-check.py --wiki-root ~/my-wiki
python3 scripts/wiki-stats.py --wiki-root ~/my-wiki
python3 scripts/wiki-tags.py --wiki-root ~/my-wiki --search "keyword"
```

## License

Apache-2.0
