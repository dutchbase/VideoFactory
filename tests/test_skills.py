"""The guided /vf-... commands: format, real paths, plain words, and the Codex copy."""
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".claude" / "skills"
MAX_LINES = 45

# Names of the guided commands (AGENTS.md has the table). A missing folder fails the test.
COMMANDS = ["vf", "vf-help", "vf-setup", "vf-new-brand", "vf-new-style", "vf-new-character", "vf-new-video",
            "vf-research", "vf-script", "vf-voice", "vf-transcript", "vf-cues", "vf-scene", "vf-render", "vf-status"]

# Company, owner and removed-feature words must not appear in the files below.
BANNED = [r"\bVAI\b", r"Slimmer met AI", r"slimmer-met-ai", r"\bVince\b", r"\b[Oo]wner", r"\bEduba\b", r"\bDesk\b",
          r"\bpixel\b", r"\bPixel\b", r"night queue", r"render queue", r"Brand-?[Oo]ps", r"Bouwsector", r"\bDutch\b"]


def load_sync():
    spec = importlib.util.spec_from_file_location("sync_skills", ROOT / "tools" / "sync_skills.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_skill(name):
    text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise AssertionError(f"{name}: no frontmatter between --- lines")
    meta = {}
    for line in m.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return text, meta, m.group(2)


def backticked(body):
    """Text between single backticks, one line at a time."""
    return [t for line in body.splitlines() for t in re.findall(r"`([^`\n]+)`", line)]


def repo_path_problem(token):
    """Return a message when `token` looks like a repo path but does not exist; else None."""
    # "/vf-..." is a command, not a path. Commands with spaces are not paths either.
    if re.search(r"\s", token) or token.startswith(("http", "~", "--", "/")) or "*" in token or "|" in token:
        return None
    if "/" not in token and not token.endswith(".md"):
        return None
    if "<" in token:                              # a path with a placeholder, for example brands/<brand>/brand.md
        prefix = token.split("<", 1)[0]
        parts = token.split("/")
        if token.startswith("videos/"):           # inside a video folder: the stage folder must exist
            for part in parts:
                if re.match(r"\d\d_\w+$", part) and not (ROOT / "stages" / part).is_dir():
                    return f"{token}: no stage folder stages/{part}"
            return None
        if prefix and not (ROOT / prefix.rstrip("/")).exists():
            return f"{token}: {prefix} does not exist"
        return None
    if not (ROOT / token.rstrip("/")).exists():
        return f"{token}: does not exist"
    return None


class SkillFormatTests(unittest.TestCase):
    def test_every_command_has_a_folder(self):
        have = {p.name for p in SKILLS.glob("vf*") if p.is_dir()}
        self.assertEqual(sorted(have), sorted(COMMANDS))

    def test_frontmatter(self):
        for name in COMMANDS:
            with self.subTest(skill=name):
                _, meta, _ = read_skill(name)
                self.assertEqual(meta.get("name"), name)
                self.assertTrue(meta.get("description"), "description is empty")
                self.assertGreater(len(meta["description"]), 40)

    def test_short(self):
        for name in COMMANDS:
            with self.subTest(skill=name):
                lines = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8").splitlines()
                self.assertLessEqual(len(lines), MAX_LINES)

    def test_points_to_the_shared_rules(self):
        for name in COMMANDS:
            with self.subTest(skill=name):
                _, _, body = read_skill(name)
                self.assertIn("_shared/talk.md", body)
                self.assertIn("_shared/guide.md", body)
                self.assertIn("Gate:", body)
                self.assertIn("Next:", body)

    def test_paths_exist(self):
        for name in COMMANDS:
            with self.subTest(skill=name):
                _, _, body = read_skill(name)
                problems = [p for p in map(repo_path_problem, backticked(body)) if p]
                self.assertEqual(problems, [])

    def test_commands_name_real_skills(self):
        for name in COMMANDS:
            with self.subTest(skill=name):
                _, _, body = read_skill(name)
                for cmd in re.findall(r"`/(vf[\w-]*)", body):
                    self.assertIn(cmd, COMMANDS)


class PlainWordsTests(unittest.TestCase):
    def test_no_company_or_removed_feature_words(self):
        files = [SKILLS / n / "SKILL.md" for n in COMMANDS]
        files += [p for p in (SKILLS / "video-retro").rglob("*") if p.is_file() and p.suffix in {".md", ".py"}]
        files += [ROOT / ".claude/agents/frame-critic.md", ROOT / ".codex/agents/frame-critic.toml"]
        for path in files:
            text = path.read_text(encoding="utf-8")
            for pattern in BANNED:
                with self.subTest(file=str(path.relative_to(ROOT)), pattern=pattern):
                    self.assertIsNone(re.search(pattern, text), f"{path.name} matches {pattern}")


class CodexCopyTests(unittest.TestCase):
    def test_agents_skills_in_sync(self):
        found = load_sync().differences()
        self.assertEqual(found, [], "run: python tools/sync_skills.py")

    def test_sync_detects_a_change(self):
        import shutil
        import tempfile
        sync = load_sync()
        with tempfile.TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "src", Path(tmp) / "dst"
            (src / "a").mkdir(parents=True)
            (src / "a" / "SKILL.md").write_text("one\n", encoding="utf-8")
            self.assertTrue(sync.differences(src, dst))
            sync.sync(src, dst)
            self.assertEqual(sync.differences(src, dst), [])
            (dst / "a" / "SKILL.md").write_text("two\n", encoding="utf-8")
            self.assertEqual(sync.differences(src, dst), ["different: a/SKILL.md"])
            (dst / "old").mkdir()
            sync.sync(src, dst)
            self.assertEqual(sync.differences(src, dst), [])
            self.assertFalse((dst / "old").exists())
            shutil.rmtree(src / "a")
            self.assertEqual(sync.differences(src, dst), ["extra skill in copy: a/"])


if __name__ == "__main__":
    unittest.main()
