# Wiki import

## When to use

Triggered by "import from GitLab", "import repo docs", "ingest this URL",
or when the user provides a remote URL or GitLab repo path for wiki
ingestion.

Import is a **pre-processing step** that converts external sources into
local markdown, then feeds them into the standard ingest pipeline. It is
not a separate wiki operation — it produces input for ingest.

## Remote page fetch

When the user provides a URL (documentation page, GitLab file, web
article):

1. **Fetch** the page content (via built-in agent web fetch tools).
2. **Convert** to clean markdown if needed (strip navigation, ads,
   boilerplate).
3. **Optionally save** a local copy if `--keep-source` is specified
   with a target directory.
4. **Ingest** via standard wiki-ingest pipeline.

**Source metadata** for URL-fetched content in page frontmatter:

```yaml
sources:
  - url: https://docs.example.com/architecture/overview
    accessed: YYYY-MM-DD
```

No dedicated script needed — the agent uses its built-in web fetch.

## GitLab repository import

### When to use

Architecture decisions, README files, ADRs, and developer docs living in
GitLab repositories. Already markdown but scattered across repos.

### Procedure

1. **Clone/pull** — The user provides a repo URL or local path. If
   remote, clone to a temp directory.
2. **Select** — Filter which files to ingest by path pattern:
   - `docs/**/*.md`
   - `README.md`
   - `adr/*.md`
   - `CONTRIBUTING.md`
   - `CHANGELOG.md`
3. **Ingest** — Standard wiki-ingest pipeline processes the selected
   files.

### Recommended file patterns

| Repo layout | Pattern | What it captures |
|---|---|---|
| Standard docs | `docs/**/*.md` | Architecture, design, guides |
| ADRs | `adr/*.md`, `docs/adr/*.md` | Architecture decision records |
| README only | `README.md` | Project overview |
| Contributing guide | `CONTRIBUTING.md` | Process and conventions |
| Full docs sweep | `**/*.md` (exclude `node_modules`, `vendor`) | Everything |

### Source metadata

```yaml
sources:
  - gitlab: https://gitlab.example.com/group/repo/-/blob/main/docs/architecture.md
    commit: abc1234
    accessed: YYYY-MM-DD
```

Include the commit SHA for traceability. The source path in frontmatter
uses the GitLab URL, not the local clone path (which is ephemeral).

### Large repos

For large repositories, use sparse checkout to avoid downloading the
entire repo:

```bash
git clone --depth 1 --filter=blob:none --sparse <repo-url> /tmp/repo-import
cd /tmp/repo-import
git sparse-checkout set docs/ adr/ README.md
```

Then ingest from the checked-out files.

## Confluence import (post-MVP)

Not implemented in the current version. Confluence content can be ingested
via:

1. Manual copy-paste into the wiki-file operation.
2. HTML export from Confluence → convert to markdown → wiki-ingest.

A dedicated `wiki-confluence.py` script is planned for a future release
to handle Confluence REST API export → markdown conversion.

## Future import sources

The import architecture is extensible. Each new source follows the
pattern: export → local markdown → standard ingest.

Potential sources:
- Slack threads (via slack-fetch skill output)
- Jira tickets (via jira-tools skill output)
- Google Docs (via export to markdown)
