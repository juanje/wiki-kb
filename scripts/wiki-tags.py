#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Wiki tag analysis tool — feeds the wiki-synthesize skill.

Analyzes frontmatter tags to find abstraction candidates, co-occurrence clusters,
disconnected similar pages, and cross-domain bridge concepts. Also generates
glossary artifacts from entity pages with type: glossary.

Usage:
    python3 scripts/wiki-tags.py --wiki-root <path> --map
    python3 scripts/wiki-tags.py --wiki-root <path> --candidates
    python3 scripts/wiki-tags.py --wiki-root <path> --full
    python3 scripts/wiki-tags.py --wiki-root <path> --glossary
    python3 scripts/wiki-tags.py --wiki-root <path> --glossary --save
    python3 scripts/wiki-tags.py --wiki-root <path> --summaries p1.md p2.md ...

Add --json to any mode for machine-readable output.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict, Counter
from itertools import combinations

EXCLUDE_FILES = {"index.md", "tags.md", "glossary.md"}

# Tags that mirror entity types — never meaningful synthesis candidates.
META_TAGS = {"person", "service", "team", "project", "concept", "glossary"}

# Tunable thresholds
MIN_PAGES_FOR_CANDIDATE_TAG = 3       # heuristic A: min pages for orphan-dense tag
MIN_COOCCUR_FOR_CLUSTER = 3           # heuristic B: min co-occurring pages
MIN_SHARED_TAGS_DISCONNECTED = 3      # heuristic C: min shared tags, unlinked pages
CROSS_DOMAIN_FOREIGN_TAGS_MIN = 2     # heuristic D: min foreign-domain tags
CROSS_DOMAIN_TAG_DOMINANCE_MIN = 3    # heuristic D: min pages for "dominant" tag


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(content):
    """Return dict of frontmatter fields from page content."""
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    fm = m.group(1)
    result = {}
    tm = re.search(r"^tags:\s*\[(.+?)\]", fm, re.MULTILINE)
    result["tags"] = [t.strip() for t in tm.group(1).split(",")] if tm else []
    result["sources"] = re.findall(r"^\s+- (.+\.md)", fm, re.MULTILINE)
    for field in ("created", "updated", "origin", "type"):
        fv = re.search(rf"^{field}:\s*(.+)", fm, re.MULTILINE)
        result[field] = fv.group(1).strip() if fv else None
    synthesis_m = re.search(r"^synthesis_sources:\s*\[(.+?)\]", fm, re.MULTILINE)
    result["synthesis_sources"] = (
        [s.strip() for s in synthesis_m.group(1).split(",")]
        if synthesis_m else []
    )
    return result


def get_page_title(content):
    """Extract the first H1 heading from page content."""
    m = re.search(r"^# (.+)", content, re.MULTILINE)
    return m.group(1).strip() if m else None


def get_page_summary(content):
    """First non-heading, non-empty paragraph after the title."""
    body = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)
    lines = body.split("\n")
    capturing = False
    result = []
    for line in lines:
        if line.startswith("# "):
            capturing = True
            continue
        if capturing:
            if line.startswith("## "):
                break
            if line.strip():
                result.append(line.strip())
            elif result:
                break
    return " ".join(result)


def get_page_connections(content):
    """Connection entries from ## Conexiones / ## Connections."""
    m = re.search(
        r"## (?:Conexiones|Connections)\n(.*?)(?:\n## |\Z)", content, re.DOTALL
    )
    if not m:
        return []
    entries = re.findall(
        r"\[(.+?)\]\(([a-zA-Z0-9_-]+\.md)\)\s*[—–-]+\s*(.+?)(?:\n|$)", m.group(1)
    )
    return [{"title": t, "page": p, "description": d.strip()} for t, p, d in entries]


def get_full_form(content):
    """Extract the Full form value from page body (glossary pages)."""
    m = re.search(r"\*\*Full form:\*\*\s*(.+)", content)
    return m.group(1).strip() if m else None


def count_content_lines(content):
    """Non-empty, non-heading lines after frontmatter."""
    body = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)
    return sum(
        1 for line in body.split("\n")
        if line.strip() and not line.strip().startswith("#")
    )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_wiki(wiki_dir):
    """Load all markdown pages from the wiki directory."""
    pages = {}
    for fn in sorted(os.listdir(wiki_dir)):
        if not fn.endswith(".md") or fn in EXCLUDE_FILES or fn.startswith("."):
            continue
        with open(os.path.join(wiki_dir, fn), encoding="utf-8") as f:
            content = f.read()
        fm = parse_frontmatter(content)
        pages[fn] = {
            "filename": fn,
            "title": get_page_title(content),
            "tags": fm["tags"],
            "type": fm.get("type"),
            "sources": fm["sources"],
            "origin": fm["origin"],
            "synthesis_sources": fm["synthesis_sources"],
            "created": fm["created"],
            "updated": fm["updated"],
            "content_lines": count_content_lines(content),
            "_content": content,
        }
    return pages


def load_index(wiki_dir):
    """Return (page-to-category dict, ordered list of categories)."""
    index_path = os.path.join(wiki_dir, "index.md")
    if not os.path.exists(index_path):
        return {}, []
    with open(index_path, encoding="utf-8") as f:
        text = f.read()
    page_to_cat = {}
    categories = []
    current = None
    for line in text.split("\n"):
        m = re.match(r"^## (.+)", line)
        if m:
            current = m.group(1)
            categories.append(current)
        elif current:
            lm = re.search(r"\]\((.+?\.md)\)", line)
            if lm:
                page_to_cat[lm.group(1)] = current
    return page_to_cat, categories


def build_tag_index(pages):
    """tag -> sorted list of page filenames."""
    idx = defaultdict(list)
    for fn, page in pages.items():
        for tag in page["tags"]:
            idx[tag].append(fn)
    return {tag: sorted(v) for tag, v in idx.items()}


def build_link_graph(pages):
    """page -> set of linked pages (internal wiki links only)."""
    graph = {}
    for fn, page in pages.items():
        links = set(re.findall(r"\[.*?\]\(([a-zA-Z0-9_-]+\.md)\)", page["_content"]))
        graph[fn] = links
    return graph


def _ascii(s):
    """Strip diacritics for accent-insensitive comparison."""
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()


def tag_has_page(tag, pages):
    """Check whether a tag has a corresponding wiki page."""
    tag_ascii = _ascii(tag)
    for fn in pages:
        stem = fn[:-3]  # strip .md
        if _ascii(stem) == tag_ascii or _ascii(stem) == tag_ascii.replace("-", "_"):
            return True
    return False


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------

def heuristic_a(pages, tag_index, min_pages=MIN_PAGES_FOR_CANDIDATE_TAG):
    """Tags with N+ pages but no dedicated wiki page."""
    results = []
    for tag, tag_pages in tag_index.items():
        if tag in META_TAGS:
            continue
        if len(tag_pages) >= min_pages and not tag_has_page(tag, pages):
            conf = min(1.0, len(tag_pages) / 10)
            results.append({
                "heuristic": "A",
                "label": "orphan-dense-tag",
                "concept": tag,
                "evidence": (
                    f'tag "{tag}" used in {len(tag_pages)} pages, '
                    f"no dedicated wiki page"
                ),
                "page_count": len(tag_pages),
                "pages": tag_pages,
                "confidence": round(conf, 2),
            })
    return sorted(results, key=lambda x: -x["page_count"])


def heuristic_b(pages, tag_index, min_cooccur=MIN_COOCCUR_FOR_CLUSTER):
    """Tag pairs that frequently co-occur — suggest a bridge concept."""
    cooccur = Counter()
    cooccur_pages = defaultdict(list)
    for fn, page in pages.items():
        for pair in combinations(sorted(page["tags"]), 2):
            cooccur[pair] += 1
            cooccur_pages[pair].append(fn)

    results = []
    for pair, count in cooccur.most_common():
        if count < min_cooccur:
            break
        tag_a, tag_b = pair
        conf = min(1.0, count / 8)
        results.append({
            "heuristic": "B",
            "label": "cooccurrence-cluster",
            "concept": f"{tag_a} × {tag_b}",
            "tags": list(pair),
            "evidence": (
                f'tags co-occur in {count} pages: '
                f'{", ".join(cooccur_pages[pair][:5])}'
                + (f" (+{count - 5} more)" if count > 5 else "")
            ),
            "page_count": count,
            "pages": sorted(cooccur_pages[pair]),
            "confidence": round(conf, 2),
        })
    return results


def heuristic_c(pages, graph, min_shared=MIN_SHARED_TAGS_DISCONNECTED):
    """Pages sharing N+ tags with no link between them."""
    results = []
    page_list = sorted(pages.keys())
    for a, b in combinations(page_list, 2):
        shared = set(pages[a]["tags"]) & set(pages[b]["tags"])
        linked = b in graph.get(a, set()) or a in graph.get(b, set())
        if len(shared) >= min_shared and not linked:
            conf = min(1.0, len(shared) / 6)
            results.append({
                "heuristic": "C",
                "label": "disconnected-similar",
                "concept": f'{pages[a]["title"]} ↔ {pages[b]["title"]}',
                "shared_tags": sorted(shared),
                "evidence": (
                    f'{len(shared)} shared tags, no link: {sorted(shared)}'
                ),
                "page_count": 2,
                "pages": [a, b],
                "confidence": round(conf, 2),
            })
    return sorted(results, key=lambda x: -len(x["shared_tags"]))


def heuristic_d(
    pages,
    page_to_cat,
    min_foreign=CROSS_DOMAIN_FOREIGN_TAGS_MIN,
    min_dominance=CROSS_DOMAIN_TAG_DOMINANCE_MIN,
):
    """Pages with tags dominant in a different category — implicit cross-domain bridges."""
    # Build per-category tag frequency
    cat_tags = defaultdict(Counter)
    for fn, cat in page_to_cat.items():
        if fn in pages:
            for tag in pages[fn]["tags"]:
                cat_tags[cat][tag] += 1

    results = []
    for fn, page in pages.items():
        home_cat = page_to_cat.get(fn)
        if not home_cat:
            continue
        # Deduplicate: one entry per tag (pick the category where it's most dominant)
        foreign_by_tag = {}
        for tag in page["tags"]:
            for cat, freq in cat_tags.items():
                if cat != home_cat and freq.get(tag, 0) >= min_dominance:
                    if tag not in foreign_by_tag or freq[tag] > cat_tags[foreign_by_tag[tag]["dominant_in"]].get(tag, 0):
                        foreign_by_tag[tag] = {"tag": tag, "dominant_in": cat}
        foreign = list(foreign_by_tag.values())
        if len(foreign) >= min_foreign:
            conf = min(1.0, len(foreign) / 5)
            results.append({
                "heuristic": "D",
                "label": "cross-domain-bridge",
                "concept": page["title"],
                "page": fn,
                "home_category": home_cat,
                "foreign_tags": foreign,
                "evidence": (
                    f'page in "{home_cat}" has {len(foreign)} tags '
                    f"dominant in other categories"
                ),
                "page_count": 1,
                "pages": [fn],
                "confidence": round(conf, 2),
            })
    return sorted(results, key=lambda x: -len(x["foreign_tags"]))


# ---------------------------------------------------------------------------
# Heuristic E: tag normalization candidates
# ---------------------------------------------------------------------------

MIN_JACCARD_CROSSLANG = 0.75  # E2: min Jaccard for cross-language synonym
MIN_SHARED_CROSSLANG = 3      # E2: min shared pages (avoids single-page coincidences)


def heuristic_e(pages, tag_index, wiki_dir):
    """Detect tags that likely refer to the same concept and should be merged.

    E1 -- Plural/singular variant: 'muscles' and 'muscle' coexist.
    E2 -- Cross-language synonym: high page overlap, different words (e.g.
         'feedback' vs 'retroalimentacion').
    E3 -- Accent variant: same word with/without diacritics in the tag list
         (distinct from tag_has_page; here we look for actual tag duplicates).
    """
    results = []
    tags = sorted(tag_index.keys())
    tag_set = set(tags)

    # E1 -- Plural/singular
    for t in tags:
        if t.endswith("s"):
            base = t[:-1]
            if base in tag_set:
                canonical = base if len(tag_index[base]) >= len(tag_index[t]) else t
                variant = t if canonical == base else base
                conf = min(1.0, (len(tag_index[canonical]) + len(tag_index[variant])) / 10)
                results.append({
                    "heuristic": "E",
                    "subtype": "E1-plural",
                    "canonical": canonical,
                    "variant": variant,
                    "concept": f"{variant} → {canonical}",
                    "evidence": (
                        f'plural/singular pair: "{canonical}" ({len(tag_index[canonical])} pages) '
                        f'/ "{variant}" ({len(tag_index[variant])} pages)'
                    ),
                    "pages_to_fix": sorted(tag_index[variant]),
                    "page_count": len(tag_index[variant]),
                    "confidence": round(conf, 2),
                })

    # E2 -- Cross-language synonym (high Jaccard, min shared pages)
    for i, a in enumerate(tags):
        for b in tags[i + 1:]:
            if a == b:
                continue
            sa, sb = set(tag_index[a]), set(tag_index[b])
            shared = len(sa & sb)
            if shared < MIN_SHARED_CROSSLANG:
                continue
            j = shared / len(sa | sb)
            if j < MIN_JACCARD_CROSSLANG:
                continue
            # Skip if one is a plural of the other (already caught by E1)
            if a.endswith("s") and a[:-1] == b:
                continue
            if b.endswith("s") and b[:-1] == a:
                continue
            # Canonical = the one with more pages (or alphabetically first on tie)
            canonical = a if len(sa) >= len(sb) else b
            variant = b if canonical == a else a
            conf = min(1.0, j * 1.2)
            results.append({
                "heuristic": "E",
                "subtype": "E2-synonym",
                "canonical": canonical,
                "variant": variant,
                "concept": f"{variant} → {canonical}",
                "evidence": (
                    f'possible synonym: jaccard={j:.2f}, {shared} shared pages '
                    f'({", ".join(sorted(sa & sb)[:3])}'
                    + ("..." if shared > 3 else "") + ")"
                ),
                "pages_to_fix": sorted(tag_index[variant]),
                "page_count": len(tag_index[variant]),
                "confidence": round(conf, 2),
            })

    # E3 -- Accent variant (same word with/without diacritics as separate tags)
    norm_groups = defaultdict(list)
    for t in tags:
        norm_groups[_ascii(t)].append(t)
    for key, group in norm_groups.items():
        if len(group) < 2:
            continue
        # Canonical = the one with more pages, or with accents on tie
        canonical = max(group, key=lambda t: (len(tag_index[t]), t != _ascii(t)))
        for variant in group:
            if variant == canonical:
                continue
            conf = min(1.0, (len(tag_index[canonical]) + len(tag_index[variant])) / 8)
            results.append({
                "heuristic": "E",
                "subtype": "E3-accent",
                "canonical": canonical,
                "variant": variant,
                "concept": f"{variant} → {canonical}",
                "evidence": (
                    f'accent variant: "{variant}" ({len(tag_index[variant])} pages) '
                    f'and "{canonical}" ({len(tag_index[canonical])} pages) normalize to same string'
                ),
                "pages_to_fix": sorted(tag_index[variant]),
                "page_count": len(tag_index[variant]),
                "confidence": round(conf, 2),
            })

    return sorted(results, key=lambda x: -x["confidence"])


def apply_tag_normalization(canonical, variant, wiki_dir):
    """Replace all occurrences of variant tag with canonical in wiki pages.

    Returns list of files modified.
    """
    modified = []
    for fn in os.listdir(wiki_dir):
        if not fn.endswith(".md") or fn in EXCLUDE_FILES or fn.startswith("."):
            continue
        path = os.path.join(wiki_dir, fn)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        # Only touch the tags: [...] frontmatter line
        new_content = re.sub(
            r"(^tags:\s*\[.*?)" + re.escape(variant) + r"(.*?\])",
            lambda m: m.group(1) + canonical + m.group(2),
            content,
            flags=re.MULTILINE,
        )
        if new_content != content:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            modified.append(fn)
    return modified


# ---------------------------------------------------------------------------
# Tag map
# ---------------------------------------------------------------------------

def generate_tag_map(pages, tag_index):
    """Generate a tag map: tag -> count, pages, has_dedicated_page."""
    return {
        tag: {
            "count": len(pgs),
            "pages": pgs,
            "has_dedicated_page": tag_has_page(tag, pages),
        }
        for tag, pgs in sorted(tag_index.items(), key=lambda x: -len(x[1]))
    }


# ---------------------------------------------------------------------------
# Tags page + JSON map (persistent artifacts)
# ---------------------------------------------------------------------------

def write_tag_artifacts(pages, tag_index, wiki_dir):
    """Write tags.md (human-readable) and tag-map.json (machine-readable).

    tags.md lives in the wiki root alongside index.md.
    tag-map.json lives in .meta/ -- consumed by agents, not humans.
    """
    from datetime import date

    tag_map = generate_tag_map(pages, tag_index)

    # Split into: tags with a dedicated page vs. synthesis candidates
    has_page = {t: info for t, info in tag_map.items() if info["has_dedicated_page"]}
    no_page = {t: info for t, info in tag_map.items() if not info["has_dedicated_page"]}

    def page_link(fn, pages):
        title = pages[fn]["title"] if fn in pages else fn.replace(".md", "")
        return f"[{title}]({fn})"

    lines = [
        "# Tag map",
        "",
        f"*Generated: {date.today()} — {len(pages)} pages, {len(tag_index)} unique tags*",
        "",
        "Thematic index of the wiki. Complements the [category index](index.md).",
        "A tag with ✓ has a dedicated page; ✗ marks a synthesis candidate.",
        "",
        "---",
        "",
        "## Concepts with dedicated page (✓)",
        "",
    ]
    for tag, info in has_page.items():
        # Find the actual wiki page for this tag
        tag_ascii = _ascii(tag)
        page_fn = next(
            (fn for fn in pages if _ascii(fn[:-3]) == tag_ascii or _ascii(fn[:-3]) == tag_ascii.replace("-", "_")),
            None,
        )
        tag_display = f"[{tag}]({page_fn})" if page_fn else tag
        lines.append(f"### {tag_display} ({info['count']} pages)")
        for fn in info["pages"]:
            lines.append(f"- {page_link(fn, pages)}")
        lines.append("")

    lines += [
        "---",
        "",
        "## Concepts without page — synthesis candidates (✗)",
        "",
        "*Sorted by frequency. Higher frequency tags have stronger synthesis potential.*",
        "",
    ]
    for tag, info in no_page.items():
        lines.append(f"### {tag} ({info['count']} pages)")
        for fn in info["pages"]:
            lines.append(f"- {page_link(fn, pages)}")
        lines.append("")

    tags_md = "\n".join(lines)
    tags_path = os.path.join(wiki_dir, "tags.md")
    with open(tags_path, "w", encoding="utf-8") as f:
        f.write(tags_md)

    # Machine-readable JSON
    meta_dir = os.path.join(wiki_dir, ".meta")
    os.makedirs(meta_dir, exist_ok=True)
    json_path = os.path.join(meta_dir, "tag-map.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tag_map, f, indent=2, ensure_ascii=False)

    return tags_path, json_path


# ---------------------------------------------------------------------------
# Glossary artifact
# ---------------------------------------------------------------------------

GLOSSARY_TOP_N = 15


def _glossary_definition(content):
    """Extract the definition paragraph from a glossary page.

    Skips **Full form:** and **Domain:** lines that precede the actual
    definition, returning only the prose definition sentence(s).
    """
    body = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)
    lines = body.split("\n")
    capturing = False
    result = []
    for line in lines:
        if line.startswith("# "):
            capturing = True
            continue
        if not capturing:
            continue
        if line.startswith("## "):
            break
        stripped = line.strip()
        if stripped.startswith("**Full form:**") or stripped.startswith("**Domain:**"):
            continue
        if stripped:
            result.append(stripped)
        elif result:
            break
    return " ".join(result)


def build_glossary(pages, graph):
    """Collect glossary entries from pages with type: glossary.

    Each entry includes title, filename, full_form, definition, and
    incoming_links (how many other pages link to this glossary page).
    Entries are sorted by incoming link count descending.
    """
    incoming = Counter()
    for _fn, targets in graph.items():
        for t in targets:
            incoming[t] += 1

    entries = []
    for fn, page in pages.items():
        if page.get("type") != "glossary":
            continue
        entries.append({
            "filename": fn,
            "title": page["title"] or fn.replace(".md", ""),
            "full_form": get_full_form(page["_content"]),
            "definition": _glossary_definition(page["_content"]),
            "incoming_links": incoming.get(fn, 0),
        })
    entries.sort(key=lambda e: -e["incoming_links"])
    return entries


def write_glossary_artifact(pages, graph, wiki_dir, top_n=GLOSSARY_TOP_N):
    """Write glossary.md with all glossary entries.

    Returns (glossary_path, top_entries) where top_entries are the top N
    entries suitable for inclusion in the index Glossary section.
    """
    from datetime import date

    entries = build_glossary(pages, graph)
    if not entries:
        return None, []

    lines = [
        "# Glossary",
        "",
        f"*Generated: {date.today()} — {len(entries)} terms*",
        "",
        "Quick reference for abbreviations, acronyms, and internal terminology.",
        "See also the [category index](index.md) and [tag map](tags.md).",
        "",
        "---",
        "",
    ]
    for e in entries:
        full = f" — {e['full_form']}." if _full_form_suffix(e["title"], e["full_form"]) else ""
        defn = e["definition"][:150] if e["definition"] else ""
        if defn and not defn.endswith("."):
            defn += "..."
        lines.append(f"- **[{e['title']}]({e['filename']})**{full} {defn}")

    glossary_md = "\n".join(lines) + "\n"
    glossary_path = os.path.join(wiki_dir, "glossary.md")
    with open(glossary_path, "w", encoding="utf-8") as f:
        f.write(glossary_md)

    return glossary_path, entries[:top_n]


def _full_form_suffix(title, full_form):
    """Return full_form display only if not already embedded in title."""
    if not full_form:
        return ""
    if full_form.lower() in title.lower():
        return ""
    return f" ({full_form})"


def fmt_glossary(entries, top_n=GLOSSARY_TOP_N):
    """Format glossary entries for human-readable output."""
    lines = [f"\n=== GLOSSARY ({len(entries)} terms, top {top_n} shown) ==="]
    for i, e in enumerate(entries):
        if i >= top_n:
            lines.append(f"\n  ... +{len(entries) - top_n} more (see glossary.md)")
            break
        full = _full_form_suffix(e["title"], e["full_form"])
        lines.append(f"  {e['filename']}: {e['title']}{full}  [{e['incoming_links']} incoming]")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Search (--search)
# ---------------------------------------------------------------------------

def search_pages(query, pages, top_n=5):
    """Rank wiki pages by keyword relevance to query.

    Scoring per keyword per page:
      tag exact match          -> +10
      filename stem contains   -> +8
      title contains           -> +6
      first paragraph contains -> +3

    All comparisons are accent-insensitive via _ascii().
    Pages with score = 0 are excluded.
    Returns list of result dicts sorted by score descending, capped at top_n.
    """
    keywords = [_ascii(k.lower()) for k in query.split() if len(k) > 1]
    if not keywords:
        return []

    scored = []
    for fn, page in pages.items():
        score = 0
        matches = defaultdict(list)

        tags_ascii = [_ascii(t.lower()) for t in page["tags"]]
        fn_ascii = _ascii(fn[:-3].lower())  # strip .md
        title_ascii = _ascii((page["title"] or "").lower())
        summary_ascii = _ascii(get_page_summary(page["_content"]).lower())

        for kw in keywords:
            if kw in tags_ascii:
                score += 10
                matches[kw].append("tag")
            if kw in fn_ascii:
                score += 8
                matches[kw].append("filename")
            if kw in title_ascii:
                score += 6
                matches[kw].append("title")
            if kw in summary_ascii:
                score += 3
                matches[kw].append("summary")

        if score > 0:
            connections = get_page_connections(page["_content"])
            scored.append({
                "filename": fn,
                "score": score,
                "matched_keywords": dict(matches),
                "title": page["title"],
                "tags": page["tags"],
                "summary": get_page_summary(page["_content"])[:200],
                "connections_count": len(connections),
                "connection_pages": [c["page"] for c in connections],
            })

    scored.sort(key=lambda x: -x["score"])
    return scored[:top_n]


# ---------------------------------------------------------------------------
# Summaries (L2 read)
# ---------------------------------------------------------------------------

def generate_summaries(filenames, wiki_dir):
    """Generate lightweight summaries for the specified page files."""
    results = []
    for fn in filenames:
        path = os.path.join(wiki_dir, fn)
        if not os.path.exists(path):
            results.append({"filename": fn, "error": "file not found"})
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        fm = parse_frontmatter(content)
        results.append({
            "filename": fn,
            "title": get_page_title(content),
            "tags": fm["tags"],
            "summary": get_page_summary(content),
            "connections": get_page_connections(content),
            "content_lines": count_content_lines(content),
            "origin": fm["origin"],
        })
    return results


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def fmt_candidates(candidates_by_heuristic):
    """Format abstraction candidates for human-readable output."""
    lines = []
    total = sum(len(v) for v in candidates_by_heuristic.values())
    lines.append(f"\n=== ABSTRACTION CANDIDATES ({total} total) ===")

    labels = {
        "A": "Orphan-dense tags (tag used in N+ pages, no dedicated page)",
        "B": "Co-occurrence clusters (tag pair in N+ pages — bridge concept?)",
        "C": "Disconnected similar pages (N+ shared tags, no link)",
        "D": "Cross-domain bridges (page with foreign-domain tags)",
    }

    for h in ("A", "B", "C", "D"):
        items = candidates_by_heuristic.get(h, [])
        lines.append(f"\n--- Heuristic {h}: {labels[h]} ---")
        if not items:
            lines.append("  None found")
            continue
        for item in items:
            conf_bar = "█" * int(item["confidence"] * 5) + "░" * (5 - int(item["confidence"] * 5))
            lines.append(
                f"  [{conf_bar}] {item['concept']} "
                f"(conf={item['confidence']:.2f}, pages={item['page_count']})"
            )
            lines.append(f"    → {item['evidence']}")
    return "\n".join(lines)


def fmt_normalize(candidates):
    """Format tag normalization candidates for human-readable output."""
    lines = [f"\n=== TAG NORMALIZATION CANDIDATES ({len(candidates)} found) ==="]
    subtypes = {
        "E1-plural": "Plural/singular variants",
        "E2-synonym": "Cross-language or synonym pairs (high page overlap)",
        "E3-accent": "Accent variants (same word with/without diacritics)",
    }
    by_subtype = defaultdict(list)
    for c in candidates:
        by_subtype[c["subtype"]].append(c)

    for key, label in subtypes.items():
        items = by_subtype.get(key, [])
        lines.append(f"\n--- {key}: {label} ---")
        if not items:
            lines.append("  None found")
            continue
        for item in items:
            conf_bar = "█" * int(item["confidence"] * 5) + "░" * (5 - int(item["confidence"] * 5))
            lines.append(f"  [{conf_bar}] {item['concept']} (conf={item['confidence']:.2f})")
            lines.append(f"    → {item['evidence']}")
            lines.append(f"    Pages to fix: {', '.join(item['pages_to_fix'])}")
    return "\n".join(lines)


def fmt_tag_map(tag_map, limit=40):
    """Format tag map for human-readable output."""
    lines = [f"\n=== TAG MAP (top {limit} by frequency) ==="]
    for i, (tag, info) in enumerate(tag_map.items()):
        if i >= limit:
            break
        marker = "✓" if info["has_dedicated_page"] else "✗"
        lines.append(
            f"  [{marker}] {tag}: {info['count']} pages"
        )
        if not info["has_dedicated_page"] and info["count"] >= MIN_PAGES_FOR_CANDIDATE_TAG:
            lines.append(f"      ^ no page — synthesis candidate")
    lines.append(f"\n  Total unique tags: {len(tag_map)}")
    return "\n".join(lines)


def fmt_summaries(summaries):
    """Format page summaries for human-readable output."""
    lines = ["\n=== PAGE SUMMARIES ==="]
    for s in summaries:
        if "error" in s:
            lines.append(f"\n  {s['filename']}: ERROR — {s['error']}")
            continue
        lines.append(f"\n  {s['filename']}")
        lines.append(f"  Title:   {s['title']}")
        lines.append(f"  Tags:    {', '.join(s['tags'])}")
        lines.append(f"  Lines:   {s['content_lines']}")
        if s["origin"]:
            lines.append(f"  Origin:  {s['origin']}")
        lines.append(f"  Summary: {s['summary'][:200]}...")
        lines.append(f"  Connections ({len(s['connections'])}):")
        for c in s["connections"][:5]:
            lines.append(f"    → {c['page']}: {c['description'][:80]}")
        if len(s["connections"]) > 5:
            lines.append(f"    ... +{len(s['connections']) - 5} more")
    return "\n".join(lines)


def fmt_search(query, results):
    """Human-readable output for --search results."""
    header = f'\n=== SEARCH: "{query}" ({len(results)} results) ==='
    if not results:
        return header + "\n\n  No pages matched. Try broader keywords or read index.md.\n"

    lines = [header, ""]
    for i, r in enumerate(results, start=1):
        tags_str = ", ".join(r["tags"])
        summary = r["summary"] or "(no summary)"
        lines.append(f"  [{i}] {r['filename']}  (score: {r['score']})")
        lines.append(f"      Title:       {r['title']}")
        lines.append(f"      Tags:        {tags_str}")
        lines.append(f"      Summary:     {summary}")
        lines.append(f"      Connections: {r['connections_count']} pages")
        lines.append("")
    return "\n".join(lines)


def fmt_stats(pages, tag_index, candidates_by_h):
    """Format synthesis stats for human-readable output."""
    total_candidates = sum(len(v) for v in candidates_by_h.values())
    lines = [
        "\n=== SYNTHESIS STATS ===",
        f"  Pages:             {len(pages)}",
        f"  Unique tags:       {len(tag_index)}",
        f"  Tags with page:    {sum(1 for t in tag_index if tag_has_page(t, pages))}",
        f"  Tags without page: {sum(1 for t in tag_index if not tag_has_page(t, pages))}",
        f"  Candidate tags (A):{len(candidates_by_h.get('A', []))}",
        f"  Cluster pairs (B): {len(candidates_by_h.get('B', []))}",
        f"  Disconnected (C):  {len(candidates_by_h.get('C', []))}",
        f"  Cross-domain (D):  {len(candidates_by_h.get('D', []))}",
        f"  Total candidates:  {total_candidates}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Wiki tag analysis for wiki-synthesize")
    parser.add_argument(
        "--wiki-root", required=True,
        help="Root directory of the wiki"
    )
    parser.add_argument("--map", action="store_true", help="Show tag -> pages index")
    parser.add_argument("--candidates", action="store_true", help="Show abstraction candidates")
    parser.add_argument("--full", action="store_true", help="Map + candidates + stats")
    parser.add_argument(
        "--summaries", nargs="+", metavar="PAGE",
        help="Show lightweight summaries for specified pages"
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument(
        "--save", action="store_true",
        help="Write tags.md (wiki root) and tag-map.json (.meta/) — use with --map or --full"
    )
    parser.add_argument(
        "--normalize", action="store_true",
        help="Detect tag normalization candidates (plural/synonym/accent variants)"
    )
    parser.add_argument(
        "--apply-normalize", nargs=2, metavar=("VARIANT", "CANONICAL"),
        help="Replace VARIANT tag with CANONICAL across all wiki pages"
    )
    parser.add_argument(
        "--glossary", action="store_true",
        help="Show glossary entries (type: glossary pages). Use with --save to write glossary.md"
    )
    parser.add_argument(
        "--glossary-top", type=int, default=GLOSSARY_TOP_N,
        help=f"Number of top glossary entries for index section (default: {GLOSSARY_TOP_N})"
    )
    parser.add_argument(
        "--search", metavar="QUERY",
        help="Search wiki pages by keyword relevance (accent-insensitive)"
    )
    parser.add_argument(
        "--top", type=int, default=5,
        help="Max results for --search (default: 5)"
    )
    args = parser.parse_args()

    if not any([args.map, args.candidates, args.full, args.summaries, args.save,
                args.normalize, args.apply_normalize, args.search, args.glossary]):
        parser.print_help()
        sys.exit(0)

    wiki_dir = args.wiki_root
    pages = load_wiki(wiki_dir)
    tag_index = build_tag_index(pages)
    graph = build_link_graph(pages)
    page_to_cat, categories = load_index(wiki_dir)

    output = {}

    run_candidates = args.candidates or args.full
    run_map = args.map or args.full

    if run_candidates or args.full:
        candidates_by_h = {
            "A": heuristic_a(pages, tag_index),
            "B": heuristic_b(pages, tag_index),
            "C": heuristic_c(pages, graph),
            "D": heuristic_d(pages, page_to_cat),
        }
        output["candidates"] = candidates_by_h

    if run_map:
        output["tag_map"] = generate_tag_map(pages, tag_index)

    if args.search is not None:
        search_results = search_pages(args.search, pages, top_n=args.top)
        # JSON mode: emit search results as a top-level list with rank field
        if args.json:
            ranked = [{"rank": i + 1, **r} for i, r in enumerate(search_results)]
            print(json.dumps(ranked, indent=2, ensure_ascii=False))
            return
        print(fmt_search(args.search, search_results))
        return

    if args.summaries:
        output["summaries"] = generate_summaries(args.summaries, wiki_dir)

    if args.full:
        output["stats"] = {
            "total_pages": len(pages),
            "unique_tags": len(tag_index),
            "tags_with_page": sum(1 for t in tag_index if tag_has_page(t, pages)),
            "tags_without_page": sum(1 for t in tag_index if not tag_has_page(t, pages)),
            "candidate_counts": {h: len(v) for h, v in candidates_by_h.items()},
        }

    if args.apply_normalize:
        variant, canonical = args.apply_normalize
        modified = apply_tag_normalization(canonical, variant, wiki_dir)
        if modified:
            print(f"Replaced tag '{variant}' → '{canonical}' in {len(modified)} file(s):")
            for fn in modified:
                print(f"  {fn}")
            # Reload and regenerate tag map
            pages = load_wiki(wiki_dir)
            tag_index = build_tag_index(pages)
            tags_path, json_path = write_tag_artifacts(pages, tag_index, wiki_dir)
            print(f"Updated: {tags_path}")
            print(f"Updated: {json_path}")
        else:
            print(f"Tag '{variant}' not found in any page.")
        return

    if args.normalize:
        norm_candidates = heuristic_e(pages, tag_index, wiki_dir)
        output["normalize"] = norm_candidates

    if args.glossary or args.full:
        output["glossary"] = build_glossary(pages, graph)

    if args.save:
        tags_path, json_path = write_tag_artifacts(pages, tag_index, wiki_dir)
        print(f"Written: {tags_path}")
        print(f"Written: {json_path}")
        if args.glossary or args.full:
            gloss_path, _top = write_glossary_artifact(
                pages, graph, wiki_dir, top_n=args.glossary_top,
            )
            if gloss_path:
                print(f"Written: {gloss_path}")

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Human-readable output
    if "normalize" in output:
        print(fmt_normalize(output["normalize"]))

    if "tag_map" in output:
        print(fmt_tag_map(output["tag_map"]))

    if "candidates" in output:
        print(fmt_candidates(output["candidates"]))

    if "stats" in output:
        print(fmt_stats(pages, tag_index, output.get("candidates", {})))

    if "glossary" in output:
        print(fmt_glossary(output["glossary"], top_n=args.glossary_top))

    if "summaries" in output:
        print(fmt_summaries(output["summaries"]))


if __name__ == "__main__":
    main()
