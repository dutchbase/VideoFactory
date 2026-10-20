"""Shared readability plus explicitly selected brand wording. Speech stays a human check."""
import re

BANNED = r"\b(simple|easy|quick|obviously|as you know)\b"
ABBR = r"\b(e\.g|i\.e|vs|etc)\."
# On-screen provenance labels are forbidden for every brand (AGENTS.md).
_LABEL = r"(?:illustrated|illustrative|real capture|stock footage|rebuilt|drawn)"
PROVENANCE = rf"[\W_]*{_LABEL}(?:[\W_]+{_LABEL})*[\W_]*"  # the whole string is a label; ordinary sentences pass


def _sentences(text: str) -> list[str]:
    text = re.sub(ABBR, lambda m: m.group(0).replace(".", ""), text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def lint_text(text: str, lang: str = "en", *, brand: str = "videofactory", narration: bool = False) -> list[str]:
    """Problems as "<rule>: <sentence>". Empty list = pass. Word lists are English only."""
    out = []
    for s in _sentences(text):
        if "—" in s:
            out.append(f"em-dash: {s}")
        if not narration and len(s.split()) > 20:
            out.append(f"over 20 words: {s}")
        if not narration and re.fullmatch(PROVENANCE, s, re.I):
            out.append(f"provenance label on screen: {s}")
        if lang == "en" and brand == "videofactory":
            if re.search(BANNED, s, re.I):
                out.append(f"banned word: {s}")
    return out


def screen_strings(js: str) -> list[str]:
    # ponytail: regex scan, misses text built from variables. Upgrade to a text data file if that matters.
    pat = r"L\.(?:text|label)\([^,]+,\s*(['\"])((?:\\.|(?!\1).)*)\1"
    return [m.group(2).replace("\\n", " ").replace("\\'", "'").replace('\\"', '"') for m in re.finditer(pat, js)]


def html_text(html: str) -> str:
    """Visible text of a HyperFrames document or sub-composition (a <template> fragment): every text node outside
    <script>, <style> and <head>, one per line."""
    from html.parser import HTMLParser

    class Body(HTMLParser):
        def __init__(self):
            super().__init__()
            self.skip, self.parts = 0, []

        def handle_starttag(self, tag, attrs):
            self.skip += tag in ("script", "style", "head")

        def handle_endtag(self, tag):
            self.skip -= tag in ("script", "style", "head") and self.skip > 0

        def handle_data(self, data):
            if not self.skip and data.strip():
                self.parts.append(data.strip())
    b = Body()
    b.feed(html)
    b.close()
    return "\n".join(b.parts)
