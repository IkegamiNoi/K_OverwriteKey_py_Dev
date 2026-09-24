"""App を実際に生成して、ダイアログを出さない範囲の UI 挙動を固定する。

- グローバルフックは一切開始しない（start_hook を呼ばない）
- ファイル保存を伴う操作は行わない（全体デフォルトの確認のみ一時ディレクトリで I/O する）
- GUI が開ける環境（通常のデスクトップセッション）で実行すること
"""
import copy
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from keyseq.application.config_service import ConfigService
from keyseq.application.save_plan import SavePlan
from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.dialogs import PresetManagerDialog, format_preset_manager_source_labels
from tests_ui.hook_resume_wait import wait_for_hook_pause_count


def _unexpected_showerror(_title, message, *_args, **_kwargs):
    raise AssertionError(f"unexpected messagebox.showerror: {message}")


def _unexpected_askyesno(*_args, **_kwargs):
    raise AssertionError("unexpected messagebox.askyesno")


class AppUiFlowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()
        cls.app.update_idletasks()
        # 実環境の構成に依存しないよう、テスト用データへ差し替える
        cls.app.data = cls.app.config_service.normalize_runtime_data(
            {
                "triggers": [],
                "keymaps": [{"id": "km1", "label": "Main", "mappings": {"a": "b"}, "triggers": [
                    {"key": "f1", "label": "one", "actions": [{"type": "text", "value": "a"}]},
                    {"key": "f2", "label": "two", "actions": []},
                ]}],
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
            # 破棄前に保留中の after(0) を流し、後続モジュールへ持ち越さない。
            cls.app.update()
            cls.app.destroy()

    def setUp(self):
        self._showerror_guard = patch(
            "keyseq.presentation.controllers.config_io.hotkey_presets_io.messagebox.showerror",
            side_effect=_unexpected_showerror,
        )
        self._askyesno_guard = patch(
            "keyseq.presentation.controllers.config_io.hotkey_presets_io.messagebox.askyesno",
            side_effect=_unexpected_askyesno,
        )
        self._showerror_guard.start()
        self._askyesno_guard.start()
        self.addCleanup(self._showerror_guard.stop)
        self.addCleanup(self._askyesno_guard.stop)

    def _preset_toggle_dialog(self, presets, *, individual: bool):
        state = {"individual": individual}
        dialog = object.__new__(PresetManagerDialog)
        dialog.parent = self.app
        dialog._temp = copy.deepcopy(presets)
        dialog._loaded_temp = copy.deepcopy(presets)
        dialog._individual_state = "off" if not individual else "active"
        dialog._displayed_source = "global" if not individual else "individual"
        dialog._global_hotkey_presets_path = (
            self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH
        )
        dialog._keymap_set_saved = True
        dialog.individual_var = SimpleNamespace(
            get=lambda: state["individual"],
            set=lambda value: state.__setitem__("individual", value),
        )
        return dialog, state

    def test_initialization_applies_global_defaults(self):
        original_apply_global_defaults = ConfigService.apply_global_defaults
        with patch.object(StartupIo, "load_startup_and_config"), patch.object(
            ConfigService,
            "apply_global_defaults",
            autospec=True,
            side_effect=original_apply_global_defaults,
        ) as apply_global_defaults:
            initialized_app = App()
        self.addCleanup(initialized_app.destroy)

        apply_global_defaults.assert_called_once_with(
            initialized_app.config_service,
            initialized_app.data,
            config_root=initialized_app.config_root,
        )

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

    def test_turning_individual_hook_keys_off_keeps_edited_hotkey_presets(self):
        edited_presets = [{"label": "Edited", "value": "ctrl+e"}]
        with tempfile.TemporaryDirectory() as config_root:
            self._write_global_hook_key_defaults(config_root)
            self.app.config_service.repository.save_json(
                os.path.join(config_root, self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH),
                {"hotkey_presets": [{"label": "Global", "value": "ctrl+g"}]},
            )
            with patch.object(self.app, "config_root", config_root):
                self.app.data["hotkey_presets"] = edited_presets
                self._switch_individual_hook_keys_off()

                self.assertEqual(self.app.data["hotkey_presets"], edited_presets)
        self.app.dirty_tracker.set_dirty(False)

    def test_save_hotkey_presets_updates_runtime_on_success(self):
        presets = [{"label": "Save", "value": "ctrl+s"}]
        with patch.object(
            self.app.hotkey_presets_io,
            "write_presets",
            return_value=True,
        ) as write_presets:
            self.assertTrue(self.app.save_hotkey_presets(presets))

        write_presets.assert_called_once_with(presets, stored_path="")
        self.assertEqual(self.app.data["hotkey_presets"], presets)

    def test_save_hotkey_presets_preserves_runtime_and_shows_error_on_failure(self):
        self.app.data["hotkey_presets"] = [{"label": "Existing", "value": "ctrl+e"}]
        before = copy.deepcopy(self.app.data)
        presets = [{"label": "New", "value": "ctrl+n"}]

        with patch.object(
            self.app.config_service,
            "save_global_hotkey_presets",
            side_effect=OSError("no disk"),
        ), patch(
            "keyseq.presentation.controllers.config_io.hotkey_presets_io.messagebox.showerror"
        ) as showerror:
            self.assertFalse(self.app.save_hotkey_presets(presets))

        self.assertEqual(self.app.data, before)
        showerror.assert_called_once_with("プリセット保存失敗", "no disk")

    def test_save_hotkey_presets_writes_individual_file_without_updating_global(self):
        before = copy.deepcopy(self.app.data)
        presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                keymap_set_path = os.path.join(
                    config_root,
                    "user",
                    "keymap_sets",
                    "main.json",
                )
                global_path = os.path.join(
                    config_root,
                    self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                )
                self.app.config_service.repository.save_json(
                    global_path,
                    {"hotkey_presets": [{"label": "Global", "value": "ctrl+g"}]},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = "user/hotkey_presets/custom.json"

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    keymap_set_path,
                ):
                    self.assertTrue(self.app.save_hotkey_presets(presets))

                self.assertEqual(
                    self.app.config_service.repository.load_json(
                        os.path.join(config_root, "user", "hotkey_presets", "custom.json")
                    ),
                    {"hotkey_presets": presets},
                )
                self.assertEqual(
                    self.app.config_service.repository.load_json(global_path),
                    {"hotkey_presets": [{"label": "Global", "value": "ctrl+g"}]},
                )
        finally:
            self.app.data = before

    def test_save_hotkey_presets_sets_default_individual_path_only_after_success(self):
        before = copy.deepcopy(self.app.data)
        presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                keymap_set_path = os.path.join(
                    config_root,
                    "user",
                    "keymap_sets",
                    "main.json",
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = ""

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    keymap_set_path,
                ):
                    self.assertTrue(self.app.save_hotkey_presets(presets))

                self.assertEqual(
                    self.app.data["hotkey_presets_path"],
                    "user/hotkey_presets/main.json",
                )
                self.assertTrue(self.app.data["hotkey_presets_individual"])
        finally:
            self.app.data = before

    def test_legacy_residual_path_saves_to_keymap_set_stem(self):
        before = copy.deepcopy(self.app.data)
        presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                keymap_set_path = os.path.join(
                    config_root,
                    "user",
                    "keymap_sets",
                    "legacy.json",
                )
                legacy_path = os.path.join(
                    config_root,
                    "user",
                    "hotkey_presets",
                    "default.json",
                )
                self.app.config_service.repository.save_json(
                    keymap_set_path,
                    {"hotkey_presets_path": "user/hotkey_presets/default.json"},
                )
                self.app.data = self.app.config_service.load_runtime_data_from_keymap_set_path(
                    keymap_set_path,
                    config_root=config_root,
                )

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    keymap_set_path,
                ), patch.object(self.app.dirty_tracker, "set_dirty") as set_dirty, patch(
                    "keyseq.presentation.controllers.config_io.hotkey_presets_io.messagebox.showerror"
                ) as showerror, patch(
                    "keyseq.presentation.controllers.config_io.keymap_set_io.filedialog.asksaveasfilename"
                ) as asksaveasfilename:
                    self.assertTrue(self.app.save_hotkey_presets(presets, individual=True))

                self.assertEqual(
                    self.app.config_service.repository.load_json(
                        os.path.join(config_root, "user", "hotkey_presets", "legacy.json")
                    ),
                    {"hotkey_presets": presets},
                )
                self.assertFalse(os.path.exists(legacy_path))
                set_dirty.assert_called_with(True)
                showerror.assert_not_called()
                asksaveasfilename.assert_not_called()
        finally:
            self.app.data = before

    def test_save_hotkey_presets_failure_preserves_all_data_for_individual_target(self):
        before = copy.deepcopy(self.app.data)
        presets = [{"label": "New", "value": "ctrl+n"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                keymap_set_path = os.path.join(
                    config_root,
                    "user",
                    "keymap_sets",
                    "main.json",
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = ""
                expected_before = copy.deepcopy(self.app.data)

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    keymap_set_path,
                ), patch.object(
                    self.app.config_service,
                    "save_hotkey_presets",
                    side_effect=OSError("no disk"),
                ), patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty, patch(
                    "keyseq.presentation.controllers.config_io.hotkey_presets_io.messagebox.showerror"
                ) as showerror:
                    self.assertFalse(self.app.save_hotkey_presets(presets))

                self.assertEqual(self.app.data, expected_before)
                set_dirty.assert_not_called()
                showerror.assert_called_once_with("プリセット保存失敗", "no disk")
        finally:
            self.app.data = before

    def test_save_hotkey_presets_turning_individual_on_writes_and_marks_dirty(self):
        before = copy.deepcopy(self.app.data)
        presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                keymap_set_path = os.path.join(config_root, "user", "keymap_sets", "main.json")
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets_path"] = ""

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    keymap_set_path,
                ), patch.object(self.app.dirty_tracker, "set_dirty") as set_dirty:
                    self.assertTrue(self.app.save_hotkey_presets(presets, individual=True))

                self.assertEqual(
                    self.app.config_service.repository.load_json(
                        os.path.join(config_root, "user", "hotkey_presets", "main.json")
                    ),
                    {"hotkey_presets": presets},
                )
                self.assertTrue(self.app.data["hotkey_presets_individual"])
                self.assertEqual(self.app.data["hotkey_presets_path"], "user/hotkey_presets/main.json")
                set_dirty.assert_called_with(True)
        finally:
            self.app.data = before

    def test_save_hotkey_presets_turning_individual_off_writes_global(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        displayed_presets = [{"label": "Displayed", "value": "ctrl+d"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH),
                    {"hotkey_presets": global_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = "user/hotkey_presets/personal.json"
                self.app.data["hotkey_presets"] = [{"label": "Individual", "value": "ctrl+i"}]

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app.hotkey_presets_io,
                    "write_presets",
                    wraps=self.app.hotkey_presets_io.write_presets,
                ) as write_presets, patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty:
                    self.assertTrue(
                        self.app.save_hotkey_presets(displayed_presets, individual=False)
                    )

                write_presets.assert_called_once_with(displayed_presets, stored_path="")
                self.assertFalse(self.app.data["hotkey_presets_individual"])
                self.assertEqual(
                    self.app.data["hotkey_presets_path"],
                    "user/hotkey_presets/personal.json",
                )
                self.assertEqual(self.app.data["hotkey_presets"], displayed_presets)
                self.assertEqual(
                    self.app.config_service.repository.load_json(
                        os.path.join(
                            config_root,
                            self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                        )
                    ),
                    {"hotkey_presets": displayed_presets},
                )
                set_dirty.assert_called_once_with(True)
        finally:
            self.app.data = before

    def test_save_hotkey_presets_rejects_individual_global_file_collision_without_mutation(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                global_stored_path = "user/hotkey_presets/default.json"
                global_path = os.path.join(config_root, global_stored_path)
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, "config.json"),
                    {"hotkey_presets_path": global_stored_path},
                )
                self.app.config_service.repository.save_json(
                    global_path,
                    {"hotkey_presets": global_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = ""
                self.app.data["hotkey_presets"] = [{"label": "Before", "value": "ctrl+b"}]
                expected_before = copy.deepcopy(self.app.data)

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    os.path.join(config_root, "user", "keymap_sets", "default.json"),
                ), patch.object(
                    self.app.hotkey_presets_io,
                    "write_presets",
                ) as write_presets, patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty, patch(
                    "keyseq.presentation.controllers.config_io.hotkey_presets_io.messagebox.showerror"
                ) as showerror:
                    self.assertFalse(self.app.save_hotkey_presets(individual_presets, individual=True))

                write_presets.assert_not_called()
                set_dirty.assert_not_called()
                self.assertEqual(self.app.data, expected_before)
                self.assertEqual(
                    self.app.config_service.repository.load_json(global_path),
                    {"hotkey_presets": global_presets},
                )
                showerror.assert_called_once()
                self.assertIn("同じファイル", showerror.call_args.args[1])
                self.assertIn(global_stored_path, showerror.call_args.args[1])
        finally:
            self.app.data = before

    def test_save_hotkey_presets_rejects_reserved_global_directory_with_distinct_message(self):
        before = copy.deepcopy(self.app.data)
        try:
            with tempfile.TemporaryDirectory() as config_root:
                reserved_stored_path = "user/hotkey_presets/global/individual.json"
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = reserved_stored_path
                expected_before = copy.deepcopy(self.app.data)

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    os.path.join(config_root, "user", "keymap_sets", "main.json"),
                ), patch.object(
                    self.app.hotkey_presets_io,
                    "write_presets",
                ) as write_presets, patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty, patch(
                    "keyseq.presentation.controllers.config_io.hotkey_presets_io.messagebox.showerror"
                ) as showerror:
                    self.assertFalse(self.app.save_hotkey_presets([], individual=True))

                write_presets.assert_not_called()
                set_dirty.assert_not_called()
                self.assertEqual(self.app.data, expected_before)
                showerror.assert_called_once()
                self.assertIn("global/ はグローバル用", showerror.call_args.args[1])
                self.assertNotIn("同じファイル", showerror.call_args.args[1])
                self.assertIn(reserved_stored_path, showerror.call_args.args[1])
        finally:
            self.app.data = before

    def test_save_hotkey_presets_allows_turning_individual_off_from_collision(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                global_stored_path = "user/hotkey_presets/default.json"
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, "config.json"),
                    {"hotkey_presets_path": global_stored_path},
                )
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, global_stored_path),
                    {"hotkey_presets": global_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = global_stored_path

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app.hotkey_presets_io,
                    "write_presets",
                    return_value=True,
                ) as write_presets, patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty, patch(
                    "keyseq.presentation.controllers.config_io.hotkey_presets_io.messagebox.showerror"
                ) as showerror:
                    self.assertTrue(self.app.save_hotkey_presets([], individual=False))

                write_presets.assert_called_once_with([], stored_path="")
                set_dirty.assert_called_once_with(True)
                showerror.assert_not_called()
                self.assertFalse(self.app.data["hotkey_presets_individual"])
                self.assertEqual(self.app.data["hotkey_presets"], [])
        finally:
            self.app.data = before

    def test_save_hotkey_presets_allows_global_save_while_individual_is_off(self):
        before = copy.deepcopy(self.app.data)
        presets = [{"label": "Global", "value": "ctrl+g"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets_path"] = "user/hotkey_presets/global/individual.json"

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app.hotkey_presets_io,
                    "write_presets",
                    return_value=True,
                ) as write_presets, patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty, patch(
                    "keyseq.presentation.controllers.config_io.hotkey_presets_io.messagebox.showerror"
                ) as showerror:
                    self.assertTrue(self.app.save_hotkey_presets(presets, individual=False))

                write_presets.assert_called_once_with(presets, stored_path="")
                set_dirty.assert_not_called()
                showerror.assert_not_called()
                self.assertEqual(self.app.data["hotkey_presets"], presets)
        finally:
            self.app.data = before

    def test_save_hotkey_presets_moves_readable_outside_individual_path_under_management(self):
        before = copy.deepcopy(self.app.data)
        presets = [{"label": "New", "value": "ctrl+n"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                global_presets = [{"label": "Global", "value": "ctrl+g"}]
                global_path = os.path.join(
                    config_root,
                    self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                )
                self.app.config_service.repository.save_json(
                    global_path,
                    {"hotkey_presets": global_presets},
                )
                outside_path = os.path.join(os.path.dirname(config_root), "outside.json")
                outside_presets = [{"label": "Outside", "value": "ctrl+o"}]
                self.app.config_service.repository.save_json(
                    outside_path,
                    {"hotkey_presets": outside_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = outside_path

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    os.path.join(config_root, "user", "keymap_sets", "main.json"),
                ), patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty, patch(
                    "keyseq.presentation.controllers.config_io.hotkey_presets_io.messagebox.showerror"
                ) as showerror, patch(
                    "keyseq.presentation.controllers.config_io.keymap_set_io.filedialog.asksaveasfilename"
                ) as asksaveasfilename:
                    self.assertTrue(self.app.save_hotkey_presets(presets, individual=True))

                self.assertEqual(
                    self.app.config_service.repository.load_json(global_path),
                    {"hotkey_presets": global_presets},
                )
                self.assertEqual(
                    self.app.config_service.repository.load_json(
                        os.path.join(config_root, "user", "hotkey_presets", "main.json")
                    ),
                    {"hotkey_presets": presets},
                )
                self.assertEqual(self.app.data["hotkey_presets_path"], "user/hotkey_presets/main.json")
                self.assertEqual(
                    self.app.config_service.repository.load_json(outside_path),
                    {"hotkey_presets": outside_presets},
                )
                set_dirty.assert_called_once_with(True)
                showerror.assert_not_called()
                asksaveasfilename.assert_not_called()
        finally:
            self.app.data = before

    def test_save_hotkey_presets_turning_individual_off_allows_invalid_path_recovery(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH),
                    {"hotkey_presets": global_presets},
                )
                invalid_path = os.path.join(os.path.dirname(config_root), "outside.json")
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = invalid_path
                self.app.data["hotkey_presets"] = [{"label": "Individual", "value": "ctrl+i"}]

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app.hotkey_presets_io,
                    "write_presets",
                    wraps=self.app.hotkey_presets_io.write_presets,
                ) as write_presets, patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty:
                    self.assertTrue(
                        self.app.save_hotkey_presets(global_presets, individual=False)
                    )

                write_presets.assert_called_once_with(global_presets, stored_path="")
                self.assertFalse(self.app.data["hotkey_presets_individual"])
                self.assertEqual(self.app.data["hotkey_presets_path"], invalid_path)
                self.assertEqual(self.app.data["hotkey_presets"], global_presets)
                set_dirty.assert_called_once_with(True)
        finally:
            self.app.data = before

    def test_save_hotkey_presets_writes_global_when_invalid_path_is_disabled(self):
        before = copy.deepcopy(self.app.data)
        presets = [{"label": "Global", "value": "ctrl+g"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets_path"] = os.path.join(
                    os.path.dirname(config_root),
                    "outside.json",
                )

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty:
                    self.assertTrue(self.app.save_hotkey_presets(presets))

                self.assertEqual(
                    self.app.config_service.repository.load_json(
                        os.path.join(config_root, self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH)
                    ),
                    {"hotkey_presets": presets},
                )
                self.assertEqual(self.app.data["hotkey_presets_path"], os.path.join(
                    os.path.dirname(config_root),
                    "outside.json",
                ))
                set_dirty.assert_not_called()
        finally:
            self.app.data = before

    def test_save_hotkey_presets_without_flag_change_does_not_mark_dirty(self):
        presets = [{"label": "Save", "value": "ctrl+s"}]
        for current_individual in (False, True):
            with self.subTest(current_individual=current_individual):
                before = copy.deepcopy(self.app.data)
                try:
                    self.app.data["hotkey_presets_individual"] = current_individual
                    self.app.data["hotkey_presets_path"] = "user/hotkey_presets/personal.json"
                    with patch.object(
                        self.app.hotkey_presets_io,
                        "write_presets",
                        return_value=True,
                    ) as write_presets, patch.object(
                        self.app.dirty_tracker,
                        "set_dirty",
                    ) as set_dirty:
                        self.assertTrue(
                            self.app.save_hotkey_presets(
                                presets,
                                individual=current_individual,
                            )
                        )
                    write_presets.assert_called_once_with(
                        presets,
                        stored_path=(
                            "user/hotkey_presets/personal.json" if current_individual else ""
                        ),
                    )
                    set_dirty.assert_not_called()
                finally:
                    self.app.data = before

    def test_save_hotkey_presets_failed_individual_toggle_keeps_all_data(self):
        before = copy.deepcopy(self.app.data)
        presets = [{"label": "New", "value": "ctrl+n"}]
        try:
            self.app.data["hotkey_presets_individual"] = False
            self.app.data["hotkey_presets_path"] = "user/hotkey_presets/retained.json"
            expected = copy.deepcopy(self.app.data)
            with patch.object(
                self.app.hotkey_presets_io,
                "write_presets",
                return_value=False,
            ), patch.object(
                self.app.dirty_tracker,
                "set_dirty",
            ) as set_dirty:
                self.assertFalse(self.app.save_hotkey_presets(presets, individual=True))

            self.assertEqual(self.app.data, expected)
            set_dirty.assert_not_called()
        finally:
            self.app.data = before

    def test_save_hotkey_presets_overwrite_or_cancel_uses_conflict_handler(self):
        before = copy.deepcopy(self.app.data)
        loaded_presets = [{"label": "Loaded", "value": "ctrl+l"}]
        edited_presets = [{"label": "Edited", "value": "ctrl+e"}]
        stored_presets = [{"label": "Stored", "value": "ctrl+s"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                stored_path = "user/hotkey_presets/main.json"
                target_path = os.path.join(config_root, stored_path)
                self.app.config_service.repository.save_json(
                    target_path,
                    {"hotkey_presets": stored_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = ""
                expected_data = copy.deepcopy(self.app.data)

                cancel_handler = Mock(return_value="cancel")
                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    os.path.join(config_root, "user", "keymap_sets", "main.json"),
                ), patch.object(
                    self.app.hotkey_presets_io,
                    "write_presets",
                ) as write_presets, patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty:
                    self.assertFalse(
                        self.app.save_hotkey_presets(
                            edited_presets,
                            individual=True,
                            loaded_presets=loaded_presets,
                            on_overwrite_conflict=cancel_handler,
                        )
                    )

                cancel_handler.assert_called_once_with(stored_path, stored_presets)
                write_presets.assert_not_called()
                set_dirty.assert_not_called()
                self.assertEqual(self.app.data, expected_data)
                self.assertEqual(
                    self.app.config_service.repository.load_json(target_path),
                    {"hotkey_presets": stored_presets},
                )

                overwrite_handler = Mock(return_value="overwrite")
                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    os.path.join(config_root, "user", "keymap_sets", "main.json"),
                ):
                    self.assertTrue(
                        self.app.save_hotkey_presets(
                            edited_presets,
                            individual=True,
                            loaded_presets=loaded_presets,
                            on_overwrite_conflict=overwrite_handler,
                        )
                    )

                overwrite_handler.assert_called_once_with(stored_path, stored_presets)
                self.assertEqual(
                    self.app.config_service.repository.load_json(target_path),
                    {"hotkey_presets": edited_presets},
                )
        finally:
            self.app.data = before

    def test_save_hotkey_presets_skips_confirmation_for_safe_targets(self):
        before = copy.deepcopy(self.app.data)
        loaded_presets = [{"label": "Loaded", "value": "ctrl+l"}]
        edited_presets = [{"label": "Edited", "value": "ctrl+e"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                keymap_set_path = os.path.join(config_root, "user", "keymap_sets", "main.json")
                stored_path = "user/hotkey_presets/personal.json"
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, stored_path),
                    {"hotkey_presets": loaded_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = stored_path

                handler = Mock()
                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app, "keymap_set_path", keymap_set_path
                ):
                    self.assertTrue(
                        self.app.save_hotkey_presets(
                            edited_presets,
                            individual=True,
                            loaded_presets=loaded_presets,
                            on_overwrite_conflict=handler,
                        )
                    )
                handler.assert_not_called()

                self.app.data["hotkey_presets_path"] = ""
                fresh_path = os.path.join(config_root, "user", "hotkey_presets", "main.json")
                if os.path.exists(fresh_path):
                    os.remove(fresh_path)
                handler = Mock()
                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app, "keymap_set_path", keymap_set_path
                ):
                    self.assertTrue(
                        self.app.save_hotkey_presets(
                            edited_presets,
                            individual=True,
                            loaded_presets=loaded_presets,
                            on_overwrite_conflict=handler,
                        )
                    )
                handler.assert_not_called()

                self.app.data["hotkey_presets_individual"] = False
                handler = Mock()
                with patch.object(self.app, "config_root", config_root):
                    self.assertTrue(
                        self.app.save_hotkey_presets(
                            edited_presets,
                            individual=False,
                            loaded_presets=loaded_presets,
                            on_overwrite_conflict=handler,
                        )
                    )
                handler.assert_not_called()
        finally:
            self.app.data = before

    def test_save_hotkey_presets_confirms_after_save_as_uses_existing_copy_target(self):
        before = copy.deepcopy(self.app.data)
        copied_presets = [{"label": "Copied", "value": "ctrl+c"}]
        displayed_presets = [{"label": "Original", "value": "ctrl+o"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                source_path = "user/hotkey_presets/original.json"
                stored_path = "user/hotkey_presets/renamed.json"
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, source_path),
                    {"hotkey_presets": displayed_presets},
                )
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, stored_path),
                    {"hotkey_presets": copied_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = source_path
                keymap_set_path = os.path.join(
                    config_root,
                    "user",
                    "keymap_sets",
                    "renamed.json",
                )
                self.assertEqual(
                    self.app.config_service.relocate_individual_hotkey_presets(
                        self.app.data,
                        config_root=config_root,
                        keymap_set_path=keymap_set_path,
                    ),
                    stored_path,
                )
                self.app.data["hotkey_presets_path"] = stored_path

                handler = Mock(return_value="cancel")
                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    keymap_set_path,
                ):
                    self.assertFalse(
                        self.app.save_hotkey_presets(
                            displayed_presets,
                            individual=True,
                            loaded_presets=displayed_presets,
                            on_overwrite_conflict=handler,
                        )
                    )

                handler.assert_called_once_with(stored_path, copied_presets)
        finally:
            self.app.data = before

    def test_save_hotkey_presets_confirms_when_external_path_redirects_to_existing_target(self):
        before = copy.deepcopy(self.app.data)
        loaded_presets = [{"label": "External", "value": "ctrl+x"}]
        stored_presets = [{"label": "Stored", "value": "ctrl+s"}]
        try:
            with tempfile.TemporaryDirectory() as config_root, tempfile.TemporaryDirectory() as outside_root:
                external_path = os.path.join(outside_root, "external.json")
                self.app.config_service.repository.save_json(
                    external_path,
                    {"hotkey_presets": loaded_presets},
                )
                stored_path = "user/hotkey_presets/main.json"
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, stored_path),
                    {"hotkey_presets": stored_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = external_path

                handler = Mock(return_value="cancel")
                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    os.path.join(config_root, "user", "keymap_sets", "main.json"),
                ):
                    self.assertFalse(
                        self.app.save_hotkey_presets(
                            [{"label": "Edited", "value": "ctrl+e"}],
                            individual=True,
                            loaded_presets=loaded_presets,
                            on_overwrite_conflict=handler,
                        )
                    )

                handler.assert_called_once_with(stored_path, stored_presets)
        finally:
            self.app.data = before

    def test_preset_manager_dialog_closes_only_after_successful_save(self):
        presets = [{"label": "Edited", "value": "ctrl+e"}]
        failed_dialog = SimpleNamespace(
            parent=self.app,
            _temp=presets,
            _loaded_temp=[{"label": "Loaded", "value": "ctrl+l"}],
            individual_var=SimpleNamespace(get=Mock(return_value=True)),
            destroy=Mock(),
        )
        with patch.object(self.app, "save_hotkey_presets", return_value=False) as save_hotkey_presets:
            PresetManagerDialog.on_ok(failed_dialog)

        self.assertEqual(save_hotkey_presets.call_args.args, (presets,))
        self.assertEqual(
            save_hotkey_presets.call_args.kwargs["individual"],
            True,
        )
        self.assertEqual(
            save_hotkey_presets.call_args.kwargs["loaded_presets"],
            failed_dialog._loaded_temp,
        )
        self.assertTrue(callable(save_hotkey_presets.call_args.kwargs["on_overwrite_conflict"]))
        failed_dialog.destroy.assert_not_called()
        self.assertEqual(failed_dialog._temp, presets)

        successful_dialog = SimpleNamespace(
            parent=self.app,
            _temp=presets,
            _loaded_temp=[{"label": "Loaded", "value": "ctrl+l"}],
            individual_var=SimpleNamespace(get=Mock(return_value=False)),
            destroy=Mock(),
        )
        with patch.object(self.app, "save_hotkey_presets", return_value=True) as save_hotkey_presets:
            PresetManagerDialog.on_ok(successful_dialog)

        self.assertEqual(save_hotkey_presets.call_args.args, (presets,))
        self.assertEqual(
            save_hotkey_presets.call_args.kwargs["individual"],
            False,
        )
        self.assertEqual(
            save_hotkey_presets.call_args.kwargs["loaded_presets"],
            successful_dialog._loaded_temp,
        )
        self.assertTrue(callable(save_hotkey_presets.call_args.kwargs["on_overwrite_conflict"]))
        successful_dialog.destroy.assert_called_once_with()

    def test_preset_manager_adopt_replaces_temporary_presets_without_saving(self):
        before = copy.deepcopy(self.app.data)
        loaded_presets = [{"label": "Loaded", "value": "ctrl+l"}]
        edited_presets = [{"label": "Edited", "value": "ctrl+e"}]
        stored_presets = [{"label": "Stored", "value": "ctrl+s"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                stored_path = "user/hotkey_presets/main.json"
                target_path = os.path.join(config_root, stored_path)
                self.app.config_service.repository.save_json(
                    target_path,
                    {"hotkey_presets": stored_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = ""
                expected_data = copy.deepcopy(self.app.data)
                dialog = SimpleNamespace(
                    parent=self.app,
                    _temp=copy.deepcopy(edited_presets),
                    _loaded_temp=copy.deepcopy(loaded_presets),
                    individual_var=SimpleNamespace(get=Mock(return_value=True)),
                    _refresh=Mock(),
                    _update_source_labels=Mock(),
                    destroy=Mock(),
                )

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    os.path.join(config_root, "user", "keymap_sets", "main.json"),
                ), patch.object(
                    self.app.hotkey_presets_io,
                    "confirm_overwrite",
                    return_value="adopt",
                ) as confirm_overwrite, patch.object(
                    self.app.hotkey_presets_io,
                    "write_presets",
                ) as write_presets, patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty:
                    PresetManagerDialog.on_ok(dialog)

                confirm_overwrite.assert_called_once_with(
                    stored_path=stored_path,
                    existing=stored_presets,
                    transient_parent=dialog,
                )
                write_presets.assert_not_called()
                set_dirty.assert_not_called()
                dialog.destroy.assert_not_called()
                dialog._refresh.assert_called_once_with()
                dialog._update_source_labels.assert_called_once_with()
                self.assertEqual(dialog._temp, stored_presets)
                self.assertEqual(dialog._loaded_temp, stored_presets)
                self.assertEqual(self.app.data, expected_data)
                self.assertEqual(
                    self.app.config_service.repository.load_json(target_path),
                    {"hotkey_presets": stored_presets},
                )
        finally:
            self.app.data = before

    def test_preset_manager_adopt_then_ok_writes_without_second_confirmation(self):
        before = copy.deepcopy(self.app.data)
        loaded_presets = [{"label": "Loaded", "value": "ctrl+l"}]
        edited_presets = [{"label": "Edited", "value": "ctrl+e"}]
        stored_presets = [{"label": "Stored", "value": "ctrl+s"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                stored_path = "user/hotkey_presets/main.json"
                target_path = os.path.join(config_root, stored_path)
                self.app.config_service.repository.save_json(
                    target_path,
                    {"hotkey_presets": stored_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = ""
                dialog = SimpleNamespace(
                    parent=self.app,
                    _temp=copy.deepcopy(edited_presets),
                    _loaded_temp=copy.deepcopy(loaded_presets),
                    individual_var=SimpleNamespace(get=Mock(return_value=True)),
                    _refresh=Mock(),
                    _update_source_labels=Mock(),
                    destroy=Mock(),
                )

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    os.path.join(config_root, "user", "keymap_sets", "main.json"),
                ), patch.object(
                    self.app.hotkey_presets_io,
                    "confirm_overwrite",
                    return_value="adopt",
                ) as confirm_overwrite, patch.object(
                    self.app.hotkey_presets_io,
                    "write_presets",
                    wraps=self.app.hotkey_presets_io.write_presets,
                ) as write_presets:
                    PresetManagerDialog.on_ok(dialog)
                    PresetManagerDialog.on_ok(dialog)

                confirm_overwrite.assert_called_once_with(
                    stored_path=stored_path,
                    existing=stored_presets,
                    transient_parent=dialog,
                )
                write_presets.assert_called_once_with(stored_presets, stored_path=stored_path)
                dialog.destroy.assert_called_once_with()
                self.assertEqual(
                    self.app.config_service.repository.load_json(target_path),
                    {"hotkey_presets": stored_presets},
                )
        finally:
            self.app.data = before

    def test_preset_manager_overwrite_confirmation_receives_none_for_unreadable_file(self):
        before = copy.deepcopy(self.app.data)
        loaded_presets = [{"label": "Loaded", "value": "ctrl+l"}]
        edited_presets = [{"label": "Edited", "value": "ctrl+e"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                stored_path = "user/hotkey_presets/main.json"
                target_path = os.path.join(config_root, stored_path)
                self.app.config_service.repository.save_json(
                    target_path,
                    {"hotkey_presets": "invalid"},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = ""
                expected_data = copy.deepcopy(self.app.data)
                dialog = SimpleNamespace(
                    parent=self.app,
                    _temp=copy.deepcopy(edited_presets),
                    _loaded_temp=copy.deepcopy(loaded_presets),
                    individual_var=SimpleNamespace(get=Mock(return_value=True)),
                    _refresh=Mock(),
                    _update_source_labels=Mock(),
                    destroy=Mock(),
                )

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    os.path.join(config_root, "user", "keymap_sets", "main.json"),
                ), patch.object(
                    self.app.hotkey_presets_io,
                    "confirm_overwrite",
                    return_value="cancel",
                ) as confirm_overwrite, patch.object(
                    self.app.hotkey_presets_io,
                    "write_presets",
                ) as write_presets:
                    PresetManagerDialog.on_ok(dialog)

                confirm_overwrite.assert_called_once_with(
                    stored_path=stored_path,
                    existing=None,
                    transient_parent=dialog,
                )
                write_presets.assert_not_called()
                dialog.destroy.assert_not_called()
                self.assertEqual(self.app.data, expected_data)
                self.assertEqual(
                    self.app.config_service.repository.load_json(target_path),
                    {"hotkey_presets": "invalid"},
                )
        finally:
            self.app.data = before

    def test_preset_manager_cancel_keeps_runtime_and_dirty_unchanged(self):
        wait_for_hook_pause_count(self, self.app, 0)
        before = copy.deepcopy(self.app.data)

        def cleanup_dialog():
            if dialog.winfo_exists():
                dialog.destroy()
            self.app.update()

        with patch.object(self.app, "save_hotkey_presets") as save_hotkey_presets, patch.object(
            self.app.dirty_tracker,
            "set_dirty",
        ) as set_dirty:
            dialog = PresetManagerDialog(self.app)
            self.addCleanup(cleanup_dialog)
            dialog.update_idletasks()
            self.assertTrue(dialog.winfo_viewable())
            dialog.destroy()
            self.app.update()

        save_hotkey_presets.assert_not_called()
        set_dirty.assert_not_called()
        self.assertEqual(self.app.data, before)

    def test_preset_manager_open_off_uses_global_or_defaults_before_ok(self):
        before = copy.deepcopy(self.app.data)
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        try:
            for global_file_presets in (global_presets, None):
                with self.subTest(global_file_presets=global_file_presets), tempfile.TemporaryDirectory() as config_root:
                    global_path = os.path.join(
                        config_root,
                        self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                    )
                    if global_file_presets is not None:
                        self.app.config_service.repository.save_json(
                            global_path,
                            {"hotkey_presets": global_file_presets},
                        )
                    expected_presets = (
                        global_file_presets
                        if global_file_presets is not None
                        else self.app.config_service.new_default_data()["hotkey_presets"]
                    )
                    self.app.data["hotkey_presets_individual"] = False
                    self.app.data["hotkey_presets_path"] = "user/hotkey_presets/personal.json"
                    self.app.data["hotkey_presets"] = individual_presets

                    with patch.object(self.app, "config_root", config_root), patch.object(
                        self.app.hook, "suspend_hook_for_dialog"
                    ), patch.object(self.app.hook, "resume_hook_after_dialog"), patch.object(
                        self.app.dirty_tracker, "set_dirty"
                    ) as set_dirty:
                        dialog = PresetManagerDialog(self.app)
                        self.assertEqual(dialog._temp, expected_presets)
                        self.assertEqual(dialog._loaded_temp, expected_presets)
                        dialog.on_ok()

                    self.assertEqual(self.app.data["hotkey_presets"], expected_presets)
                    self.assertEqual(
                        self.app.config_service.repository.load_json(global_path),
                        {"hotkey_presets": expected_presets},
                    )
                    set_dirty.assert_not_called()
        finally:
            self.app.data = before

    def test_preset_manager_open_on_keeps_current_list(self):
        before = copy.deepcopy(self.app.data)
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH),
                    {"hotkey_presets": global_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = "user/hotkey_presets/missing.json"
                self.app.data["hotkey_presets"] = individual_presets

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app.hook, "suspend_hook_for_dialog"
                ), patch.object(self.app.hook, "resume_hook_after_dialog"):
                    dialog = PresetManagerDialog(self.app)
                    self.assertEqual(dialog._temp, individual_presets)
                    self.assertEqual(dialog._loaded_temp, individual_presets)
                    dialog.destroy()
        finally:
            self.app.data = before

    def test_preset_manager_open_off_then_cancel_keeps_runtime_and_files_unchanged(self):
        before = copy.deepcopy(self.app.data)
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                global_path = os.path.join(
                    config_root,
                    self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                )
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets_path"] = "user/hotkey_presets/personal.json"
                self.app.data["hotkey_presets"] = individual_presets
                expected_data = copy.deepcopy(self.app.data)

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app.hook, "suspend_hook_for_dialog"
                ), patch.object(self.app.hook, "resume_hook_after_dialog"), patch.object(
                    self.app.dirty_tracker, "set_dirty"
                ) as set_dirty:
                    dialog = PresetManagerDialog(self.app)
                    self.assertEqual(
                        dialog._temp,
                        self.app.config_service.new_default_data()["hotkey_presets"],
                    )
                    dialog.destroy()

                self.assertEqual(self.app.data, expected_data)
                self.assertFalse(os.path.exists(global_path))
                set_dirty.assert_not_called()
        finally:
            self.app.data = before

    def test_preset_manager_toggle_on_reloads_individual_and_ok_preserves_global(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root, tempfile.TemporaryDirectory() as outside_root:
                global_path = os.path.join(
                    config_root,
                    self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                )
                individual_path = os.path.join(outside_root, "individual.json")
                self.app.config_service.repository.save_json(
                    global_path,
                    {"hotkey_presets": global_presets},
                )
                self.app.config_service.repository.save_json(
                    individual_path,
                    {"hotkey_presets": individual_presets},
                )
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets_path"] = individual_path
                self.app.data["hotkey_presets"] = global_presets

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    os.path.join(config_root, "user", "keymap_sets", "main.json"),
                ):
                    dialog, state = self._preset_toggle_dialog(global_presets, individual=False)
                    state["individual"] = True
                    with patch.object(PresetManagerDialog, "_refresh") as refresh, patch.object(
                        PresetManagerDialog,
                        "_update_source_labels",
                    ) as update_labels:
                        PresetManagerDialog._reload_presets_for_individual_toggle(dialog)

                    self.assertEqual(dialog._temp, individual_presets)
                    refresh.assert_called_once_with()
                    update_labels.assert_called_once_with()
                    self.assertTrue(
                        self.app.save_hotkey_presets(dialog._temp, individual=state["individual"])
                    )

                self.assertEqual(
                    self.app.config_service.repository.load_json(global_path),
                    {"hotkey_presets": global_presets},
                )
                self.assertEqual(
                    self.app.config_service.repository.load_json(individual_path),
                    {"hotkey_presets": individual_presets},
                )
        finally:
            self.app.data = before

    def test_preset_manager_toggle_on_without_individual_file_carries_list_and_creates_file(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                global_path = os.path.join(
                    config_root,
                    self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                )
                self.app.config_service.repository.save_json(
                    global_path,
                    {"hotkey_presets": global_presets},
                )
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets_path"] = ""
                self.app.data["hotkey_presets"] = global_presets
                keymap_set_path = os.path.join(config_root, "user", "keymap_sets", "main.json")

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app,
                    "keymap_set_path",
                    keymap_set_path,
                ):
                    dialog, state = self._preset_toggle_dialog(global_presets, individual=False)
                    state["individual"] = True
                    with patch.object(PresetManagerDialog, "_refresh") as refresh, patch.object(
                        PresetManagerDialog,
                        "_update_source_labels",
                    ) as update_labels:
                        PresetManagerDialog._reload_presets_for_individual_toggle(dialog)

                    self.assertEqual(dialog._temp, global_presets)
                    refresh.assert_not_called()
                    update_labels.assert_called_once_with()
                    self.assertTrue(
                        self.app.save_hotkey_presets(dialog._temp, individual=state["individual"])
                    )

                self.assertEqual(
                    self.app.config_service.repository.load_json(
                        os.path.join(config_root, "user", "hotkey_presets", "main.json")
                    ),
                    {"hotkey_presets": global_presets},
                )
        finally:
            self.app.data = before

    def test_preset_manager_toggle_off_reloads_global_and_writes_it(self):
        before = copy.deepcopy(self.app.data)
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                global_path = os.path.join(
                    config_root,
                    self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                )
                self.app.config_service.repository.save_json(
                    global_path,
                    {"hotkey_presets": global_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = "user/hotkey_presets/personal.json"
                self.app.data["hotkey_presets"] = individual_presets

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty:
                    dialog, state = self._preset_toggle_dialog(individual_presets, individual=True)
                    state["individual"] = False
                    with patch.object(PresetManagerDialog, "_refresh"), patch.object(
                        PresetManagerDialog,
                        "_update_source_labels",
                    ):
                        PresetManagerDialog._reload_presets_for_individual_toggle(dialog)

                    self.assertEqual(dialog._temp, global_presets)
                    self.assertTrue(
                        self.app.save_hotkey_presets(dialog._temp, individual=state["individual"])
                    )

                self.assertFalse(self.app.data["hotkey_presets_individual"])
                self.assertEqual(
                    self.app.config_service.repository.load_json(global_path),
                    {"hotkey_presets": global_presets},
                )
                set_dirty.assert_called_once_with(True)
        finally:
            self.app.data = before

    def test_preset_manager_toggle_off_uses_defaults_and_reopen_still_writes_defaults(self):
        before = copy.deepcopy(self.app.data)
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = "user/hotkey_presets/personal.json"
                self.app.data["hotkey_presets"] = individual_presets
                defaults = self.app.config_service.new_default_data()["hotkey_presets"]

                with patch.object(self.app, "config_root", config_root):
                    first_dialog, first_state = self._preset_toggle_dialog(
                        individual_presets,
                        individual=True,
                    )
                    first_state["individual"] = False
                    with patch.object(PresetManagerDialog, "_refresh"), patch.object(
                        PresetManagerDialog,
                        "_update_source_labels",
                    ):
                        PresetManagerDialog._reload_presets_for_individual_toggle(first_dialog)

                    self.assertEqual(first_dialog._temp, defaults)
                    with patch.object(self.app.hook, "resume_hook_after_dialog"), patch(
                        "keyseq.presentation.dialogs.preset_manager.tk.Toplevel.destroy",
                    ):
                        PresetManagerDialog.destroy(first_dialog)

                    reopened_dialog, reopened_state = self._preset_toggle_dialog(
                        individual_presets,
                        individual=True,
                    )
                    reopened_state["individual"] = False
                    with patch.object(PresetManagerDialog, "_refresh"), patch.object(
                        PresetManagerDialog,
                        "_update_source_labels",
                    ):
                        PresetManagerDialog._reload_presets_for_individual_toggle(reopened_dialog)

                    self.assertEqual(reopened_dialog._temp, defaults)
                    self.assertTrue(
                        self.app.save_hotkey_presets(
                            reopened_dialog._temp,
                            individual=reopened_state["individual"],
                        )
                    )

                self.assertEqual(
                    self.app.config_service.repository.load_json(
                        os.path.join(
                            config_root,
                            self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                        )
                    ),
                    {"hotkey_presets": defaults},
                )
        finally:
            self.app.data = before

    def test_preset_manager_toggle_confirms_only_when_replacement_discards_edits(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        edited_presets = [{"label": "Edited", "value": "ctrl+e"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                self.app.config_service.repository.save_json(
                    os.path.join(
                        config_root,
                        self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                    ),
                    {"hotkey_presets": global_presets},
                )
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, "user", "hotkey_presets", "personal.json"),
                    {"hotkey_presets": individual_presets},
                )
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets_path"] = "user/hotkey_presets/personal.json"

                with patch.object(self.app, "config_root", config_root):
                    no_dialog, no_state = self._preset_toggle_dialog(global_presets, individual=False)
                    no_dialog._temp = copy.deepcopy(edited_presets)
                    no_state["individual"] = True
                    with patch(
                        "keyseq.presentation.dialogs.preset_manager.messagebox.askyesno",
                        return_value=False,
                    ) as askyesno, patch.object(PresetManagerDialog, "_refresh") as refresh, patch.object(
                        PresetManagerDialog,
                        "_update_source_labels",
                    ) as update_labels:
                        PresetManagerDialog._reload_presets_for_individual_toggle(no_dialog)

                    askyesno.assert_called_once()
                    self.assertFalse(no_state["individual"])
                    self.assertEqual(no_dialog._temp, edited_presets)
                    refresh.assert_not_called()
                    update_labels.assert_not_called()

                    yes_dialog, yes_state = self._preset_toggle_dialog(global_presets, individual=False)
                    yes_dialog._temp = copy.deepcopy(edited_presets)
                    yes_state["individual"] = True
                    with patch(
                        "keyseq.presentation.dialogs.preset_manager.messagebox.askyesno",
                        return_value=True,
                    ) as askyesno, patch.object(PresetManagerDialog, "_refresh"), patch.object(
                        PresetManagerDialog,
                        "_update_source_labels",
                    ):
                        PresetManagerDialog._reload_presets_for_individual_toggle(yes_dialog)

                    askyesno.assert_called_once()
                    self.assertEqual(yes_dialog._temp, individual_presets)

                    clean_dialog, clean_state = self._preset_toggle_dialog(global_presets, individual=False)
                    clean_state["individual"] = True
                    with patch(
                        "keyseq.presentation.dialogs.preset_manager.messagebox.askyesno",
                    ) as askyesno, patch.object(PresetManagerDialog, "_refresh"), patch.object(
                        PresetManagerDialog,
                        "_update_source_labels",
                    ):
                        PresetManagerDialog._reload_presets_for_individual_toggle(clean_dialog)

                    askyesno.assert_not_called()
        finally:
            self.app.data = before

    def test_preset_manager_toggle_then_cancel_keeps_runtime_files_and_dirty_unchanged(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                global_path = os.path.join(
                    config_root,
                    self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                )
                individual_path = os.path.join(config_root, "user", "hotkey_presets", "personal.json")
                self.app.config_service.repository.save_json(
                    global_path,
                    {"hotkey_presets": global_presets},
                )
                self.app.config_service.repository.save_json(
                    individual_path,
                    {"hotkey_presets": individual_presets},
                )
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets_path"] = "user/hotkey_presets/personal.json"
                self.app.data["hotkey_presets"] = global_presets
                expected_data = copy.deepcopy(self.app.data)

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app.dirty_tracker,
                    "set_dirty",
                ) as set_dirty:
                    dialog, state = self._preset_toggle_dialog(global_presets, individual=False)
                    state["individual"] = True
                    with patch.object(PresetManagerDialog, "_refresh"), patch.object(
                        PresetManagerDialog,
                        "_update_source_labels",
                    ):
                        PresetManagerDialog._reload_presets_for_individual_toggle(dialog)
                    with patch.object(self.app.hook, "resume_hook_after_dialog"), patch(
                        "keyseq.presentation.dialogs.preset_manager.tk.Toplevel.destroy",
                    ):
                        PresetManagerDialog.destroy(dialog)

                self.assertEqual(dialog._temp, individual_presets)
                self.assertEqual(self.app.data, expected_data)
                self.assertEqual(
                    self.app.config_service.repository.load_json(global_path),
                    {"hotkey_presets": global_presets},
                )
                self.assertEqual(
                    self.app.config_service.repository.load_json(individual_path),
                    {"hotkey_presets": individual_presets},
                )
                set_dirty.assert_not_called()
        finally:
            self.app.data = before

    def test_preset_manager_individual_toggle_is_disabled_for_unsaved_keymap_set(self):
        before = copy.deepcopy(self.app.data)
        keymap_set_path = self.app.keymap_set_path
        try:
            self.app.keymap_set_path = ""
            with patch.object(self.app.hook, "suspend_hook_for_dialog"), patch.object(
                self.app.hook,
                "resume_hook_after_dialog",
            ):
                dialog = PresetManagerDialog(self.app)
                self.addCleanup(dialog.destroy)
                self.assertTrue(dialog.individual_check.instate(["disabled"]))
        finally:
            self.app.data = before
            self.app.keymap_set_path = keymap_set_path

    def test_preset_manager_labels_off_show_global_destination(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                global_path = self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, global_path),
                    {"hotkey_presets": global_presets},
                )
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets_path"] = "user/hotkey_presets/personal.json"
                self.app.data["hotkey_presets"] = [{"label": "Current", "value": "ctrl+c"}]
                keymap_set_path = os.path.join(config_root, "user", "keymap_sets", "main.json")

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app, "keymap_set_path", keymap_set_path
                ), patch.object(self.app.hook, "suspend_hook_for_dialog"), patch.object(
                    self.app.hook, "resume_hook_after_dialog"
                ):
                    dialog = PresetManagerDialog(self.app)
                    try:
                        save_destination = dialog.save_destination_var.get()
                        source = dialog.source_var.get()
                        availability = dialog.individual_unavailable_var.get()
                        displayed_source = dialog._displayed_source
                    finally:
                        dialog.destroy()
        finally:
            self.app.data = before

        self.assertIn(global_path, save_destination)
        self.assertEqual(source, "")
        self.assertEqual(availability, "")
        self.assertEqual(displayed_source, "global")

    def test_preset_manager_labels_on_show_individual_destination(self):
        before = copy.deepcopy(self.app.data)
        individual_path = "user/hotkey_presets/personal.json"
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, individual_path),
                    {"hotkey_presets": individual_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = individual_path
                self.app.data["hotkey_presets"] = individual_presets
                keymap_set_path = os.path.join(config_root, "user", "keymap_sets", "main.json")

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app, "keymap_set_path", keymap_set_path
                ), patch.object(self.app.hook, "suspend_hook_for_dialog"), patch.object(
                    self.app.hook, "resume_hook_after_dialog"
                ):
                    dialog = PresetManagerDialog(self.app)
                    try:
                        save_destination = dialog.save_destination_var.get()
                        source = dialog.source_var.get()
                        availability = dialog.individual_unavailable_var.get()
                        displayed_source = dialog._displayed_source
                    finally:
                        dialog.destroy()
        finally:
            self.app.data = before

        self.assertIn(individual_path, save_destination)
        self.assertEqual(source, "")
        self.assertEqual(availability, "")
        self.assertEqual(displayed_source, "individual")

    def test_preset_manager_labels_external_individual_use_default_destination(self):
        before = copy.deepcopy(self.app.data)
        individual_presets = [{"label": "External", "value": "ctrl+e"}]
        try:
            with tempfile.TemporaryDirectory() as config_root, tempfile.TemporaryDirectory() as outside_root:
                external_path = os.path.join(outside_root, "external.json")
                self.app.config_service.repository.save_json(
                    external_path,
                    {"hotkey_presets": individual_presets},
                )
                self.app.data["hotkey_presets_individual"] = True
                self.app.data["hotkey_presets_path"] = external_path
                self.app.data["hotkey_presets"] = individual_presets
                keymap_set_path = os.path.join(config_root, "user", "keymap_sets", "main.json")

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app, "keymap_set_path", keymap_set_path
                ), patch.object(self.app.hook, "suspend_hook_for_dialog"), patch.object(
                    self.app.hook, "resume_hook_after_dialog"
                ):
                    dialog = PresetManagerDialog(self.app)
                    try:
                        save_destination = dialog.save_destination_var.get()
                        source = dialog.source_var.get()
                        availability = dialog.individual_unavailable_var.get()
                        individual_state = dialog._individual_state
                    finally:
                        dialog.destroy()
        finally:
            self.app.data = before

        self.assertIn("user/hotkey_presets/main.json", save_destination.replace("\\", "/"))
        self.assertIn("config 外", source)
        self.assertEqual(availability, "")
        self.assertEqual(individual_state, "external")

    def test_preset_manager_individual_check_invokes_reload(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [{"label": "Global", "value": "ctrl+g"}]
        individual_path = "user/hotkey_presets/personal.json"
        individual_presets = [{"label": "Individual", "value": "ctrl+i"}]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                self.app.config_service.repository.save_json(
                    os.path.join(
                        config_root,
                        self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                    ),
                    {"hotkey_presets": global_presets},
                )
                self.app.config_service.repository.save_json(
                    os.path.join(config_root, individual_path),
                    {"hotkey_presets": individual_presets},
                )
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets_path"] = individual_path
                self.app.data["hotkey_presets"] = global_presets
                keymap_set_path = os.path.join(config_root, "user", "keymap_sets", "main.json")

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app, "keymap_set_path", keymap_set_path
                ), patch.object(self.app.hook, "suspend_hook_for_dialog"), patch.object(
                    self.app.hook, "resume_hook_after_dialog"
                ):
                    dialog = PresetManagerDialog(self.app)
                    try:
                        dialog.individual_check.invoke()
                        temporary_presets = copy.deepcopy(dialog._temp)
                        individual_enabled = dialog.individual_var.get()
                    finally:
                        dialog.destroy()
        finally:
            self.app.data = before

        self.assertTrue(individual_enabled)
        self.assertEqual(temporary_presets, individual_presets)

    def test_preset_manager_suspends_and_resumes_hook(self):
        with tempfile.TemporaryDirectory() as config_root:
            keymap_set_path = os.path.join(config_root, "user", "keymap_sets", "main.json")
            with patch.object(self.app, "config_root", config_root), patch.object(
                self.app, "keymap_set_path", keymap_set_path
            ):
                wait_for_hook_pause_count(self, self.app, 0)  # 先行テストが残した解除予約を流す
                dialog = PresetManagerDialog(self.app)
                try:
                    self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
                finally:
                    dialog.destroy()
                wait_for_hook_pause_count(self, self.app, 0)

    def test_preset_manager_listbox_matches_temporary_presets(self):
        before = copy.deepcopy(self.app.data)
        global_presets = [
            {"label": "First", "value": "ctrl+1"},
            {"label": "Second", "value": "ctrl+2"},
        ]
        try:
            with tempfile.TemporaryDirectory() as config_root:
                self.app.config_service.repository.save_json(
                    os.path.join(
                        config_root,
                        self.app.config_service.HOTKEY_PRESETS_RELATIVE_PATH,
                    ),
                    {"hotkey_presets": global_presets},
                )
                self.app.data["hotkey_presets_individual"] = False
                self.app.data["hotkey_presets"] = []

                with patch.object(self.app, "config_root", config_root), patch.object(
                    self.app.hook, "suspend_hook_for_dialog"
                ), patch.object(self.app.hook, "resume_hook_after_dialog"):
                    dialog = PresetManagerDialog(self.app)
                    try:
                        temporary_presets = copy.deepcopy(dialog._temp)
                        listbox_items = dialog.listbox.get(0, "end")
                    finally:
                        dialog.destroy()
        finally:
            self.app.data = before

        self.assertEqual(temporary_presets, global_presets)
        self.assertEqual(
            listbox_items,
            ("01. ctrl+1: First", "02. ctrl+2: Second"),
        )

    def test_preset_manager_source_labels_cover_sources_and_unsaved_reason(self):
        off = format_preset_manager_source_labels(
            individual_for_save=False,
            individual_state="off",
            displayed_source="global",
            individual_path="",
            default_individual_path="user/hotkey_presets/main.json",
            global_path="user/hotkey_presets/global/default.json",
            keymap_set_saved=True,
        )
        self.assertEqual(
            off,
            ("保存先: グローバル（user/hotkey_presets/global/default.json）", "", ""),
        )

        active = format_preset_manager_source_labels(
            individual_for_save=True,
            individual_state="active",
            displayed_source="individual",
            individual_path="user/hotkey_presets/main.json",
            default_individual_path="user/hotkey_presets/main.json",
            global_path="user/hotkey_presets/global/default.json",
            keymap_set_saved=True,
        )
        self.assertEqual(active, ("保存先: user/hotkey_presets/main.json", "", ""))

        missing = format_preset_manager_source_labels(
            individual_for_save=True,
            individual_state="missing",
            displayed_source="global",
            individual_path="user/hotkey_presets/main.json",
            default_individual_path="user/hotkey_presets/main.json",
            global_path="user/hotkey_presets/global/default.json",
            keymap_set_saved=True,
        )
        self.assertEqual(missing[1], "グローバルを表示中")

        external = format_preset_manager_source_labels(
            individual_for_save=True,
            individual_state="external",
            displayed_source="individual",
            individual_path="user/hotkey_presets/main.json",
            default_individual_path="user/hotkey_presets/main.json",
            global_path="user/hotkey_presets/global/default.json",
            keymap_set_saved=False,
        )
        self.assertEqual(
            external,
            (
                "保存先: user/hotkey_presets/main.json",
                "config 外のファイルを読み込み中。次の保存で管理下へ移ります。"
                "user/hotkey_presets/main.json へ保存します",
                "構成セットを保存すると専用にできます",
            ),
        )
        self.assertNotIn("無効", external[1])

        external_missing_while_global = format_preset_manager_source_labels(
            individual_for_save=False,
            individual_state="external_missing",
            displayed_source="global",
            individual_path="",
            default_individual_path="user/hotkey_presets/main.json",
            global_path="user/hotkey_presets/global/default.json",
            keymap_set_saved=True,
        )
        self.assertEqual(
            external_missing_while_global[0],
            "保存先: グローバル（user/hotkey_presets/global/default.json）",
        )
        self.assertIn("config 外にあり、読み込めません", external_missing_while_global[1])
        self.assertIn("user/hotkey_presets/main.json", external_missing_while_global[1])
        self.assertIn("専用を再度有効にすると", external_missing_while_global[1])
        self.assertNotIn("無効", external_missing_while_global[1])

        builtin = format_preset_manager_source_labels(
            individual_for_save=True,
            individual_state="missing",
            displayed_source="builtin",
            individual_path="user/hotkey_presets/main.json",
            default_individual_path="user/hotkey_presets/main.json",
            global_path="user/hotkey_presets/global/default.json",
            keymap_set_saved=True,
        )
        self.assertEqual(builtin[1], "読み込めませんでした（既定を表示中）")
        self.assertNotIn("グローバルを表示中", builtin[1])

        global_builtin = format_preset_manager_source_labels(
            individual_for_save=False,
            individual_state="off",
            displayed_source="builtin",
            individual_path="",
            default_individual_path="user/hotkey_presets/main.json",
            global_path="user/hotkey_presets/global/default.json",
            keymap_set_saved=True,
        )
        self.assertEqual(
            global_builtin[1],
            "グローバルを読み込めませんでした。組込既定を表示中"
            "（OK でグローバルを作成します）",
        )

    def test_open_preset_manager_does_not_mark_keymap_set_dirty(self):
        self.app.data["hotkey_presets"] = [{"label": "Before", "value": "ctrl+b"}]
        updated_presets = [{"label": "After", "value": "ctrl+a"}]
        dirty_state_before = self.app.dirty_tracker.has_unsaved_changes()

        with patch.object(self.app.dirty_tracker, "set_dirty") as set_dirty:
            with patch("keyseq.presentation.app.PresetManagerDialog") as dialog_class, patch.object(
                self.app,
                "_set_flash_message",
            ) as set_flash_message:
                dialog_class.return_value.wait_window.side_effect = lambda: self.app.data.__setitem__(
                    "hotkey_presets",
                    updated_presets,
                )
                self.app.open_preset_manager()

        set_dirty.assert_not_called()
        self.assertEqual(dirty_state_before, self.app.dirty_tracker.has_unsaved_changes())
        set_flash_message.assert_called_once_with("プリセットを更新しました。")

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

    def test_failed_keymap_set_save_discards_retained_individual_hook_keys(self):
        with tempfile.TemporaryDirectory() as config_root:
            self._write_global_hook_key_defaults(config_root)
            with patch.object(self.app, "config_root", config_root):
                self._switch_individual_hook_keys_off()
                save_path = os.path.join(config_root, "user", "keymap_sets", "failed.json")
                with patch.object(
                    self.app.keymap_set_io,
                    "_collect_child_save_plan",
                    return_value=(SavePlan(), "", False),
                ), patch.object(
                    self.app.paths, "normalize_keymap_set_save_path", return_value=save_path
                ), patch.object(
                    self.app.keymap_set_io, "choose_split_base_dir_for_keymap_set", return_value=""
                ), patch.object(
                    self.app.config_service, "save_runtime_data", side_effect=OSError("disk full")
                ), patch(
                    "keyseq.presentation.controllers.config_io.keymap_set_io.messagebox.showerror"
                ), patch.object(self.app, "_set_flash_message"):
                    self.assertFalse(
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
        self.app.dirty_tracker.set_dirty(False)

    def test_cancelled_keymap_set_save_retains_individual_hook_keys(self):
        with tempfile.TemporaryDirectory() as config_root:
            self._write_global_hook_key_defaults(config_root)
            with patch.object(self.app, "config_root", config_root):
                self._switch_individual_hook_keys_off()
                save_path = os.path.join(config_root, "user", "keymap_sets", "cancelled.json")
                with patch.object(
                    self.app.keymap_set_io,
                    "_collect_child_save_plan",
                    return_value=(None, "", False),
                ), patch.object(
                    self.app.paths, "normalize_keymap_set_save_path", return_value=save_path
                ), patch.object(
                    self.app.keymap_set_io, "choose_split_base_dir_for_keymap_set", return_value=""
                ), patch.object(self.app.config_service, "save_runtime_data") as save_runtime, patch.object(
                    self.app, "_set_flash_message"
                ):
                    self.assertFalse(
                        self.app.keymap_set_io.save_keymap_set_to(
                            save_path,
                            flash_message="保存しました。",
                            show_success_dialog=False,
                        )
                    )
                save_runtime.assert_not_called()

                self.app.ui_vars.hook_keys_individual_var.set(True)
                self.app.toggle_hook_keys_individual()
                self.assertEqual(self.app.data["hook_stop_key"], "f5")
                self.assertEqual(self.app.data["hook_toggle_key"], "f6")
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
