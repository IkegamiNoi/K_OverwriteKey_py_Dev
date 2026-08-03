"""ConfigIoController の構成セット(A)と起動設定(B)の現行挙動を固定する。

task_01（`tests_ui/test_config_io_characterization.py`・C+D/E/F）と対になる安全網②。
期待値は現行実装の実挙動であり、あるべき姿ではない。

設計制約（task_01 と同一）:
- patch は `tkinter` モジュール属性 / `config_service`・`paths` などは app に紐づくインスタンス属性へ。
  実装モジュールのモジュール変数は patch しない。
- 呼び出し口はアクセサ（`_config_set_io` / `_startup_io`）に集約。task_05 でファサードを削除したため、
  アクセサは分割オブジェクト（`app.keymap_set_io` / `app.startup_io`）を返す。
- A/B は単一 JSON を直接書かず config_service へ委譲するため、ファイルのバイト列比較ではなく
  コントローラが config_service へ渡す引数（変換ロジック）を assert する。
"""
from __future__ import annotations

import os
import tempfile
import tkinter
import unittest
from unittest.mock import patch

from keyseq.application.save_plan import (
    ACTION_SAVE,
    ACTION_SAVE_AS,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
)
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io import child_save_dialog as child_save_dialog_module


def _unexpected_trigger_set_dependency(*_args, **_kwargs):
    raise AssertionError(
        "想定外の依存確認ダイアログ。期待するならテスト側で patch すること"
    )


def _unexpected_recalculated_overwrite(*_args, **_kwargs):
    raise AssertionError(
        "想定外の再計算後上書き確認。期待するならテスト側で patch すること"
    )


def _unexpected_showerror(_title, message, *_args, **_kwargs):
    raise AssertionError(f"想定外のエラーダイアログ: {message}")


def _config_set_io(app):
    # A/A' は KeymapSetIo（task_04 で分割）。task_05 でファサードを削除し App が直接公開する。
    # 同一クラスタ内メソッド（confirm_save_if_dirty / save_keymap_set / apply_loaded_data_to_ui 等）を
    # self. で呼ぶため、分割オブジェクトを返して patch が内部呼び出しを intercept できるようにする。
    # クロスモジュール呼び出し（write_startup=StartupIo / apply=KeymapSetIo）は所有オブジェクトを直接 patch する。
    return app.keymap_set_io


def _startup_io(app):
    return app.startup_io


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
        self._dependency_confirm_guard = patch.object(
            child_save_dialog_module.ChildSaveDialog,
            "confirm_trigger_set_dependency",
            side_effect=_unexpected_trigger_set_dependency,
        )
        self._recalculated_overwrite_guard = patch.object(
            child_save_dialog_module.ChildSaveDialog,
            "confirm_recalculated_overwrite",
            side_effect=_unexpected_recalculated_overwrite,
        )
        self._showerror_guard = patch.object(
            tkinter.messagebox,
            "showerror",
            side_effect=_unexpected_showerror,
        )
        self._dependency_confirm_guard.start()
        self._recalculated_overwrite_guard.start()
        self._showerror_guard.start()
        self.addCleanup(self._dependency_confirm_guard.stop)
        self.addCleanup(self._recalculated_overwrite_guard.stop)
        self.addCleanup(self._showerror_guard.stop)
        self.app.data = {"keymaps": [], "triggers": [], "active_keymap_id": ""}
        self.app._selected_trigger_idx = 0
        self.app.config_root = os.getcwd()
        self.app.base_dir = os.getcwd()
        self.app.user_root = os.getcwd()
        self.app.keymap_set_path = ""
        self.app.startup_path = ""
        self.app._startup_settings = {}
        self.app.dirty_tracker.set_trigger_set_source_path("")
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

    def _prepare_loaded_keymap_set(self, root):
        path = os.path.join(root, "user", "keymap_sets", "loaded.json")
        old_data = self.app.config_service.new_default_data()
        # 個別指定 ON でなければ hook キーは保存時に空文字化される（phase 07 task_03）。
        old_data["hook_keys_individual"] = True
        old_data["hook_stop_key"] = "f12"
        old_data["triggers"][0]["actions"] = [{"type": "text", "value": "old-f1"}]
        old_data["triggers"][1]["actions"] = [{"type": "text", "value": "old-f2"}]
        self.app.config_root = root
        self.app.data, self.app._startup_settings = self.app.config_service.save_runtime_data(
            path,
            old_data,
            config_root=root,
            startup_data={},
        )
        targets = self.app.config_service.resolve_child_save_targets(
            self.app.data,
            config_root=root,
            keymap_set_path=path,
        )
        self.app.data = self.app.config_service.load_runtime_data_from_keymap_set_path(
            path,
            config_root=root,
        )
        self.app.keymap_set_path = path
        _config_set_io(self.app).apply_loaded_data_to_ui()
        self.app.dirty_tracker.clear_individual_dirty_flags()
        self.app.dirty_tracker.set_dirty(False)
        return path, targets

    @staticmethod
    def _default_child_choices(rows, root):
        choices = {}
        for row in rows:
            if row.default_action == ACTION_SAVE_AS:
                choices[(row.kind, row.key)] = (
                    ACTION_SAVE_AS,
                    os.path.join(root, "copies", f"{row.key}.json"),
                )
            else:
                choices[(row.kind, row.key)] = (ACTION_SAVE, "")
        return choices

    def _save_restored_as(self, root, path):
        rows_seen = []

        def choose_actions(rows):
            rows_seen.extend(rows)
            return self._default_child_choices(rows, root)

        with patch.object(
            self.app.paths, "normalize_keymap_set_save_path", side_effect=lambda value: value
        ), patch.object(
            _config_set_io(self.app), "choose_split_base_dir_for_keymap_set", return_value=""
        ), patch.object(
            tkinter.filedialog, "asksaveasfilename", return_value=path
        ) as ask, patch.object(
            self.app.child_save_dialog, "ask_child_save_actions", side_effect=choose_actions
        ), patch.object(tkinter.messagebox, "showinfo"):
            self.assertTrue(_config_set_io(self.app).save_keymap_set(show_success_dialog=False))
        return ask, rows_seen

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
        # 保存確認の分岐だけを固定するため、子保存ダイアログを含む下流の保存経路は意図的に迂回する。
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
        # 保存確認の分岐だけを固定するため、子保存ダイアログを含む下流の保存経路は意図的に迂回する。
        with patch.object(self.app.dirty_tracker, "has_unsaved_changes", return_value=True), patch.object(
            tkinter.messagebox, "askyesnocancel", return_value=True
        ), patch.object(_config_set_io(self.app), "save_keymap_set", return_value=True) as save, patch.object(
            _config_set_io(self.app), "save_as", return_value=True
        ) as save_as:
            self.assertTrue(_config_set_io(self.app).confirm_save_if_dirty("読込"))
            save_as.assert_called_once_with(show_success_dialog=False)
            save.assert_not_called()

    def test_save_keymap_set_empty_path_delegates_to_save_as(self):
        # 保存先ルーティングだけを固定するため、子保存ダイアログを含む下流の保存経路は意図的に迂回する。
        with patch.object(_config_set_io(self.app), "save_as", return_value=True) as save_as, patch.object(
            _config_set_io(self.app), "save_keymap_set_to"
        ) as save_to:
            self.assertTrue(_config_set_io(self.app).save_keymap_set(show_success_dialog=False))
        save_as.assert_called_once_with(show_success_dialog=False)
        save_to.assert_not_called()

    def test_save_keymap_set_nonempty_path_saves_to_current_path(self):
        self.app.keymap_set_path = "current.json"
        # 保存先ルーティングだけを固定するため、子保存ダイアログを含む下流の保存経路は意図的に迂回する。
        with patch.object(_config_set_io(self.app), "save_as") as save_as, patch.object(
            _config_set_io(self.app), "save_keymap_set_to", return_value=True
        ) as save_to:
            self.assertTrue(_config_set_io(self.app).save_keymap_set(show_success_dialog=False))
        save_to.assert_called_once_with(
            "current.json",
            flash_message="保存しました。",
            show_success_dialog=False,
        )
        save_as.assert_not_called()

    def test_save_as_empty_path_uses_default_initialfile(self):
        with patch.object(self.app, "suggest_keymap_set_dialog_path", return_value="default.json"), patch.object(
            self.app, "suggest_keymap_set_dialog_dir", return_value="config"
        ), patch.object(tkinter.filedialog, "asksaveasfilename", return_value="") as ask:
            self.assertFalse(_config_set_io(self.app).save_as())
        self.assertEqual(ask.call_args.kwargs["initialfile"], "keymap_set.json")

    def test_save_as_nonempty_path_uses_current_filename_initialfile(self):
        self.app.keymap_set_path = "current.json"
        with patch.object(self.app, "suggest_keymap_set_dialog_path", return_value="directory/current.json"), patch.object(
            self.app, "suggest_keymap_set_dialog_dir", return_value="directory"
        ), patch.object(tkinter.filedialog, "asksaveasfilename", return_value="") as ask:
            self.assertFalse(_config_set_io(self.app).save_as())
        self.assertEqual(ask.call_args.kwargs["initialfile"], "current.json")

    # ===================== A: save_keymap_set_to =====================
    def test_save_keymap_set_to_success_updates_state(self):
        calls = []
        # 空の fake data では dirty な子が無く、子保存ダイアログは対象外として保存後状態を固定する。
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
        # 空の fake data では dirty な子が無く、子保存ダイアログは対象外として成功通知だけを確認する。
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
        # 空の fake data では dirty な子が無く、子保存ダイアログは対象外として失敗時の状態を固定する。
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
        showerror.assert_called_once_with("保存失敗", "disk full")
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
        showerror.assert_called_once_with("読込失敗", "bad")

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
        ), patch.object(self.app.dirty_tracker, "set_dirty"
        ) as set_dirty, self._record_flash(calls), patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).new_config()
        self.assertEqual(self.app.keymap_set_path, "")
        self.assertEqual(self.app.data.get("triggers"), [])
        set_dirty.assert_called_once_with(True)
        self.assertIn(("flash", "新規作成しました（未保存）。", {}), calls)

    def test_new_config_resets_trigger_set_state_and_runtime_data(self):
        previous_path = "C:/previous/triggers.json"
        self.app.dirty_tracker.set_trigger_set_source_path(previous_path)
        self.app.dirty_tracker.trigger_set_imported = True
        self.app.dirty_tracker.mark_trigger_set_dirty()
        patches = self._silence_refresh()

        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            self.app, "_set_flash_message"
        ), patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).new_config()

        self.assertEqual(self.app.dirty_tracker.trigger_set_source_path, "")
        self.assertNotIn(
            self.app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH,
            self.app.data,
        )
        self.assertFalse(self.app.dirty_tracker.trigger_set_dirty)
        self.assertFalse(self.app.dirty_tracker.trigger_set_imported)

    def test_new_config_then_save_reaches_save_as_dialog(self):
        selected_path = "directory/saved.json"
        calls = []
        patches = self._silence_refresh()
        # 親 keymap_set の別名保存ダイアログだけを固定するため、子保存ダイアログを含む下流は意図的に迂回する。
        with patch.object(self.app.config_service, "new_default_data", return_value={"d": 1}), patch.object(
            self.app.config_service, "normalize_runtime_data", side_effect=lambda d: d
        ), patch.object(self.app.dirty_tracker, "set_dirty"), self._record_flash(calls), patches[0], patches[1], patches[2], patches[3], patch.object(
            self.app, "suggest_keymap_set_dialog_path", return_value="default.json"
        ), patch.object(self.app, "suggest_keymap_set_dialog_dir", return_value="config"), patch.object(
            tkinter.filedialog, "asksaveasfilename", return_value=selected_path
        ) as ask, patch.object(
            _config_set_io(self.app), "save_keymap_set_to", return_value=True
        ) as save_to:
            _config_set_io(self.app).new_config()
            self.assertEqual(self.app.keymap_set_path, "")
            self.assertTrue(_config_set_io(self.app).save_keymap_set(show_success_dialog=False))

        self.assertIn(("flash", "新規作成しました（未保存）。", {}), calls)
        ask.assert_called_once()
        self.assertEqual(ask.call_args.kwargs["initialfile"], "keymap_set.json")
        save_to.assert_called_once_with(
            selected_path,
            flash_message="別名で保存しました。",
            show_success_dialog=False,
        )

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
            self.app.dirty_tracker, "set_dirty"
        ) as set_dirty, self._record_flash(calls), patch.object(
            tkinter.messagebox, "showinfo"
        ) as showinfo, patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).import_config()
        self.assertEqual(self.app.data, {"legacy": True})
        self.assertEqual(self.app.keymap_set_path, "")
        set_dirty.assert_called_once_with(True)
        showinfo.assert_called_once()

    def test_import_config_success_clears_nonempty_keymap_set_path(self):
        self.app.keymap_set_path = "current.json"
        patches = self._silence_refresh()
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="legacy.json"
        ), patch.object(
            self.app.config_service, "load_legacy_runtime_data", return_value={"legacy": True}
        ), patch.object(_config_set_io(self.app), "apply_loaded_data_to_ui"), patch.object(
            self.app.dirty_tracker, "set_dirty"
        ), patch.object(self.app, "_set_flash_message"), patch.object(
            tkinter.messagebox, "showinfo"
        ), patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).import_config()
        self.assertEqual(self.app.keymap_set_path, "")

    def test_import_config_exception(self):
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="legacy.json"
        ), patch.object(
            self.app.config_service, "load_legacy_runtime_data", side_effect=ValueError("bad")
        ), patch.object(self.app, "_set_flash_message"), patch.object(
            tkinter.messagebox, "showerror"
        ) as showerror:
            _config_set_io(self.app).import_config()
            showerror.assert_called_once_with("Import 失敗", "bad")

    def test_import_config_exception_preserves_nonempty_keymap_set_path(self):
        self.app.keymap_set_path = "current.json"
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="legacy.json"
        ), patch.object(
            self.app.config_service, "load_legacy_runtime_data", side_effect=ValueError("bad")
        ), patch.object(self.app, "_set_flash_message"), patch.object(
            tkinter.messagebox, "showerror"
        ) as showerror:
            _config_set_io(self.app).import_config()
        self.assertEqual(self.app.keymap_set_path, "current.json")
        showerror.assert_called_once_with("Import 失敗", "bad")

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
            showerror.assert_called_once_with("Export 失敗", "no")

    def test_restore_default_no_does_nothing(self):
        with patch.object(tkinter.messagebox, "askyesnocancel", return_value=False) as ask_save, patch.object(
            tkinter.messagebox, "askyesno", return_value=False
        ), patch.object(
            self.app.config_service, "new_default_data"
        ) as new_default:
            _config_set_io(self.app).restore_default()
            new_default.assert_not_called()
        ask_save.assert_not_called()

    def test_restore_default_yes(self):
        calls = []
        patches = self._silence_refresh()
        with patch.object(tkinter.messagebox, "askyesnocancel", return_value=False), patch.object(
            tkinter.messagebox, "askyesno", return_value=True
        ), patch.object(
            self.app.config_service, "new_default_data", return_value={"d": 1}
        ), patch.object(
            self.app.dirty_tracker,
            "set_dirty",
            wraps=self.app.dirty_tracker.set_dirty,
        ) as set_dirty, self._record_flash(calls), patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).restore_default()
        # 既定に戻した直後に hook キーの全体デフォルトが注入される（phase 07 task_02）。
        # config.json に全体デフォルトが無いため空文字で入る。
        self.assertEqual(self.app.data, {"d": 1, "hook_stop_key": "", "hook_toggle_key": ""})
        self.assertEqual(set_dirty.call_args.args, (True,))
        self.assertEqual(set_dirty.call_args.kwargs, {})
        self.assertTrue(self.app.dirty_tracker.config_dirty)

    def test_restore_default_save_as_cancel_preserves_loaded_files(self):
        with tempfile.TemporaryDirectory() as root:
            old_path, targets = self._prepare_loaded_keymap_set(root)
            before = {
                path: open(path, "rb").read()
                for path in (old_path, *targets.values())
            }
            patches = self._silence_refresh()

            with patch.object(
                tkinter.messagebox, "askyesnocancel", return_value=False
            ), patch.object(tkinter.messagebox, "askyesno", return_value=True), patch.object(
                self.app, "_set_flash_message"
            ), patches[0], patches[1], patches[2], patches[3]:
                _config_set_io(self.app).restore_default()

            with patch.object(tkinter.filedialog, "asksaveasfilename", return_value="") as ask:
                self.assertFalse(_config_set_io(self.app).save_keymap_set(show_success_dialog=False))

            ask.assert_called_once()
            self.assertEqual(self.app.keymap_set_path, "")
            self.assertEqual(
                {path: open(path, "rb").read() for path in before},
                before,
            )

    def test_restore_default_saves_new_keymap_set_without_changing_loaded_files(self):
        with tempfile.TemporaryDirectory() as root:
            old_path, targets = self._prepare_loaded_keymap_set(root)
            before = {
                path: open(path, "rb").read()
                for path in (old_path, *targets.values())
            }
            new_path = os.path.join(root, "user", "keymap_sets", "restored.json")
            patches = self._silence_refresh()

            with patch.object(
                tkinter.messagebox, "askyesnocancel", return_value=False
            ), patch.object(tkinter.messagebox, "askyesno", return_value=True), patch.object(
                self.app, "_set_flash_message"
            ), patches[0], patches[1], patches[2], patches[3]:
                _config_set_io(self.app).restore_default()

            ask, rows = self._save_restored_as(root, new_path)

            ask.assert_called_once()
            self.assertEqual(self.app.keymap_set_path, new_path)
            self.assertEqual(
                {path: open(path, "rb").read() for path in before},
                before,
            )
            new_trigger_set = os.path.join(root, "user", "trigger_sets", "restored.json")
            self.assertTrue(os.path.exists(new_path))
            self.assertTrue(os.path.exists(new_trigger_set))
            self.assertEqual(
                {(row.kind, row.key) for row in rows},
                {(CHILD_TRIGGER_SET, ""), (CHILD_SEQUENCE, "f1"), (CHILD_SEQUENCE, "f2")},
            )

    def test_restore_default_overwrites_named_parent_and_trigger_set_but_not_sequences(self):
        with tempfile.TemporaryDirectory() as root:
            old_path, targets = self._prepare_loaded_keymap_set(root)
            parent_before = open(old_path, "rb").read()
            trigger_set_path = targets[(CHILD_TRIGGER_SET, "")]
            trigger_set_before = open(trigger_set_path, "rb").read()
            sequences_before = {
                key: open(targets[(CHILD_SEQUENCE, key)], "rb").read()
                for key in ("f1", "f2")
            }
            patches = self._silence_refresh()

            with patch.object(
                tkinter.messagebox, "askyesnocancel", return_value=False
            ), patch.object(tkinter.messagebox, "askyesno", return_value=True), patch.object(
                self.app, "_set_flash_message"
            ), patches[0], patches[1], patches[2], patches[3]:
                _config_set_io(self.app).restore_default()

            _ask, rows = self._save_restored_as(root, old_path)

            self.assertNotEqual(open(old_path, "rb").read(), parent_before)
            self.assertNotEqual(open(trigger_set_path, "rb").read(), trigger_set_before)
            self.assertEqual(
                {
                    key: open(targets[(CHILD_SEQUENCE, key)], "rb").read()
                    for key in ("f1", "f2")
                },
                sequences_before,
            )
            actions = {(row.kind, row.key): row.default_action for row in rows}
            self.assertEqual(actions[(CHILD_TRIGGER_SET, "")], ACTION_SAVE)
            self.assertEqual(actions[(CHILD_SEQUENCE, "f1")], ACTION_SAVE_AS)
            self.assertEqual(actions[(CHILD_SEQUENCE, "f2")], ACTION_SAVE_AS)

    def test_restore_default_cancel_paths_preserve_data_and_keymap_set_path(self):
        original_data = self.app.data
        original_path = "current.json"

        with self.subTest(case="未保存確認をキャンセル"):
            self.app.keymap_set_path = original_path
            self.app.dirty_tracker.set_dirty(True)
            with patch.object(tkinter.messagebox, "askyesnocancel", return_value=None) as ask_save, patch.object(
                tkinter.messagebox, "askyesno"
            ) as ask_restore:
                _config_set_io(self.app).restore_default()
            ask_save.assert_called_once()
            ask_restore.assert_not_called()
            self.assertIs(self.app.data, original_data)
            self.assertEqual(self.app.keymap_set_path, original_path)

        with self.subTest(case="保存後の別名保存をキャンセル"):
            self.app.keymap_set_path = ""
            self.app.dirty_tracker.set_dirty(True)
            with patch.object(tkinter.messagebox, "askyesnocancel", return_value=True) as ask_save, patch.object(
                _config_set_io(self.app), "save_as", return_value=False
            ) as save_as, patch.object(tkinter.messagebox, "askyesno") as ask_restore:
                _config_set_io(self.app).restore_default()
            ask_save.assert_called_once()
            save_as.assert_called_once_with(show_success_dialog=False)
            ask_restore.assert_not_called()
            self.assertIs(self.app.data, original_data)
            self.assertEqual(self.app.keymap_set_path, "")

        with self.subTest(case="例の復元確認をキャンセル"):
            events = []
            self.app.keymap_set_path = original_path
            self.app.dirty_tracker.set_dirty(True)
            with patch.object(
                tkinter.messagebox,
                "askyesnocancel",
                side_effect=lambda *_args: events.append("save") or False,
            ), patch.object(
                tkinter.messagebox,
                "askyesno",
                side_effect=lambda *_args: events.append("restore") or False,
            ):
                _config_set_io(self.app).restore_default()
            self.assertEqual(events, ["save", "restore"])
            self.assertIs(self.app.data, original_data)
            self.assertEqual(self.app.keymap_set_path, original_path)

    def test_restore_default_save_dialog_lists_dirty_trigger_set_and_sequences(self):
        with tempfile.TemporaryDirectory() as root:
            _old_path, targets = self._prepare_loaded_keymap_set(root)
            previous_sequences = {
                key: open(targets[(CHILD_SEQUENCE, key)], "rb").read()
                for key in ("f1", "f2")
            }
            new_path = os.path.join(root, "user", "keymap_sets", "listed.json")
            patches = self._silence_refresh()

            with patch.object(
                tkinter.messagebox, "askyesnocancel", return_value=False
            ), patch.object(tkinter.messagebox, "askyesno", return_value=True), patch.object(
                self.app, "_set_flash_message"
            ), patches[0], patches[1], patches[2], patches[3]:
                _config_set_io(self.app).restore_default()

            _ask, rows = self._save_restored_as(root, new_path)

            rows_by_child = {(row.kind, row.key): row for row in rows}
            self.assertEqual(
                set(rows_by_child),
                {(CHILD_TRIGGER_SET, ""), (CHILD_SEQUENCE, "f1"), (CHILD_SEQUENCE, "f2")},
            )
            self.assertEqual(rows_by_child[(CHILD_SEQUENCE, "f1")].default_action, ACTION_SAVE_AS)
            self.assertEqual(rows_by_child[(CHILD_SEQUENCE, "f2")].default_action, ACTION_SAVE_AS)
            self.assertEqual(
                {
                    key: open(targets[(CHILD_SEQUENCE, key)], "rb").read()
                    for key in ("f1", "f2")
                },
                previous_sequences,
            )
            for key in ("f1", "f2"):
                copy_path = os.path.join(root, "copies", f"{key}.json")
                self.assertTrue(os.path.exists(copy_path))
                self.assertEqual(
                    self.app.config_service.repository.load_json(copy_path)["actions"],
                    self.app.data["triggers"][0 if key == "f1" else 1]["actions"],
                )
            trigger_set_path = os.path.join(root, "user", "trigger_sets", "listed.json")
            trigger_set = self.app.config_service.repository.load_json(trigger_set_path)
            for trigger in trigger_set["triggers"]:
                copy_path = os.path.join(root, "copies", f"{trigger['key']}.json")
                self.assertEqual(
                    trigger["sequence_path"],
                    self.app.config_service.to_config_relative_or_absolute(copy_path, root),
                )

    def test_restore_default_resets_trigger_set_state_and_runtime_data(self):
        previous_path = "C:/previous/triggers.json"
        self.app.dirty_tracker.set_trigger_set_source_path(previous_path)
        self.app.dirty_tracker.trigger_set_imported = True
        self.app.dirty_tracker.mark_trigger_set_dirty()
        patches = self._silence_refresh()

        with patch.object(tkinter.messagebox, "askyesnocancel", return_value=False), patch.object(
            tkinter.messagebox, "askyesno", return_value=True
        ), patch.object(
            self.app, "_set_flash_message"
        ), patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).restore_default()

        self.assertEqual(self.app.dirty_tracker.trigger_set_source_path, "")
        self.assertNotIn(
            self.app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH,
            self.app.data,
        )
        self.assertTrue(self.app.dirty_tracker.trigger_set_dirty)
        self.assertFalse(self.app.dirty_tracker.trigger_set_imported)

    def test_new_config_trigger_set_save_does_not_write_previous_source(self):
        with tempfile.TemporaryDirectory() as directory:
            previous_path = os.path.join(directory, "previous-trigger-set.json")
            previous_bytes = b'{"triggers": ["previous"]}'
            with open(previous_path, "wb") as file:
                file.write(previous_bytes)
            self.app.dirty_tracker.set_trigger_set_source_path(previous_path)
            patches = self._silence_refresh()

            with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
                self.app, "_set_flash_message"
            ), patch.object(
                self.app.io_dialogs,
                "choose_save_path_with_collision",
                return_value="",
            ) as choose, patch.object(
                self.app.config_service,
                "save_trigger_set_file",
            ) as save, patches[0], patches[1], patches[2], patches[3]:
                _config_set_io(self.app).new_config()
                self.assertFalse(self.app.trigger_set_io.save_trigger_set_file())

            choose.assert_called_once()
            self.assertEqual(choose.call_args.kwargs["title"], "トリガー一覧を保存")
            save.assert_not_called()
            with open(previous_path, "rb") as file:
                self.assertEqual(file.read(), previous_bytes)

    def test_restore_default_trigger_set_save_does_not_write_previous_source(self):
        with tempfile.TemporaryDirectory() as directory:
            previous_path = os.path.join(directory, "previous-trigger-set.json")
            previous_bytes = b'{"triggers": ["previous"]}'
            with open(previous_path, "wb") as file:
                file.write(previous_bytes)
            self.app.dirty_tracker.set_trigger_set_source_path(previous_path)
            self.app.dirty_tracker.mark_trigger_set_dirty()
            patches = self._silence_refresh()

            with patch.object(
                tkinter.messagebox, "askyesnocancel", return_value=False
            ), patch.object(tkinter.messagebox, "askyesno", return_value=True), patch.object(
                self.app, "_set_flash_message"
            ), patch.object(
                self.app.io_dialogs,
                "choose_save_path_with_collision",
                return_value="",
            ) as choose, patch.object(
                self.app.config_service,
                "save_trigger_set_file",
            ) as save, patches[0], patches[1], patches[2], patches[3]:
                _config_set_io(self.app).restore_default()
                self.assertFalse(self.app.trigger_set_io.save_trigger_set_file())

            choose.assert_called_once()
            self.assertEqual(choose.call_args.kwargs["title"], "トリガー一覧を保存")
            save.assert_not_called()
            with open(previous_path, "rb") as file:
                self.assertEqual(file.read(), previous_bytes)

    def test_load_and_import_keep_trigger_set_state_synchronized(self):
        loaded_path = "C:/loaded/triggers.json"
        loaded_data = self.app.config_service.new_default_data()
        loaded_data[self.app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH] = loaded_path
        patches = self._silence_refresh()

        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="C:/loaded/keymap-set.json"
        ), patch.object(
            self.app.config_service,
            "load_runtime_data_from_keymap_set_path",
            return_value=loaded_data,
        ), patch.object(self.app, "_set_flash_message"), patch.object(
            tkinter.messagebox, "showinfo"
        ), patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).load_keymap_set_from()

        self.assertEqual(self.app.dirty_tracker.trigger_set_source_path, loaded_path)
        self.assertEqual(
            self.app.data[self.app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH],
            loaded_path,
        )
        self.assertFalse(self.app.dirty_tracker.trigger_set_dirty)
        self.assertFalse(self.app.dirty_tracker.trigger_set_imported)

        imported_path = "C:/imported/triggers.json"
        imported_data = self.app.config_service.new_default_data()
        imported_data[self.app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH] = imported_path
        patches = self._silence_refresh()

        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="C:/imported/config.json"
        ), patch.object(
            self.app.config_service,
            "load_legacy_runtime_data",
            return_value=imported_data,
        ), patch.object(self.app, "_set_flash_message"), patch.object(
            tkinter.messagebox, "showinfo"
        ), patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).import_config()

        self.assertEqual(self.app.dirty_tracker.trigger_set_source_path, imported_path)
        self.assertEqual(
            self.app.data[self.app.config_service.INTERNAL_TRIGGER_SET_SOURCE_PATH],
            imported_path,
        )
        self.assertFalse(self.app.dirty_tracker.trigger_set_dirty)
        self.assertFalse(self.app.dirty_tracker.trigger_set_imported)

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
        ), patch.object(self.app.startup_io, "write_startup") as write_startup, patch.object(
            tkinter.messagebox, "showerror"
        ) as showerror:
            # write_startup は B（StartupIo）でクロスモジュール。set_startup は self._app.startup_io.write_startup を呼ぶため所有オブジェクトを patch。
            _config_set_io(self.app).set_startup_keymap_set()
            showerror.assert_called_once_with("設定", "bad")
            write_startup.assert_not_called()  # 読込例外時は後続を実行しない

    def test_set_startup_keymap_set_writes_only_keymap_set_path(self):
        patches = self._silence_refresh()
        with patch.object(_config_set_io(self.app), "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog, "askopenfilename", return_value="k.json"
        ), patch.object(
            self.app.config_service, "load_runtime_data_from_keymap_set_path", return_value={"loaded": True}
        ), patch.object(
            self.app.paths, "to_config_relative_or_absolute", return_value="user/keymap_sets/k.json"
        ), patch.object(self.app.startup_io, "write_startup") as write_startup, patch.object(
            _config_set_io(self.app), "apply_loaded_data_to_ui"
        ), patch.object(self.app.dirty_tracker, "set_dirty"), patch.object(
            self.app, "_set_flash_message"
        ), patch.object(tkinter.messagebox, "showinfo"), patches[0], patches[1], patches[2], patches[3]:
            _config_set_io(self.app).set_startup_keymap_set()

        write_startup.assert_called_once_with({"keymap_set_path": "user/keymap_sets/k.json"})

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
        showerror.assert_called_once_with("startup.json 保存失敗", "disk full")
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
                "ui_font_delta_pt": 2,
                "last_used_directory": "D",
                "keymap_set_path": "X.json",
            },
        )
        self.assertEqual(self.app._startup_settings, saved["base"])

    def test_write_startup_omits_prompt_if_missing_without_existing_value(self):
        saved = {}
        with patch.object(self.app.paths, "preferred_startup_path", return_value="startup.json"), patch.object(
            self.app.config_service, "save_startup", side_effect=lambda path, base: saved.update({"base": dict(base)})
        ):
            _startup_io(self.app).write_startup({"ui_font_delta_pt": 0})

        self.assertNotIn("prompt_if_missing", saved["base"])

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
            showerror.assert_called_once_with("startup.json 保存失敗", "no disk")

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
            ) as load, patch.object(self.app.keymap_set_io, "apply_loaded_data_to_ui") as apply_ui, patch.object(
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
            self.app.keymap_set_io, "apply_loaded_data_to_ui"
        ) as apply_ui:
            _startup_io(self.app).load_startup_and_config()
        # 空データフォールバックでも hook キーの全体デフォルトが注入される（phase 07 task_02）。
        self.assertEqual(self.app.data, {"empty": True, "hook_stop_key": "", "hook_toggle_key": ""})
        self.assertEqual(self.app.keymap_set_path, "")
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
            ), patch.object(self.app.keymap_set_io, "apply_loaded_data_to_ui"):
                _startup_io(self.app).load_startup_and_config()
            # 例外は握りつぶされ、空データにフォールバックする
            # （空データにも hook キーの全体デフォルトが注入される。phase 07 task_02）
            self.assertEqual(self.app.data, {"empty": True, "hook_stop_key": "", "hook_toggle_key": ""})
            # 読込例外時も keymap_set_path は空のまま（受入 4）
            self.assertEqual(self.app.keymap_set_path, "")


if __name__ == "__main__":
    unittest.main()
