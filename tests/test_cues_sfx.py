"""Effects play only from a cue heading (employers-post-free, 2026-10-17: tags in description lines were silently lost)."""
import contextlib, io, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import anim


class CueSfx(unittest.TestCase):
    def test_heading_tag_is_parsed(self):
        cues = anim.parse_cues_md('## intro "hello there" [sfx: whoosh, pop]\nA card lands.\n')
        self.assertEqual(cues[0]["sfx"], ["whoosh", "pop"])

    def test_tag_in_description_stops(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            anim.parse_cues_md('## intro "hello there"\nA card lands. [sfx: pop]\n')

    def test_comment_before_first_cue_is_fine(self):
        cues = anim.parse_cues_md('<!-- ## id "phrase" [sfx: stamp] -->\n## intro "hello there"\n')
        self.assertEqual(cues[0]["sfx"], [])


if __name__ == "__main__":
    unittest.main()
