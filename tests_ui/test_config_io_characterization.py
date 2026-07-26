"""ConfigIoController の個別 JSON IO と共有ダイアログの現行挙動を固定する。"""
from __future__ import annotations

import os
import tempfile
import tkinter
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from keyseq.presentation import app as app_module


def _expected_json_bytes(text: str) -> bytes:
    """config_service はテキストモードで書き出すため、改行はプラットフォーム依存になる。
    内容・キー順・インデントの変化は検出しつつ、改行差（LF/CRLF）だけを吸収する。"""
    return text.replace("\n", os.linesep).encode("utf-8")


def _dialog_io(app):
    return app.io_dialogs


def _keymap_io(app):
    return app.keymap_io


def _trigger_set_io(app):
    return app.trigger_set_io


def _sequence_io(app):
    return app.sequence_io


class _FakeDialog:
    def __init__(self, mode, buttons):
        self._mode = mode
        self._buttons = buttons
        self._protocols = {}
        self.title_value = None

    def title(self, value):
        self.title_value = value

    def resizable(self, _width, _height):
        pass

    def transient(self, _master):
        pass

    def grab_set(self):
        pass

    def protocol(self, name, command):
        self._protocols[name] = command

    def destroy(self):
        pass

    def wait_window(self):
        if self._mode == "ok":
            self._buttons["OK"]()
        elif self._mode == "cancel":
            self._buttons["キャンセル"]()
        else:
            self._protocols["WM_DELETE_WINDOW"]()


class _FakeWidget:
    def __init__(self, *, text=None):
        self.text = text

    def pack(self, **_kwargs):
        return self


class _FakeBoolVar:
    def __init__(self, *, value=False):
        self._value = value

    def get(self):
        return self._value


class ConfigIoCharacterizationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._load_startup_patch = patch.object(
            app_module.ConfigService,
            "load_startup",
            return_value={},
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
        # production のリセットと同じ 0 を入れる（setter は int 化するため None は不可）。
        # 「未選択」の再現は trigger_panel.selected_trigger / keymap_panel.selected_keymap_list_index の patch で行う。
        self.app._selected_trigger_idx = 0
        self.app.config_root = os.getcwd()
        self.app.keymap_set_path = ""
        self.app.dirty_tracker.trigger_set_source_path = ""
        self.app.dirty_tracker.trigger_set_imported = False
        self.app.dirty_tracker.trigger_set_dirty = False
        self.app.dirty_tracker.is_dirty = False
        self.app.dirty_tracker.config_dirty = False

    def _ask_link_result(self, mode, checked):
        buttons = {}
        labels = []
        checkbuttons = []
        dialog = _FakeDialog(mode, buttons)

        def make_button(_master, *, text, command, **_kwargs):
            buttons[text] = command
            return _FakeWidget(text=text)

        def make_label(_master, *, text, **_kwargs):
            labels.append(text)
            return _FakeWidget(text=text)

        def make_checkbutton(_master, *, text, **_kwargs):
            checkbuttons.append(text)
            return _FakeWidget(text=text)

        with patch.object(tkinter, "Toplevel", return_value=dialog), patch.object(
            tkinter,
            "BooleanVar",
            return_value=_FakeBoolVar(value=checked),
        ), patch.object(tkinter.ttk, "Frame", return_value=_FakeWidget()), patch.object(
            tkinter.ttk,
            "Label",
            side_effect=make_label,
        ), patch.object(tkinter.ttk, "Checkbutton", side_effect=make_checkbutton), patch.object(
            tkinter.ttk,
            "Button",
            side_effect=make_button,
        ), patch.object(self.app.hook, "suspend_hook_for_dialog") as suspend, patch.object(
            self.app.hook,
            "resume_hook_after_dialog",
        ) as resume:
            if mode == "ok":
                actual = _dialog_io(self.app).ask_link_label_to_filename(
                    title="ラベル連動",
                    path="C:/tmp/linked.json",
                )
                self.assertEqual(actual, checked)
            else:
                with self.assertRaisesRegex(RuntimeError, "^キャンセルされました。$"):
                    _dialog_io(self.app).ask_link_label_to_filename(
                        title="ラベル連動",
                        path="C:/tmp/linked.json",
                    )
            self.assertEqual(dialog.title_value, "ラベル連動")
            self.assertEqual(labels, ["保存名: linked"])
            self.assertEqual(checkbuttons, ["ラベル名も保存名に合わせる"])
            self.assertEqual(suspend.call_count, resume.call_count)
            self.assertEqual(suspend.call_count, 1)

    # ---- 分割耐性のための境界 mock ヘルパ ----
    # save_X_to_path を内部メソッドとして直接 mock すると、分割でオブジェクト同一性が変わり
    # patch が外れる。代わりにその外部境界（config_service / refresh / messagebox）を無害化して
    # 実 save_X_to_path を走らせ、save_calls に保存呼び出しを記録して「どのパスへ保存したか」を固定する。
    def _keymap_save_patches(self, save_calls):
        def fake_save(path, keymap):
            save_calls.append((path, keymap))
            # 実 save_keymap_to_path は get_keymaps()[index] = saved でリスト要素を差し替える。
            # コピーを返すと後続ブロックが差し替え後の別オブジェクトを掴むため、同一オブジェクトを返す。
            return keymap
        return (
            patch.object(self.app.config_service, "save_keymap_file", side_effect=fake_save),
            patch.object(self.app.keymap_panel, "refresh_keymap_list_ui"),
            patch.object(self.app.layout, "refresh_keyboard_window"),
            patch.object(self.app.dirty_tracker, "sync_dirty_state"),
            patch.object(tkinter.messagebox, "showinfo"),
        )

    def _trigger_set_save_patches(self, save_calls):
        def fake_save(path, data, *, config_root):
            save_calls.append((path, data.get("triggers")))
            return list(data.get("triggers") or []), {}
        return (
            patch.object(self.app.config_service, "save_trigger_set_file", side_effect=fake_save),
            patch.object(self.app.trigger_panel, "refresh_triggers"),
            patch.object(self.app.trigger_panel, "refresh_actions"),
            patch.object(self.app.dirty_tracker, "sync_dirty_state"),
            patch.object(tkinter.messagebox, "showinfo"),
        )

    def _sequence_save_patches(self, save_calls):
        def fake_save(path, trigger):
            save_calls.append((path, trigger))
            return {}
        return (
            patch.object(self.app.config_service, "save_sequence_file", side_effect=fake_save),
            patch.object(self.app.dirty_tracker, "mark_trigger_set_dirty"),
            patch.object(self.app.trigger_panel, "refresh_triggers"),
            patch.object(self.app.trigger_panel, "refresh_actions"),
            patch.object(tkinter.messagebox, "showinfo"),
        )

    # C: 共有ダイアログヘルパ
    def test_choose_save_path_with_collision_all_branches(self):
        with tempfile.TemporaryDirectory() as directory:
            suggested = os.path.join(directory, "suggested.json")
            with patch.object(tkinter.messagebox, "askyesnocancel") as ask:
                self.assertEqual(
                    _dialog_io(self.app).choose_save_path_with_collision(
                        title="保存",
                        suggested_path=suggested,
                    ),
                    suggested,
                )
                ask.assert_not_called()

            Path(suggested).touch()
            expected_message = (
                f"同名ファイルが既にあります。\n\n{suggested}\n\n"
                "上書きしますか？\n「いいえ」で別名保存します。"
            )
            with patch.object(tkinter.messagebox, "askyesnocancel", return_value=True) as ask:
                self.assertEqual(
                    _dialog_io(self.app).choose_save_path_with_collision(
                        title="保存",
                        suggested_path=suggested,
                    ),
                    suggested,
                )
                ask.assert_called_once_with("保存先の確認", expected_message)

            chosen = os.path.join(directory, "chosen.json")
            with patch.object(tkinter.messagebox, "askyesnocancel", return_value=False) as ask, patch.object(
                tkinter.filedialog,
                "asksaveasfilename",
                return_value=chosen,
            ) as ask_save:
                self.assertEqual(
                    _dialog_io(self.app).choose_save_path_with_collision(
                        title="保存",
                        suggested_path=suggested,
                    ),
                    chosen,
                )
                ask.assert_called_once_with("保存先の確認", expected_message)
                ask_save.assert_called_once_with(
                    title="保存",
                    initialdir=os.path.dirname(os.path.abspath(suggested)),
                    initialfile="suggested.json",
                    defaultextension=".json",
                    filetypes=[("JSON", "*.json"), ("All", "*.*")],
                )

            with patch.object(tkinter.messagebox, "askyesnocancel", return_value=None) as ask:
                self.assertEqual(
                    _dialog_io(self.app).choose_save_path_with_collision(
                        title="保存",
                        suggested_path=suggested,
                    ),
                    "",
                )
                ask.assert_called_once_with("保存先の確認", expected_message)

    def test_ask_link_label_to_filename_all_branches_balance_hook(self):
        for mode, checked in (("ok", True), ("ok", False), ("cancel", False), ("close", False)):
            with self.subTest(mode=mode, checked=checked):
                self._ask_link_result(mode, checked)

    # D: keymap 個別 JSON IO
    def test_keymap_save_selected_no_selection_reports_and_returns_false(self):
        with patch.object(self.app.keymap_panel, "selected_keymap_list_index", return_value=None), patch.object(
            tkinter.messagebox,
            "showinfo",
        ) as showinfo:
            self.assertFalse(_keymap_io(self.app).save_selected_keymap())
        showinfo.assert_called_once_with("キーマップ", "対象のキーマップを選択してください。")

    def test_keymap_save_selected_imported_dirty_yes_no_and_missing_source(self):
        keymap = {"id": "map", "label": "Map", "mappings": {}}
        self.app.data["keymaps"] = [keymap]
        source = "C:/loaded/map.json"
        keymap.update(
            {
                self.app.config_service.INTERNAL_KEYMAP_SOURCE_PATH: source,
                self.app.config_service.INTERNAL_KEYMAP_IMPORTED: True,
                self.app.config_service.INTERNAL_KEYMAP_DIRTY: True,
            }
        )
        # imported+dirty+yes → save_selected_keymap_as 経由で別名パスへ保存される
        save_calls = []
        p = self._keymap_save_patches(save_calls)
        with patch.object(self.app.keymap_panel, "selected_keymap_list_index", return_value=0), patch.object(
            tkinter.messagebox, "askyesno", return_value=True
        ) as ask, patch.object(
            tkinter.filedialog, "asksaveasfilename", return_value="C:/as/map.json"
        ), patch.object(_dialog_io(self.app), "ask_link_label_to_filename", return_value=False), p[0], p[1], p[2], p[3], p[4]:
            self.assertTrue(_keymap_io(self.app).save_selected_keymap())
            ask.assert_called_once_with("保存", "読込で持ってきたキーマップです。\n別名で保存しますか？")
            self.assertEqual(save_calls, [("C:/as/map.json", keymap)])

        # imported+dirty+no → 既存 source パスへ保存
        save_calls = []
        p = self._keymap_save_patches(save_calls)
        with patch.object(self.app.keymap_panel, "selected_keymap_list_index", return_value=0), patch.object(
            tkinter.messagebox, "askyesno", return_value=False
        ) as ask, p[0], p[1], p[2], p[3], p[4]:
            self.assertTrue(_keymap_io(self.app).save_selected_keymap())
            ask.assert_called_once_with("保存", "読込で持ってきたキーマップです。\n別名で保存しますか？")
            self.assertEqual(save_calls, [(source, keymap)])

        # source なし → choose_save_path_with_collision の返すパスへ保存
        keymap.pop(self.app.config_service.INTERNAL_KEYMAP_SOURCE_PATH)
        save_calls = []
        p = self._keymap_save_patches(save_calls)
        with patch.object(self.app.keymap_panel, "selected_keymap_list_index", return_value=0), patch.object(
            _dialog_io(self.app), "choose_save_path_with_collision", return_value="C:/new/map.json"
        ) as choose, p[0], p[1], p[2], p[3], p[4]:
            self.assertTrue(_keymap_io(self.app).save_selected_keymap())
            self.assertEqual(choose.call_args.kwargs["title"], "キーマップを保存")
            self.assertEqual(save_calls, [("C:/new/map.json", keymap)])

    def test_keymap_save_as_links_label_and_cancel_does_not_save(self):
        keymap = {"id": "map", "label": "Before", "mappings": {}}
        self.app.data["keymaps"] = [keymap]
        save_calls = []
        p = self._keymap_save_patches(save_calls)
        with patch.object(self.app.keymap_panel, "selected_keymap_list_index", return_value=0), patch.object(
            tkinter.filedialog, "asksaveasfilename", return_value="C:/new/After.json"
        ) as ask_save, patch.object(
            _dialog_io(self.app), "ask_link_label_to_filename", return_value=True
        ) as link, p[0], p[1], p[2], p[3], p[4]:
            self.assertTrue(_keymap_io(self.app).save_selected_keymap_as())
            self.assertEqual(ask_save.call_args.kwargs["title"], "キーマップを別名で保存")
            link.assert_called_once_with(title="キーマップ名の連動", path="C:/new/After.json")
            self.assertEqual(keymap["label"], "After")
            self.assertEqual(save_calls, [("C:/new/After.json", keymap)])

        # ask_link がキャンセル（RuntimeError）→ 保存しない
        save_calls = []
        p = self._keymap_save_patches(save_calls)
        with patch.object(self.app.keymap_panel, "selected_keymap_list_index", return_value=0), patch.object(
            tkinter.filedialog, "asksaveasfilename", return_value="C:/new/cancel.json"
        ), patch.object(
            _dialog_io(self.app),
            "ask_link_label_to_filename",
            side_effect=RuntimeError("キャンセルされました。"),
        ), p[0], p[1], p[2], p[3], p[4]:
            self.assertFalse(_keymap_io(self.app).save_selected_keymap_as())
            self.assertEqual(save_calls, [])

    def test_keymap_save_to_path_writes_bytes_refreshes_and_reports_in_order(self):
        keymap = {"id": "map", "label": "Map", "mappings": {}}
        self.app.data["keymaps"] = [keymap]
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "map.json")
            with patch.object(self.app.keymap_panel, "refresh_keymap_list_ui", side_effect=lambda **kw: calls.append(("refresh", kw))), patch.object(
                self.app.layout,
                "refresh_keyboard_window",
                side_effect=lambda: calls.append(("keyboard", {})),
            ), patch.object(self.app.dirty_tracker, "sync_dirty_state", side_effect=lambda: calls.append(("sync", {}))), patch.object(
                self.app,
                "_set_flash_message",
                side_effect=lambda message, **kw: calls.append(("flash", message, kw)),
            ), patch.object(tkinter.messagebox, "showinfo", side_effect=lambda *args: calls.append(("info", args))):
                self.assertTrue(_keymap_io(self.app).save_keymap_to_path(0, keymap, path))
            self.assertEqual(
                Path(path).read_bytes(),
                _expected_json_bytes('{\n  "label": "Map",\n  "mappings": {}\n}'),
            )
        self.assertEqual(
            calls,
            [
                ("refresh", {"preferred_index": 0}),
                ("keyboard", {}),
                ("sync", {}),
                ("flash", "キーマップを保存しました。", {}),
                ("info", ("保存", f"キーマップを保存しました:\n{path}")),
            ],
        )

    def test_keymap_save_to_path_exception_reports_failure(self):
        error = ValueError("disk full")
        with patch.object(self.app.config_service, "save_keymap_file", side_effect=error), patch.object(
            self.app,
            "_set_flash_message",
        ) as flash, patch.object(tkinter.messagebox, "showerror") as showerror:
            self.assertFalse(_keymap_io(self.app).save_keymap_to_path(0, {"id": "map"}, "C:/bad.json"))
        flash.assert_called_once_with("キーマップ保存失敗: disk full", auto_clear=False)
        showerror.assert_called_once_with("保存失敗", "disk full")

    def test_keymap_load_success_empty_and_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "load.json")
            Path(path).write_bytes(b'{"label": "Loaded", "mappings": {}}')
            with patch.object(tkinter.filedialog, "askopenfilename", return_value=path) as ask_open, patch.object(
                self.app.keymap_panel,
                "refresh_keymap_list_ui",
            ) as refresh, patch.object(self.app.layout, "refresh_keyboard_window") as keyboard, patch.object(
                self.app.dirty_tracker,
                "set_dirty",
            ) as set_dirty, patch.object(self.app, "_set_flash_message") as flash, patch.object(
                tkinter.messagebox,
                "showinfo",
            ) as showinfo:
                _keymap_io(self.app).load_keymap_file()
            self.assertEqual(ask_open.call_args.kwargs["title"], "キーマップを読込")
            self.assertEqual(self.app.data["keymaps"][-1]["label"], "Loaded")
            self.assertEqual(self.app.data["active_keymap_id"], "load")
            refresh.assert_called_once_with(preferred_index=0)
            keyboard.assert_called_once_with()
            set_dirty.assert_called_once_with(True)
            flash.assert_called_once_with("キーマップを読み込みました。")
            showinfo.assert_called_once_with("読込", f"キーマップを読み込みました:\n{path}")

        with patch.object(tkinter.filedialog, "askopenfilename", return_value=""), patch.object(
            self.app.config_service,
            "load_keymap_file",
        ) as load:
            self.assertIsNone(_keymap_io(self.app).load_keymap_file())
            load.assert_not_called()

        error = ValueError("bad keymap")
        with patch.object(tkinter.filedialog, "askopenfilename", return_value="C:/bad.json"), patch.object(
            self.app.config_service,
            "load_keymap_file",
            side_effect=error,
        ), patch.object(self.app, "_set_flash_message") as flash, patch.object(
            tkinter.messagebox,
            "showerror",
        ) as showerror:
            _keymap_io(self.app).load_keymap_file()
        flash.assert_called_once_with("キーマップ読込失敗: bad keymap", auto_clear=False)
        showerror.assert_called_once_with("読込失敗", "bad keymap")

    # E: trigger_set 個別 JSON IO
    def test_trigger_set_save_uses_collision_not_unreachable_import_prompt(self):
        # idea_05 で変更予定: dirty_tracker の source_path はこの保存経路の読取先ではない。
        self.app.dirty_tracker.trigger_set_source_path = "C:/loaded/triggers.json"
        self.app.dirty_tracker.trigger_set_imported = True
        self.app.dirty_tracker.trigger_set_dirty = True
        save_calls = []
        p = self._trigger_set_save_patches(save_calls)
        with patch.object(tkinter.messagebox, "askyesno") as ask, patch.object(
            _dialog_io(self.app), "choose_save_path_with_collision", return_value="C:/new/triggers.json"
        ) as choose, p[0], p[1], p[2], p[3], p[4]:
            self.assertTrue(_trigger_set_io(self.app).save_trigger_set_file())
            ask.assert_not_called()
            self.assertEqual(choose.call_args.kwargs["title"], "トリガー一覧を保存")
            self.assertEqual([c[0] for c in save_calls], ["C:/new/triggers.json"])

    def test_trigger_set_save_as_never_links_label_and_cancel_returns_false(self):
        save_calls = []
        p = self._trigger_set_save_patches(save_calls)
        with patch.object(tkinter.filedialog, "asksaveasfilename", return_value="C:/new/triggers.json") as ask_save, patch.object(
            _dialog_io(self.app), "ask_link_label_to_filename"
        ) as link, p[0], p[1], p[2], p[3], p[4]:
            self.assertTrue(_trigger_set_io(self.app).save_trigger_set_file_as())
            self.assertEqual(ask_save.call_args.kwargs["title"], "トリガー一覧を別名で保存")
            link.assert_not_called()  # E: save_as はラベル連動を呼ばない
            self.assertEqual([c[0] for c in save_calls], ["C:/new/triggers.json"])

        # asksaveasfilename キャンセル → 保存しない
        save_calls = []
        p = self._trigger_set_save_patches(save_calls)
        with patch.object(tkinter.filedialog, "asksaveasfilename", return_value=""), p[0], p[1], p[2], p[3], p[4]:
            self.assertFalse(_trigger_set_io(self.app).save_trigger_set_file_as())
            self.assertEqual(save_calls, [])

    def test_trigger_set_save_to_path_writes_bytes_updates_dirty_and_reports(self):
        trigger = {"key": "a", "label": "Run", "actions": []}
        self.app.data["triggers"] = [trigger]
        self.app.dirty_tracker.trigger_set_imported = True
        self.app.dirty_tracker.trigger_set_dirty = True
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            self.app.config_root = directory
            path = os.path.join(directory, "triggers.json")
            expected = _expected_json_bytes(
                "{\n  \"triggers\": [\n    {\n      \"key\": \"a\",\n"
                "      \"suppress\": true,\n"
                "      \"sequence_path\": \"sequences/Run.json\"\n"
                "    }\n  ]\n}"
            )
            with patch.object(self.app.trigger_panel, "refresh_triggers", side_effect=lambda: calls.append("triggers")), patch.object(
                self.app.trigger_panel,
                "refresh_actions",
                side_effect=lambda: calls.append("actions"),
            ), patch.object(self.app.dirty_tracker, "sync_dirty_state", side_effect=lambda: calls.append("sync")), patch.object(
                self.app,
                "_set_flash_message",
                side_effect=lambda message, **kw: calls.append(("flash", message, kw)),
            ), patch.object(tkinter.messagebox, "showinfo", side_effect=lambda *args: calls.append(("info", args))):
                self.assertTrue(_trigger_set_io(self.app).save_trigger_set_to_path(path))
            self.assertEqual(Path(path).read_bytes(), expected)
        self.assertEqual(self.app.dirty_tracker.trigger_set_source_path, path)
        self.assertFalse(self.app.dirty_tracker.trigger_set_imported)
        self.assertFalse(self.app.dirty_tracker.trigger_set_dirty)
        self.assertEqual(
            calls,
            [
                "triggers",
                "actions",
                "sync",
                ("flash", "トリガー一覧を保存しました。", {}),
                ("info", ("保存", f"トリガー一覧を保存しました:\n{path}")),
            ],
        )

    def test_trigger_set_save_to_path_exception_reports_failure(self):
        error = ValueError("disk full")
        with patch.object(self.app.config_service, "save_trigger_set_file", side_effect=error), patch.object(
            self.app,
            "_set_flash_message",
        ) as flash, patch.object(tkinter.messagebox, "showerror") as showerror:
            self.assertFalse(_trigger_set_io(self.app).save_trigger_set_to_path("C:/bad.json"))
        flash.assert_called_once_with("トリガー一覧保存失敗: disk full", auto_clear=False)
        showerror.assert_called_once_with("保存失敗", "disk full")

    def test_trigger_set_load_confirms_first_then_success_empty_and_exception(self):
        with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=False) as confirm, patch.object(
            tkinter.filedialog,
            "askopenfilename",
        ) as ask_open:
            self.assertIsNone(_trigger_set_io(self.app).load_trigger_set_file())
            confirm.assert_called_once_with("トリガー一覧読込")
            ask_open.assert_not_called()

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "triggers.json")
            Path(path).write_bytes(b'{"triggers": []}')
            with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True), patch.object(
                tkinter.filedialog,
                "askopenfilename",
                return_value=path,
            ) as ask_open, patch.object(self.app.trigger_panel, "refresh_triggers") as refresh_triggers, patch.object(
                self.app.trigger_panel,
                "refresh_actions",
            ) as refresh_actions, patch.object(self.app.dirty_tracker, "set_dirty") as set_dirty, patch.object(
                self.app,
                "_set_flash_message",
            ) as flash, patch.object(tkinter.messagebox, "showinfo") as showinfo:
                _trigger_set_io(self.app).load_trigger_set_file()
            self.assertEqual(ask_open.call_args.kwargs["title"], "トリガー一覧を読込")
            self.assertEqual(self.app.data["triggers"], [])
            self.assertEqual(self.app.dirty_tracker.trigger_set_source_path, path)
            self.assertTrue(self.app.dirty_tracker.trigger_set_imported)
            self.assertFalse(self.app.dirty_tracker.trigger_set_dirty)
            refresh_triggers.assert_called_once_with()
            refresh_actions.assert_called_once_with()
            set_dirty.assert_called_once_with(True)
            flash.assert_called_once_with("トリガー一覧を読み込みました。")
            showinfo.assert_called_once_with("読込", f"トリガー一覧を読み込みました:\n{path}")

        with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog,
            "askopenfilename",
            return_value="",
        ), patch.object(self.app.config_service, "load_trigger_set_file") as load:
            _trigger_set_io(self.app).load_trigger_set_file()
            load.assert_not_called()

        error = ValueError("bad trigger set")
        with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True), patch.object(
            tkinter.filedialog,
            "askopenfilename",
            return_value="C:/bad.json",
        ), patch.object(self.app.config_service, "load_trigger_set_file", side_effect=error), patch.object(
            self.app,
            "_set_flash_message",
        ) as flash, patch.object(tkinter.messagebox, "showerror") as showerror:
            _trigger_set_io(self.app).load_trigger_set_file()
        flash.assert_called_once_with("トリガー一覧読込失敗: bad trigger set", auto_clear=False)
        showerror.assert_called_once_with("読込失敗", "bad trigger set")

    # F: sequence 個別 JSON IO
    def test_sequence_save_selected_no_selection_reports_and_returns_false(self):
        with patch.object(self.app.trigger_panel, "selected_trigger", return_value=None), patch.object(
            tkinter.messagebox,
            "showinfo",
        ) as showinfo:
            self.assertFalse(_sequence_io(self.app).save_selected_sequence())
        showinfo.assert_called_once_with("出力シーケンス", "対象のトリガーを選択してください。")

    def test_sequence_save_selected_imported_dirty_yes_no_and_missing_source(self):
        trigger = {"key": "a", "label": "Run", "actions": []}
        source = "C:/loaded/run.json"
        trigger.update(
            {
                self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH: source,
                self.app.config_service.INTERNAL_SEQUENCE_IMPORTED: True,
                self.app.config_service.INTERNAL_SEQUENCE_DIRTY: True,
            }
        )
        # imported+dirty+yes → save_selected_sequence_as 経由で別名パスへ保存される
        save_calls = []
        p = self._sequence_save_patches(save_calls)
        with patch.object(self.app.trigger_panel, "selected_trigger", return_value=trigger), patch.object(
            tkinter.messagebox, "askyesno", return_value=True
        ) as ask, patch.object(
            tkinter.filedialog, "asksaveasfilename", return_value="C:/as/run.json"
        ), patch.object(_dialog_io(self.app), "ask_link_label_to_filename", return_value=False), p[0], p[1], p[2], p[3], p[4]:
            self.assertTrue(_sequence_io(self.app).save_selected_sequence())
            ask.assert_called_once_with("保存", "読込で持ってきた出力シーケンスです。\n別名で保存しますか？")
            self.assertEqual(save_calls, [("C:/as/run.json", trigger)])

        # imported+dirty+no → 既存 source パスへ保存
        save_calls = []
        p = self._sequence_save_patches(save_calls)
        with patch.object(self.app.trigger_panel, "selected_trigger", return_value=trigger), patch.object(
            tkinter.messagebox, "askyesno", return_value=False
        ) as ask, p[0], p[1], p[2], p[3], p[4]:
            self.assertTrue(_sequence_io(self.app).save_selected_sequence())
            ask.assert_called_once_with("保存", "読込で持ってきた出力シーケンスです。\n別名で保存しますか？")
            self.assertEqual(save_calls, [(source, trigger)])

        # source なし → choose_save_path_with_collision の返すパスへ保存
        trigger.pop(self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH)
        save_calls = []
        p = self._sequence_save_patches(save_calls)
        with patch.object(self.app.trigger_panel, "selected_trigger", return_value=trigger), patch.object(
            _dialog_io(self.app), "choose_save_path_with_collision", return_value="C:/new/run.json"
        ) as choose, p[0], p[1], p[2], p[3], p[4]:
            self.assertTrue(_sequence_io(self.app).save_selected_sequence())
            self.assertEqual(choose.call_args.kwargs["title"], "出力シーケンスを保存")
            self.assertEqual(save_calls, [("C:/new/run.json", trigger)])

    def test_sequence_save_as_links_label_and_cancel_does_not_save(self):
        trigger = {"key": "a", "label": "Before", "actions": []}
        save_calls = []
        p = self._sequence_save_patches(save_calls)
        with patch.object(self.app.trigger_panel, "selected_trigger", return_value=trigger), patch.object(
            tkinter.filedialog, "asksaveasfilename", return_value="C:/new/After.json"
        ) as ask_save, patch.object(
            _dialog_io(self.app), "ask_link_label_to_filename", return_value=True
        ) as link, p[0], p[1], p[2], p[3], p[4]:
            self.assertTrue(_sequence_io(self.app).save_selected_sequence_as())
            self.assertEqual(ask_save.call_args.kwargs["title"], "出力シーケンスを別名で保存")
            link.assert_called_once_with(title="出力シーケンス名の連動", path="C:/new/After.json")
            self.assertEqual(trigger["label"], "After")
            self.assertEqual(save_calls, [("C:/new/After.json", trigger)])

        # ask_link がキャンセル（RuntimeError）→ 保存しない
        save_calls = []
        p = self._sequence_save_patches(save_calls)
        with patch.object(self.app.trigger_panel, "selected_trigger", return_value=trigger), patch.object(
            tkinter.filedialog, "asksaveasfilename", return_value="C:/new/cancel.json"
        ), patch.object(
            _dialog_io(self.app),
            "ask_link_label_to_filename",
            side_effect=RuntimeError("キャンセルされました。"),
        ), p[0], p[1], p[2], p[3], p[4]:
            self.assertFalse(_sequence_io(self.app).save_selected_sequence_as())
            self.assertEqual(save_calls, [])

    def test_sequence_save_to_path_writes_bytes_updates_trigger_and_marks_dirty(self):
        trigger = {"key": "a", "label": "Run", "actions": []}
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "run.json")
            with patch.object(self.app.dirty_tracker, "mark_trigger_set_dirty", side_effect=lambda: calls.append("dirty")), patch.object(
                self.app.trigger_panel,
                "refresh_triggers",
                side_effect=lambda: calls.append("triggers"),
            ), patch.object(self.app.trigger_panel, "refresh_actions", side_effect=lambda: calls.append("actions")), patch.object(
                self.app,
                "_set_flash_message",
                side_effect=lambda message, **kw: calls.append(("flash", message, kw)),
            ), patch.object(tkinter.messagebox, "showinfo", side_effect=lambda *args: calls.append(("info", args))):
                self.assertTrue(_sequence_io(self.app).save_sequence_to_path(trigger, path))
            self.assertEqual(
                Path(path).read_bytes(),
                _expected_json_bytes(
                    '{\n  "label": "Run",\n  "run_to_end": false,\n'
                    '  "run_to_end_delay_ms": 300,\n  "actions": []\n}'
                ),
            )
        self.assertEqual(trigger[self.app.config_service.INTERNAL_SEQUENCE_SOURCE_PATH], path)
        self.assertFalse(trigger[self.app.config_service.INTERNAL_SEQUENCE_IMPORTED])
        self.assertFalse(trigger[self.app.config_service.INTERNAL_SEQUENCE_DIRTY])
        self.assertEqual(
            calls,
            [
                "dirty",
                "triggers",
                "actions",
                ("flash", "出力シーケンスを保存しました。", {}),
                ("info", ("保存", f"出力シーケンスを保存しました:\n{path}")),
            ],
        )

    def test_sequence_save_to_path_exception_reports_failure(self):
        error = ValueError("disk full")
        with patch.object(self.app.config_service, "save_sequence_file", side_effect=error), patch.object(
            self.app,
            "_set_flash_message",
        ) as flash, patch.object(tkinter.messagebox, "showerror") as showerror:
            self.assertFalse(_sequence_io(self.app).save_sequence_to_path({"key": "a"}, "C:/bad.json"))
        flash.assert_called_once_with("出力シーケンス保存失敗: disk full", auto_clear=False)
        showerror.assert_called_once_with("保存失敗", "disk full")

    def test_sequence_load_no_selection_success_empty_and_exception(self):
        with patch.object(self.app.trigger_panel, "selected_trigger", return_value=None), patch.object(
            tkinter.messagebox,
            "showinfo",
        ) as showinfo:
            self.assertIsNone(_sequence_io(self.app).load_sequence_file())
        showinfo.assert_called_once_with("出力シーケンス", "読込先のトリガーを選択してください。")

        trigger = {"key": "a", "label": "Before", "actions": []}
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "run.json")
            Path(path).write_bytes(b'{"label": "Loaded", "run_to_end": true, "run_to_end_delay_ms": 3, "actions": []}')
            with patch.object(self.app.trigger_panel, "selected_trigger", return_value=trigger), patch.object(
                tkinter.filedialog,
                "askopenfilename",
                return_value=path,
            ) as ask_open, patch.object(self.app.dirty_tracker, "mark_trigger_set_dirty") as mark_dirty, patch.object(
                self.app.trigger_panel,
                "refresh_triggers",
            ) as refresh_triggers, patch.object(self.app.trigger_panel, "refresh_actions") as refresh_actions, patch.object(
                self.app,
                "_set_flash_message",
            ) as flash, patch.object(tkinter.messagebox, "showinfo") as showinfo:
                _sequence_io(self.app).load_sequence_file()
            self.assertEqual(ask_open.call_args.kwargs["title"], "出力シーケンスを読込")
            self.assertEqual(trigger["label"], "Loaded")
            mark_dirty.assert_called_once_with()
            refresh_triggers.assert_called_once_with()
            refresh_actions.assert_called_once_with()
            flash.assert_called_once_with("出力シーケンスを読み込みました。")
            showinfo.assert_called_once_with("読込", f"出力シーケンスを読み込みました:\n{path}")

        with patch.object(self.app.trigger_panel, "selected_trigger", return_value=trigger), patch.object(
            tkinter.filedialog,
            "askopenfilename",
            return_value="",
        ), patch.object(self.app.config_service, "load_sequence_file") as load:
            _sequence_io(self.app).load_sequence_file()
            load.assert_not_called()

        error = ValueError("bad sequence")
        with patch.object(self.app.trigger_panel, "selected_trigger", return_value=trigger), patch.object(
            tkinter.filedialog,
            "askopenfilename",
            return_value="C:/bad.json",
        ), patch.object(self.app.config_service, "load_sequence_file", side_effect=error), patch.object(
            self.app,
            "_set_flash_message",
        ) as flash, patch.object(tkinter.messagebox, "showerror") as showerror:
            _sequence_io(self.app).load_sequence_file()
        flash.assert_called_once_with("出力シーケンス読込失敗: bad sequence", auto_clear=False)
        showerror.assert_called_once_with("読込失敗", "bad sequence")


if __name__ == "__main__":
    unittest.main()
