import json, re, shutil, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import libcore as C
import library as LIBR
import fxcheck
import upstream

LIB = LIBR.LIB
PARTS = sorted(p.parent for p in (LIB / "fx").glob("*/*/block.md"))


def shelf(d: Path, *parts: str) -> Path:
    """A small library in d: blocks/core, the fx kit and the named fx parts (category/id) copied from the real shelf."""
    root = Path(d) / "library"
    shutil.copytree(LIB / "blocks" / "core", root / "blocks" / "core")
    shutil.copytree(LIB / "fx" / "_kit", root / "fx" / "_kit")
    for part in parts:
        shutil.copytree(LIB / "fx" / part, root / "fx" / part)
    return root


def video(d: Path, engine: str | None) -> Path:
    v = Path(d) / "videos" / "demo"
    (v / "04_scene").mkdir(parents=True)
    if engine:
        (v / "project.json").write_text(json.dumps({"engine": engine}))
    return v


class Rules(unittest.TestCase):
    def test_every_shipped_part_passes_the_rules(self):
        self.assertGreaterEqual(len(PARTS), 2)
        for folder in PARTS:
            with self.subTest(part=folder.name):
                self.assertEqual(fxcheck.static(folder.name), [])

    def test_every_pick_is_on_the_shelf(self):
        picks = re.findall(r"^- \[x\] `upstream:([^`]+)`", (LIB / "upstream" / "PICKS.md").read_text(encoding="utf-8"), re.M)
        self.assertEqual(len(picks), 50)
        sources = {(m["source"]["site"], m["source"]["name"])
                   for m in (C.frontmatter((f / "block.md").read_text(encoding="utf-8")) for f in PARTS)}
        self.assertEqual([p for p in picks if tuple(p.split("/", 1)) not in sources], [])

    def test_banned_code_and_colours_are_found(self):
        with tempfile.TemporaryDirectory() as d:
            root = shelf(d, "text/blur-reveal")
            js = root / "fx" / "text" / "blur-reveal" / "blur-reveal.js"
            js.write_text(js.read_text() + "\nconst x = Math.random(); el.style.color = '#ff0000'; setTimeout(() => 0, 1);\n")
            problems = " ".join(fxcheck.static("blur-reveal", root))
            for word in ("Math.random", "hex colour", "timers"):
                self.assertIn(word, problems)

    def test_template_text_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = shelf(d, "text/blur-reveal")
            md = root / "fx" / "text" / "blur-reveal" / "block.md"
            md.write_text(md.read_text().replace('api: ["FX.blurReveal(', 'api: ["FX.blurReveal(H, el, {at}): rewrite this line ', 1))
            self.assertIn("template text left", " ".join(fxcheck.static("blur-reveal", root)))

    def test_unknown_category_folder_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = shelf(d, "text/blur-reveal")
            (root / "fx" / "text").rename(root / "fx" / "words")
            self.assertTrue(any("categories.json" in p for p in fxcheck.static("blur-reveal", root)))


class Use(unittest.TestCase):
    def test_lines_follow_the_engine(self):
        for engine, setup in (("hyperframes", "Blocks.core(tl)"), (None, "Blocks.core(P.timeline())")):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as d:
                root = shelf(d, "text/blur-reveal")
                v = video(d, engine)
                out = "\n".join(LIBR.use(v, "fx:blur-reveal", root=root))
                for f in ("blocks/core.js", "fx/kit.js", "fx/blur-reveal.js"):
                    self.assertTrue((v / "04_scene" / f).is_file(), f)
                self.assertIn(setup, out)
                self.assertIn('<script src="fx/blur-reveal.js"></script>', out)
                self.assertLess(out.index("blocks/core.js"), out.index("fx/kit.js"))
                self.assertIn("fx:blur-reveal", (v / "04_scene" / "assets" / "library.md").read_text())

    def test_animated_icon_is_copied_with_its_licence(self):
        src = LIB / "icons-animated" / "lucide-animated" / "bell.js"
        if not src.is_file():
            self.skipTest("no animated icons on the shelf")
        for engine, hint in (("hyperframes", "AnimIcon.play"), (None, 'data-play="@word"')):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as d:
                root = Path(d) / "library"
                (root / "icons-animated" / "lucide-animated").mkdir(parents=True)
                shutil.copy(src, root / "icons-animated" / "lucide-animated" / "bell.js")
                v = video(d, engine)
                out = LIBR.use(v, "animicon:lucide-animated/bell", root=root)
                self.assertTrue((v / "04_scene/assets/icons-animated/lucide-animated/bell.js").is_file())
                self.assertIn("MIT", out[0])
                self.assertIn(hint, "\n".join(out))


class Catalog(unittest.TestCase):
    def test_every_item_has_a_known_category(self):
        items = LIBR.scan(LIB)
        cats = set(LIBR.CATEGORIES["categories"])
        self.assertEqual(sorted({e["ref"] for e in items if e.get("category") not in cats})[:5], [])

    def test_catalog_names_every_kind_and_stays_small(self):
        text = LIBR.catalog(LIBR.scan(LIB))
        for kind in ("fx", "block", "icon", "animicon", "lottie", "upstream"):
            self.assertIn(f"| {kind} |", text)
        self.assertIn("lib find", text)
        self.assertLess(len(text.splitlines()), 200)

    def test_shipped_catalog_is_current(self):
        brands = {b.parent.name: LIBR.scan(b) for b in sorted((C.ROOT / "brands").glob("*/library")) if b.is_dir()}
        self.assertEqual((LIB / "CATALOG.md").read_text(encoding="utf-8"), LIBR.catalog(LIBR.scan(LIB), brands),
                         "run: python anim.py lib index")

    def test_find_filters_by_kind_and_category(self):
        with tempfile.TemporaryDirectory() as d:
            root = shelf(d, "text/blur-reveal", "backgrounds/particle-field")
            refs = lambda **k: [e["ref"] for e in LIBR.find("", root=root, **k)]
            self.assertEqual(refs(kind="fx", category="text"), ["fx:blur-reveal"])
            self.assertEqual(refs(kind="fx", category="backgrounds"), ["fx:particle-field"])
            self.assertEqual([e["ref"] for e in LIBR.find("calm depth", root=root)], ["fx:particle-field"])

    def test_parts_list_skips_a_broken_part(self):
        with tempfile.TemporaryDirectory() as d:
            root = shelf(d, "text/blur-reveal")
            (root / "fx" / "text" / "half-done").mkdir()
            (root / "fx" / "text" / "half-done" / "block.md").write_text("no frontmatter yet")
            parts = LIBR.fx_parts(root)
            self.assertIn('"text/blur-reveal"', parts)
            self.assertNotIn("half-done", parts)


class Cli(unittest.TestCase):
    def test_lib_commands_are_wired(self):
        import subprocess
        run = lambda *a: subprocess.run([sys.executable, str(C.ROOT / "anim.py"), "lib", *a], capture_output=True, text=True)
        self.assertIn("fx:blur-reveal: OK", run("fx", "check", "blur-reveal", "--no-browser").stdout)
        found = run("find", "--kind", "fx", "--category", "text", "--brand", "videofactory")
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertIn("fx:blur-reveal", found.stdout)
        helptext = run("-h").stdout
        for cmd in ("upstream", "port", "fx"):
            self.assertIn(cmd, helptext)


class Upstream(unittest.TestCase):
    def test_twin_names_match_across_sites(self):
        self.assertEqual(upstream._base("transition-wipe"), "wipe")
        self.assertEqual(upstream._base("bit-glitch-in"), "glitch-in")
        self.assertEqual(upstream._base("mesh-gradient-bg"), "mesh-gradient")

    def test_source_is_ported_and_twins_are_covered(self):
        with tempfile.TemporaryDirectory() as d:
            root = shelf(d, "text/blur-reveal")
            md = root / "fx" / "text" / "blur-reveal" / "block.md"
            md.write_text(md.read_text().replace("\nsource: ", '\ntwins: ["remotionui/blur-focus-in"]\nsource: ', 1) if "\ntwins:" not in md.read_text()
                          else md.read_text())
            found = upstream._ported(root)
            self.assertEqual(found[("onda", "blur-reveal")], ("fx:blur-reveal", "ported"))
            self.assertEqual(found[("remotionui", "blur-focus-in")], ("fx:blur-reveal", "covered"))

    def test_shipped_catalog_items_are_complete(self):
        keys = {"name", "title", "category", "difficulty", "status", "license", "source_file"}
        for f in sorted((LIB / "upstream").glob("*.json")):
            if f.name == "sources.json":
                continue
            with self.subTest(source=f.stem):
                items = json.loads(f.read_text(encoding="utf-8"))
                self.assertTrue(items)
                self.assertEqual([i["name"] for i in items if keys - set(i)], [])
                self.assertEqual([i["name"] for i in items if i["status"] not in ("available", "ported", "covered", "skip")], [])
                self.assertEqual([i["name"] for i in items if i["status"] == "ported" and not i.get("ported_as")], [])


if __name__ == "__main__":
    unittest.main()
