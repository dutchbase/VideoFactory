"""The sound library (audio.py): sorting, ZIP range reads, inbox sorting, index, find and use, all offline."""
import io, json, subprocess, sys, tempfile, unittest, zipfile, zlib
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "_runtime"))
import audio
import check
import synth


def wav(path, seconds=0.3, freq=440):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={seconds}:sample_rate=22050",
                    str(path)], check=True)
    return path


def ranges(data: bytes):
    return lambda a, b: io.BytesIO(data[a:b + 1])


SOURCES = {"licences": {"CC0-1.0": {"url": "https://creativecommons.org/publicdomain/zero/1.0/", "terms": "free"},
                        "Sonniss-GDC": {"url": "https://sonniss.com/gdc-bundle-license/", "terms": "no sharing"}},
           "categories": {"sfx": {"whoosh": "", "ui": "", "impact": "", "other": ""}, "music": {"lofi-chill": "", "other": ""}},
           "sources": [{"id": "pack", "kind": "sfx", "method": "inbox", "page": "https://example.org/pack", "author": "A", "licence": "CC0-1.0"},
                       {"id": "tunes", "kind": "music", "method": "inbox", "page": "https://example.org/tunes", "author": "B",
                        "licence": "CC0-1.0", "category": "lofi-chill"},
                       {"id": "big", "kind": "sfx", "method": "sonniss", "remote": True, "page": "https://example.org/big",
                        "author": "S", "licence": "Sonniss-GDC", "parts": ["https://example.org/p1.zip"]}]}


class Sorting(unittest.TestCase):
    def test_slug_is_safe_for_sfx_tokens(self):
        self.assertEqual(audio.slug("WHSHAir_Fast Pass, Big (01)_BOOM.wav"), "whshair_fast-pass-big-01-_boom.wav")
        self.assertEqual(audio.slug("../Ünïcode..name"), "unicode.name")
        synth.parse_sfx(f"file:sfx/whoosh/{audio.slug('Fast, Pass [1].wav')}")

    def test_ucs_name_wins_then_pack_then_words(self):
        self.assertEqual(audio.classify_sfx("BOOM - Pack/WHSHAir_Fast Pass_BOOM_X.wav"), "whoosh")
        self.assertEqual(audio.classify_sfx("x/METLImpt_Pipe Hit_ABC.wav"), "impact")  # subcategory Impt
        self.assertEqual(audio.classify_sfx("x/UIClick_Soft_ABC.wav", "impact"), "ui")
        self.assertEqual(audio.classify_sfx("x/door_open.wav", "ui"), "ui")
        self.assertEqual(audio.classify_sfx("Cinematic Risers/big_one.wav"), "transition")
        self.assertEqual(audio.classify_sfx("x/DSGNMisc_Texture_ABC.wav"), "designed")
        self.assertEqual(audio.classify_sfx("x/qwerty.wav"), "other")
        self.assertEqual(audio.title_of("EQUISprt_Climbing Gear, Lock 01_344 Audio_Vol 1.wav"), "Climbing Gear, Lock 01")
        self.assertEqual(audio.classify_sfx("Sound Sower - Vehicles Pass-by/31 Cars, traffic, road.wav"), "vehicle")
        self.assertEqual(audio.classify_sfx("Bluezone - Crab - Creature/Bluezone_ambience_ocean_waves_002.wav"), "ambience")
        self.assertEqual(audio.pack_of("Sonniss.com - GDC 2019 - Game Audio Bundle Part 2of8/L.A. Sounds - Pack/x.wav"), "L.A. Sounds - Pack")
        self.assertEqual(audio.pack_of("BOOM - Pack/x.wav"), "BOOM - Pack")

    def test_music_mixed_pack_reads_title(self):
        self.assertEqual(audio.classify_music("Spooky Night", "playful-game", mixed=True), "dark-tension")
        self.assertEqual(audio.classify_music("Spooky Night", "lofi-chill"), "lofi-chill")
        self.assertEqual(audio.classify_music("Untitled 3", "playful-game", mixed=True), "playful-game")


class RangeZip(unittest.TestCase):
    def make(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(zipfile.ZipInfo("Pack A/"), b"")
            z.writestr("Pack A/stored.wav", b"RIFF" + bytes(range(256)) * 40, compress_type=zipfile.ZIP_STORED)
            z.writestr("Pack A/Ünï deflated.wav", b"RIFF" + b"abc" * 5000, compress_type=zipfile.ZIP_DEFLATED)
        return buf.getvalue()

    def test_list_and_fetch_one_member(self):
        data = self.make()
        entries = audio.zip_entries(ranges(data), len(data))
        self.assertEqual([e["name"] for e in entries], ["Pack A/stored.wav", "Pack A/Ünï deflated.wav"])
        with tempfile.TemporaryDirectory() as d:
            for e in entries:
                out = audio.zip_member(ranges(data), e, Path(d) / Path(e["name"]).name)
                self.assertEqual(out.read_bytes(), zipfile.ZipFile(io.BytesIO(data)).read(e["name"]))

    def test_broken_data_fails_the_crc(self):
        data = bytearray(self.make())
        e = audio.zip_entries(ranges(bytes(data)), len(data))[0]
        data[e["offset"] + 30 + len(e["name"]) + 10] ^= 0xFF
        with tempfile.TemporaryDirectory() as d, self.assertRaises(ValueError):
            audio.zip_member(ranges(bytes(data)), e, Path(d) / "x.wav")
        self.assertEqual(zlib.crc32(b""), 0)


class Library(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "audio"
        self.root.mkdir()
        (self.root / "sources.json").write_text(json.dumps(SOURCES))
        self.patch = mock.patch.object(audio, "AUDIO", self.root)
        self.patch.start()
        src = Path(self.tmp.name) / "src"
        a = wav(src / "Swoosh Fast.wav", freq=500)
        wav(src / "click.wav", freq=900)
        (self.root / "inbox" / "pack").mkdir(parents=True)
        with zipfile.ZipFile(self.root / "inbox" / "pack" / "pack.zip", "w") as z:
            z.write(a, "Pack/WAV/Swoosh Fast.wav")
            z.write(src / "click.wav", "Pack/click.wav")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(a), str(src / "Swoosh Fast.mp3")], check=True)
            z.write(src / "Swoosh Fast.mp3", "Pack/MP3/Swoosh Fast.mp3")  # same track, worse format
        (self.root / "inbox" / "pack" / "zz click copy.wav").write_bytes((src / "click.wav").read_bytes())  # duplicate
        wav(self.root / "inbox" / "tunes" / "Rainy Day Loop.wav", seconds=1.0, freq=300)
        self.whoosh = a

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_inbox_sort_dedupe_index_find(self):
        logs = []
        audio.fetch(log=logs.append)
        self.assertIn("pack: 2 files from inbox/pack/ (1 duplicates skipped)", logs)
        self.assertFalse(any((self.root / "inbox").rglob("*.*")), "the inbox is emptied")
        shelf = sorted(p.relative_to(self.root).as_posix() for p in (self.root / "sfx").rglob("*.*"))
        self.assertEqual(shelf, ["sfx/ui/pack/click.wav", "sfx/whoosh/pack/swoosh-fast.wav"])
        self.assertTrue((self.root / "music" / "lofi-chill" / "tunes" / "rainy-day-loop.wav").exists())
        stats = audio.index(log=lambda *_: None)
        self.assertEqual(stats, {"sfx_local": 2, "sfx_remote": 0, "music": 1})
        rows = audio._tsv(self.root / "index" / "sfx-whoosh.tsv")
        self.assertEqual((rows[0]["where"], rows[0]["name"], rows[0]["licence"]), ("local", "Swoosh Fast", "CC0-1.0"))
        self.assertAlmostEqual(float(rows[0]["dur_s"]), 0.3, places=1)
        music = audio._tsv(self.root / "index" / "music-lofi-chill.tsv")[0]
        self.assertEqual((music["loop"], music["author"]), ("yes", "B"))
        md = (self.root / "INDEX.md").read_text()
        self.assertIn("| whoosh |", md)
        self.assertIn("index/music-lofi-chill.tsv", md)
        self.assertEqual([r["name"] for r in audio.find("swoosh")], ["Swoosh Fast"])
        self.assertEqual(audio.find("swoosh", max_s=0.1), [])
        self.assertEqual(audio.find("rainy", kind="music")[0]["title"], "Rainy Day Loop")

    def test_remote_rows_skip_files_already_on_disk_and_get_checks_crc(self):
        audio.fetch(log=lambda *_: None)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.write(self.whoosh, "Vendor - Lib/WHSHAir_Swoosh Fast_V_L.wav")  # same bytes as a local file
            z.writestr("Vendor - Lib/IMPTMetal_Big Hit_V_L.wav", (self.whoosh.read_bytes() + b"x" * 999), compress_type=zipfile.ZIP_DEFLATED)
        data = buf.getvalue()
        with mock.patch.object(audio, "_ranges", lambda url: ranges(data)), mock.patch.object(audio, "_size", lambda url: len(data)):
            audio.catalog(log=lambda *_: None)
            audio.index(log=lambda *_: None)
            remote = audio.find("big hit")
            self.assertEqual([(r["where"], r["category"], r["licence"]) for r in remote], [("remote", "impact", "Sonniss-GDC")])
            self.assertEqual(audio.find("swoosh")[0]["where"], "local")
            got = audio.get([remote[0]["id"]], log=lambda *_: None)
        path = self.root / got[0]["path"]
        self.assertEqual(path.relative_to(self.root).as_posix(), "sfx/impact/big/vendor-lib/imptmetal_big-hit_v_l.wav")
        self.assertEqual(path.read_bytes(), zipfile.ZipFile(io.BytesIO(data)).read("Vendor - Lib/IMPTMetal_Big Hit_V_L.wav"))
        audio.index(log=lambda *_: None)
        self.assertEqual(audio.find("big hit")[0]["where"], "local")

    def test_index_moves_files_when_a_category_changes(self):
        audio.fetch(log=lambda *_: None)
        cfg = json.loads((self.root / "sources.json").read_text())
        cfg["sources"][0]["category"] = "impact"
        (self.root / "sources.json").write_text(json.dumps(cfg))
        logs = []
        audio.index(log=logs.append)
        self.assertIn("2 effects moved to another category (sorting rules or sources.json changed)", logs)
        self.assertEqual(sorted(p.name for p in (self.root / "sfx" / "impact" / "pack").iterdir()), ["click.wav", "swoosh-fast.wav"])
        self.assertFalse((self.root / "sfx" / "ui").exists(), "empty folders are removed")
        self.assertEqual(len(audio.find("swoosh", category="impact")), 1)

    def test_use_cuts_copies_and_writes_a_licence_line_check_accepts(self):
        audio.fetch(log=lambda *_: None)
        audio.index(log=lambda *_: None)
        aid = audio.find("swoosh")[0]["id"]
        vdir = Path(self.tmp.name) / "video"
        lines = audio.use(vdir, aid, "whoosh-1", "0", "0.2")
        dest = vdir / "04_scene" / "assets" / "sfx" / "whoosh-1.wav"
        self.assertTrue(dest.exists())
        self.assertIn("[sfx: file:sfx/whoosh-1.wav]", lines[1])
        sound_md = (vdir / "04_scene" / "assets" / "sound.md").read_text()
        cues = [{"id": "s0", "sfx": ["file:sfx/whoosh-1.wav"]}]
        counters, _ = check.sfx_counters(cues, sound_md, lambda n: vdir / "04_scene" / "assets" / n, synth.parse_sfx)
        self.assertEqual(counters, {"sound effect unknown": 0, "sound effect unlicensed": 0})
        audio.use(vdir, aid, "whoosh-1", "0", "0.2")
        self.assertEqual((vdir / "04_scene" / "assets" / "sound.md").read_text(), sound_md, "the line is written once")
        music = audio.use(vdir, audio.find("rainy")[0]["id"], "rain")
        self.assertIn("music: file:music-rain.wav 0.2", music[1])
        self.assertIn("audio:", (vdir / "04_scene" / "assets" / "library.md").read_text())


if __name__ == "__main__":
    unittest.main()
