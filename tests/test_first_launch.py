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

    def test_run_waits_for_window_opened_in_current_language(self):
        # 窓（Tk）は作らずに、窓を今の言語で開き、閉じるまで待って結果を返すことを確かめる。
        for language in ("ja", "en"):
            expected = WelcomeResult(language, estimate_layout_id(language), "sample")
            opened = []

            class FakeWindow:
                def __init__(self, app, *, language):
                    opened.append((app, language))
                    self.result = expected

            class FakeApp:
                def __init__(self):
                    self.waited = []

                def wait_window(self, window):
                    self.waited.append(window)

            app = FakeApp()
            with self.subTest(language=language), patch(
                "keyseq.presentation.welcome.first_launch.current_language", return_value=language,
            ), patch("keyseq.presentation.welcome.first_launch.WelcomeWindow", FakeWindow):
                result = run_first_launch_welcome(app)
                self.assertEqual(opened, [(app, language)])
                self.assertEqual(len(app.waited), 1)
                self.assertIs(result, expected)
                with self.assertRaises(FrozenInstanceError):
                    result.start = "empty"
