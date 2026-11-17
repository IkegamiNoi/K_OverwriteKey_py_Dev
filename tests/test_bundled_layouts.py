import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from keyseq.infrastructure.bundled_layouts import install_bundled_layouts


class BundledLayoutsTests(unittest.TestCase):
    def test_copies_only_when_destination_is_missing(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            source = base / "source"
            source.mkdir()
            (source / "one.json").write_text("one")
            user_root = base / "new" / "user"
            self.assertTrue(install_bundled_layouts(source, user_root))
            self.assertEqual((user_root / "keylayout" / "one.json").read_text(), "one")
            self.assertFalse(install_bundled_layouts(source, user_root))

    def test_existing_destination_and_missing_source_are_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            source = base / "source"
            source.mkdir()
            destination = base / "user" / "keylayout"
            destination.mkdir(parents=True)
            (destination / "keep.json").write_text("keep")
            self.assertFalse(install_bundled_layouts(source, destination.parent))
            self.assertFalse(install_bundled_layouts(base / "missing", base / "other"))
            self.assertEqual([p.name for p in destination.iterdir()], ["keep.json"])
            self.assertFalse((base / "other").exists())

    def test_copy_error_cleans_destination_and_temporary_directory(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            source = base / "source"
            source.mkdir()
            (source / "one.json").write_text("one")
            (source / "two.json").write_text("two")
            user_root = base / "user"
            copy = __import__("shutil").copy2
            calls = 0

            def fail_second(src, dst):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("copy failed")
                return copy(src, dst)

            with patch("keyseq.infrastructure.bundled_layouts.shutil.copy2", side_effect=fail_second):
                with self.assertRaises(OSError):
                    install_bundled_layouts(source, user_root)
            self.assertFalse((user_root / "keylayout").exists())
            self.assertFalse((user_root / "keylayout.tmp").exists())

    def test_stale_temporary_directory_is_replaced(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            source = base / "source"
            source.mkdir()
            (source / "layout.json").write_text("fresh")
            user_root = base / "user"
            stale = user_root / "keylayout.tmp"
            stale.mkdir(parents=True)
            (stale / "stale.json").write_text("stale")
            self.assertTrue(install_bundled_layouts(source, user_root))
            self.assertEqual([p.name for p in (user_root / "keylayout").iterdir()], ["layout.json"])


if __name__ == "__main__":
    unittest.main()
