from types import SimpleNamespace
import unittest

from keyseq.presentation.views.menu_bar import (
    _on_aqua_preset_shortcut,
    is_aqua_preset_keycode,
)


class AquaPresetShortcutTests(unittest.TestCase):
    def test_keycode_recognizes_only_p(self):
        self.assertTrue(is_aqua_preset_keycode(35 << 24))
        self.assertFalse(is_aqua_preset_keycode(34 << 24))
        self.assertFalse(is_aqua_preset_keycode(0xFF << 24))

    def test_handler_calls_app_only_for_p_keycode(self):
        calls = []
        app = SimpleNamespace(
            _on_shortcut_open_preset_manager=lambda event: calls.append(event) or "opened"
        )
        p_event = SimpleNamespace(keycode=35 << 24)
        other_event = SimpleNamespace(keycode=34 << 24)

        self.assertEqual(_on_aqua_preset_shortcut(app, p_event), "opened")
        self.assertIsNone(_on_aqua_preset_shortcut(app, other_event))
        self.assertEqual(calls, [p_event])


if __name__ == "__main__":
    unittest.main()
