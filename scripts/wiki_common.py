"""Shared utilities for wiki-kb scripts.

Provides common constants and helpers used across all wiki scripts:
- Page listing with recursive directory walk
- Link regex for wiki-internal markdown links
- Link resolution from page-relative to wiki-root-relative paths
"""

import os
import re

EXCLUDE_FILES = {
    "index.md", "tags.md", "glossary.md",
    "README.md", "AGENTS.md", "CLAUDE.md",
}

# Matches markdown links to .md files, including subdirectory paths
# like [Title](subdir/page.md) or [Title](../other/page.md).
WIKI_LINK_RE = r"\[.*?\]\(([a-zA-Z0-9_./-]+\.md)\)"


def list_wiki_pages(wiki_dir):
    """Return sorted list of page paths relative to wiki_dir.

    Walks subdirectories recursively, skipping hidden directories
    (.meta, .staging, .obsidian, etc.).  Root-level meta files
    (index.md, tags.md, glossary.md) are excluded.

    Works with both flat wikis (returns ``["page.md", ...]``) and
    organized wikis (returns ``["teams/page.md", ...]``).
    """
    pages = []
    for root, dirs, files in os.walk(wiki_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for fn in files:
            if not fn.endswith(".md") or fn.startswith("."):
                continue
            relpath = os.path.relpath(os.path.join(root, fn), wiki_dir)
            if relpath in EXCLUDE_FILES:
                continue
            pages.append(relpath)
    return sorted(pages)


def resolve_wiki_link(page_relpath, link_target):
    """Resolve a link target to a wiki-root-relative path.

    Given a page at ``teams/toolchain.md`` with a link to
    ``../services/test-console.md``, returns ``services/test-console.md``.
    For flat wikis where *page_relpath* is ``toolchain.md`` and the
    link is ``other.md``, returns ``other.md``.
    """
    page_dir = os.path.dirname(page_relpath)
    return os.path.normpath(os.path.join(page_dir, link_target))
