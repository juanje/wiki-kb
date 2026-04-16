#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Extract missing backlinks with forward descriptions, grouped by target.

Output is structured for direct use in subagent prompts during wiki-lint
fix mode: for each target page that needs backlinks, lists every source
page with its title and the original connection description.

Usage:
    python3 scripts/wiki-backlinks.py --wiki-root <path>              # grouped report
    python3 scripts/wiki-backlinks.py --wiki-root <path> --json       # machine-readable
    python3 scripts/wiki-backlinks.py --wiki-root <path> --batch 30   # split into batches
"""

import argparse
import json
import os
import re
from collections import defaultdict

EXCLUDE_FILES = {"index.md", "tags.md"}


def build_title_map(wiki_dir):
    """Build a mapping of filename -> display title from index.md."""
    index_path = os.path.join(wiki_dir, "index.md")
    if not os.path.exists(index_path):
        return {}
    with open(index_path) as f:
        text = f.read()
    return {
        m.group(2): m.group(1)
        for m in re.finditer(r"- \[(.+?)\]\((.+?\.md)\)", text)
    }


def build_link_graph_with_descriptions(wiki_dir, pages):
    """Return link graph and connection descriptions."""
    graph = {}
    descriptions = {}

    for p in pages:
        with open(os.path.join(wiki_dir, p)) as f:
            content = f.read()
        links = set(re.findall(r"\[.*?\]\(([a-zA-Z0-9_-]+\.md)\)", content))
        graph[p] = links

        conn_match = re.search(
            r"## (?:Conexiones|Connections)\n(.*?)(?:\n## |\Z)", content, re.DOTALL
        )
        if conn_match:
            for m in re.finditer(
                r"- \[([^\]]+)\]\(([a-zA-Z0-9_-]+\.md)\)\s*[—–-]\s*(.+)",
                conn_match.group(1),
            ):
                descriptions[(p, m.group(2))] = {
                    "link_title": m.group(1),
                    "description": m.group(3).strip(),
                }

    return graph, descriptions


def find_missing_backlinks(wiki_dir):
    """Find all unidirectional links (missing backlinks) in the wiki."""
    pages = sorted(
        f for f in os.listdir(wiki_dir)
        if f.endswith(".md") and f not in EXCLUDE_FILES and not f.startswith(".")
    )
    title_map = build_title_map(wiki_dir)
    graph, descriptions = build_link_graph_with_descriptions(wiki_dir, pages)

    by_target = defaultdict(list)
    for page, targets in graph.items():
        for t in targets:
            if t in graph and page not in graph[t]:
                desc_entry = descriptions.get((page, t), {})
                by_target[t].append({
                    "source": page,
                    "source_title": title_map.get(page, page.replace(".md", "")),
                    "forward_title": desc_entry.get("link_title", "?"),
                    "forward_description": desc_entry.get("description", "(inline link, no Connections description)"),
                })

    result = []
    for target in sorted(by_target, key=lambda x: len(by_target[x]), reverse=True):
        result.append({
            "target": target,
            "target_title": title_map.get(target, target.replace(".md", "")),
            "count": len(by_target[target]),
            "backlinks": by_target[target],
        })

    return result


def split_into_batches(targets, batch_size):
    """Split targets into batches of roughly batch_size backlinks each."""
    batches = []
    current_batch = []
    current_count = 0
    for t in targets:
        current_batch.append(t)
        current_count += t["count"]
        if current_count >= batch_size:
            batches.append(current_batch)
            current_batch = []
            current_count = 0
    if current_batch:
        batches.append(current_batch)
    return batches


def format_report(targets):
    """Format the missing backlinks as a human-readable grouped report."""
    total = sum(t["count"] for t in targets)
    lines = [f"Missing backlinks: {total} across {len(targets)} target pages\n"]

    for t in targets:
        lines.append(f"TARGET: {t['target']} ({t['count']} missing)")
        for bl in t["backlinks"]:
            lines.append(
                f"  <- {bl['source']} (\"{bl['source_title']}\") "
                f"— {bl['forward_description']}"
            )
        lines.append("")

    return "\n".join(lines)


def format_batches(batches):
    """Format the missing backlinks split into sized batches."""
    lines = [f"Total batches: {len(batches)}\n"]
    for i, batch in enumerate(batches, 1):
        total_bl = sum(t["count"] for t in batch)
        targets_str = ", ".join(t["target"] for t in batch)
        lines.append(f"--- Batch {i} ({total_bl} backlinks, {len(batch)} targets) ---")
        lines.append(f"Targets: {targets_str}\n")
        for t in batch:
            lines.append(f"TARGET: {t['target']} ({t['count']})")
            for bl in t["backlinks"]:
                lines.append(
                    f"  {bl['source']} (\"{bl['source_title']}\") "
                    f"— {bl['forward_description']}"
                )
            lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract missing backlinks for wiki-lint fix mode"
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--batch",
        type=int,
        metavar="SIZE",
        help="Split into batches of ~SIZE backlinks each",
    )
    parser.add_argument("--wiki-root", required=True, help="Path to the wiki root directory")
    args = parser.parse_args()

    targets = find_missing_backlinks(args.wiki_root)

    if not targets:
        print("No missing backlinks — all connections are bidirectional.")
        return

    if args.json:
        print(json.dumps(targets, indent=2, ensure_ascii=False))
    elif args.batch:
        batches = split_into_batches(targets, args.batch)
        print(format_batches(batches))
    else:
        print(format_report(targets))


if __name__ == "__main__":
    main()
