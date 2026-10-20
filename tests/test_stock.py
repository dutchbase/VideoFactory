import json, os, sys, tempfile, unittest, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import libcore as L
import stock as S

PEXELS_VIDEO = {"videos": [{"id": 11, "width": 3840, "height": 2160, "duration": 9, "url": "https://pexels.com/video/11",
    "image": "https://img/11.jpg", "user": {"name": "Ann"},
    "video_files": [{"width": 3840, "height": 2160, "link": "https://v/4k.mp4", "file_type": "video/mp4"},
                    {"width": 1280, "height": 720, "link": "https://v/hd.mp4", "file_type": "video/mp4"},
                    {"width": 640, "height": 360, "link": "https://v/sd.mp4", "file_type": "video/mp4"}]}]}
PEXELS_PHOTO = {"photos": [{"id": 22, "width": 4000, "height": 3000, "url": "https://pexels.com/photo/22", "photographer": "Bob",
    "alt": "desk", "src": {"large2x": "https://p/22.jpg", "tiny": "https://p/22t.jpg"}}]}
PIXABAY_VIDEO = {"hits": [
    {"id": 33, "pageURL": "https://pixabay.com/v/33", "duration": 7, "user": "Cy",
     "videos": {"large": {"url": "https://x/l.mp4", "width": 1920, "height": 1080, "thumbnail": "https://x/t.jpg"},
                "tiny": {"url": "https://x/t.mp4", "width": 480, "height": 270, "thumbnail": "https://x/t.jpg"}}},
    {"id": 34, "pageURL": "https://pixabay.com/v/34", "duration": 5, "user": "Di",
     "videos": {"large": {"url": "https://x/p.mp4", "width": 1080, "height": 1920, "thumbnail": "https://x/t.jpg"}}}]}
PIXABAY_PHOTO = {"hits": [{"id": 44, "pageURL": "https://pixabay.com/p/44", "user": "Ed", "tags": "office",
    "imageWidth": 5000, "imageHeight": 3000, "largeImageURL": "https://x/44l.jpg", "fullHDURL": "https://x/44f.jpg",
    "previewURL": "https://x/44p.jpg"}]}
UNSPLASH = {"results": [{"id": "ab", "width": 4000, "height": 6000, "alt_description": "a cafe", "user": {"name": "Flo"},
    "links": {"html": "https://unsplash.com/photos/ab", "download_location": "https://api.unsplash.com/photos/ab/download"},
    "urls": {"raw": "https://images.unsplash.com/ab?ixid=1", "thumb": "https://images.unsplash.com/ab?w=200"}}]}


def fake(routes, calls=None, fail=None):
    def fetch(url, headers):
        if calls is not None:
            calls.append(url)
        if fail:
            raise fail
        for part, body in routes.items():
            if part in url:
                return body if isinstance(body, bytes) else json.dumps(body).encode()
        raise AssertionError(f"unexpected url {url}")
    return fetch


class Stock(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        S.CACHE = Path(self.tmp.name)
        for k in ("PEXELS_API_KEY", "PIXABAY_API_KEY", "UNSPLASH_ACCESS_KEY"):
            os.environ[k] = "k"

    def tearDown(self):
        self.tmp.cleanup()
        for k in ("PEXELS_API_KEY", "PIXABAY_API_KEY", "UNSPLASH_ACCESS_KEY"):
            os.environ.pop(k, None)

    KEYS = {"ref", "provider", "kind", "id", "title", "width", "height", "duration", "thumb", "page_url", "author", "download_url", "license"}

    def test_pexels_video_normalized_and_hd_chosen(self):
        r = S.search("pexels", "desk", "video", fetch=fake({"/videos/search": PEXELS_VIDEO}))
        self.assertEqual(set(r[0]), self.KEYS)
        self.assertEqual(r[0]["ref"], "stock:pexels/video/11")
        self.assertEqual(r[0]["download_url"], "https://v/hd.mp4")
        self.assertEqual(r[0]["license"], "Pexels")

    def test_pexels_photo(self):
        r = S.search("pexels", "desk", "photo", fetch=fake({"/v1/search": PEXELS_PHOTO}))
        self.assertEqual((r[0]["ref"], r[0]["download_url"], r[0]["author"]), ("stock:pexels/photo/22", "https://p/22.jpg", "Bob"))

    def test_pixabay_video_orientation_filtered_by_size(self):
        f = fake({"/api/videos/": PIXABAY_VIDEO})
        land = S.search("pixabay", "x", "video", "landscape", fetch=f)
        port = S.search("pixabay", "x", "video", "portrait", fetch=f)
        self.assertEqual([i["id"] for i in land], ["33"])
        self.assertEqual([i["id"] for i in port], ["34"])

    def test_pixabay_photo_prefers_fullhd(self):
        r = S.search("pixabay", "x", "photo", fetch=fake({"/api/": PIXABAY_PHOTO}))
        self.assertEqual(r[0]["download_url"], "https://x/44f.jpg")
        self.assertEqual(set(r[0]), self.KEYS)

    def test_unsplash_photo(self):
        r = S.search("unsplash", "cafe", "photo", "portrait", fetch=fake({"/search/photos": UNSPLASH}))
        self.assertEqual(r[0]["ref"], "stock:unsplash/photo/ab")
        self.assertIn("w=2400", r[0]["download_url"])
        self.assertTrue(self.KEYS <= set(r[0]))

    def test_unsplash_video_is_an_error(self):
        with self.assertRaises(ValueError):
            S.search("unsplash", "x", "video", fetch=fake({}))

    def test_missing_key_names_variable(self):
        del os.environ["PEXELS_API_KEY"]
        with self.assertRaises(L.KeyMissing) as c:
            S.search("pexels", "x", "video", fetch=fake({}), env_file=Path("/nonexistent"))
        self.assertIn("PEXELS_API_KEY", str(c.exception))

    def test_rate_limit_message(self):
        import urllib.error
        err = urllib.error.HTTPError("u", 429, "x", {}, None)
        with self.assertRaises(L.NetError) as c:
            S.search("pexels", "x", "video", fetch=fake({}, fail=err))
        self.assertIn("rate limit", str(c.exception))

    def test_search_is_cached(self):
        calls = []
        f = fake({"/videos/search": PEXELS_VIDEO}, calls)
        S.search("pexels", "desk", "video", fetch=f)
        S.search("pexels", "desk", "video", fetch=f)
        self.assertEqual(len(calls), 1)

    def test_pick_video_file(self):
        mk = lambda w: {"width": w, "height": w * 9 // 16, "url": f"u{w}"}
        self.assertEqual(S.pick_video_file([mk(3840), mk(1280), mk(640)])["width"], 1280)
        self.assertEqual(S.pick_video_file([mk(3840), mk(640)])["width"], 640)
        self.assertEqual(S.pick_video_file([mk(3840), mk(2560)])["width"], 2560)
        self.assertEqual(S.pick_video_file([mk(1920), mk(1080)])["width"], 1080)

    def test_download_once_and_sidecar(self):
        calls = []
        item = S.search("pexels", "desk", "video", fetch=fake({"/videos/search": PEXELS_VIDEO}))[0]
        f = fake({"hd.mp4": b"VIDEO"}, calls)
        p = S.download(item, fetch=f)
        self.assertEqual(p.read_bytes(), b"VIDEO")
        self.assertEqual(json.loads(p.with_suffix(".json").read_text())["id"], "11")
        S.download(item, fetch=f)
        self.assertEqual(len(calls), 1)

    def test_unsplash_download_tracks(self):
        calls = []
        item = S.search("unsplash", "cafe", "photo", fetch=fake({"/search/photos": UNSPLASH}))[0]
        S.download(item, fetch=fake({"/download": {"url": "x"}, "images.unsplash.com": b"JPG"}, calls))
        self.assertTrue(any(c.endswith("/photos/ab/download") for c in calls))

    def test_failed_download_leaves_nothing(self):
        item = S.search("pexels", "desk", "video", fetch=fake({"/videos/search": PEXELS_VIDEO}))[0]
        with self.assertRaises(L.NetError):
            S.download(item, fetch=fake({}, fail=urllib.error.URLError("down")))
        self.assertEqual(list(S.CACHE.glob("stock/**/11.*")), [])

    def test_item_from_ref_reads_sidecar(self):
        item = S.search("pexels", "desk", "video", fetch=fake({"/videos/search": PEXELS_VIDEO}))[0]
        S.download(item, fetch=fake({"hd.mp4": b"V"}))
        self.assertEqual(S.load_item("stock:pexels/video/11")["author"], "Ann")
        with self.assertRaises(ValueError):
            S.load_item("stock:pexels/video/../x")



class StockIds(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old, S.CACHE = S.CACHE, Path(self.tmp.name)
        self.addCleanup(setattr, S, "CACHE", self.old)

    def test_case_sensitive_and_dash_ids_round_trip(self):
        for pid in ("tNbk1kTlSY8", "-uv6f6mKFbg"):
            item = {"provider": "unsplash", "kind": "photo", "id": pid}
            found = S.CACHE / "found"
            found.mkdir(exist_ok=True)
            (found / f"unsplash-photo-{S._stem(pid)}.json").write_text(json.dumps(item))
            self.assertEqual(S.load_item(f"stock:unsplash/photo/{pid}")["id"], pid)
        self.assertEqual(S._stem("-ab"), "_-ab")
        for bad in ("../x", "a/b", ""):
            with self.assertRaises(ValueError):
                S._stem(bad)


if __name__ == "__main__":
    unittest.main()
