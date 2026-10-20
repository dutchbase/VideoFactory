import shutil
import tempfile
import unittest
from pathlib import Path

from studio.workspace import (
    WorkspaceError,
    create_style,
    import_existing_styles,
    list_style_families,
    list_styles,
    read_file,
    save_style,
)


ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {"modern"}


def isolated_catalog(root: Path) -> None:
    shutil.copytree(ROOT / "styles/_families", root / "styles/_families")


def legacy_modern(root: Path, review: str | None = None) -> Path:
    folder = root / "styles/modern"
    folder.mkdir(parents=True)
    style = folder / "style.md"
    style.write_text('---\nid: "modern"\ntitle: "My Modern"\nbase_kit: "modern"\n---\n\nUser-authored recipe.\n', encoding="utf-8")
    if review is not None:
        (folder / "REVIEW.md").write_text(review, encoding="utf-8")
    return style


class CreativeCatalogTests(unittest.TestCase):
    def test_families_point_to_existing_sources(self):
        families = list_style_families(ROOT)
        self.assertEqual({family["id"] for family in families}, FAMILIES)
        for family in families:
            self.assertEqual(family["default_variant"], family["id"])
            self.assertTrue(family["references"])
            for reference in family["references"]:
                self.assertTrue((ROOT / reference).is_file(), reference)
            for slug in family["reference_videos"]:
                self.assertTrue((ROOT / "videos" / slug / "04_scene/index.html").is_file(), slug)

        by_id = {family["id"]: family for family in families}
        self.assertIn("_runtime/modern.css", by_id["modern"]["references"])
        self.assertEqual(by_id["modern"]["reference_videos"], [])

    def test_import_is_idempotent_and_records_review_state_without_sample(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            isolated_catalog(root)

            imported = import_existing_styles(root)
            self.assertEqual({style["id"] for style in imported}, FAMILIES)
            self.assertEqual({style["origin"] for style in imported}, {"existing-reference"})
            self.assertEqual({style["readiness"] for style in imported}, {"needs-review"})
            modern = next(style for style in imported if style["id"] == "modern")
            self.assertEqual(modern["renderer"], "modern")
            self.assertFalse(modern["template_ready"])
            self.assertIsNone(modern["sample"])

            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in (root / "styles").rglob("*") if path.is_file()
            }
            again = import_existing_styles(root)
            after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in (root / "styles").rglob("*") if path.is_file()
            }
            self.assertEqual({style["id"] for style in again}, FAMILIES)
            self.assertEqual(after, before)

    def test_import_preserves_user_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            isolated_catalog(root)
            import_existing_styles(root)

            style = root / "styles/modern/style.md"
            materials = root / "styles/modern/materials.md"
            review = root / "styles/modern/REVIEW.md"
            style.write_text(style.read_text(encoding="utf-8") + "\nUser note.\n", encoding="utf-8")
            materials.write_text("user materials\n", encoding="utf-8")
            review.write_text("Review in progress\n", encoding="utf-8")
            user_files = {path: path.read_bytes() for path in (style, materials, review)}

            import_existing_styles(root)

            self.assertEqual({path: path.read_bytes() for path in user_files}, user_files)

    def test_default_variant_name_does_not_assign_imported_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            isolated_catalog(root)
            style_path = legacy_modern(root, "Review in progress\n")
            review_path = style_path.parent / "REVIEW.md"
            user_files = {style_path: style_path.read_bytes(), review_path: review_path.read_bytes()}

            listed = next(style for style in list_styles(root) if style["id"] == "modern")
            self.assertIsNone(listed["family_id"])
            self.assertEqual(listed["origin"], "legacy")
            self.assertEqual(listed["references"], [])
            self.assertEqual(listed["reference_videos"], [])
            self.assertEqual(listed["readiness"], "draft")

            import_existing_styles(root)

            self.assertEqual({path: path.read_bytes() for path in user_files}, user_files)
            listed = next(style for style in list_styles(root) if style["id"] == "modern")
            self.assertIsNone(listed["family_id"])
            self.assertEqual(listed["origin"], "legacy")
            self.assertEqual(listed["references"], [])
            self.assertEqual(listed["reference_videos"], [])
            self.assertEqual(listed["readiness"], "draft")

    def test_import_does_not_create_review_note_for_existing_style(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            isolated_catalog(root)
            style_path = legacy_modern(root)
            review_path = style_path.parent / "REVIEW.md"
            user_style = style_path.read_bytes()

            import_existing_styles(root)

            self.assertEqual(style_path.read_bytes(), user_style)
            self.assertFalse(review_path.exists())

    def test_legacy_and_new_style_metadata_are_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            legacy = root / "styles/legacy/style.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text(
                '---\nid: "legacy"\ntitle: "Legacy"\nbase_kit: "modern"\n---\n\nOld recipe.\n',
                encoding="utf-8",
            )
            (legacy.parent / "materials.md").write_text("# Materials\n", encoding="utf-8")
            listed = {style["id"]: style for style in list_styles(root)}
            self.assertEqual(listed["legacy"]["base_kit"], "modern")
            self.assertIsNone(listed["legacy"]["family_id"])
            self.assertEqual(listed["legacy"]["supported_formats"], [])
            self.assertEqual(listed["legacy"]["renderer"], "modern")
            self.assertEqual(listed["legacy"]["origin"], "legacy")
            self.assertEqual(listed["legacy"]["reference_videos"], [])
            self.assertEqual(listed["legacy"]["references"], [])
            self.assertEqual(listed["legacy"]["readiness"], "draft")

            for family_id in ("modern",):
                style = create_style(
                    root,
                    f"custom-{family_id}",
                    f"Custom {family_id}",
                    "modern",
                    family_id=family_id,
                    renderer=family_id,
                    supported_formats=["wide"],
                    origin="user-authored",
                    reference_videos=[],
                    references=["_shared/modern.md"],
                    readiness="draft",
                )
                self.assertEqual(style["family_id"], family_id)
                content = read_file(root, style["path"])
                updated = content["text"].replace(f"Custom {family_id}", f"Updated {family_id}")
                saved = save_style(root, style["id"], updated, content["revision"])
                self.assertEqual(saved["title"], f"Updated {family_id}")
                self.assertEqual(saved["renderer"], family_id)

            with self.assertRaises(WorkspaceError):
                create_style(root, "old-kit", "Old kit", "unknown-kit")

            with self.assertRaises(WorkspaceError):
                create_style(root, "unsafe", "Unsafe", references=["_auth/session.json"])


if __name__ == "__main__":
    unittest.main()
