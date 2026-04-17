#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Organize a flat wiki into subdirectories based on index categories.

Reads index.md to determine each page's category, computes a directory
slug for each category, moves pages into subdirectories, and updates
all internal links across the wiki.

Usage:
    python3 scripts/wiki-organize.py --wiki-root <path>              # dry-run (default)
    python3 scripts/wiki-organize.py --wiki-root <path> --apply      # execute moves
    python3 scripts/wiki-organize.py --wiki-root <path> --json       # machine-readable plan
"""

import argparse
import json
import os
import re
import shutil
import sys

from wiki_common import EXCLUDE_FILES, WIKI_LINK_RE, list_wiki_pages


def slugify(name):
    """Convert a category name to a directory slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def parse_index_categories(wiki_dir):
    """Return {page_filename: category_name} from index.md."""
    index_path = os.path.join(wiki_dir, "index.md")
    if not os.path.exists(index_path):
        print("Error: index.md not found", file=sys.stderr)
        sys.exit(1)
    with open(index_path) as f:
        text = f.read()

    page_to_cat = {}
    current_cat = None
    for line in text.split("\n"):
        m = re.match(r"^## (.+)", line)
        if m:
            current_cat = m.group(1)
            continue
        if current_cat:
            lm = re.search(r"\]\((.+?\.md)\)", line)
            if lm:
                page_to_cat[lm.group(1)] = current_cat
    return page_to_cat


def build_move_plan(wiki_dir, page_to_cat):
    """Build a plan of {old_relpath: new_relpath} for each page."""
    plan = {}
    pages = set(list_wiki_pages(wiki_dir))

    for page, cat in page_to_cat.items():
        if page not in pages:
            continue
        if os.path.dirname(page):
            continue
        subdir = slugify(cat)
        new_path = os.path.join(subdir, page)
        plan[page] = new_path

    for page in pages:
        if page not in plan and not os.path.dirname(page):
            plan[page] = page

    return plan


def update_links_in_content(content, page_old_path, page_new_path, move_plan):
    """Update all wiki links in content to reflect new page locations."""
    def replace_link(match):
        full_match = match.group(0)
        link_target = match.group(1)

        if not link_target.endswith(".md"):
            return full_match

        old_page_dir = os.path.dirname(page_old_path)
        resolved = os.path.normpath(os.path.join(old_page_dir, link_target))

        new_target_path = move_plan.get(resolved, resolved)
        new_page_dir = os.path.dirname(page_new_path)
        new_relative = os.path.relpath(new_target_path, new_page_dir)

        return full_match.replace(f"]({link_target})", f"]({new_relative})")

    return re.sub(WIKI_LINK_RE, replace_link, content)


def update_root_file_links(content, move_plan):
    """Update links in root files (index.md, tags.md, glossary.md).

    Root files stay in the wiki root, so links become the new relpath
    directly (e.g. ``teams/page.md``).
    """
    def replace_link(match):
        full_match = match.group(0)
        link_target = match.group(1)
        new_path = move_plan.get(link_target, link_target)
        return full_match.replace(f"]({link_target})", f"]({new_path})")

    return re.sub(WIKI_LINK_RE, replace_link, content)


def execute_plan(wiki_dir, move_plan, page_to_cat):
    """Move files and update all links."""
    moved = []

    for old_path, new_path in move_plan.items():
        if old_path == new_path:
            continue
        new_abs = os.path.join(wiki_dir, new_path)
        os.makedirs(os.path.dirname(new_abs), exist_ok=True)

    for old_path in sorted(move_plan.keys()):
        new_path = move_plan[old_path]
        abs_old = os.path.join(wiki_dir, old_path)
        if not os.path.exists(abs_old):
            continue

        with open(abs_old, encoding="utf-8") as f:
            content = f.read()

        new_content = update_links_in_content(content, old_path, new_path, move_plan)

        if old_path != new_path:
            abs_new = os.path.join(wiki_dir, new_path)
            with open(abs_new, "w", encoding="utf-8") as f:
                f.write(new_content)
            os.remove(abs_old)
            moved.append({"from": old_path, "to": new_path})
        elif new_content != content:
            with open(abs_old, "w", encoding="utf-8") as f:
                f.write(new_content)

    for root_file in EXCLUDE_FILES:
        path = os.path.join(wiki_dir, root_file)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        new_content = update_root_file_links(content, move_plan)
        if new_content != content:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

    return moved


def format_plan(move_plan, page_to_cat):
    """Format the move plan as a human-readable report."""
    lines = ["=== ORGANIZATION PLAN ===", ""]

    by_dir = {}
    for old, new in sorted(move_plan.items()):
        target_dir = os.path.dirname(new) or "(root)"
        by_dir.setdefault(target_dir, []).append((old, new))

    for target_dir, items in sorted(by_dir.items()):
        if target_dir == "(root)":
            lines.append(f"Staying in root ({len(items)} pages):")
            for old, new in items:
                lines.append(f"  {old}")
        else:
            lines.append(f"→ {target_dir}/ ({len(items)} pages):")
            for old, new in items:
                lines.append(f"  {old} → {new}")
        lines.append("")

    moves = [(o, n) for o, n in move_plan.items() if o != n]
    lines.append(f"Total moves: {len(moves)}")
    lines.append(f"Pages staying in root: {sum(1 for o, n in move_plan.items() if o == n)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Organize flat wiki into subdirectories by index category"
    )
    parser.add_argument("--wiki-root", required=True, help="Path to the wiki root directory")
    parser.add_argument("--apply", action="store_true", help="Execute the moves (default is dry-run)")
    parser.add_argument("--json", action="store_true", help="Output plan as JSON")
    args = parser.parse_args()

    wiki_dir = os.path.normpath(args.wiki_root)
    if not os.path.isdir(wiki_dir):
        print(f"Error: {wiki_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    page_to_cat = parse_index_categories(wiki_dir)
    move_plan = build_move_plan(wiki_dir, page_to_cat)

    if args.json:
        output = {
            "plan": [
                {"from": old, "to": new, "category": page_to_cat.get(old, "(orphan)")}
                for old, new in sorted(move_plan.items())
            ],
            "total_moves": sum(1 for o, n in move_plan.items() if o != n),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    print(format_plan(move_plan, page_to_cat))

    if not args.apply:
        print("\nDry run — no files moved. Use --apply to execute.")
        return

    moved = execute_plan(wiki_dir, move_plan, page_to_cat)
    print(f"\n=== EXECUTED ===")
    print(f"Moved {len(moved)} pages:")
    for m in moved:
        print(f"  {m['from']} → {m['to']}")
    print("\nRun wiki-check.py to verify all links are intact.")


if __name__ == "__main__":
    main()
