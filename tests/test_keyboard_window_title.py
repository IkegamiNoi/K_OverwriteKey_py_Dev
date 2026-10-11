import unittest

from keyseq.presentation.keyboard_window import keyboard_window_title


class KeyboardWindowTitleTest(unittest.TestCase):
    def test_title_includes_layout_name(self):
        self.assertEqual(keyboard_window_title("US配列", None), "Keyboard UI — US配列")

    def test_title_without_layout_name(self):
        self.assertEqual(keyboard_window_title("", None), "Keyboard UI")

    def test_editing_title_includes_key_and_cancel_hint(self):
        self.assertEqual(
            keyboard_window_title("US配列", "caps lock"),
            "Keyboard UI — 編集中: caps lock（Escでキャンセル）",
        )

    def test_editing_title_does_not_require_layout_name(self):
        self.assertEqual(
            keyboard_window_title("", "a"),
            "Keyboard UI — 編集中: a（Escでキャンセル）",
        )
