import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import patch

from keyseq.presentation.config_paths import ConfigPaths
from keyseq.presentation.welcome import (
    WelcomeResult, estimate_layout_id, is_first_launch, run_first_launch_welcome,
)


class FirstLaunchTest(unittest.TestCase):
    def test_estimate_layout_id(self):
        for language, expected in (("ja", "jis"), ("en", "us_tkl"), ("fr", "us_tkl")):
            with self.subTest(language=language):
                self.assertEqual(estimate_layout_id(language), expected)

    def test_first_launch_requires_both_startup_paths_to_be_absent(self):
        for existing in (None, "config/config.json", "settings/startup.json"):
            with self.subTest(existing=existing), tempfile.TemporaryDirectory() as root:
                paths = ConfigPaths(
                    base_dir=root, config_root=str(Path(root) / "config"),
                    user_root=str(Path(root) / "config/user"), config_service=None,
                )
                if existing is not None:
                    target = Path(root) / existing
                    target.parent.mkdir(parents=True)
                    target.touch()
                self.assertEqual(is_first_launch(paths), existing is None)

    def test_default_result_uses_current_language_without_a_window(self):
        for language in ("ja", "en"):
            with self.subTest(language=language), patch(
                "keyseq.presentation.welcome.first_launch.current_language", return_value=language,
            ):
                result = run_first_launch_welcome(object())
                self.assertEqual(result, WelcomeResult(language, estimate_layout_id(language), "sample"))
                with self.assertRaises(FrozenInstanceError):
                    result.start = "empty"
