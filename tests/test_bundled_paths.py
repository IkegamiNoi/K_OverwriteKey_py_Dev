import unittest
from pathlib import Path
from unittest.mock import patch

from keyseq.presentation.bundled_paths import bundled_keylayout_dir, bundled_root


class BundledPathsTests(unittest.TestCase):
    def test_frozen_root_uses_meipass(self):
        with patch("keyseq.presentation.bundled_paths.sys.frozen", True, create=True), \
                patch("keyseq.presentation.bundled_paths.sys._MEIPASS", "C:/bundle", create=True):
            self.assertEqual(bundled_root(), Path("C:/bundle"))
            self.assertEqual(bundled_keylayout_dir(), Path("C:/bundle/config/user/keylayout"))

    def test_development_keylayout_is_in_repository_bundle_root(self):
        with patch("keyseq.presentation.bundled_paths.sys.frozen", False, create=True):
            self.assertEqual(bundled_keylayout_dir(), bundled_root() / "config" / "user" / "keylayout")


if __name__ == "__main__":
    unittest.main()
