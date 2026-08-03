"""App を実際に生成して、ダイアログを出さない範囲の UI 挙動を固定する。

- グローバルフックは一切開始しない（start_hook を呼ばない）
- ファイル保存を伴う操作は行わない（全体デフォルトの確認のみ一時ディレクトリで I/O する）
- GUI が開ける環境（通常のデスクトップセッション）で実行すること
"""
import os
import tempfile
import unittest
from unittest.mock import call, patch

from keyseq.application.save_plan import SavePlan
from keyseq.presentation.app import App


class AppUiFlowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()
        cls.app.update_idletasks()
        # 実環境の構成に依存しないよう、テスト用データへ差し替える
        cls.app.data = cls.app.config_service.normalize_runtime_data(
            {
                "triggers": [
                    {"key": "f1", "label": "one", "actions": [{"type": "text", "value": "a"}]},
                    {"key": "f2", "label": "two", "actions": []},
                ],
                "keymaps": [{"id": "km1", "label": "Main", "mappings": {"a": "b"}}],
                "active_keymap_id": "km1",
            }
        )
        cls.app.state.reset_indices()
        cls.app.trigger_panel.refresh_triggers()
        cls.app.trigger_panel.refresh_actions()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.dirty_tracker.set_dirty(False)
        finally:
            cls.app.destroy()

    def _write_global_hook_key_defaults(self, config_root: str) -> None:
        self.app.config_service.save_startup(
            os.path.join(config_root, "config.json"),
            {"hook_stop_key": "f9", "hook_toggle_key": "f10"},
        )

    def _switch_individual_hook_keys_off(self, stop_key: str = "f5", toggle_key: str = "f6") -> None:
        self.app.data["hook_keys_individual"] = True
        self.app.data["hook_stop_key"] = stop_key
        self.app.data["hook_toggle_key"] = toggle_key
        self.app._sync_control_vars_from_data()
        self.app.ui_vars.hook_keys_individual_var.set(False)
        self.app.toggle_hook_keys_individual()

    def test_trigger_lists_populated(self):
        self.assertEqual(self.app.full_view.trigger_box.trigger_list.size(), 2)
        self.assertEqual(self.app.compact_view.trigger_box.trigger_list.size(), 2)

    def test_selection_updates_status(self):
        self.app.trigger_panel.set_selected_trigger_index(1)
        self.assertIn("選択中: f2", self.app.ui_vars.status_var.get())
        self.app.trigger_panel.set_selected_trigger_index(0)
        self.assertIn("選択中: f1", self.app.ui_vars.status_var.get())

    def test_status_shows_hook_off(self):
        self.app.trigger_panel.update_status()
        self.assertIn("フック: OFF", self.app.ui_vars.status_var.get())

    def test_dirty_flag_reflected_in_file_status(self):
        self.app.dirty_tracker.set_dirty(True)
        self.assertIn("未保存", self.app.ui_vars.file_status_var.get())
        self.app.dirty_tracker.set_dirty(False)
        self.assertIn("保存済み", self.app.ui_vars.file_status_var.get())

    def test_dirty_snapshot_restores_clean_and_dirty_states(self):
        tracker = self.app.dirty_tracker
        tracker.set_dirty(False)
        clean_snapshot = tracker.capture_dirty_snapshot()
        tracker.set_dirty(True)
        tracker.restore_dirty_snapshot(clean_snapshot)
        self.assertFalse(tracker.is_dirty)
        self.assertFalse(tracker.config_dirty)

        tracker.set_dirty(True)
        dirty_snapshot = tracker.capture_dirty_snapshot()
        tracker.set_dirty(False)
        tracker.restore_dirty_snapshot(dirty_snapshot)
        self.assertTrue(tracker.is_dirty)
        self.assertTrue(tracker.config_dirty)
        tracker.set_dirty(False)

    def test_hook_key_capture_and_clear_individual_values_mark_dirty(self):
        capture = self.app.stop_key_capture
        self.app.data["hook_keys_individual"] = True
        self.app.data["hook_stop_key"] = "f3"
        self.app.ui_vars.stop_key_var.set("f3")
        self.app.dirty_tracker.set_dirty(False)

        with patch.object(self.app.startup_io, "write_global_hook_keys") as write_global_hook_keys:
            self.assertTrue(capture._apply_key("f9"))
            self.assertEqual(self.app.data["hook_stop_key"], "f9")
            self.assertEqual(self.app.ui_vars.stop_key_var.get(), "f9")
            self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())
            write_global_hook_keys.assert_not_called()

            self.app.dirty_tracker.set_dirty(False)
            capture.clear()
            self.assertEqual(self.app.data["hook_stop_key"], "")
            self.assertEqual(self.app.ui_vars.stop_key_var.get(), "")
            self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

            self.app.dirty_tracker.set_dirty(False)
            capture.clear()
            self.assertFalse(self.app.dirty_tracker.has_unsaved_changes())
            write_global_hook_keys.assert_not_called()

    def test_hook_key_capture_and_clear_global_defaults_preserve_dirty_state(self):
        stop_capture = self.app.stop_key_capture
        toggle_capture = self.app.toggle_key_capture
        self.app.data["hook_keys_individual"] = False
        self.app.data["hook_stop_key"] = "f3"
        self.app.data["hook_toggle_key"] = "f4"
        self.app.ui_vars.stop_key_var.set("f3")
        self.app.ui_vars.toggle_key_var.set("f4")
        self.app.dirty_tracker.set_dirty(False)

        with patch.object(self.app.startup_io, "write_global_hook_keys", return_value=True) as write_global_hook_keys:
            self.assertTrue(stop_capture._apply_key("f9"))
            self.assertEqual(self.app.data["hook_stop_key"], "f9")
            self.assertEqual(self.app.ui_vars.stop_key_var.get(), "f9")
            self.assertFalse(self.app.dirty_tracker.has_unsaved_changes())

            self.app.dirty_tracker.set_dirty(True)
            self.assertTrue(toggle_capture._apply_key("f10"))
            self.assertEqual(self.app.data["hook_toggle_key"], "f10")
            self.assertEqual(self.app.ui_vars.toggle_key_var.get(), "f10")
            self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

            stop_capture.clear()
            self.assertEqual(self.app.data["hook_stop_key"], "")
            self.assertEqual(self.app.ui_vars.stop_key_var.get(), "")
            self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())
            self.assertEqual(
                write_global_hook_keys.call_args_list,
                [
                    call(stop_key="f9", toggle_key="f4"),
                    call(stop_key="f9", toggle_key="f10"),
                    call(stop_key="", toggle_key="f10"),
                ],
            )
        self.app.dirty_tracker.set_dirty(False)

    def test_global_hook_key_save_failure_keeps_values_and_restores_dirty_state(self):
        capture = self.app.stop_key_capture
        self.app.data["hook_keys_individual"] = False
        self.app.data["hook_stop_key"] = "f3"
        self.app.data["hook_toggle_key"] = "f4"
        self.app.ui_vars.stop_key_var.set("f3")
        self.app.dirty_tracker.set_dirty(False)

        with patch.object(self.app.startup_io, "write_global_hook_keys", return_value=False):
            self.assertFalse(capture._apply_key("f9"))
        self.assertEqual(self.app.data["hook_stop_key"], "f3")
        self.assertEqual(self.app.ui_vars.stop_key_var.get(), "f3")
        self.assertFalse(self.app.dirty_tracker.has_unsaved_changes())

        with patch.object(self.app.startup_io, "write_global_hook_keys", side_effect=OSError("no disk")):
            with self.assertRaises(OSError):
                capture._apply_key("f9")
        self.assertEqual(self.app.data["hook_stop_key"], "f3")
        self.assertEqual(self.app.ui_vars.stop_key_var.get(), "f3")
        self.assertFalse(self.app.dirty_tracker.has_unsaved_changes())

    def test_compact_and_full_view_switch(self):
        self.app.show_compact_view()
        self.assertTrue(self.app._compact_mode)
        self.assertIn("選択:", self.app.ui_vars.status_var.get())
        self.app.show_full_view()
        self.assertFalse(self.app._compact_mode)

    def test_hook_suspend_counter_nesting(self):
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
        self.app.hook.suspend_hook_for_dialog()
        self.app.hook.suspend_hook_for_dialog()
        self.assertEqual(self.app.hook.get_hook_pause_count(), 2)
        self.app.hook.resume_hook_after_dialog()
        self.app.hook.resume_hook_after_dialog()
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def test_hook_keys_individual_checks_share_var_and_compact_is_display_only(self):
        full_check = self.app.full_view.hook_frame.hook_keys_individual_check
        compact_check = self.app.compact_view.hook_frame.hook_keys_individual_check

        self.assertEqual(str(full_check.cget("variable")), str(compact_check.cget("variable")))
        self.assertEqual(str(full_check.cget("variable")), str(self.app.ui_vars.hook_keys_individual_var))
        self.assertEqual(str(compact_check.cget("state")), "disabled")

    def test_hook_keys_individual_syncs_from_loaded_data(self):
        self.app.data["hook_keys_individual"] = True
        self.app.keymap_set_io.apply_loaded_data_to_ui()
        self.assertTrue(self.app.ui_vars.hook_keys_individual_var.get())

        self.app.data["hook_keys_individual"] = False
        self.app.keymap_set_io.apply_loaded_data_to_ui()
        self.assertFalse(self.app.ui_vars.hook_keys_individual_var.get())

    def test_turning_individual_hook_keys_off_applies_global_defaults_and_marks_dirty(self):
        with tempfile.TemporaryDirectory() as config_root:
            self._write_global_hook_key_defaults(config_root)
            with patch.object(self.app, "config_root", config_root):
                self.app.dirty_tracker.set_dirty(False)
                self._switch_individual_hook_keys_off()

                self.assertFalse(self.app.data["hook_keys_individual"])
                self.assertEqual(self.app.data["hook_stop_key"], "f9")
                self.assertEqual(self.app.data["hook_toggle_key"], "f10")
                self.assertEqual(self.app.ui_vars.stop_key_var.get(), "f9")
                self.assertEqual(self.app.ui_vars.toggle_key_var.get(), "f10")
                self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())
        self.app.dirty_tracker.set_dirty(False)

    def test_turning_individual_hook_keys_on_restores_retained_values_or_clears_values(self):
        with tempfile.TemporaryDirectory() as config_root:
            self._write_global_hook_key_defaults(config_root)
            with patch.object(self.app, "config_root", config_root):
                self._switch_individual_hook_keys_off()
                self.app.ui_vars.hook_keys_individual_var.set(True)
                self.app.toggle_hook_keys_individual()
                self.assertEqual(self.app.data["hook_stop_key"], "f5")
                self.assertEqual(self.app.data["hook_toggle_key"], "f6")
                self.assertEqual(self.app.ui_vars.stop_key_var.get(), "f5")
                self.assertEqual(self.app.ui_vars.toggle_key_var.get(), "f6")

                self.app.data["hook_stop_key"] = "f7"
                self.app.data["hook_toggle_key"] = "f8"
                self.app._sync_control_vars_from_data()
                self.app.ui_vars.hook_keys_individual_var.set(False)
                self.app.toggle_hook_keys_individual()
                self.app.ui_vars.hook_keys_individual_var.set(True)
                self.app.toggle_hook_keys_individual()
                self.assertEqual(self.app.data["hook_stop_key"], "f7")
                self.assertEqual(self.app.data["hook_toggle_key"], "f8")
                self.assertEqual(self.app.ui_vars.stop_key_var.get(), "f7")
                self.assertEqual(self.app.ui_vars.toggle_key_var.get(), "f8")

                self.app.discard_retained_hook_keys()
                self.app.data["hook_keys_individual"] = False
                self.app.data["hook_stop_key"] = "f9"
                self.app.data["hook_toggle_key"] = "f10"
                self.app._sync_control_vars_from_data()
                self.app.ui_vars.hook_keys_individual_var.set(True)
                self.app.toggle_hook_keys_individual()
                self.assertEqual(self.app.data["hook_stop_key"], "")
                self.assertEqual(self.app.data["hook_toggle_key"], "")
                self.assertEqual(self.app.ui_vars.stop_key_var.get(), "")
                self.assertEqual(self.app.ui_vars.toggle_key_var.get(), "")
        self.app.dirty_tracker.set_dirty(False)

    def test_saving_keymap_set_discards_retained_individual_hook_keys(self):
        with tempfile.TemporaryDirectory() as config_root:
            self._write_global_hook_key_defaults(config_root)
            with patch.object(self.app, "config_root", config_root):
                self._switch_individual_hook_keys_off()
                save_path = os.path.join(config_root, "user", "keymap_sets", "saved.json")
                with patch.object(
                    self.app.keymap_set_io,
                    "_collect_child_save_plan",
                    return_value=(SavePlan(), "", False),
                ), patch.object(
                    self.app.paths, "normalize_keymap_set_save_path", return_value=save_path
                ), patch.object(
                    self.app.keymap_set_io, "choose_split_base_dir_for_keymap_set", return_value=""
                ), patch.object(
                    self.app.config_service,
                    "save_runtime_data",
                    return_value=(self.app.data, self.app._startup_settings),
                ), patch.object(
                    self.app.paths, "preferred_startup_path", return_value=os.path.join(config_root, "config.json")
                ), patch.object(self.app, "_set_flash_message"):
                    self.assertTrue(
                        self.app.keymap_set_io.save_keymap_set_to(
                            save_path,
                            flash_message="保存しました。",
                            show_success_dialog=False,
                        )
                    )

                self.app.ui_vars.hook_keys_individual_var.set(True)
                self.app.toggle_hook_keys_individual()
                self.assertEqual(self.app.data["hook_stop_key"], "")
                self.assertEqual(self.app.data["hook_toggle_key"], "")
                self.assertEqual(self.app.ui_vars.stop_key_var.get(), "")
                self.assertEqual(self.app.ui_vars.toggle_key_var.get(), "")
        self.app.dirty_tracker.set_dirty(False)

    def test_loading_new_or_default_data_discards_retained_individual_hook_keys(self):
        with tempfile.TemporaryDirectory() as config_root:
            self._write_global_hook_key_defaults(config_root)
            with patch.object(self.app, "config_root", config_root):
                for action in ("loaded", "new", "default"):
                    with self.subTest(action=action):
                        self._switch_individual_hook_keys_off()
                        if action == "loaded":
                            self.app.keymap_set_io.apply_loaded_data_to_ui()
                        elif action == "new":
                            with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True):
                                self.app.keymap_set_io.new_config()
                        else:
                            with patch.object(
                                self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True
                            ), patch(
                                "keyseq.presentation.controllers.config_io.keymap_set_io.messagebox.askyesno",
                                return_value=True,
                            ):
                                self.app.keymap_set_io.restore_default()

                        self.app.ui_vars.hook_keys_individual_var.set(True)
                        self.app.toggle_hook_keys_individual()
                        self.assertEqual(self.app.data["hook_stop_key"], "")
                        self.assertEqual(self.app.data["hook_toggle_key"], "")
                        self.assertEqual(self.app.ui_vars.stop_key_var.get(), "")
                        self.assertEqual(self.app.ui_vars.toggle_key_var.get(), "")
        self.app.dirty_tracker.set_dirty(False)

    def test_stop_key_capture_start_and_cancel(self):
        self.app.start_stop_key_capture()
        self.assertTrue(self.app.stop_key_capture.capturing)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        self.app.stop_key_capture.stop(cancel=True)
        self.assertFalse(self.app.stop_key_capture.capturing)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def test_keymap_list_shows_active_marker(self):
        self.app.keymap_panel.refresh_keymap_list_ui()
        first = self.app.full_view.keymap_box.keymap_listbox.get(0)
        self.assertTrue(first.startswith("> "))
        self.assertIn("Main", first)

    def test_keyboard_window_opens_and_closes(self):
        self.app.layout.open_keyboard_window()
        self.assertIsNotNone(self.app.layout.keyboard_window)
        self.app.layout.keyboard_window._handle_close()
        self.assertIsNone(self.app.layout.keyboard_window)

    def test_validate_hotkey_empty(self):
        self.assertEqual(
            self.app.validate_hotkey(""),
            ("hotkey が空です。", ""),
        )

    def test_validate_hotkey_whitespace_only(self):
        self.assertEqual(
            self.app.validate_hotkey("   "),
            ("hotkey が空です。", ""),
        )

    def test_validate_hotkey_empty_around_plus(self):
        expected = (
            "hotkey の '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。",
            "",
        )
        for hotkey in ("ctrl++c", "+ctrl+c", "ctrl+c+"):
            with self.subTest(hotkey=hotkey):
                self.assertEqual(self.app.validate_hotkey(hotkey), expected)

    def test_validate_hotkey_duplicate_key(self):
        self.assertEqual(
            self.app.validate_hotkey("ctrl+ctrl+c"),
            ("hotkey に同じキーが重複しています（例: 'ctrl+ctrl+c'）。", ""),
        )

    def test_validate_hotkey_unknown_key_name(self):
        message, normalized = self.app.validate_hotkey("ctrl+keyseq_invalid_unknown_key_9f4c")
        self.assertTrue(
            message.startswith(
                "不明なキー名があります: 'keyseq_invalid_unknown_key_9f4c'（詳細: "
            )
        )
        self.assertEqual(normalized, "")

    def test_validate_hotkey_valid(self):
        self.assertEqual(self.app.validate_hotkey("ctrl+c"), ("", "ctrl+c"))

    def test_validate_hotkey_normalizes_whitespace_and_case(self):
        self.assertEqual(self.app.validate_hotkey(" Ctrl + C "), ("", "ctrl+c"))


if __name__ == "__main__":
    unittest.main()
