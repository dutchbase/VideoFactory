import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import library as LIBR
import fxcheck

PARTS = sorted(p.parent.name for p in (LIBR.LIB / "fx").glob("*/*/block.md"))


class Demos(unittest.TestCase):
    """Every fx demo runs in the Modern kit and in HyperFrames without errors; the same time gives the same picture,
    also after seeks out of order; the picture changes over time."""

    @classmethod
    def setUpClass(cls):
        LIBR._write(LIBR.LIB / "fx" / "_demo" / "parts.js", LIBR.fx_parts(LIBR.LIB))

    def test_every_part_in_both_engines(self):
        for fid in PARTS:
            with self.subTest(part=fid):
                self.assertEqual(fxcheck.browser(fid), [])


if __name__ == "__main__":
    unittest.main()
