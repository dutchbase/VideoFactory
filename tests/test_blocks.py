"""Scene blocks: reusable HyperFrames parts in library/blocks/, found by lib find and copied by use."""
import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import anim
import library as LIBR


def block(root, bid, tags, depends=(), files=None):
    d = root / "blocks" / bid; d.mkdir(parents=True)
    files = files or [f"{bid}.js"]
    for f in files:
        (d / f).write_text(f"/* {bid} */\n")
    meta = {"id": bid, "title": f"{bid} title", "description": f"A {bid} block.", "tags": list(tags), "kind": "block",
            "engine": "hyperframes", "files": files, "depends": list(depends), "api": [f"Blocks.{bid}(H, root)"], "preview_at": 1.0}
    (d / "block.md").write_text("---\n" + "\n".join(f"{k}: {json.dumps(v)}" for k, v in meta.items()) + "\n---\n\n# " + bid + "\n")
    return d


class BlockIndex(unittest.TestCase):
    def test_index_lists_blocks(self):
        items = {e["ref"]: e for e in LIBR.index()}
        self.assertIn("block:core", items)
        self.assertEqual(items["block:core"]["kind"], "block")
        self.assertTrue(items["block:core"]["tags"])

    def test_find_matches_tags(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            block(root, "chatx", ["chat", "conversation", "prompt"])
            block(root, "other", ["stamp"])
            self.assertEqual([e["ref"] for e in LIBR.find("conversation", root)], ["block:chatx"])
            self.assertEqual([e["ref"] for e in LIBR.find("CHATX title", root)], ["block:chatx"])
            self.assertEqual(LIBR.find("conversation stamp", root), [])

    def test_index_lists_captures(self):
        refs = [e["ref"] for e in LIBR.find("recording chatgpt")]
        self.assertEqual(refs, ["capture:chatgpt-chat"])
        self.assertIn("capture:claude-chat", [e["ref"] for e in LIBR.find("recording claude")])


class BlockUse(unittest.TestCase):
    def test_use_copies_block_and_deps(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "lib"
            block(root, "core", ["helpers"])
            block(root, "chatx", ["chat"], depends=["core"], files=["chatx.js", "chatx.css"])
            vdir = Path(d) / "v"; (vdir / "04_scene").mkdir(parents=True)
            lines = LIBR.use(vdir, "block:chatx", root=root)
            for f in ("core.js", "chatx.js", "chatx.css"):
                self.assertTrue((vdir / "04_scene/blocks" / f).is_file(), f)
            text = "\n".join(lines)
            self.assertLess(text.index('src="blocks/core.js"'), text.index('src="blocks/chatx.js"'))
            self.assertIn('href="blocks/chatx.css"', text)
            log = (vdir / "04_scene/assets/library.md").read_text()
            self.assertIn("block:core | own", log)
            self.assertIn("block:chatx | own", log)

    def test_unknown_block_refused(self):
        with tempfile.TemporaryDirectory() as d:
            vdir = Path(d) / "v"; (vdir / "04_scene").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "lib find"):
                LIBR.use(vdir, "block:nope", root=Path(d))

    def test_scene_with_blocks_passes_render_rule(self):
        with tempfile.TemporaryDirectory() as d:
            vdir = Path(d); (vdir / "04_scene").mkdir(); (vdir / "01_voice").mkdir()
            voice = vdir / "01_voice/voice.wav"; voice.write_bytes(b"voice")
            (vdir / "project.json").write_text(json.dumps({"brand": "videofactory"}))
            LIBR.use(vdir, "block:core")
            (vdir / "04_scene/index.html").write_text('<audio src="../01_voice/voice.wav"></audio><script src="blocks/core.js"></script>')
            anim.check_hf_audio(vdir, voice, {"meta": {}, "cueList": []})


if __name__ == "__main__":
    unittest.main()
