#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for wiki-tags.py --search feature.

Run from repo root:
    python3 scripts/test_wiki_search.py
    python3 -m pytest scripts/test_wiki_search.py -v

All unit tests use synthetic fixtures — independent of real wiki content.
"""

import importlib.util
import json
import os
import subprocess
import sys
import unittest

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "wiki-tags.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("wiki_tags", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wt = _load_module()


def _make_page(filename, title, tags, summary_text, connections_text=""):
    """Build a minimal wiki page dict as load_wiki() would produce."""
    tags_str = ", ".join(tags)
    content = (
        f"---\ntags: [{tags_str}]\ncreated: 2026-01-01\n---\n\n"
        f"# {title}\n\n{summary_text}\n\n"
        "## Key points\n\n- Test point.\n\n"
    )
    if connections_text:
        content += f"## Connections\n\n{connections_text}\n"
    return {
        "filename": filename,
        "title": title,
        "tags": tags,
        "sources": [],
        "origin": None,
        "synthesis_sources": [],
        "created": "2026-01-01",
        "updated": "2026-01-01",
        "content_lines": 10,
        "_content": content,
    }


PAGES = {
    "protective-brain.md": _make_page(
        "protective-brain.md",
        "The protective brain",
        ["pain", "protection", "brain", "perception"],
        "The brain interprets body signals as threat or safety.",
        "[Chronic pain and movement](chronic-pain-movement.md) — stabilized pattern\n"
        "[Sedentarism](sedentarism.md) — inactive attractor\n"
        "[Attractor](attractor.md) — base concept\n",
    ),
    "chronic-pain-movement.md": _make_page(
        "chronic-pain-movement.md",
        "Chronic pain and movement",
        ["pain", "protection", "movement"],
        "Chronic pain is not acute pain that persists, but a distinct neurological pattern.",
        "[The protective brain](protective-brain.md) — underlying mechanism\n",
    ),
    "sedentarism.md": _make_page(
        "sedentarism.md",
        "Sedentarism as a deep attractor",
        ["sedentarism", "attractors", "habits"],
        "Sedentarism is not a choice but an emergent attractor of modern conditions.",
    ),
    "attractor.md": _make_page(
        "attractor.md",
        "Attractor",
        ["complex-systems", "attractors", "stability"],
        "A set of states toward which a system tends to evolve over time.",
        "[Sedentarism](sedentarism.md) — example of body attractor\n",
    ),
    "pareto-training.md": _make_page(
        "pareto-training.md",
        "Pareto in training",
        ["training", "pareto", "efficiency"],
        "The Pareto principle applied to training: 20% of effort produces 80% of adaptations.",
    ),
    "extended-cognition.md": _make_page(
        "extended-cognition.md",
        "Extended cognition",
        ["cognition", "body", "environment"],
        "Cognition does not occur only in the brain but is distributed across body and environment.",
    ),
}


class TestSearchPagesScoring(unittest.TestCase):
    """Tests for the scoring algorithm in search_pages()."""

    def _search(self, query, top_n=5):
        return wt.search_pages(query, PAGES, top_n=top_n)

    def test_tag_exact_match_scores_10(self):
        results = self._search("pain")
        filenames = [r["filename"] for r in results]
        self.assertIn("protective-brain.md", filenames)
        self.assertIn("chronic-pain-movement.md", filenames)
        top = results[0]
        self.assertGreaterEqual(top["score"], 10)

    def test_tag_match_keyword_recorded(self):
        results = self._search("pain")
        by_file = {r["filename"]: r for r in results}
        self.assertIn("protective-brain.md", by_file)
        matches = by_file["protective-brain.md"]["matched_keywords"]
        self.assertIn("pain", matches)
        self.assertIn("tag", matches["pain"])

    def test_filename_match_scores_8(self):
        results = self._search("sedentarism")
        by_file = {r["filename"]: r for r in results}
        self.assertIn("sedentarism.md", by_file)
        match_info = by_file["sedentarism.md"]["matched_keywords"]
        self.assertGreaterEqual(by_file["sedentarism.md"]["score"], 18)
        self.assertIn("filename", match_info["sedentarism"])

    def test_title_match_scores_6(self):
        results = self._search("deep")
        by_file = {r["filename"]: r for r in results}
        self.assertIn("sedentarism.md", by_file)
        matches = by_file["sedentarism.md"]["matched_keywords"]
        self.assertIn("title", matches["deep"])
        self.assertGreaterEqual(by_file["sedentarism.md"]["score"], 6)

    def test_summary_match_scores_3(self):
        results = self._search("signals")
        by_file = {r["filename"]: r for r in results}
        self.assertIn("protective-brain.md", by_file)
        matches = by_file["protective-brain.md"]["matched_keywords"]
        self.assertIn("summary", matches["signals"])
        self.assertGreaterEqual(by_file["protective-brain.md"]["score"], 3)

    def test_multiple_keywords_accumulate_scores(self):
        results = self._search("pain protection")
        by_file = {r["filename"]: r for r in results}
        self.assertIn("protective-brain.md", by_file)
        self.assertGreaterEqual(by_file["protective-brain.md"]["score"], 20)

    def test_multi_keyword_ranking(self):
        results = self._search("pain protection")
        top2 = {r["filename"] for r in results[:2]}
        self.assertTrue(
            "protective-brain.md" in top2 or "chronic-pain-movement.md" in top2
        )
        self.assertNotIn("attractor.md", top2)
        self.assertNotIn("pareto-training.md", top2)

    def test_zero_score_pages_excluded(self):
        results = self._search("pareto")
        filenames = [r["filename"] for r in results]
        self.assertNotIn("protective-brain.md", filenames)
        self.assertNotIn("attractor.md", filenames)
        self.assertIn("pareto-training.md", filenames)

    def test_top_n_limits_results(self):
        results = self._search("pain", top_n=1)
        self.assertEqual(len(results), 1)

    def test_top_n_default_is_5(self):
        results = wt.search_pages("a", PAGES)
        self.assertLessEqual(len(results), 5)

    def test_result_has_required_fields(self):
        results = self._search("pain")
        self.assertTrue(len(results) > 0)
        required = {"filename", "score", "matched_keywords", "title", "tags",
                    "summary", "connections_count", "connection_pages"}
        for r in results:
            self.assertTrue(required.issubset(r.keys()), f"Missing fields in {r}")

    def test_results_sorted_by_score_descending(self):
        results = self._search("pain protection brain")
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_connection_pages_is_list_of_filenames(self):
        results = self._search("brain")
        by_file = {r["filename"]: r for r in results}
        if "protective-brain.md" in by_file:
            conn_pages = by_file["protective-brain.md"]["connection_pages"]
            self.assertIsInstance(conn_pages, list)
            for cp in conn_pages:
                self.assertTrue(cp.endswith(".md"), f"Not a .md filename: {cp}")

    def test_connections_count_matches_connection_pages_length(self):
        results = self._search("pain")
        for r in results:
            self.assertEqual(r["connections_count"], len(r["connection_pages"]))


class TestSearchEdgeCases(unittest.TestCase):

    def test_empty_query_returns_empty_list(self):
        results = wt.search_pages("", PAGES)
        self.assertEqual(results, [])

    def test_single_char_query_ignored(self):
        results = wt.search_pages("a", PAGES)
        for r in results:
            self.assertIsInstance(r, dict)

    def test_no_match_returns_empty_list(self):
        results = wt.search_pages("xyzzy", PAGES)
        self.assertEqual(results, [])

    def test_whitespace_only_query(self):
        results = wt.search_pages("   ", PAGES)
        self.assertEqual(results, [])

    def test_empty_pages_dict(self):
        results = wt.search_pages("pain", {})
        self.assertEqual(results, [])

    def test_summary_truncated_to_200_chars(self):
        results = wt.search_pages("pain", PAGES)
        for r in results:
            self.assertLessEqual(len(r["summary"]), 200)


class TestFmtSearch(unittest.TestCase):

    def _fmt(self, query, top_n=5):
        results = wt.search_pages(query, PAGES, top_n=top_n)
        return wt.fmt_search(query, results)

    def test_header_contains_query(self):
        out = self._fmt("pain")
        self.assertIn("pain", out)

    def test_header_contains_result_count(self):
        results = wt.search_pages("pain", PAGES)
        out = wt.fmt_search("pain", results)
        self.assertIn(str(len(results)), out)

    def test_filename_in_output(self):
        results = wt.search_pages("pain", PAGES)
        out = wt.fmt_search("pain", results)
        for r in results:
            self.assertIn(r["filename"], out)

    def test_zero_results_message(self):
        out = wt.fmt_search("xyzzy", [])
        self.assertIn("0", out)

    def test_rank_numbers_in_output(self):
        results = wt.search_pages("pain", PAGES)
        out = wt.fmt_search("pain", results)
        self.assertIn("[1]", out)
        if len(results) >= 2:
            self.assertIn("[2]", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
