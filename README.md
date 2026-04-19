# wiki-kb

An [Agent Skill](https://agentskills.io/specification) that builds and maintains a local, portable, markdown-based knowledge base. Plain files, no database, no external service.

## What it does

Transforms documents, conversations, and scattered knowledge into an interconnected wiki of atomic markdown pages. Works for team knowledge, technical documentation, articles, and personal research alike.

| Operation | Purpose |
|---|---|
| **Ingest** | Process documents into atomic wiki pages with frontmatter, backlinks, and index |
| **Lint** | Health checks: orphans, broken links, missing backlinks, thin pages, under-tagged pages; includes fix mode |
| **Synthesize** | Discover emergent concepts via tag clustering, co-occurrence, and cross-topic bridges |
| **File** | Capture ephemeral knowledge (conversations, quick notes) into the wiki on demand |

Plus **Import** (repos, URLs) and 12 structured **entity types**: glossary, service, team, project, person, process, meeting, repository, article, author, guide, reference.

## Self-contained wiki

The skill **builds and maintains** the wiki. The wiki **answers queries on its own**.

During first-time setup, the skill generates `AGENTS.md` (and a `CLAUDE.md` symlink) inside the wiki root. These files instruct any AI assistant to navigate the wiki's internal links, cite sources, and never invent answers. Open the wiki directory as a workspace and start asking questions — no skill needed.

```
<wiki-root>/
├── AGENTS.md              # Query instructions for AI assistants
├── CLAUDE.md              # Symlink to AGENTS.md
├── index.md               # Categorized navigation
├── tags.md                # Thematic navigation by tag
├── glossary.md            # All glossary terms with definitions
├── <category-slug>/       # Pages grouped by index category
│   └── <page>.md
└── .meta/                 # Local operational state (git-ignored)
```

## Quick start

1. Add the skill to your agent's skill directory.
2. Tell your agent: *"ingest `path/to/document.md` into the wiki"*.
3. The agent reads `SKILL.md`, routes to the right reference, and executes the pipeline.
4. Open the wiki directory and ask questions — the `AGENTS.md` handles it.

The wiki defaults to `./wiki/` in your workspace. Override with an explicit path or a `WIKI_ROOT` variable.

## Requirements

- Python 3.10+
- Any AI coding agent that supports the [Agent Skills spec](https://agentskills.io/specification) (Claude Code, Cursor, Windsurf, etc.)

No external Python dependencies. All scripts are stdlib-only.

## Skill structure

```
wiki-kb/
├── SKILL.md                  # Router
├── templates/
│   └── AGENTS.md             # Template copied to wiki root on setup
├── references/
│   ├── wiki-ingest.md        # Full ingest procedure
│   ├── wiki-lint.md          # Health checks and fix mode
│   ├── wiki-synthesize.md    # Concept synthesis
│   ├── wiki-file.md          # Ephemeral capture
│   ├── wiki-entities.md      # Entity type templates
│   ├── wiki-import.md        # Import from repos/URLs
│   └── wiki-organize.md      # Migrate flat wiki to subdirectories
└── scripts/
    ├── wiki-check.py         # Structural checks
    ├── wiki-stats.py         # Graph statistics
    ├── wiki-tags.py          # Tag management, search, synthesis heuristics, --fix-tags
    ├── wiki-backlinks.py     # Missing backlink extraction
    ├── wiki-log-filter.py    # Skip already-processed files
    └── wiki-organize.py      # Subdirectory migration
```

## Scripts

All scripts accept `--wiki-root <path>` and `--json`. Run from the skill directory:

```bash
python3 scripts/wiki-check.py --wiki-root ~/my-wiki
python3 scripts/wiki-stats.py --wiki-root ~/my-wiki
python3 scripts/wiki-tags.py --wiki-root ~/my-wiki --search "keyword"
python3 scripts/wiki-tags.py --wiki-root ~/my-wiki --fix-tags
```

## Troubleshooting

### Claude Code asks permission to read skill files

Claude Code may prompt for permission when the agent tries to read files from the skill directory (`references/`, `scripts/`). This is a [known issue](https://github.com/anthropics/claude-code/issues/15757) — skills installed outside the project root are treated as external files.

**Fix:** add a permission rule to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "permissions": {
    "allow": [
      "Read(~/.claude/skills/*)"
    ]
  }
}
```

Adjust the path if your skills are installed elsewhere.

## License

Apache-2.0
