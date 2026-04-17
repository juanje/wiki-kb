# Wiki ingest

## When to use

Triggered by "ingest", "add to knowledge base", "build wiki", "process
documents into wiki", or when the user provides a source file/directory
for wiki processing.

Use "force ingest" or "re-ingest" to bypass the log filter and re-process
files that were already ingested — useful when a source was updated, the
skill improved, or you want finer extraction.

## Inputs

- **Source** (required) — path to a file, directory, or URL.
- **Force mode** — re-process already-ingested files.
- **`--keep-source`** — save a copy of fetched remote content to a
  user-specified directory before ingesting. Not enabled by default.

## Wiki structure reminder

```
<wiki-root>/
├── index.md          → Categorized list of all pages (includes top glossary terms)
├── tags.md           → Thematic navigation (by tag)
├── glossary.md       → All glossary terms — full form + definition (generated)
├── .meta/log.md      → Ingestion history (git-ignored)
├── .staging/         → Temporary manifests and plans (cleaned after write)
└── [pages].md        → Individual wiki pages (flat namespace)
```

### Page format

```markdown
---
tags: [tag1, tag2]
sources:
  - path/to/source-document.md
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Title]

[Summary — 2-5 sentences: what this concept is, why it matters, and the
core insight. Useful standalone even if the reader stops here.]

## Key points
- [Essential knowledge with reasoning chains — "because X, therefore Y"]
- [Minimum 2-3 points per page]

## Examples
- [Concrete example with enough context to stand alone]
- [Source attribution for each example]

## Connections
- [Related page](related-page.md) — how and why they connect

## Sources
- [Source title](path/to/source.md)
```

All section headings are fixed English: `## Key points`, `## Examples`,
`## Connections`, `## Sources`.

Each page is one concept. The filename is the concept name as a slug:
`<wiki-root>/concept-name.md`.

### Entity pages

When extracting content, watch for entity-type material: proper names,
abbreviations, internal tools, team names, people. These use structured
templates. Load `references/wiki-entities.md` alongside this reference
when creating entity pages.

## Procedure

**Always follow the full pipeline** (Extract → Consolidate → Reconcile →
Write → Clean up → Commit), regardless of work set size.

### 1. Assess the input

Use the log filter script to check what needs processing:

```bash
python3 <skill-dir>/scripts/wiki-log-filter.py --wiki-root <path> <source_path> [<source_path> ...]

# Force mode:
python3 <skill-dir>/scripts/wiki-log-filter.py --wiki-root <path> --force <source_path>
```

Outputs two lists: files to process and files already ingested.

**Subagent strategy:**

| Work set size | Strategy |
|---|---|
| 1 file | Process directly |
| 2-4 files | Agent's choice |
| 5+ files | Use subagents for Extract phase (parallel, batches of 3-5) |

### 2. Extract (per document)

Read each source file and produce an **extraction manifest** at
`<wiki-root>/.staging/<source-filename>-manifest.md`.

**Manifest format:**

```markdown
# Extraction manifest

## Source
- **File:** path/to/source.md
- **Title:** [article title]
- **Date:** YYYY-MM-DD

## Concepts extracted

### 1. [Concept name]
- **Description:** One sentence.
- **Type:** concept | glossary | service | team | project | person | technique | principle | example-pattern
- **Key points:** (minimum 2-3)
  - [Include reasoning chains, not just conclusions]
- **Examples from source:** (minimum 1)
  - [Concrete, with enough context to stand alone]
- **Related concepts:** [names of related concepts]

## Cross-references detected
- **Internal links in source:** [list]
- **Implicit references:** [concepts mentioned but not linked]
```

**Extraction guidelines:**

- 5-8 concepts per dense article; fewer for meta/recap content.
- Each concept is **atomic** — one coherent topic per entry.
- Capture the author's framing and voice, not a neutral summary.
- Capture reasoning chains ("because X, therefore Y").
- Examples are first-class — always extract with sufficient context.
- Tag foundational references consistently (authors, domain terms).
- **Entity detection:** when extracting, watch for proper names
  (capitalized, specific), abbreviations, internal tool names, team
  names, and people. Set the Type field accordingly. The agent will
  route these to entity templates during the Write phase.
- **Tagging:** do not tag entities with their type name (`person`,
  `service`, `team`, `project`, `concept`, `glossary`). The `type`
  frontmatter field already classifies the page. Tags should describe
  the domain (e.g., `automotive`, `certification`, `ci-cd`).

**Subagent prompt template:**

> Read [file_path]. Extract all concepts, entities, examples, principles,
> and cross-references. Write an extraction manifest to
> `<wiki-root>/.staging/[filename]-manifest.md` following the manifest
> format in `references/wiki-ingest.md`. Return a one-line summary of
> concepts extracted.

### 3. Consolidate (multi-document only)

When processing 2+ documents, merge overlapping concepts across manifests
before reconciling. Write a consolidated manifest at
`<wiki-root>/.staging/_consolidated.md`.

**Merge heuristic:** Only merge when concepts genuinely overlap (same
topic, different angles). If a concept has 2+ key points of its own or
1+ substantial example with reasoning, it likely deserves its own page
even if related concepts exist.

Skip this step for single-file ingestion.

### 4. Reconcile

Compare the manifest against the wiki's current state. For each concept,
decide:

| Situation | Action |
|---|---|
| Not in wiki | **Create** — new page |
| Wiki defines it independently | **Enrich** — add examples, connections, source |
| Wiki covers it only in combination (X-and-Y) | **Create** standalone if enough substance + broader connections; else **Enrich** |
| Related but distinct page exists | **Create** + plan backlinks |
| Single data point or minor variation | **Absorb** — add as section/bullet in broader page |

**Re-ingestion guard:** When enriching, check the target page's `sources`
frontmatter. If the source is already listed, only add genuinely new
content.

Write a **reconciliation plan** to `<wiki-root>/.staging/_plan.md`:

```markdown
# Reconciliation plan

## Create
1. **[filename].md** — [description]. Tags: [...]. Category: [...].

## Enrich
1. **[existing-page].md** — [what to add]. From concept: [which].

## Absorb
1. **[concept]** → into **[existing-page].md** — [as what].

## Backlinks to add
1. **[page-a].md** ↔ **[page-b].md** — [reason]

## Index updates
- New entries: [list with categories]
- New categories: [if any]
```

### 5. Write

Execute the reconciliation plan.

**Source visibility:** If source files are local working documents
(personal notes, workspace files, ephemeral paths like `~/...`), omit
both the `sources:` frontmatter field and the `## Sources` section
from wiki pages. Source traceability is preserved in `.meta/log.md`
(git-ignored). Only include visible sources when the source is a
permanent, shareable reference (URL, git repo, published document).

**Page naming:** Each wiki page represents one concept, and its
filename is that concept as a short slug. The source file structure is
irrelevant — only the extracted concept matters.

- Source `~/git/toolchain-chatbot/data/.../con_ostree.html` about
  OSTree → create `ostree.md`
- Source `docs/architecture/pipeline-overview.md` about the automotive
  pipeline → create `automotive-pipeline.md`
- Source with 5 concepts → create 5 separate pages, one per concept

The filename is always `<wiki-root>/concept-name.md`. No directories,
no nesting, no replication of the source's file structure.

#### 5a. Create new pages

For each "Create" item: choose a filename that matches the concept
name as a short slug (lowercase, hyphens). Write it directly in
`<wiki-root>/`.

If the manifest Type indicates an entity (glossary, service, team,
project, person, process, meeting, repository), use the corresponding
template from `references/wiki-entities.md`.

Populate from manifest: summary, key points, examples, sources. If the
manifest has examples, they MUST appear in a dedicated Examples section.

#### 5b. Enrich existing pages

For each "Enrich" item:

1. Read the existing page.
2. Add substance under matching sections (not just mentions).
3. Update sources in both frontmatter AND visible Sources section.
4. Update `updated` date in frontmatter.

#### 5c. Absorb minor concepts

Add as bullet, example, or subsection in the target page. Update frontmatter.

#### 5d. Add backlinks

Bidirectional — both pages get a connection entry in `## Connections`
with a brief note on why they connect.

#### 5e. Update index

Add new entries to `<wiki-root>/index.md` under their categories. Keep
entries alphabetical within categories. For the `## Glossary` section,
use the compact format with Full form:
`- **[TERM]** — Full Form. One-line definition. [→](term.md)`

#### 5f. Update log

Append today's ingestion record to `<wiki-root>/.meta/log.md`.

```markdown
## YYYY-MM-DD
- **Ingested:** path/to/source.md
  - Created: page-a.md, page-b.md
  - Enriched: page-c.md (added examples)
  - Index: added N entries under "Category"
```

#### 5g. Cross-referencing pass

```bash
python3 <skill-dir>/scripts/wiki-check.py --wiki-root <path>
```

Fix any missing backlinks found.

#### 5h. Regenerate tag map and glossary

```bash
python3 <skill-dir>/scripts/wiki-tags.py --wiki-root <path> --map --glossary --save
```

### 6. Clean up

Delete all files in `<wiki-root>/.staging/`.

### 7. Git commit

```bash
git add <wiki-root>/ && git commit -m "wiki: ingest [source description]"
```

## Quality criteria

- **Preserve the author's voice** — distill in their framing, not neutral.
- **Atomic pages** — one topic each; split when in doubt.
- **Connections earn their place** — every backlink explains *why*.
- **Examples are first-class** — not optional filler.
- **Index is navigable** — find any concept in < 3 seconds.
- **Incremental integrity** — no broken links, orphans, or ghost entries.
