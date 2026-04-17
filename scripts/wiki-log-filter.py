#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Filter source files against wiki ingestion history.

Given one or more source paths (files or directories), checks log.md to
determine which files need processing vs which are already ingested.

Usage:
    python3 scripts/wiki-log-filter.py --wiki-root <path> source1/ source2.md
    python3 scripts/wiki-log-filter.py --wiki-root <path> --force source/
    python3 scripts/wiki-log-filter.py --wiki-root <path> --json file1.md file2.md
"""

import argparse
import json
import os
import re
from datetime import datetime


def parse_log(wiki_root):
    """Return dict of source_filename -> log_date from log.md.

    Only scans lines that can actually contain source file references:
    - '- **Ingested:** path/to/file.md, ...' lines
    - '  - Source articles: file1.md, file2.md, ...' lines

    Deliberately ignores Created/Enriched/Backlinks/Index lines to avoid
    false positives from wiki page names matching source article names.
    """
    log_path = os.path.join(wiki_root, ".meta", "log.md")
    if not os.path.exists(log_path):
        return {}

    with open(log_path) as f:
        text = f.read()

    ingested = {}
    current_date = None

    for line in text.split("\n"):
        date_match = re.match(r"^## (\d{4}-\d{2}-\d{2})", line)
        if date_match:
            current_date = date_match.group(1)
            continue

        if not current_date:
            continue

        # "- **Ingested:** path/to/file.md, path/to/other.md — optional note"
        ingested_match = re.match(r"^-\s+\*\*Ingested:\*\*\s+(.+?)(?:\s+—.*)?$", line)
        if ingested_match:
            paths = [p.strip() for p in ingested_match.group(1).split(",")]
            for path in paths:
                path = path.strip()
                if path.endswith(".md"):
                    ingested[os.path.basename(path)] = current_date
            continue

        # "  - Source articles: file1.md, file2.md, ..." (directory batch ingestions)
        source_match = re.search(r"Source articles?:\s*(.+)", line)
        if source_match:
            fnames = re.findall(r"([a-zA-Z0-9_./-]+\.md)", source_match.group(1))
            for fname in fnames:
                ingested[fname] = current_date

    return ingested


def list_source_files(source_path):
    """List markdown files from the given path (file or directory).

    If the path is relative, it is resolved relative to the current
    working directory.
    """
    full_path = os.path.abspath(source_path)

    if os.path.isfile(full_path):
        return [source_path]

    if os.path.isdir(full_path):
        files = []
        for fn in sorted(os.listdir(full_path)):
            if fn.endswith(".md") and fn != "index.md":
                files.append(os.path.join(source_path, fn))
        return files

    return []


def filter_files(source_paths, force=False, wiki_root=None):
    """Return (to_process, already_ingested) lists for one or more source paths."""
    ingested_log = parse_log(wiki_root)

    all_files = []
    for sp in source_paths:
        all_files.extend(list_source_files(sp))

    if force:
        return [{"file": f, "reason": "force mode"} for f in all_files], []

    to_process = []
    already = []

    for fpath in all_files:
        fname = os.path.basename(fpath)
        if fname in ingested_log:
            log_date = ingested_log[fname]
            full_path = os.path.abspath(fpath)
            if os.path.exists(full_path):
                mtime = datetime.fromtimestamp(
                    os.path.getmtime(full_path)
                ).strftime("%Y-%m-%d")
                if mtime > log_date:
                    to_process.append({"file": fpath, "reason": f"modified ({mtime}) after ingestion ({log_date})"})
                else:
                    already.append({"file": fpath, "ingested": log_date})
            else:
                already.append({"file": fpath, "ingested": log_date, "note": "file not found"})
        else:
            to_process.append({"file": fpath, "reason": "not in log"})

    return to_process, already


def main():
    parser = argparse.ArgumentParser(
        description="Filter source files against wiki ingestion log"
    )
    parser.add_argument(
        "source",
        nargs="+",
        help="One or more source file or directory paths",
    )
    parser.add_argument("--force", action="store_true", help="Include all files (bypass log filter)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--wiki-root", required=True, help="Path to the wiki root directory")
    args = parser.parse_args()

    to_process, already = filter_files(args.source, args.force, args.wiki_root)

    if args.json:
        print(json.dumps({"to_process": to_process, "already_ingested": already}, indent=2, ensure_ascii=False))
        return

    sources_display = ", ".join(args.source)
    print(f"Source: {sources_display}")
    print(f"Mode: {'force' if args.force else 'normal'}\n")

    print(f"=== TO PROCESS ({len(to_process)}) ===")
    if to_process:
        for item in to_process:
            print(f"  {item['file']} — {item['reason']}")
    else:
        print("  None — all files already ingested")

    print(f"\n=== ALREADY INGESTED ({len(already)}) ===")
    if already:
        for item in already:
            note = f" ({item.get('note', '')})" if item.get("note") else ""
            print(f"  {item['file']} — ingested {item['ingested']}{note}")
    else:
        print("  None")


if __name__ == "__main__":
    main()
