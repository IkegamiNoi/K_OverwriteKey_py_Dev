"""ヘッダの文言切替・フォント変更時の要求幅を実際の Tk で確認する。"""

import unittest
from tkinter import font as tkfont, ttk
from unittest.mock import patch

from keyseq.presentation import app as app_module, theme
from keyseq.presentation.app import App
from keyseq.presentation.button_width_rules import fixed_button_width_chars
from keyseq.presentation.hook_button_texts import (
    CAPTURE_ACTIVE_TEXT, CAPTURE_IDLE_TEXT, CAPTURE_TEXTS,
    HOOK_TOGGLE_TEXTS, TRIGGER_DISABLE_TEXT, TRIGGER_ENABLE_TEXT,
    TRIGGER_TOGGLE_TEXTS,
)


class HeaderButtonWidthsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sizes = dict(theme._BASE_FONT_SIZES)
        cls.addClassCleanup(cls._restore_sizes, sizes)
        for target, name, value in (
            (app_module.ConfigService, "load_startup", {}),
            (app_module.StartupIo, "write_startup", True),
            (app_module.ConfigService, "save_startup", None),
        ):
            patcher = patch.object(target, name, return_value=value)
            patcher.start()
            cls.addClassCleanup(patcher.stop)
        cls.app = App()
        cls.addClassCleanup(cls.app.destroy)
        cls.addClassCleanup(cls.app.pane_layout.cancel_window_width_save)
        cls.app.update()

    @staticmethod
    def _restore_sizes(sizes: dict) -> None:
        theme._BASE_FONT_SIZES.clear()
        theme._BASE_FONT_SIZES.update(sizes)

    def setUp(self) -> None:
        frame = self.app.full_view.hook_frame
        self.button_texts = (
            (frame.stop_key_capture_btn, CAPTURE_TEXTS),
            (frame.toggle_key_capture_btn, CAPTURE_TEXTS),
            (frame.hook_toggle_btn, HOOK_TOGGLE_TEXTS),
            (frame.trigger_toggle_btn, TRIGGER_TOGGLE_TEXTS),
        )
        self.original_texts = [(button, button.cget("text"))
                               for button, _texts in self.button_texts]

    def tearDown(self) -> None:
        self.app.stop_key_capture.stop(cancel=True)
        self.app._apply_font_delta(0)
        for button, text in self.original_texts:
            button.configure(text=text)
        self.app.show_full_view()
        self.app.update_idletasks()
        self.app.pane_layout.cancel_window_width_save()

    def test_full_buttons_keep_width_for_all_texts_and_font_sizes(self) -> None:
        for delta in (-3, 0, 3):
            self.app._apply_font_delta(delta)
            self.app.update_idletasks()
            for button, texts in self.button_texts:
                width = button.winfo_reqwidth()
                for text in texts:
                    with self.subTest(delta=delta, button=str(button), text=text):
                        button.configure(text=text)
                        natural = ttk.Button(button.master, text=text)
                        try:
                            self.app.update_idletasks()
                            self.assertEqual(button.winfo_reqwidth(), width)
                            self.assertGreaterEqual(width, natural.winfo_reqwidth())
                        finally:
                            natural.destroy()

    def test_trigger_toggle_texts_and_key_labels_use_pause_resume_wording(self) -> None:
        self.assertEqual(
            TRIGGER_TOGGLE_TEXTS,
            ("キーマップ一時停止", "キーマップ再開"),
        )
        self.assertEqual(TRIGGER_DISABLE_TEXT, "キーマップ一時停止")
        self.assertEqual(TRIGGER_ENABLE_TEXT, "キーマップ再開")

        full_label = self.app.full_view.hook_frame.full_hook_line2.grid_slaves(
            row=1, column=0
        )[0]
        compact_label = self.app.compact_view.hook_frame.compact_hook_line2.grid_slaves(
            row=1, column=0
        )[0]
        self.assertEqual(full_label.cget("text"), "一時停止/再開キー: ")
        self.assertEqual(compact_label.cget("text"), "一時停止/再開キー: ")

    def test_font_change_reapplies_width_in_full_and_compact_views(self) -> None:
        for compact in (False, True):
            with self.subTest(compact=compact):
                self.app._apply_font_delta(0)
                if compact:
                    self.app.show_compact_view()
                self.app._apply_font_delta(3)
                for button, texts in self.button_texts:
                    font = tkfont.Font(
                        root=button, font=ttk.Style(button).lookup("TButton", "font")
                    )
                    expected = fixed_button_width_chars(
                        [font.measure(text) for text in texts], font.measure("0")
                    )
                    self.assertEqual(int(button.cget("width")), expected)

    def test_compact_buttons_have_no_fixed_width(self) -> None:
        frame = self.app.compact_view.hook_frame
        for delta in (0, 3):
            self.app._apply_font_delta(delta)
            for button in (frame.hook_toggle_btn, frame.trigger_toggle_btn):
                with self.subTest(delta=delta, button=str(button)):
                    self.assertIn(str(button.cget("width")), ("0", ""))

    def test_keyboard_layout_dropdown_widths(self) -> None:
        self.assertEqual(
            int(self.app.full_view.display_frame.keyboard_layout_combo.cget("width")), 12
        )
        self.assertEqual(
            int(self.app.compact_view.display_frame.compact_keyboard_layout_combo.cget("width")),
            12,
        )

    def test_capture_start_and_cancel_keep_width_and_restore_suspend_count(self) -> None:
        button = self.app.full_view.hook_frame.stop_key_capture_btn
        self.app.update_idletasks()
        width = button.winfo_reqwidth()
        suspend_count = self.app.hook.hook_suspend_count
        try:
            self.app.stop_key_capture.start()
            self.app.update_idletasks()
            self.assertEqual(button.cget("text"), CAPTURE_ACTIVE_TEXT)
            self.assertEqual(button.winfo_reqwidth(), width)
            self.assertEqual(self.app.hook.hook_suspend_count, suspend_count + 1)
        finally:
            self.app.stop_key_capture.stop(cancel=True)
        self.assertEqual(button.cget("text"), CAPTURE_IDLE_TEXT)
        self.assertEqual(self.app.hook.hook_suspend_count, suspend_count)


if __name__ == "__main__":
    unittest.main()
