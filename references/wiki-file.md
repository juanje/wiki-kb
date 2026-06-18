# Wiki file

## When to use

Triggered by "file this", "add this to the wiki", "capture this to wiki",
or when the user passes a temporary file path with intent to add its
content to the knowledge base.

Also triggered when an assistant answering questions from the wiki
synthesizes information from multiple pages into something new — the
wiki's `AGENTS.md` instructs it to offer filing the answer. If the
user agrees, this is the procedure to follow.

Handles **ephemeral knowledge** — insights from conversations, verbal
brain dumps, or temporary notes. For durable source documents (articles,
interviews), use wiki-ingest instead.

**User controls the wiki.** Never file without an explicit user trigger.

## Inputs

- **Source** — one of:
  - **Conversation context** (default): the agent identifies fileable
    content from the current conversation.
  - **File path**: user passes a path to a temporary file. The agent
    reads but never modifies or deletes the file.
- **Target** (optional) — if the user says "add this to [page]", the
  target is explicit.

## Page format

Same body structure as ingest pages. Frontmatter differs:

```markdown
---
type: concept
description: >-
  One-sentence summary of what this concept is.
tags: [tag1, tag2]
origin: conversation | ephemeral
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `type` — `concept` for regular pages; entity type for entities.
- `description` — one sentence, derived from the content being filed.
- `origin: conversation` — content from chat.
- `origin: ephemeral` — content from a temporary file.
- No `sources:` field — no permanent source document.

## Procedure

### 1. Identify content

**From conversation:**

Review the current conversation. Extract concepts, insights, examples,
or connections that meet the scope criteria.

**From file:**

Read the file at the user-provided path. Extract concepts — same logic
as wiki-ingest extraction but without a formal manifest.

**Tagging:** Include authors, thinkers, or foundational domain concepts
as tags for synthesis signal.

### 2. Reconcile

For each candidate concept:

1. Search for related existing pages:
   ```bash
   python3 <skill-dir>/scripts/wiki-tags.py --wiki-root <path> --search "keywords"
   ```
2. If matches found, read the matched pages.
3. Decide:

| Situation | Action |
|---|---|
| Not in wiki | **Create** new page |
| Wiki defines it independently | **Enrich** — add examples, connections, key points |
| Wiki covers it only in combination | **Create** if broader connections; else **Enrich** |
| Related but distinct page exists | **Create** + plan backlinks |
| Minor data point | **Absorb** — add as bullet or example |

### 3. Propose plan

Present to the user before writing:

```
Filing plan:
- Create: [concept] → [filename].md (tags: [...])
- Enrich: [existing-page].md — add [what]
- Absorb: [content] → into [existing-page].md
- Skip: [concept] — [reason]
```

**Wait for user approval.**

### 4. Write

Execute the approved plan:

#### 4a. Create new pages

Write the page to `<wiki-root>/[category-slug]/[page-name].md`,
creating the category subdirectory if it doesn't exist yet.
If the content describes an entity (glossary term,
service, team, project, person), use the corresponding template from
`references/wiki-entities.md`.

#### 4b. Enrich existing pages

Add content under appropriate sections. Update `updated:` date. Do not
add to `sources:` — ephemeral content has no persistent source path.

#### 4c. Absorb

Add as bullet, example, or subsection. Update `updated:` date.

#### 4d. Add backlinks

Bidirectional connections with explanations.

### 5. Integrate

#### 5a. Update index

Add new pages to `<wiki-root>/index.md`.

#### 5b. Regenerate tag map and glossary

```bash
python3 <skill-dir>/scripts/wiki-tags.py --wiki-root <path> --map --glossary --save
```

#### 5c. Update log

```markdown
## Filed YYYY-MM-DD
- **Origin:** conversation | ephemeral [file path if applicable]
- **Created:** page-a.md, page-b.md
- **Enriched:** page-c.md (added [what])
- **Absorbed:** [concept] → page-d.md
```

### 6. Git commit

```bash
git add <wiki-root>/ && git commit -m "wiki-file: [brief description]"
```

## Quality criteria

- **Earn your pages.** Filed pages must name something useful, not recap.
- **Preserve voice.** Content carries the user's framing.
- **Connections earn their place.** Every backlink explains why.
- **No over-filing.** Same discipline as synthesis. When in doubt, skip.
