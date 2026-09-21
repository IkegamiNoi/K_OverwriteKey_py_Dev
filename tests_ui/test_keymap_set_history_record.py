"""構成セット履歴の presentation 呼び出し契約を固定する。"""

import json
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import Mock, call, patch

from keyseq.application.config_service import ConfigService
from keyseq.application.save_plan import SavePlan
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import keymap_set_io, startup_io
from keyseq.presentation.controllers.config_io.keymap_set_history_io import KeymapSetHistoryIo


class KeymapSetHistoryRecordTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = Mock()
        self.app.config_root = "config-root"
        self.app.user_root = "user-root"
        self.app.base_dir = "base-dir"
        self.app.keymap_set_path = ""
        self.app._startup_settings = {}
        self.app.data = {"keymaps": [], "triggers": []}
        self.app.config_service = ConfigService(Mock())
        self.io = keymap_set_io.KeymapSetIo(self.app)
        self.app.keymap_set_io = self.io
        self.app.startup_io = startup_io.StartupIo(self.app)
        self.app.keymap_set_history_io = KeymapSetHistoryIo(self.app)
        self.record = self._patch(
            ConfigService, "record_keymap_set_history", return_value=(True, ""),
        )
        self.load = self._patch(
            self.app.config_service, "load_runtime_data_from_keymap_set_path",
            return_value=self.app.data,
        )
        self.apply_ui = self._patch(self.io, "apply_loaded_data_to_ui")
        self.confirm = self._patch(self.io, "confirm_save_if_dirty", return_value=True)
        self.select = self._patch(
            keymap_set_io.filedialog, "askopenfilename", return_value="selected.json",
        )
        self.info = self._patch(keymap_set_io.messagebox, "showinfo")
        self.error = self._patch(keymap_set_io.messagebox, "showerror")
        self.events = Mock()
        self.events.attach_mock(self.app._set_flash_message, "flash")
        self.events.attach_mock(self.info, "info")
        self.events.attach_mock(self.record, "record")

    def _patch(self, target: Any, name: str, **kwargs: Any) -> Any:
        patcher = patch.object(target, name, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def _assert_recorded(self, path: str) -> None:
        self.record.assert_called_once_with(path, config_root=self.app.config_root)

    def test_menu_load_preserves_order_and_messages(self) -> None:
        self.events.attach_mock(self.confirm, "confirm")
        self.events.attach_mock(self.select, "select")
        self.events.attach_mock(self.load, "load")
        self.assertIsNone(self.io.load_keymap_set_from())
        self.assertEqual(self.events.mock_calls, [
            call.confirm("読込"),
            call.select(
                title="keymap_set.json を読込",
                initialdir=self.app.suggest_keymap_set_dialog_dir(),
                filetypes=[("JSON", "*.json"), ("All", "*.*")],
            ),
            call.load("selected.json", config_root="config-root"),
            call.flash("読み込みました。"),
            call.info("読込", "読み込みました:\nselected.json"),
            call.record("selected.json", config_root="config-root"),
        ])
        self._assert_recorded("selected.json")
        self.app.dirty_tracker.set_dirty.assert_called_once_with(False)

    def test_path_load_returns_ok_without_confirmation(self) -> None:
        self.assertEqual(
            self.io.load_keymap_set_path("direct.json"), keymap_set_io.KEYMAP_SET_LOAD_OK,
        )
        self._assert_recorded("direct.json")
        self.confirm.assert_not_called()
        self.select.assert_not_called()
        self.assertEqual(self.app.keymap_set_path, "direct.json")

    def test_path_load_failure_returns_failed_without_record(self) -> None:
        self.load.side_effect = ValueError("壊れたJSON")
        self.assertEqual(
            self.io.load_keymap_set_path("bad.json"), keymap_set_io.KEYMAP_SET_LOAD_FAILED,
        )
        self.record.assert_not_called()
        self.app._set_flash_message.assert_called_once_with(
            "読込失敗: 壊れたJSON", auto_clear=False,
        )
        self.error.assert_called_once_with("読込失敗", "壊れたJSON")
        self.info.assert_not_called()

    def test_menu_load_failure_preserves_messages(self) -> None:
        self.load.side_effect = ValueError("読めません")
        self.assertIsNone(self.io.load_keymap_set_from())
        self.record.assert_not_called()
        self.app._set_flash_message.assert_called_once_with(
            "読込失敗: 読めません", auto_clear=False,
        )
        self.error.assert_called_once_with("読込失敗", "読めません")

    def test_load_history_failure_follows_success_notifications(self) -> None:
        self.record.return_value = (False, "理由")
        self.assertEqual(
            self.io.load_keymap_set_path("direct.json"), keymap_set_io.KEYMAP_SET_LOAD_OK,
        )
        self.assertEqual(self.events.mock_calls, [
            call.flash("読み込みました。"),
            call.info("読込", "読み込みました:\ndirect.json"),
            call.record("direct.json", config_root="config-root"),
            call.flash("理由", auto_clear=False),
        ])
        self.error.assert_not_called()

    def test_menu_load_confirmation_cancel_does_not_select_or_record(self) -> None:
        self.confirm.return_value = False
        self.io.load_keymap_set_from()
        self.select.assert_not_called()
        self.load.assert_not_called()
        self.record.assert_not_called()

    def test_menu_load_file_selection_cancel_does_not_record(self) -> None:
        self.select.return_value = ""
        self.io.load_keymap_set_from()
        self.load.assert_not_called()
        self.record.assert_not_called()

    def test_startup_selection_records_without_history_failure_notice(self) -> None:
        self.record.return_value = (False, "理由")
        write = self._patch(self.app.startup_io, "write_startup", return_value=True)
        self.io.set_startup_keymap_set()
        self._assert_recorded("selected.json")
        write.assert_called_once()
        self.app._set_flash_message.assert_called_once_with("起動時読み込み設定を更新しました。")
        self.info.assert_called_once_with(
            "設定", "次回起動時はこの keymap_set を読み込みます:\nselected.json",
        )

    def test_startup_settings_save_failure_keeps_existing_notice(self) -> None:
        self.record.return_value = (False, "理由")
        self._patch(self.app.startup_io, "write_startup", return_value=False)
        self.io.set_startup_keymap_set()
        self._assert_recorded("selected.json")
        self.app._set_flash_message.assert_called_once_with(
            "起動時読み込み設定の保存に失敗しました。", auto_clear=False,
        )
        self.info.assert_not_called()

    def _prepare_startup(self, *, exists: bool) -> None:
        self.app._startup_settings = {"keymap_set_path": "stored.json"}
        self.app.paths.resolve_keymap_set_path.return_value = "resolved.json"
        self._patch(startup_io.os.path, "exists", return_value=exists)
        self.empty = self._patch(
            self.app.config_service, "new_empty_data", return_value={"triggers": []},
        )
        self._patch(self.app.config_service, "apply_global_defaults")

    def test_automatic_startup_success_does_not_record(self) -> None:
        self._prepare_startup(exists=True)
        loaded_data = self.load.return_value
        self.app.startup_io.load_startup_and_config()
        self.record.assert_not_called()
        self.assertIs(self.app.data, loaded_data)
        self.assertTrue(self.app.startup_io.entry_loaded)
        self.assertEqual(self.app.keymap_set_path, "resolved.json")
        self.empty.assert_not_called()
        self.app._set_flash_message.assert_not_called()
        self.info.assert_not_called()
        self.error.assert_not_called()

    def test_app_creation_does_not_record_history(self) -> None:
        startup_path = str(Path(__file__).resolve())
        self._patch(ConfigService, "ensure_split_config_dirs")
        self._patch(
            ConfigService, "load_startup", return_value={"keymap_set_path": startup_path},
        )
        load = self._patch(
            ConfigService, "load_runtime_data_from_keymap_set_path",
            return_value=self.app.config_service.new_default_data(),
        )
        app = app_module.App()
        try:
            app.update_idletasks()
            load.assert_called_once_with(startup_path, config_root=app.config_root)
            self.assertTrue(app.startup_io.entry_loaded)
            self.assertEqual(app.keymap_set_path, startup_path)
            self.record.assert_not_called()
        finally:
            try:
                app.update()
            finally:
                app.destroy()

    def test_automatic_startup_missing_file_does_not_record(self) -> None:
        self._prepare_startup(exists=False)
        self.app.startup_io.load_startup_and_config()
        self.load.assert_not_called()
        self._assert_empty_startup()

    def test_automatic_startup_broken_json_does_not_record(self) -> None:
        self._prepare_startup(exists=True)
        self.load.side_effect = json.JSONDecodeError("broken", "{", 1)
        self.app.startup_io.load_startup_and_config()
        self._assert_empty_startup()

    def _assert_empty_startup(self) -> None:
        self.record.assert_not_called()
        self.empty.assert_called_once_with()
        self.assertEqual(self.app.data, {"triggers": []})
        self.assertFalse(self.app.startup_io.entry_loaded)
        self.assertEqual(self.app.keymap_set_path, "")
        self.app._set_flash_message.assert_not_called()
        self.error.assert_not_called()

    def _prepare_save(self) -> None:
        self.app.paths.normalize_keymap_set_save_path.return_value = "normalized.json"
        self._patch(self.io, "choose_split_base_dir_for_keymap_set", return_value="split")
        self._patch(
            self.io, "_collect_child_save_plan", return_value=(SavePlan(), "", False),
        )
        self._patch(self.io, "_skipped_dirty_children", return_value=([], [], False))
        self._patch(self.io, "_clear_saved_child_dirty_flags")
        self._patch(
            self.app.config_service, "relocate_individual_hotkey_presets", return_value="",
        )
        self.save = self._patch(
            self.app.config_service, "save_runtime_data", return_value=(self.app.data, {}),
        )
        self._patch(
            keymap_set_io.filedialog, "asksaveasfilename", return_value="raw.json",
        )
        self.app.suggest_keymap_set_dialog_path.return_value = "suggested.json"

    def test_save_as_records_normalized_destination(self) -> None:
        self._prepare_save()
        self.assertTrue(self.io.save_as())
        self._assert_recorded("normalized.json")
        self.assertEqual(self.app.keymap_set_path, "normalized.json")
        self.assertEqual(self.events.mock_calls, [
            call.flash("別名で保存しました。"),
            call.info("保存", "保存しました:\nnormalized.json"),
            call.record("normalized.json", config_root="config-root"),
        ])

    def test_overwrite_records_normalized_destination(self) -> None:
        self._prepare_save()
        self.app.keymap_set_path = "raw.json"
        self.assertTrue(self.io.save_keymap_set())
        self.app.paths.normalize_keymap_set_save_path.assert_called_once_with("raw.json")
        self._assert_recorded("normalized.json")

    def test_save_history_failure_follows_success_notifications(self) -> None:
        self._prepare_save()
        self.record.return_value = (False, "理由")
        self.assertTrue(self.io.save_as())
        self.assertEqual(self.events.mock_calls, [
            call.flash("別名で保存しました。"),
            call.info("保存", "保存しました:\nnormalized.json"),
            call.record("normalized.json", config_root="config-root"),
            call.flash("理由", auto_clear=False),
        ])
        self.error.assert_not_called()

    def test_save_failure_does_not_record(self) -> None:
        self._prepare_save()
        self.save.side_effect = OSError("保存不可")
        self.assertFalse(self.io.save_as())
        self.record.assert_not_called()

    def test_save_history_exception_does_not_report_save_failure(self) -> None:
        self._prepare_save()
        self.record.side_effect = RuntimeError("履歴例外")
        self.assertTrue(self.io.save_as())
        self._assert_recorded("normalized.json")
        self.assertEqual(self.app.keymap_set_path, "normalized.json")
        self.assertEqual(self.events.mock_calls, [
            call.flash("別名で保存しました。"),
            call.info("保存", "保存しました:\nnormalized.json"),
            call.record("normalized.json", config_root="config-root"),
            call.flash("構成セットの履歴を記録できませんでした: 履歴例外", auto_clear=False),
        ])
        self.error.assert_not_called()

    def test_load_history_exception_does_not_report_load_failure(self) -> None:
        loaded_data = self.load.return_value
        self.record.side_effect = RuntimeError("履歴例外")
        self.assertEqual(
            self.io.load_keymap_set_path("direct.json"), keymap_set_io.KEYMAP_SET_LOAD_OK,
        )
        self._assert_recorded("direct.json")
        self.assertIs(self.app.data, loaded_data)
        self.assertEqual(self.app.keymap_set_path, "direct.json")
        self.assertEqual(self.events.mock_calls, [
            call.flash("読み込みました。"),
            call.info("読込", "読み込みました:\ndirect.json"),
            call.record("direct.json", config_root="config-root"),
            call.flash("構成セットの履歴を記録できませんでした: 履歴例外", auto_clear=False),
        ])
        self.error.assert_not_called()

    def test_new_config_does_not_record(self) -> None:
        self._patch(self.app.config_service, "apply_global_defaults")
        self.io.new_config()
        self.record.assert_not_called()
        self.assertEqual(self.app.keymap_set_path, "")

    def test_import_config_does_not_record(self) -> None:
        self._patch(
            self.app.config_service, "load_legacy_runtime_data", return_value=self.app.data,
        )
        self._patch(self.app.config_service, "clear_individual_hotkey_presets")
        self._patch(self.app.config_service, "apply_global_defaults")
        self.io.import_config()
        self.record.assert_not_called()
        self.info.assert_called_once_with("Import", "単一JSONを取り込みました:\nselected.json")
        self.error.assert_not_called()

    def test_restore_default_does_not_record(self) -> None:
        self._patch(keymap_set_io.messagebox, "askyesno", return_value=True)
        self._patch(self.app.config_service, "apply_global_defaults")
        self.io.restore_default()
        self.record.assert_not_called()
        self.assertEqual(self.app.keymap_set_path, "")


if __name__ == "__main__":
    unittest.main()
