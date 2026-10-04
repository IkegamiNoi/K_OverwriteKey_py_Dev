"""KeymapSwitchBatchDialog の入力・キャンセル動作を固定する。"""

from types import SimpleNamespace
from tkinter import font as tkfont, ttk
import unittest
from unittest.mock import patch

from keyseq.presentation import app as app_module
from keyseq.presentation.button_width_rules import fixed_button_width_chars
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.dialogs.keymap_switch_batch_dialog import KeymapSwitchBatchDialog
from keyseq.presentation.hook_button_texts import CAPTURE_TEXTS


class KeymapSwitchBatchDialogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(StartupIo, "load_startup_and_config"):
            cls.app = app_module.App()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.app.update()
        self.dialogs = []

    def tearDown(self):
        for dialog in self.dialogs:
            if dialog.winfo_exists():
                dialog.destroy()
        self.app.update()

    def _dialog(self, rows, validate=None):
        dialog = KeymapSwitchBatchDialog(
            self.app,
            "切替キー設定",
            rows,
            validate or (lambda _values: None),
        )
        self.dialogs.append(dialog)
        return dialog

    def test_single_row_hides_kind_and_name_header(self):
        for kind in ("既存", "新規"):
            with self.subTest(kind=kind):
                dialog = self._dialog([(kind, "新しいキーマップ", "", "")])

                self.assertEqual(len(dialog.key_vars), 1)
                self.assertEqual(len(dialog.label_vars), 1)
                labels = [
                    str(child.cget("text"))
                    for child in dialog._row_frames[0].winfo_children()
                    if isinstance(child, ttk.Label)
                ]
                self.assertNotIn(kind, labels)
                self.assertNotIn("新しいキーマップ", labels)
                dialog.destroy()

    def test_each_row_can_capture_key_without_clear_button_and_width_stays_fixed(self):
        dialog = self._dialog([
            ("既存", "Main", "Main", "f8"),
            ("新規", "Other", "Other", ""),
        ])

        self.assertFalse(hasattr(dialog, "clear_buttons"))
        self.assertFalse(hasattr(dialog, "_clear_key"))
        for row in dialog._row_frames:
            button_labels = [
                str(child.cget("text"))
                for child in row.winfo_children()
                if isinstance(child, ttk.Button)
            ]
            self.assertNotIn("クリア", button_labels)

        widths = []
        for button in dialog.capture_buttons:
            font_spec = ttk.Style(button).lookup("TButton", "font")
            font = tkfont.Font(root=button, font=font_spec or "TkDefaultFont")
            expected = fixed_button_width_chars(
                [font.measure(text) for text in CAPTURE_TEXTS], font.measure("0")
            )
            width = int(button.cget("width"))
            self.assertEqual(width, expected)
            widths.append(width)

        dialog._start_capture(0)
        self.assertEqual(int(dialog.capture_buttons[0].cget("width")), widths[0])
        dialog._on_capture_keypress(SimpleNamespace(keysym="F8"))
        self.assertEqual(dialog.key_vars[0].get(), "f8")
        dialog._start_capture(1)
        self.assertEqual(int(dialog.capture_buttons[1].cget("width")), widths[1])
        dialog._on_capture_keypress(SimpleNamespace(keysym="F9"))

        self.assertEqual(dialog.key_vars[1].get(), "f9")
        self.assertFalse(dialog._capturing)
        self.assertEqual(
            [int(button.cget("width")) for button in dialog.capture_buttons], widths
        )

    def test_validation_error_keeps_dialog_open_and_focuses_row(self):
        dialog = self._dialog(
            [("既存", "Main", "Main", "f8"), ("新規", "Other", "Other", "f9")],
            validate=lambda _values: (1, "切替キーが重複しています"),
        )

        # アプリにフォーカスが無い環境では Tk が焦点を記録しないため、エラーの行の欄へ focus_set したことで確かめる
        with patch("keyseq.presentation.dialogs.keymap_switch_batch_dialog.messagebox.showerror") as showerror,                 patch.object(dialog.key_entries[1], "focus_set") as focus_set:
            dialog._ok()
            self.app.update_idletasks()

        showerror.assert_called_once_with("設定できません", "切替キーが重複しています", parent=dialog)
        self.assertTrue(dialog.winfo_exists())
        focus_set.assert_called_once_with()
        self.assertIsNone(dialog.result)

    def test_ok_normalizes_keys_trims_labels_and_closes(self):
        seen = []
        dialog = self._dialog(
            [("新規", "New", "", "")],
            validate=lambda values: seen.append(values) or None,
        )
        dialog.key_vars[0].set(" F10 ")
        dialog.label_vars[0].set("  Main map  ")

        dialog._ok()

        expected = [{"key": "f10", "label": "Main map"}]
        self.assertEqual(seen, [expected])
        self.assertEqual(dialog.result, expected)
        self.assertFalse(dialog.winfo_exists())

    def test_cancel_button_and_escape_leave_none_result(self):
        by_button = self._dialog([("新規", "One", "", "")])
        by_button._cancel()
        self.assertIsNone(by_button.result)

        by_escape = self._dialog([("新規", "Two", "", "")])
        by_escape._on_escape()
        self.assertIsNone(by_escape.result)
        self.assertFalse(by_escape.winfo_exists())

    def test_escape_during_capture_stops_capture_without_closing(self):
        dialog = self._dialog([("新規", "One", "", "")])
        dialog._start_capture(0)

        dialog._on_escape()

        self.assertFalse(dialog._capturing)
        self.assertTrue(dialog.winfo_exists())
        self.assertIsNone(dialog.result)

        # 押しっぱなしによる自動反復では閉じず、キーを離した後の Escape で閉じる。
        dialog._on_escape()
        self.assertTrue(dialog.winfo_exists())
        dialog._on_escape_release()
        dialog._on_escape()
        self.assertFalse(dialog.winfo_exists())

    def test_window_close_protocol_cancels(self):
        dialog = self._dialog([("新規", "One", "", "")])
        close_command = dialog.protocol("WM_DELETE_WINDOW")

        self.assertTrue(close_command)
        dialog.tk.call(close_command)

        self.assertIsNone(dialog.result)
        self.assertFalse(dialog.winfo_exists())

    def test_six_rows_use_scrollable_body_with_height_limit(self):
        dialog = self._dialog([
            ("貼り付け", f"Map {index}", f"Map {index}", "")
            for index in range(6)
        ])
        self.app.update_idletasks()

        self.assertIsNotNone(dialog._canvas)
        self.assertEqual(int(dialog._canvas.cget("height")), dialog._SCROLL_HEIGHT)
        self.assertGreater(dialog._rows_frame.winfo_reqheight(), dialog._canvas.winfo_height())
