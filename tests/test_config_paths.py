import os
import tempfile
import unittest

from keyseq.application.config_service import ConfigService
from keyseq.infrastructure.json_repository import JsonRepository
from keyseq.presentation.config_paths import ConfigPaths


class ConfigPathsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = self.tmp.name
        self.base_dir = base
        self.config_root = os.path.join(base, "config")
        self.user_root = os.path.join(self.config_root, "user")
        os.makedirs(self.user_root, exist_ok=True)
        self.paths = ConfigPaths(
            base_dir=self.base_dir,
            config_root=self.config_root,
            user_root=self.user_root,
            config_service=ConfigService(JsonRepository()),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_preferred_paths(self):
        self.assertEqual(
            self.paths.preferred_keymap_set_path(),
            os.path.join(self.config_root, "user", "keymap_sets", "default.json"),
        )
        self.assertEqual(
            self.paths.preferred_startup_path(),
            os.path.join(self.config_root, "config.json"),
        )

    def test_normalize_keymap_set_save_path(self):
        # 空 → デフォルト
        self.assertEqual(
            self.paths.normalize_keymap_set_save_path(""),
            self.paths.preferred_keymap_set_path(),
        )
        # "config/" 始まりの相対 → base_dir 基準
        self.assertEqual(
            self.paths.normalize_keymap_set_save_path("config/user/keymap_sets/a.json"),
            os.path.normpath(os.path.join(self.base_dir, "config", "user", "keymap_sets", "a.json")),
        )
        # その他の相対 → config_root 基準
        self.assertEqual(
            self.paths.normalize_keymap_set_save_path("user/keymap_sets/a.json"),
            os.path.normpath(os.path.join(self.config_root, "user", "keymap_sets", "a.json")),
        )
        # レガシー settings/ 配下 → デフォルトへ矯正
        legacy = os.path.join(self.base_dir, "settings", "config.json")
        self.assertEqual(
            self.paths.normalize_keymap_set_save_path(legacy),
            self.paths.preferred_keymap_set_path(),
        )

    def test_resolve_startup_path_prefers_new_location(self):
        new_path = os.path.join(self.config_root, "config.json")
        # 新ファイルが無い → レガシー位置を返す
        self.assertEqual(
            self.paths.resolve_startup_path(),
            os.path.join(self.base_dir, "settings", "startup.json"),
        )
        with open(new_path, "w", encoding="utf-8") as f:
            f.write("{}")
        self.assertEqual(self.paths.resolve_startup_path(), new_path)

    def test_suggest_dialog_dir_falls_back(self):
        # keymap_sets ディレクトリが無い場合は config_root
        self.assertEqual(
            self.paths.suggest_keymap_set_dialog_dir(""),
            self.config_root,
        )

    def test_suggest_dialog_dir_uses_preferred_keymap_sets_dir_when_present(self):
        os.makedirs(self.paths.preferred_keymap_sets_dir())
        self.assertEqual(
            self.paths.suggest_keymap_set_dialog_dir(""),
            self.paths.preferred_keymap_sets_dir(),
        )


if __name__ == "__main__":
    unittest.main()
