# Wiki lint

## When to use

Triggered by "lint", "check wiki", "wiki health", "review the wiki",
"maintain the wiki", or when the user asks about the state of the
knowledge base.

Run after a batch ingestion, when the wiki has grown significantly,
or periodically.

## Inputs

- **Scope** (optional) — `full` (default) or a specific category/page.
- **Mode** (optional) — `report` (default) or `fix` (apply safe fixes).

## Procedure

### 1. Automated structural checks + stats

Run all three scripts from the repo root:

```bash
python3 scripts/wiki-check.py --wiki-root <path>
python3 scripts/wiki-stats.py --wiki-root <path>
python3 scripts/wiki-tags.py --wiki-root <path> --normalize
```

**Checks covered by `wiki-check.py`:**

| Check | Severity | Auto-fixable |
|---|---|---|
| 2a. Orphan pages (not in index) | High | Yes — add to index |
| 2b. Ghost entries (index → no file) | High | Yes — remove from index |
| 2c. Broken internal links | Medium | Partial — fix if target exists under different name |
| 2d. Missing backlinks (A→B without B→A) | Low | Yes — add reverse link |
| 2e. Frontmatter integrity (missing fields) | Low | Yes — add defaults |
| 2f. Source list consistency (frontmatter vs visible section) | Medium | Yes — sync both |
| Thin pages (< 5 content lines) | Info | No — report only |
| Isolated pages (zero connections) | Info | No — report only |
| Stale content (source modified after `updated`) | Info | No — report only |

### 2. Content checks (LLM judgment)

For large wikis (20+ pages), delegate to subagents (one per category
or batch of 10-15 pages).

**Subagent prompt:**

> Read the following wiki pages: [list of file paths]. For each page,
> check for: (1) overlapping content with other pages in this batch,
> (2) internal contradictions or conflicting claims with other pages.
> Return a structured list of findings with page name, issue type, and
> details.

#### 2g. Duplicate or overlapping pages

Two or more pages covering substantially the same concept.

- Report the pair with overlapping content highlighted.
- No auto-fix — requires human judgment.

#### 2h. Contradictions

Pages making conflicting claims about the same concept.

- Report both pages with conflicting passages.
- No auto-fix — may be intentional (different contexts).

### 3. Connection analysis

#### 3a. Missing connections

Scan page content for mentions of concepts that have wiki pages but
aren't linked.

- Report the page, mentioned concept, and suggested link.
- No auto-fix — connection quality matters more than coverage.

#### 3b. Concept gaps

Concepts frequently mentioned across pages but without their own page.

- Report the concept, count, and which pages mention it.
- No auto-fix — suggest running ingest or creating manually.

### 4. Report findings

**Every check must appear in the report** — "None" confirms execution.

```markdown
## Wiki health report — YYYY-MM-DD

### Critical (breaks navigation)
- Orphan pages: [list or "None"]
- Ghost entries: [list or "None"]

### Warnings (degrades quality)
- Broken links: [list or "None"]
- Source mismatches: [list or "None"]
- Thin pages: [list or "None"]
- Stale content: [list or "None"]
- Overlapping pages: [list or "None"]

### Suggestions (improvements)
- Missing backlinks: [count + details, or "None — all bidirectional"]
- Missing connections: [list or "None"]
- Contradictions: [list or "None"]
- Concept gaps: [list or "None"]

### Stats
- Total pages: N | Total connections: N | Bidirectional: N%
- Categories: N | Sources ingested: N
- Average connections per page: N
- Most connected: [name] (N) | Least connected: [name] (N)
```

### 5. Apply fixes (if fix mode)

Apply auto-fixable issues in order:

1. **Ghost entries** (2b) — remove from index.
2. **Orphan pages** (2a) — add to index.
3. **Broken links** (2c) — fix if target exists under different name.
4. **Source mismatches** (2f) — sync frontmatter and visible Sources.
5. **Missing backlinks** (2d) — run:
   ```bash
   python3 scripts/wiki-backlinks.py --wiki-root <path> --batch 30
   ```
   Launch one subagent per batch. Each subagent reads each target page
   and adds reciprocal entries whose description reflects the reverse
   perspective.
6. **Frontmatter integrity** (2e) — add missing fields.
7. **Tag normalization** — for each candidate from `--normalize`:
   - E1 (plural/singular) and E3 (accent variant) are auto-fixable:
     ```bash
     python3 scripts/wiki-tags.py --wiki-root <path> --apply-normalize VARIANT CANONICAL
     ```
   - E2 (synonym/cross-language) — report only; requires human judgment.

### 6. Regenerate tag map and glossary (if fixes applied)

```bash
python3 scripts/wiki-tags.py --wiki-root <path> --map --glossary --save
```

### 7. Git commit (if fixes applied)

```bash
git add <wiki-root>/ && git commit -m "wiki-lint: YYYY-MM-DD health check"
```

## Quality criteria

- **Don't over-report.** Calibrate thresholds to wiki size.
- **Suggestions, not mandates.** Content checks produce suggestions.
- **Stats tell the story.** Quick sense of wiki health.
- **Idempotent.** Running twice produces the same report.
