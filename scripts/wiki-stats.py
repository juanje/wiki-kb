#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Wiki graph statistics.

Usage:
    python3 scripts/wiki-stats.py --wiki-root <path>            # human-readable
    python3 scripts/wiki-stats.py --wiki-root <path> --json     # machine-readable
"""

import argparse
import json
import os
import re
import sys

EXCLUDE_FILES = {"index.md", "tags.md"}


def gather_stats(wiki_dir):
    # Parse index for categories
    index_path = os.path.join(wiki_dir, "index.md")
    categories = {}
    if os.path.exists(index_path):
        with open(index_path) as f:
            text = f.read()
        current_cat = None
        for line in text.split("\n"):
            m = re.match(r"^## (.+)", line)
            if m:
                current_cat = m.group(1)
                categories[current_cat] = 0
            elif current_cat and re.match(r"^- \[", line):
                categories[current_cat] += 1

    # List pages and build link graph
    pages = sorted(
        f for f in os.listdir(wiki_dir)
        if f.endswith(".md") and f not in EXCLUDE_FILES and not f.startswith(".")
    )

    graph = {}
    all_sources = set()
    for p in pages:
        with open(os.path.join(wiki_dir, p)) as f:
            content = f.read()
        links = set(re.findall(r"\[.*?\]\(([a-zA-Z0-9_-]+\.md)\)", content))
        graph[p] = links
        fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            all_sources.update(re.findall(r"^\s+- (.+\.md)", fm_match.group(1), re.MULTILINE))

    total_pages = len(pages)
    total_directed = sum(len(v) for v in graph.values())

    # Bidirectionality
    bidi_count = 0
    for page, targets in graph.items():
        for t in targets:
            if t in graph and page in graph[t]:
                bidi_count += 1
    bidi_pct = (bidi_count / total_directed * 100) if total_directed > 0 else 0

    # Outgoing connections
    outgoing = {p: len(graph.get(p, set())) for p in pages}
    most_out = max(outgoing, key=outgoing.get) if outgoing else None
    least_out = min(outgoing, key=outgoing.get) if outgoing else None
    avg_conn = total_directed / total_pages if total_pages > 0 else 0

    # Incoming connections
    incoming = {p: 0 for p in pages}
    for page, targets in graph.items():
        for t in targets:
            if t in incoming:
                incoming[t] += 1
    most_in = max(incoming, key=incoming.get) if incoming else None
    least_in = min(incoming, key=incoming.get) if incoming else None
    zero_incoming = sorted(p for p, c in incoming.items() if c == 0)

    # Lowest outgoing
    lowest_out = sorted(outgoing.items(), key=lambda x: x[1])[:10]
    # Highest incoming
    highest_in = sorted(incoming.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_pages": total_pages,
        "total_directed_connections": total_directed,
        "bidirectional_pct": round(bidi_pct, 1),
        "categories": categories,
        "total_categories": len(categories),
        "total_sources_ingested": len(all_sources),
        "avg_connections_per_page": round(avg_conn, 1),
        "most_connected_outgoing": {"page": most_out, "count": outgoing.get(most_out, 0)} if most_out else None,
        "least_connected_outgoing": {"page": least_out, "count": outgoing.get(least_out, 0)} if least_out else None,
        "most_linked_to_incoming": {"page": most_in, "count": incoming.get(most_in, 0)} if most_in else None,
        "least_linked_to_incoming": {"page": least_in, "count": incoming.get(least_in, 0)} if least_in else None,
        "zero_incoming_pages": zero_incoming,
        "top_10_incoming": [{"page": p, "count": c} for p, c in highest_in],
        "bottom_10_outgoing": [{"page": p, "count": c} for p, c in lowest_out],
    }


def format_stats(stats):
    lines = [
        "=== WIKI STATS ===",
        f"  Total pages:          {stats['total_pages']}",
        f"  Directed connections: {stats['total_directed_connections']}",
        f"  Bidirectional:        {stats['bidirectional_pct']}%",
        f"  Categories:           {stats['total_categories']}",
        f"  Sources ingested:     {stats['total_sources_ingested']}",
        f"  Avg connections/page: {stats['avg_connections_per_page']}",
        "",
    ]
    if stats["most_connected_outgoing"]:
        m = stats["most_connected_outgoing"]
        lines.append(f"  Most connected (out): {m['page']} ({m['count']})")
    if stats["least_connected_outgoing"]:
        m = stats["least_connected_outgoing"]
        lines.append(f"  Least connected (out): {m['page']} ({m['count']})")
    if stats["most_linked_to_incoming"]:
        m = stats["most_linked_to_incoming"]
        lines.append(f"  Most linked-to (in):  {m['page']} ({m['count']})")

    lines.append("\n=== PAGES PER CATEGORY ===")
    for cat, count in stats["categories"].items():
        lines.append(f"  {cat}: {count}")

    if stats["zero_incoming_pages"]:
        lines.append("\n=== PAGES WITH 0 INCOMING LINKS ===")
        for p in stats["zero_incoming_pages"]:
            lines.append(f"  - {p}")

    lines.append("\n=== TOP 10 MOST LINKED-TO (incoming) ===")
    for item in stats["top_10_incoming"]:
        lines.append(f"  {item['page']}: {item['count']}")

    lines.append("\n=== BOTTOM 10 LEAST CONNECTED (outgoing) ===")
    for item in stats["bottom_10_outgoing"]:
        lines.append(f"  {item['page']}: {item['count']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Wiki graph statistics")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--wiki-root", required=True,
                        help="Path to the wiki root directory")
    args = parser.parse_args()

    stats = gather_stats(args.wiki_root)

    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print(format_stats(stats))


if __name__ == "__main__":
    main()
