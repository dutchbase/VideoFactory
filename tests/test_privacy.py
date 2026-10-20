"""Privacy scan for captures: never private data on screen. Hits name kind and place, never the text."""
import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import privacy

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "_runtime/fonts/archivo/Archivo[wdth,wght].ttf"


def frame(path, text, size=14, dark=False, w=1280, h=800):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (w, h), (26, 26, 26) if dark else (244, 242, 236))
    d = ImageDraw.Draw(im)
    d.text((300, 380), text, font=ImageFont.truetype(str(FONT), size), fill=(244, 242, 236) if dark else (26, 26, 26))
    im.save(path)
    return path


class Text(unittest.TestCase):
    def test_scan_text_kinds(self):
        hits = {
            "email": "mail me@example.com morgen",
            "phone": "call 06-12345678 or +31 6 12345678",
            "iban": "account NL91 ABNA 0417 1643 00",
            "card": "card 4111 1111 1111 1111",
            "key": "key sk-abcdefghijklmnopqrstuvwx",
            "url-query": "https://example.nl/cb?token=abc123",
        }
        for kind, text in hits.items():
            self.assertEqual(privacy.scan_text(text), [kind], text)

    def test_no_false_hits(self):
        for text in ("version 2.0.1", "€ 19,95", "2026-10-13 12:30", "30,5 s", "NL91ABNA0417164301",
                     "4111 1111 1111 1112", "Write a short, friendly mail to my customer.", "33 words"):
            self.assertEqual(privacy.scan_text(text), [], text)


class Image(unittest.TestCase):
    def test_scan_small_email_in_frame(self):
        with tempfile.TemporaryDirectory() as d:
            for dark in (False, True):
                hits = privacy.scan_image(frame(Path(d) / f"f{dark}.png", "me@example.com", dark=dark))
                self.assertEqual([h["kind"] for h in hits], ["email"], f"dark={dark}")
                x, y, w, h = hits[0]["box"]
                self.assertTrue(280 <= x <= 320 and 360 <= y <= 410, hits[0]["box"])  # in original pixels

    def test_scan_clean_frame(self):
        self.assertEqual(privacy.scan_image(ROOT / "library/blocks/chat/preview.png"), [])

    def test_scan_frames_skips_duplicates_and_numbers_frames(self):
        with tempfile.TemporaryDirectory() as d:
            clean = frame(Path(d) / "a.png", "Write a short mail.")
            same = frame(Path(d) / "b.png", "Write a short mail.")
            hit = frame(Path(d) / "c.png", "me@example.com", size=20)
            hits = privacy.scan_frames([clean, same, hit])
            self.assertEqual([(h["kind"], h["frame"]) for h in hits], [("email", 3)])

    def test_message_never_contains_match(self):
        with tempfile.TemporaryDirectory() as d:
            msg = privacy.message(privacy.scan_frames([frame(Path(d) / "a.png", "me@example.com", size=20)]))
            self.assertIn("email", msg)
            self.assertNotIn("me@example.com", msg)
            self.assertNotIn("example", msg)


if __name__ == "__main__":
    unittest.main()
