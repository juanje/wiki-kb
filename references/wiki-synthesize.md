# Wiki synthesize

## When to use

Triggered by "synthesize", "find abstractions", "what concepts are
missing", "discover patterns".

Run after significant batch ingestion, when the wiki has grown
substantially. Complements wiki-ingest (adds knowledge from outside)
by surfacing knowledge already implicit in the wiki.

## What it does

Discovers emergent concepts — ideas that appear across multiple wiki
pages but have no dedicated page — and creates those pages by
synthesizing from existing content.

## Inputs

- **Scope** (optional) — `full` (default) or a specific heuristic
  (`A`, `B`, `C`, `D`).
- **Threshold** (optional) — minimum confidence. Default: 0.4.

## Scaling strategy — progressive disclosure

| Layer | What's read | Cost | Who |
|---|---|---|---|
| L1 — Metadata | Frontmatter (tags, dates) + filenames | Near-zero | Python script |
| L2 — Structure | Title + summary + connections | Low | Python script (`--summaries`) |
| L3 — Content | Full page text | High | LLM — only confirmed candidates |

**Subagent strategy:**

| Candidates after triage | Strategy |
|---|---|
| ≤5 | Process directly |
| 6-15 | Agent's choice |
| 16+ | Use subagents (one per candidate or batch of 3) |

## Heuristics

Detected by `python3 scripts/wiki-tags.py --wiki-root <path> --candidates`:

| Heuristic | Signal | Threshold |
|---|---|---|
| **A — Orphan-dense tag** | Tag in ≥3 pages with no dedicated page | 3+ pages |
| **B — Co-occurrence cluster** | Tag pair co-occurring in ≥3 pages | 3+ co-occurrences |
| **C — Disconnected similar** | Two pages sharing ≥3 tags, no link between them | 3+ shared tags |
| **D — Cross-domain bridge** | Page in category X with ≥2 tags dominant in category Y | 2+ cross-domain tags |

## Procedure

### 1. Detect candidates (L1)

```bash
python3 scripts/wiki-tags.py --wiki-root <path> --candidates
```

Ranked list grouped by heuristic. No wiki pages read.

### 2. Triage

Filter candidates before any page reads:

- **Classify A candidates first:**
  - **Foundational concept** — domain-specific term the wiki references
    but never defines. Being a category name does not disqualify it.
    Route to foundational page (step 5b).
  - **Author/thinker** — person referenced across pages with no page.
    Route to author card (step 5c).
  - **Emergent synthesis** — pattern that pages express from different
    angles but no one has articulated. Route to synthesis (step 5).
  - **Already has a page** — existing page defines this concept
    independently. Remove.
  - **Pure vocabulary** — common words without domain-specific meaning.
    Remove.
- **Already covered (B):** Co-occurring tags both in a well-developed
  page (≥15 content lines, 3+ connections). Remove.
- **Link gap, not concept gap (C):** Obvious direct relationship between
  disconnected pages → flag for wiki-lint. Remove.
- **Thin signal (all):** Below confidence threshold. Remove.
- **Already synthesized:** Check `.meta/log.md` for past synthesis. Skip.

### 3. L2 read — structural confirmation

```bash
python3 scripts/wiki-tags.py --wiki-root <path> --summaries page1.md page2.md ...
```

Decide for each candidate:

| Signal | Decision |
|---|---|
| Pages describe different angles of same idea | → Synthesize |
| Different domains, shared structural pattern | → Synthesize (cross-domain) |
| Simply related but well-connected | → Skip |
| Concept already named in one page | → Skip (enrich that page) |
| No existing page defines this concept | → Foundational page (step 5b) |
| Insufficient material (just mentions) | → Skip |

### 4. L3 read — full content

Read full text of implicated pages for confirmed candidates.

**Subagent prompt (for 16+ candidates):**

> Read the following wiki pages: [list]. These pages share the concept
> of [concept name]. Synthesize a new wiki page that articulates the
> common thread that's implicit across them — not a summary of each,
> but the underlying idea they all express from different angles. Follow
> the wiki page format from `references/wiki-synthesize.md`.

### 5. Write synthesized pages

**Synthesis is not summary.** Articulate the pattern, not instances.

```markdown
---
tags: [tag1, tag2]
origin: synthesis
synthesis_sources: [page1.md, page2.md, page3.md]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Concept name]

[Summary — 2-3 sentences: what this concept is, why it matters]

## Key points
- [Distilled insight — abstract from sources, don't copy]

## Manifestations
- **[Source page title](source-page.md):** [How this page expresses the concept]

## Connections
- [Source page A](source-a.md) — [why it connects]
- [Broader related concept](related.md) — [relationship]
```

### 5b. Write foundational pages

Concise definition grounded in internal content, not external references.

**Material check (L3):** Verify enough substance for definition + 2-3
key properties. If pages only mention the term in passing, skip.

```markdown
---
tags: [tag1, tag2]
origin: foundational
synthesis_sources: [page1.md, page2.md, page3.md]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Concept name]

[Definition — 2-3 sentences: what this concept is and why it matters]

## Key properties
- [Core property or principle]

## In the wiki
- **[Page title](page.md):** [How this page applies the concept]

## Connections
- [Related concept](related.md) — [relationship]
```

### 5c. Write author cards

```markdown
---
tags: [author-name, relevant-domain-tags]
origin: foundational
synthesis_sources: [page1.md, page2.md, page3.md]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Author name]

[Who they are — 1-2 sentences]

## Main ideas
- [Key idea as referenced in the wiki]

## Publications
- [Book or work title] — [one-line relevance]

## In the wiki
- **[Page title](page.md):** [How this page references the author's work]

## Connections
- [Related concept](related.md) — [relationship]
```

### 6. Integrate

#### 6a. Add backlinks
Add connection entry in each source page pointing to the new page.

#### 6b. Update index
Add new pages under appropriate category.

#### 6c. Regenerate tag map

```bash
python3 scripts/wiki-tags.py --wiki-root <path> --map --save
```

#### 6d. Update log

```markdown
## Synthesis YYYY-MM-DD
- **Candidates evaluated:** N
- **Pages created:** [list]
- **Candidates skipped:** [brief reason for each]
```

### 7. Git commit

```bash
git add <wiki-root>/ && git commit -m "wiki-synthesize: YYYY-MM-DD"
```

## Quality criteria

- **Synthesis ≠ summary.** Name the pattern, don't restate instances.
- **Earn your pages.** Better 2 real concepts than 8 spurious ones.
- **Cross-domain pages are high value.**
- **Foundational ≠ encyclopedia.** Define as the wiki uses it.
- **Don't duplicate examples.** Source pages own them; synthesis references.
