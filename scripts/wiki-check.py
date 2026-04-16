#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Structural health checks for a wiki-kb knowledge base.

Runs: orphan pages, ghost entries, broken links, missing backlinks,
frontmatter integrity, source consistency, thin pages, isolated pages,
stale content.

Usage:
    python3 scripts/wiki-check.py --wiki-root <path>
    python3 scripts/wiki-check.py --wiki-root <path> --json
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

EXCLUDE_FILES = {"index.md", "tags.md"}
REQUIRED_FM_FIELDS = ["tags", "sources", "created", "updated"]
THIN_THRESHOLD = 5


def parse_index(wiki_dir):
    """Return set of filenames listed in index.md and category map."""
    index_path = os.path.join(wiki_dir, "index.md")
    if not os.path.exists(index_path):
        return set(), {}
    with open(index_path) as f:
        text = f.read()
    entries = set()
    categories = {}
    current_cat = None
    for line in text.split("\n"):
        cat_match = re.match(r"^## (.+)", line)
        if cat_match:
            current_cat = cat_match.group(1)
            categories[current_cat] = 0
        elif current_cat and re.match(r"^- \[", line):
            link_match = re.search(r"\]\((.+?\.md)\)", line)
            if link_match:
                entries.add(link_match.group(1))
                categories[current_cat] += 1
    return entries, categories


def list_pages(wiki_dir):
    """Return set of .md filenames in wiki dir (excluding meta files)."""
    pages = set()
    for fn in os.listdir(wiki_dir):
        if fn.endswith(".md") and fn not in EXCLUDE_FILES and not fn.startswith("."):
            pages.add(fn)
    return pages


def parse_frontmatter(content):
    """Extract frontmatter fields from page content."""
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    fm_text = m.group(1)
    fields = {}
    for field in REQUIRED_FM_FIELDS:
        if re.search(rf"^{field}:", fm_text, re.MULTILINE):
            fields[field] = True
    sources = re.findall(r"^\s+- (.+\.md)", fm_text, re.MULTILINE)
    fields["_sources_list"] = sources
    # Origin field — synthesis/conversation/ephemeral/foundational pages
    # have no external sources, so checks can skip them.
    origin_m = re.search(r"^origin:\s*(.+)", fm_text, re.MULTILINE)
    fields["_origin"] = origin_m.group(1).strip() if origin_m else None
    # Type field — entity pages (glossary, service, etc.) may also lack sources.
    type_m = re.search(r"^type:\s*(.+)", fm_text, re.MULTILINE)
    fields["_type"] = type_m.group(1).strip() if type_m else None
    return fields


def parse_visible_sources(content, wiki_dir):
    """Extract source paths from the visible Sources/Fuentes section.

    Links in the visible section are relative markdown links like
    ``[title](../path/to/source.md)`` or ``[title](path/to/source.md)``.
    We resolve them relative to *wiki_dir* and return normalised paths.
    """
    m = re.search(r"## (?:Fuentes|Sources)\n(.*?)(?:\n## |\Z)", content, re.DOTALL)
    if not m:
        return []
    raw_paths = re.findall(r"\]\(([^)]+\.md)\)", m.group(1))
    resolved = []
    for raw in raw_paths:
        full = os.path.normpath(os.path.join(wiki_dir, raw))
        resolved.append(full)
    return resolved


def build_link_graph(wiki_dir, pages):
    """Build {page: set(targets)} from internal wiki links."""
    graph = {}
    for p in pages:
        with open(os.path.join(wiki_dir, p)) as f:
            content = f.read()
        links = set(re.findall(r"\[.*?\]\(([a-zA-Z0-9_-]+\.md)\)", content))
        graph[p] = links
    return graph


def check_orphans(index_entries, actual_pages):
    """Pages on disk that are not listed in index.md."""
    return sorted(actual_pages - index_entries)


def check_ghosts(index_entries, actual_pages):
    """Entries in index.md whose files don't exist on disk."""
    return sorted(index_entries - actual_pages)


def check_broken_links(wiki_dir, graph, actual_pages):
    """Internal links that point to non-existent pages."""
    broken = []
    for page, targets in graph.items():
        for t in targets:
            if t not in actual_pages:
                broken.append({"page": page, "target": t})
    return broken


def check_missing_backlinks(graph):
    """Pages that link to a target which doesn't link back."""
    missing = []
    for page, targets in graph.items():
        for t in targets:
            if t in graph and page not in graph[t]:
                missing.append({"source": page, "target": t})
    return missing


def check_frontmatter(wiki_dir, pages):
    """Check that every page has the required frontmatter fields.

    Pages whose origin is synthesis/conversation/ephemeral/foundational,
    or whose type indicates a non-ingest entity page, are exempt from the
    ``sources`` requirement.
    """
    issues = []
    no_source_origins = {"synthesis", "conversation", "ephemeral", "foundational"}
    for p in sorted(pages):
        with open(os.path.join(wiki_dir, p)) as f:
            content = f.read()
        fields = parse_frontmatter(content)
        origin = fields.get("_origin")
        page_type = fields.get("_type")
        # Skip sources requirement for:
        # - Pages with non-ingest origin (synthesis/conversation/etc.)
        # - Entity pages (those with an explicit type field)
        skip_sources = origin in no_source_origins or page_type is not None
        required = [
            f for f in REQUIRED_FM_FIELDS
            if not (f == "sources" and skip_sources)
        ]
        missing = [f for f in required if f not in fields]
        if missing:
            issues.append({"page": p, "missing": missing})
    return issues


def check_source_consistency(wiki_dir, pages):
    """Verify frontmatter sources match the visible Sources section."""
    issues = []
    no_source_origins = {"synthesis", "conversation", "ephemeral", "foundational"}
    for p in sorted(pages):
        with open(os.path.join(wiki_dir, p)) as f:
            content = f.read()
        fields = parse_frontmatter(content)
        origin = fields.get("_origin")
        if origin in no_source_origins:
            continue
        fm_sources = set()
        for src in fields.get("_sources_list", []):
            fm_sources.add(os.path.normpath(os.path.join(wiki_dir, src)))
        vis_sources = set(parse_visible_sources(content, wiki_dir))
        only_fm = fm_sources - vis_sources
        only_vis = vis_sources - fm_sources
        if only_fm or only_vis:
            issues.append({
                "page": p,
                "only_frontmatter": sorted(only_fm),
                "only_visible": sorted(only_vis),
            })
    return issues


def check_thin_pages(wiki_dir, pages):
    """Pages with fewer than THIN_THRESHOLD content lines."""
    thin = []
    for p in sorted(pages):
        with open(os.path.join(wiki_dir, p)) as f:
            content = f.read()
        body = re.sub(r"^---\n.*?\n---\n", "", content, flags=re.DOTALL)
        lines = [
            l for l in body.strip().split("\n")
            if l.strip() and not l.strip().startswith("#")
        ]
        if len(lines) < THIN_THRESHOLD:
            thin.append({"page": p, "content_lines": len(lines)})
    return thin


def check_isolated_pages(graph):
    """Pages with zero outgoing internal links."""
    return sorted([p for p in graph if len(graph[p]) == 0])


def check_stale_content(wiki_dir, pages):
    """Pages whose sources have been modified after the page's updated date.

    Source paths in frontmatter are resolved relative to wiki_root.
    """
    stale = []
    for p in sorted(pages):
        path = os.path.join(wiki_dir, p)
        with open(path) as f:
            content = f.read()
        upd_match = re.search(r"updated:\s*(\d{4}-\d{2}-\d{2})", content)
        if not upd_match:
            continue
        updated = upd_match.group(1)
        fields = parse_frontmatter(content)
        for src in fields.get("_sources_list", []):
            # Resolve source path relative to wiki root
            if os.path.isabs(src):
                full_path = src
            else:
                full_path = os.path.normpath(os.path.join(wiki_dir, src))
            if os.path.exists(full_path):
                mtime = datetime.fromtimestamp(
                    os.path.getmtime(full_path)
                ).strftime("%Y-%m-%d")
                if mtime > updated:
                    stale.append({
                        "page": p,
                        "source": src,
                        "page_updated": updated,
                        "source_modified": mtime,
                    })
    return stale


def run_all_checks(wiki_dir):
    """Execute all health checks and return results dict."""
    index_entries, categories = parse_index(wiki_dir)
    actual_pages = list_pages(wiki_dir)
    graph = build_link_graph(wiki_dir, actual_pages)

    results = {
        "orphans": check_orphans(index_entries, actual_pages),
        "ghosts": check_ghosts(index_entries, actual_pages),
        "broken_links": check_broken_links(wiki_dir, graph, actual_pages),
        "missing_backlinks": check_missing_backlinks(graph),
        "frontmatter": check_frontmatter(wiki_dir, actual_pages),
        "source_consistency": check_source_consistency(wiki_dir, actual_pages),
        "thin_pages": check_thin_pages(wiki_dir, actual_pages),
        "isolated_pages": check_isolated_pages(graph),
        "stale_content": check_stale_content(wiki_dir, actual_pages),
    }
    return results


def format_report(results):
    """Format results as a human-readable text report."""
    lines = []

    def section(title, items, fmt_fn, empty_msg="None"):
        lines.append(f"\n=== {title} ===")
        if not items:
            lines.append(f"  {empty_msg}")
        else:
            for item in items:
                lines.append(f"  {fmt_fn(item)}")
            lines.append(f"  Count: {len(items)}")

    section("ORPHAN PAGES", results["orphans"], lambda x: f"- {x}")
    section("GHOST ENTRIES", results["ghosts"], lambda x: f"- {x}")
    section(
        "BROKEN INTERNAL LINKS",
        results["broken_links"],
        lambda x: f"{x['page']} -> {x['target']}",
    )
    section(
        "MISSING BACKLINKS",
        results["missing_backlinks"],
        lambda x: f"{x['source']} -> {x['target']} (no backlink)",
    )
    section(
        "FRONTMATTER ISSUES",
        results["frontmatter"],
        lambda x: f"{x['page']}: missing {x['missing']}",
        "All pages have complete frontmatter",
    )
    section(
        "SOURCE MISMATCHES",
        results["source_consistency"],
        lambda x: (
            f"{x['page']}: "
            + (f"only in FM: {x['only_frontmatter']}" if x["only_frontmatter"] else "")
            + (" | " if x["only_frontmatter"] and x["only_visible"] else "")
            + (f"only in Sources: {x['only_visible']}" if x["only_visible"] else "")
        ),
        "All pages have matching sources",
    )
    section(
        "THIN PAGES",
        results["thin_pages"],
        lambda x: f"{x['page']} ({x['content_lines']} content lines)",
    )
    section(
        "ISOLATED PAGES",
        results["isolated_pages"],
        lambda x: f"- {x}",
    )
    section(
        "STALE CONTENT",
        results["stale_content"],
        lambda x: (
            f"{x['page']} (updated: {x['page_updated']}) "
            f"<- {x['source']} (modified: {x['source_modified']})"
        ),
    )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Wiki-KB structural health checks")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--wiki-root",
        required=True,
        help="Path to wiki root directory",
    )
    args = parser.parse_args()

    wiki_dir = os.path.normpath(args.wiki_root)
    if not os.path.isdir(wiki_dir):
        print(f"Error: {wiki_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    results = run_all_checks(wiki_dir)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_report(results))


if __name__ == "__main__":
    main()
