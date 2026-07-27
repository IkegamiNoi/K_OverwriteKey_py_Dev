"""App 起動時の設定ディレクトリ骨格作成を固定する。"""
import unittest
from unittest.mock import patch

from keyseq.presentation import app as app_module


class StartupDirSkeletonTest(unittest.TestCase):
    def setUp(self):
        self._ensure_dirs_patch = patch.object(
            app_module.ConfigService,
            "ensure_split_config_dirs",
        )
        self._load_startup_patch = patch.object(
            app_module.ConfigService,
            "load_startup",
            return_value={},
        )
        self._save_json_patch = patch.object(app_module.JsonRepository, "save_json")
        self._ensure_dirs = self._ensure_dirs_patch.start()
        self._load_startup_patch.start()
        self._save_json = self._save_json_patch.start()
        self.app = app_module.App()
        self.app.update_idletasks()

    def tearDown(self):
        self.app.destroy()
        self._save_json_patch.stop()
        self._load_startup_patch.stop()
        self._ensure_dirs_patch.stop()

    def test_startup_creates_split_config_directories(self):
        self._ensure_dirs.assert_called_once_with(self.app.config_root)

    def test_startup_does_not_persist_anything(self):
        """起動時は config.json を含め一切保存しない（作成は初回保存時。暫定仕様 04 §2）。

        保存全般を対象にした意図的な広い固定。起動時に永続化が増えたらそれ自体が
        仕様変更であり、本テストが落ちるのが正しい。
        """
        self._save_json.assert_not_called()


if __name__ == "__main__":
    unittest.main()
