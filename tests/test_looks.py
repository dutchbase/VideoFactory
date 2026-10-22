"""Looks: card schema, the shipped catalog, per-brand picks and the resolution order (looks/CONTEXT.md)."""
import json, shutil, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from studio import looks


def card(root, axis, ident, pairs, **extra):
    d = root / "looks" / axis / ident; d.mkdir(parents=True)
    meta = {"id": ident, "axis": axis, "title": ident.title(), "summary": "s", "aliases": [], "sources": [], "best_for": [],
            "formats": ["wide"], "pairs_with": pairs, "preview": "native", "build": "native", **extra}
    body = "".join(f"\n{s}\ntext\n" for s in looks.SECTIONS)
    (d / "look.md").write_text("---\n" + "\n".join(f"{k}: {json.dumps(v)}" for k, v in meta.items()) + "\n---\n" + body)
    (d / "preview.html").write_text('<div style="color: var(--accent)"></div>')
    return d


def tiny(root):
    card(root, "visual", "plain", {"editing": "cut", "content": "explain"}, palette_roles={"ink": "ink"})
    card(root, "visual", "glass", {"editing": "cut", "content": "explain"}, palette_roles={"ink": "ink"})
    card(root, "editing", "cut", ["plain"])
    card(root, "editing", "drift", ["glass"])
    card(root, "content", "explain", ["plain"])


class Catalog(unittest.TestCase):
    def test_shipped_cards_pass(self):
        self.assertEqual(looks.card_problems(ROOT), [])
        cards = looks.load_cards(ROOT)
        self.assertGreaterEqual(len(cards["visual"]), 30)
        self.assertTrue(cards["editing"] and cards["content"])

    def test_hard_coded_colour_is_a_problem(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); tiny(root)
            (root / "looks/visual/plain/preview.html").write_text('<div style="color:#ff0000"></div>')
            self.assertTrue(any("hard-codes" in p for p in looks.card_problems(root)))

    def test_missing_section_and_bad_pair(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); tiny(root)
            card(root, "visual", "broken", {"editing": "nope", "content": "explain"}, palette_roles={"ink": "ink"})
            path = root / "looks/visual/broken/look.md"
            path.write_text(path.read_text().replace("## Behaviour", "## Motion"))
            problems = looks.card_problems(root)
            self.assertTrue(any("## Behaviour" in p for p in problems))
            self.assertTrue(any("pairs_with" in p for p in problems))


class Picks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name); tiny(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_resolution_order(self):
        looks.write_prefs(self.root, "b", {"default": {"visual": "plain"}, "shortlist": ["glass"],
                                           "rules": {"course": {"visual": "glass", "editing": "drift"}}})
        self.assertEqual(looks.prefs_problems(self.root, "b"), [])
        got = looks.resolve(self.root, "b", "course")
        self.assertEqual(got["visual"], (["glass"], "rule for course"))
        self.assertEqual(got["editing"], (["drift"], "rule for course"))
        self.assertEqual(got["content"], (["explain"], "pairs with glass"))
        self.assertEqual(looks.resolve(self.root, "b", "short")["visual"], (["plain"], "brand default"))
        self.assertEqual(looks.resolve(self.root, "b", "course", {"visual": "plain"})["visual"], (["plain"], "your choice"))

    def test_no_prefs_gives_none(self):
        self.assertEqual(looks.resolve(self.root, "b")["visual"], ([], "none"))

    def test_shortlist_max_and_unknown_ids(self):
        looks.write_prefs(self.root, "b", {"shortlist": ["plain", "glass", "plain", "glass", "plain", "glass"]})
        self.assertTrue(any("at most 5" in p for p in looks.prefs_problems(self.root, "b")))
        looks.write_prefs(self.root, "b", {"default": {"visual": "ghost"}})
        self.assertTrue(any("ghost" in p for p in looks.prefs_problems(self.root, "b")))

    def test_copy_into_video_freezes_cards(self):
        dest = self.root / "videos/b/x/04_scene"; dest.mkdir(parents=True)
        picked = looks.copy_into_video(self.root, dest, looks.resolve(self.root, "b", None, {"visual": "plain"}))
        self.assertEqual(picked, {"visual": ["plain"], "editing": ["cut"], "content": ["explain"]})
        self.assertTrue((dest / "looks/visual-plain.md").is_file())

    def test_one_video_several_looks(self):
        looks.write_prefs(self.root, "b", {"rules": {"course": {"visual": ["glass", "plain"]}}})
        self.assertEqual(looks.prefs_problems(self.root, "b"), [])
        got = looks.resolve(self.root, "b", "course", {"editing": "drift,cut"})
        self.assertEqual(got["visual"], (["glass", "plain"], "rule for course"))
        self.assertEqual(got["editing"], (["drift", "cut"], "your choice"))
        self.assertEqual(got["content"], (["explain"], "pairs with glass"))
        dest = self.root / "v/04_scene"; dest.mkdir(parents=True)
        looks.copy_into_video(self.root, dest, got)
        self.assertEqual(sorted(f.name for f in (dest / "looks").iterdir()),
                         ["content-explain.md", "editing-cut.md", "editing-drift.md", "visual-glass.md", "visual-plain.md"])
        with self.assertRaises(looks.WorkspaceError):
            looks.resolve(self.root, "b", None, {"visual": "glass,ghost"})

    def test_board_marks_picks(self):
        looks.write_prefs(self.root, "b", {"default": {"visual": "plain"}, "shortlist": ["glass"]})
        page = looks.board_html(self.root, "b", looks.load_cards(self.root), looks.load_prefs(self.root, "b"), {})
        self.assertIn("default", page); self.assertIn("shortlist 1", page); self.assertIn("needs AI image", page)


if __name__ == "__main__":
    unittest.main()
