"""ConfigIoController の構成セット(A)と起動設定(B)の現行挙動を固定する。

task_01（`tests_ui/test_config_io_characterization.py`・C+D/E/F）と対になる安全網②。
期待値は現行実装の実挙動であり、あるべき姿ではない。

設計制約（task_01 と同一・後続の分割 task_04 で壊れないため）:
- patch は `tkinter` モジュール属性 / `config_service`・`paths` などは app に紐づくインスタンス属性へ。
  実装モジュール（config_io_controller）のモジュール変数は patch しない。
- 呼び出し口はアクセサ（`_config_set_io` / `_startup_io`）に集約（task_05 の差し替えに備える）。
- A/B は単一 JSON を直接書かず config_service へ委譲するため、ファイルのバイト列比較ではなく
  コントローラが config_service へ渡す引数（変換ロジック）を assert する。
"""
from __future__ import annotations

import os
import tempfile
import tkinter
import unittest
from unittest.mock import patch

from keyseq.presentation import app as app_module


def _config_set_io(app):
    return app.config_io


def _startup_io(app):
    return app.config_io


class KeymapSetStartupCharacterizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._load_startup_patch = patch.object(
            app_module.ConfigService, "load_startup", return_value={}
        )
        cls._makedirs_patch = patch.object(app_module.os, "makedirs")
        cls._load_startup_patch.start()
        cls._makedirs_patch.start()
        try:
            cls.app = app_module.App()
            cls.app.update_idletasks()
        finally:
            cls._makedirs_patch.stop()
            cls._load_startup_patch.stop()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.app.data = {"keymaps": [], "triggers": [], "active_keymap_id": ""}
        self.app._selected_trigger_idx = 0
        self.app.config_root = os.getcwd()
        self.app.base_dir = os.getcwd()
        self.app.user_root = os.getcwd()
        self.app.keymap_set_path = ""
        self.app.startup_path = ""
        self.app._startup_settings = {}
        self.app.dirty_tracker.trigger_set_source_path = ""
        self.app.dirty_tracker.trigger_set_imported = False
        self.app.dirty_tracker.trigger_set_dirty = False
        self.app.dirty_tracker.is_dirty = False
        self.app.dirty_tracker.config_dirty = False

    # ------- 共通ヘルパ（ダイアログ/flash の記録） -------
    def _record_flash(self, calls):
        return patch.object(
            self.app,
            "_set_flash_message",
            side_effect=lambda message, **kw: calls.append(("flash", message, kw)),
        )

    def _silence_refresh(self):
        # A の各経路が呼ぶ UI refresh を無害化する（副作用を切る）。
        return (
            patch.object(self.app, "_sync_control_vars_from_data"),
            patch.object(self.app.state, "reset_indices"),
            patch.object(self.app.trigger_panel, "refresh_triggers"),
            patch.object(self.app.trigger_panel, "refresh_actions"),
        )

    # ===================== A: confirm_save_if_dirty =====================
    def test_confirm_save_if_dirty_returns_true_without_dialog_when_clean(self):
        with patch.object(self.app.dirty_tracker, "has_unsaved_changes", return_value=False), patch.object(
            tkinter.messagebox, "askyesnocancel"
        ) as ask:
            self.assertTrue(_config_set_io(self.app).confirm_save_if_dirty("新規作成"))
            ask.assert_not_called()

    def test_confirm_save_if_dirty_cancel_returns_false(self):
        with patch.object(self.app.dirty_tracker, "has_unsaved_changes", return_value=True), patch.object(
            tkinter.messagebox, "askyesnocancel", return_value=None
        ) as ask:
            self.assertFalse(_config_set_io(self.app).confirm_save_if_dirty("読込"))
            ask.assert_called_once_with(
                "未保存の変更",
                "未保存の変更があります。\n読込の前に保存しますか？",
            )

    def test_confirm_save_if_dirty_no_returns_true_without_saving(self):
        with patch.object(self.app.dirty_tracker, "has_unsaved_changes", return_value=True), patch.object(
            tkinter.messagebox, "askyesnocancel", return_value=False
        ), patch.object(_config_set_io(self.app), "save_keymap_set") as save, patch.object(
            _config_set_io(self.app), "save_as"
        ) as save_as:
            self.assertTrue(_config_set_io(self.app).confirm_save_if_dirty("読込"))
            save.assert_not_called()
            save_as.assert_not_called()

    def test_confirm_save_if_dirty_yes_with_path_uses_save_keymap_set(self):
        self.app.keymap_set_path = "X.json"
        with patch.object(self.app.dirty_tracker, "has_unsaved_changes", return_value=True), patch.object(
            tkinter.messagebox, "askyesnocancel", return_value=True
        ), patch.object(_config_set_io(self.app), "save_keymap_set", return_value=True) as save, patch.object(
            _config_set_io(self.app), "save_as", return_value=True
        ) as save_as:
            self.assertTrue(_config_set_io(self.app).confirm_save_if_dirty("読込"))
            save.assert_called_once_with(show_success_dialog=False)
            save_as.assert_not_called()

    def test_confirm_save_if_dirty_yes_without_path_uses_save_as(self):
        self.app.keymap_set_path = ""
        with patch.object(self.app.dirty_tracker, "has_unsaved_changes", return_value=True), patch.object(
            tkinter.messagebox, "askyesnocancel", return_value=True
        ), patch.object(_config_set_io(self.app), "save_keymap_set", return_value=True) as save, patch.object(
            _config_set_io(self.app), "save_as", return_value=True
        ) as save_as:
            self.assertTrue(_config_set_io(self.app).confirm_save_if_dirty("読込"))
            save_as.assert_called_once_with(show_success_dialog=False)
            save.assert_not_called()

    # ===================== A: save_keymap_set_to =====================
    def test_save_keymap_set_to_success_updates_state(self):
        calls = []
        with patch.object(self.app.paths, "normalize_keymap_set_save_path", side_effect=lambda p: p), patch.object(
            _config_set_io(self.app), "choose_split_base_dir_for_keymap_set", return_value=""
        ), patch.object(
            self.app.config_service, "save_runtime_data", return_value=({"saved": True}, {"payload": 1})
        ) as save_runtime, patch.object(
            self.app.paths, "preferred_startup_path", return_value="startup.json"
        ), patch.object(self.app.dirty_tracker, "clear_individual_dirty_flags") as clear_flags, patch.object(
            self.app.dirty_tracker, "set_dirty"
        ) as set_dirty, self._record_flash(calls), patch.object(
            tkinter.messagebox, "showinfo"
        ) as showinfo:
            ok = _config_set_io(self.app).save_keymap_set_to(
                "out.json", flash_message="保存しました。", show_success_dialog=True
            )
        self.assertTrue(ok)
        save_runtime.assert_called_once()
        self.assertEqual(self.app.keymap_set_path, "out.json")
        self.assertEqual(self.app.data, {"saved": True})
        self.assertEqual(self.app._startup_settings, {"payload": 1})
        clear_flags.assert_called_once_with()
        set_dirty.assert_called_once_with(False)
        self.assertIn(("flash", "保存しました。", {}), calls)
        showinfo.assert_called_once()

    def test_save_keymap_set_to_no_success_dialog(self):
        with patch.object(self.app.paths, "normalize_keymap_set_save_path", side_effect=lambda p: p), patch.object(
            _config_set_io(self.app), "choose_split_base_dir_for_keymap_set", return_value=""
        ), patch.object(
            self.app.config_service, "save_runtime_data", return_value=({}, {})
        ), patch.object(
            self.app.paths, "preferred_startup_path", return_value="startup.json"
        ), patch.object(self.app.dirty_tracker, "clear_individual_dirty_flags"), patch.object(
            self.app.dirty_tracker, "set_dirty"
        ), patch.object(self.app, "_set_flash_message"), patch.object(
            tkinter.messagebox, "showinfo"
        ) as showinfo:
            ok = _config_set_io(self.app).save_keymap_set_to(
                "out.json", flash_message="保存しました。", show_success_dialog=False
            )
        self.assertTrue(ok)
        showinfo.assert_not_called()

    def test_save_keymap_set_to_exception_keeps_dirty(self):
        calls = []
        with patch.object(self.app.paths, "normalize_keymap_set_save_path", side_effect=lambda p: p), patch.object(
            _config_set_io(self.app), "choose_split_base_dir_for_keymap_set", return_value=""
        ), patch.object(
            self.app.config_service, "save_runtime_data", side_effect=OSError("disk full")
        ), patch.object(self.app.dirty_tracker, "set_dirty") as set_dirty, self._record_flash(calls), patch.object(
            tkinter.messagebox, "showerror"
        ) as showerror:
            ok = _config_set_io(self.app).save_keymap_set_to(
                "out.json", flash_message="保存しました。", show_success_dialog=True
            )
        self.assertFalse(ok)
        self.assertEqual(calls, [("flash", "保存失敗: disk full", {"auto_clear": False})])
        showerror.assert_called_once()
        set_dirty.assert_not_called()

    # ===================== A: choose_split_base_dir_for_keymap_set =====================
    def test_choose_split_base_dir_within_config_root_returns_empty(self):
        with patch.object(self.app.paths, "is_within_config_root", return_value=True), patch.object(
            tkinter.messagebox, "askyesno"
        ) as ask:
            self.assertEqual(
                _config_set_io(self.app).choose_split_base_dir_for_keymap_set("x.json"), ""
            )
            ask.assert_not_called()

    def test_choose_split_base_dir_outside_yes_returns_dir(self):
        target = os.path.join(os.getcwd(), "sub", "x.json")
        with patch.object(self.app.paths, "is_within_config_root", return_value=False), patch.object(
            tkinter.messagebox, "askyesno", return_value=True
        ):
            self.assertEqual(
                _config_set_io(self.app).choose_split_base_dir_for_keymap_set(target),
                os.path.dirname(os.path.abspath(target)),
            )

    def test_choose_split_base_dir_outside_no_returns_empty(self):
        with patch.object(self.app.paths, "is_within_config_root", return_value=False), patch.object(
            tkinter.messagebox, "askyesno", return_value=False
        ):
            self.assertEqual(
                _config_set_io(self.app).choose_split_base_dir_for_keymap_set("x.json"), ""
            )

    # ===================== A: load_keymap_set_from =====================
    def test_load_keymap_set_from_confirm_false_early_return(self):
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=False), patch.object(
            tkinter.filedialog, "askopenfilename"
        ) as ask:
            self.assertIsNone(_config_set_io(self.app).load_keymap_set_from())
            ask.assert_not_called()

    def test_load_keymap_set_from_empty_path_returns(self):
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value=""
        ), patch.object(self.app.config_service, "load_runtime_data_from_keymap_set_path") as load:
            self.assertIsNone(_config_set_io(self.app).load_keymap_set_from())
            load.assert_not_called()

    def test_load_keymap_set_from_success(self):
        calls = []
        patches = self._silence_refresh()
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="in.json"
        ), patch.object(
            self.app.config_service, "load_runtime_data_from_keymap_set_path", return_value={"loaded": True}
        ), patch.object(_config_set_io(self.app), "apply_loaded_data_to_ui") as apply_ui, patch.object(
            self.app.dirty_tracker, "set_dirty"
        ) as set_dirty, self._record_flash(calls), patch.object(
            tkinter.messagebox, "showinfo"
        ) as showinfo, patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).load_keymap_set_from()
        self.assertEqual(self.app.data, {"loaded": True})
        self.assertEqual(self.app.keymap_set_path, "in.json")
        apply_ui.assert_called_once_with()
        set_dirty.assert_called_once_with(False)
        self.assertIn(("flash", "読み込みました。", {}), calls)
        showinfo.assert_called_once()

    def test_load_keymap_set_from_exception(self):
        calls = []
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="in.json"
        ), patch.object(
            self.app.config_service, "load_runtime_data_from_keymap_set_path", side_effect=ValueError("bad")
        ), self._record_flash(calls), patch.object(tkinter.messagebox, "showerror") as showerror:
            _config_set_io(self.app).load_keymap_set_from()
        self.assertEqual(calls, [("flash", "読込失敗: bad", {"auto_clear": False})])
        showerror.assert_called_once()

    # ===================== A: new_config / import / export / restore =====================
    def test_new_config_confirm_false_early_return(self):
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=False), patch.object(
            self.app.config_service, "new_default_data"
        ) as new_default:
            _config_set_io(self.app).new_config()
            new_default.assert_not_called()

    def test_new_config_success(self):
        calls = []
        patches = self._silence_refresh()
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            self.app.config_service, "new_default_data", return_value={"d": 1}
        ), patch.object(
            self.app.config_service, "normalize_runtime_data", side_effect=lambda d: d
        ), patch.object(self.app.paths, "preferred_keymap_set_path", return_value="k.json"), patch.object(
            self.app.dirty_tracker, "set_dirty"
        ) as set_dirty, self._record_flash(calls), patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).new_config()
        self.assertEqual(self.app.keymap_set_path, "k.json")
        self.assertEqual(self.app.data.get("triggers"), [])
        set_dirty.assert_called_once_with(True)
        self.assertIn(("flash", "新規作成しました（未保存）。", {}), calls)

    def test_import_config_confirm_false_early_return(self):
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=False), patch.object(
            tkinter.filedialog, "askopenfilename"
        ) as ask, patch.object(self.app.config_service, "load_legacy_runtime_data") as load:
            _config_set_io(self.app).import_config()
            ask.assert_not_called()
            load.assert_not_called()

    def test_import_config_empty_path_returns(self):
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value=""
        ), patch.object(self.app.config_service, "load_legacy_runtime_data") as load:
            _config_set_io(self.app).import_config()
            load.assert_not_called()

    def test_import_config_success(self):
        calls = []
        patches = self._silence_refresh()
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="legacy.json"
        ), patch.object(
            self.app.config_service, "load_legacy_runtime_data", return_value={"legacy": True}
        ), patch.object(_config_set_io(self.app), "apply_loaded_data_to_ui"), patch.object(
            self.app.paths, "preferred_keymap_set_path", return_value="k.json"
        ), patch.object(self.app.dirty_tracker, "set_dirty") as set_dirty, self._record_flash(calls), patch.object(
            tkinter.messagebox, "showinfo"
        ) as showinfo, patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).import_config()
        self.assertEqual(self.app.data, {"legacy": True})
        set_dirty.assert_called_once_with(True)
        showinfo.assert_called_once()

    def test_import_config_exception(self):
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="legacy.json"
        ), patch.object(
            self.app.config_service, "load_legacy_runtime_data", side_effect=ValueError("bad")
        ), patch.object(self.app, "_set_flash_message"), patch.object(
            tkinter.messagebox, "showerror"
        ) as showerror:
            _config_set_io(self.app).import_config()
            showerror.assert_called_once()

    def test_export_config_empty_path_returns(self):
        with patch.object(tkinter.filedialog, "asksaveasfilename", return_value=""), patch.object(
            self.app.config_service, "export_runtime_data"
        ) as export:
            _config_set_io(self.app).export_config()
            export.assert_not_called()

    def test_export_config_success(self):
        with patch.object(tkinter.filedialog, "asksaveasfilename", return_value="out.json"), patch.object(
            self.app.config_service, "export_runtime_data"
        ) as export, patch.object(self.app, "_set_flash_message"), patch.object(
            tkinter.messagebox, "showinfo"
        ) as showinfo:
            _config_set_io(self.app).export_config()
            export.assert_called_once()
            showinfo.assert_called_once()

    def test_export_config_exception(self):
        with patch.object(tkinter.filedialog, "asksaveasfilename", return_value="out.json"), patch.object(
            self.app.config_service, "export_runtime_data", side_effect=OSError("no")
        ), patch.object(self.app, "_set_flash_message"), patch.object(
            tkinter.messagebox, "showerror"
        ) as showerror:
            _config_set_io(self.app).export_config()
            showerror.assert_called_once()

    def test_restore_default_no_does_nothing(self):
        with patch.object(tkinter.messagebox, "askyesno", return_value=False), patch.object(
            self.app.config_service, "new_default_data"
        ) as new_default:
            _config_set_io(self.app).restore_default()
            new_default.assert_not_called()

    def test_restore_default_yes(self):
        calls = []
        patches = self._silence_refresh()
        with patch.object(tkinter.messagebox, "askyesno", return_value=True), patch.object(
            self.app.config_service, "new_default_data", return_value={"d": 1}
        ), patch.object(self.app.dirty_tracker, "set_dirty") as set_dirty, self._record_flash(calls), patches[
            0
        ], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).restore_default()
        self.assertEqual(self.app.data, {"d": 1})
        set_dirty.assert_called_once_with(True)

    # ===================== A: set_startup_keymap_set =====================
    def test_set_startup_keymap_set_confirm_false_early_return(self):
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=False), patch.object(
            tkinter.filedialog, "askopenfilename"
        ) as ask:
            _config_set_io(self.app).set_startup_keymap_set()
            ask.assert_not_called()

    def test_set_startup_keymap_set_load_exception_early_return(self):
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="k.json"
        ), patch.object(
            self.app.config_service, "load_runtime_data_from_keymap_set_path", side_effect=ValueError("bad")
        ), patch.object(_config_set_io(self.app), "write_startup") as write_startup, patch.object(
            tkinter.messagebox, "showerror"
        ) as showerror:
            _config_set_io(self.app).set_startup_keymap_set()
            showerror.assert_called_once()
            write_startup.assert_not_called()  # 読込例外時は後続を実行しない

    def test_set_startup_keymap_set_continues_after_write_startup_save_failure(self):
        # 現挙動: write_startup 内で save 失敗を握りつぶした後も、
        # データ適用・dirty 解除・成功 showinfo を続行する（暫定仕様 §7-2）。
        calls = []
        patches = self._silence_refresh()
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="k.json"
        ), patch.object(
            self.app.config_service, "load_runtime_data_from_keymap_set_path", return_value={"loaded": True}
        ), patch.object(self.app.paths, "to_config_relative_or_absolute", side_effect=lambda p: p), patch.object(
            self.app.paths, "preferred_startup_path", return_value="startup.json"
        ), patch.object(
            self.app.config_service, "save_startup", side_effect=OSError("disk full")
        ), patch.object(_config_set_io(self.app), "apply_loaded_data_to_ui") as apply_ui, patch.object(
            self.app.dirty_tracker, "set_dirty"
        ) as set_dirty, self._record_flash(calls), patch.object(
            tkinter.messagebox, "showerror"
        ) as showerror, patch.object(tkinter.messagebox, "showinfo") as showinfo, patches[0], patches[
            1
        ], patches[2], patches[3]:
            _config_set_io(self.app).set_startup_keymap_set()
        # write_startup 内の保存失敗は showerror で握りつぶされる
        showerror.assert_called_once()
        # だが後続は続行する
        self.assertEqual(self.app.data, {"loaded": True})
        self.assertEqual(self.app.keymap_set_path, "k.json")
        apply_ui.assert_called_once_with()
        set_dirty.assert_called_once_with(False)
        self.assertIn(("flash", "起動時読み込み設定を更新しました。", {}), calls)
        showinfo.assert_called_once()

    # ===================== B: write_startup =====================
    def test_write_startup_merges_defaults_current_and_arg(self):
        self.app._startup_settings = {"last_used_directory": "D", "keymap_set_path": "X.json"}
        saved = {}
        with patch.object(self.app.paths, "preferred_startup_path", return_value="startup.json"), patch.object(
            self.app.config_service, "save_startup", side_effect=lambda path, base: saved.update({"path": path, "base": dict(base)})
        ):
            _startup_io(self.app).write_startup({"ui_font_delta_pt": 2})
        self.assertEqual(
            saved["base"],
            {
                "prompt_if_missing": True,
                "ui_font_delta_pt": 2,
                "last_used_directory": "D",
                "keymap_set_path": "X.json",
            },
        )
        self.assertEqual(self.app._startup_settings, saved["base"])

    def test_write_startup_drops_config_path_and_coerces_font_delta(self):
        self.app._startup_settings = {"config_path": "should_be_removed"}
        saved = {}
        with patch.object(self.app.paths, "preferred_startup_path", return_value="startup.json"), patch.object(
            self.app.config_service, "save_startup", side_effect=lambda path, base: saved.update({"base": dict(base)})
        ):
            _startup_io(self.app).write_startup({"ui_font_delta_pt": 99})
        self.assertNotIn("config_path", saved["base"])
        self.assertEqual(saved["base"]["ui_font_delta_pt"], 3)  # -3..+3 にクランプ

    def test_write_startup_save_failure_is_swallowed(self):
        with patch.object(self.app.paths, "preferred_startup_path", return_value="startup.json"), patch.object(
            self.app.config_service, "save_startup", side_effect=OSError("no disk")
        ), patch.object(tkinter.messagebox, "showerror") as showerror:
            # 例外を raise しない（握りつぶす）
            _startup_io(self.app).write_startup({"ui_font_delta_pt": 0})
            showerror.assert_called_once()

    # ===================== B: load_startup_and_config =====================
    def test_load_startup_and_config_loads_when_stored_path_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            existing = os.path.join(directory, "k.json")
            with open(existing, "w", encoding="utf-8") as f:
                f.write("{}")
            self.app._startup_settings = {"keymap_set_path": existing}
            with patch.object(self.app.paths, "preferred_keymap_set_path", return_value="default.json"), patch.object(
                self.app.paths, "resolve_keymap_set_path", return_value=existing
            ), patch.object(
                self.app.config_service, "load_runtime_data_from_keymap_set_path", return_value={"loaded": True}
            ) as load, patch.object(_startup_io(self.app), "apply_loaded_data_to_ui") as apply_ui, patch.object(
                self.app.config_service, "new_empty_data"
            ) as new_empty:
                _startup_io(self.app).load_startup_and_config()
            self.assertEqual(self.app.data, {"loaded": True})
            self.assertEqual(self.app.keymap_set_path, existing)
            apply_ui.assert_called_once_with()
            new_empty.assert_not_called()
            load.assert_called_once()

    def test_load_startup_and_config_empty_when_stored_path_missing(self):
        missing = os.path.join(tempfile.gettempdir(), "definitely_absent_keymap_set_xyz.json")
        self.app._startup_settings = {"keymap_set_path": missing}
        with patch.object(self.app.paths, "preferred_keymap_set_path", return_value="default.json"), patch.object(
            self.app.paths, "resolve_keymap_set_path", return_value=missing
        ), patch.object(self.app.config_service, "new_empty_data", return_value={"empty": True}), patch.object(
            _startup_io(self.app), "apply_loaded_data_to_ui"
        ) as apply_ui:
            _startup_io(self.app).load_startup_and_config()
        self.assertEqual(self.app.data, {"empty": True})
        self.assertEqual(self.app.keymap_set_path, "default.json")
        apply_ui.assert_called_once_with()

    def test_load_startup_and_config_swallows_load_exception_and_falls_back(self):
        # 現挙動: 実在パスの読込が例外でも except: pass で握りつぶし、空データ起動へ（:261-262）。
        with tempfile.TemporaryDirectory() as directory:
            existing = os.path.join(directory, "k.json")
            with open(existing, "w", encoding="utf-8") as f:
                f.write("{}")
            self.app._startup_settings = {"keymap_set_path": existing}
            with patch.object(self.app.paths, "preferred_keymap_set_path", return_value="default.json"), patch.object(
                self.app.paths, "resolve_keymap_set_path", return_value=existing
            ), patch.object(
                self.app.config_service, "load_runtime_data_from_keymap_set_path", side_effect=ValueError("corrupt")
            ), patch.object(
                self.app.config_service, "new_empty_data", return_value={"empty": True}
            ), patch.object(_startup_io(self.app), "apply_loaded_data_to_ui"):
                _startup_io(self.app).load_startup_and_config()
            # 例外は握りつぶされ、空データにフォールバックする
            self.assertEqual(self.app.data, {"empty": True})


if __name__ == "__main__":
    unittest.main()
