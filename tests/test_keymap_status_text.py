import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from keyseq.presentation.controllers.keymap_panel.keymap_panel_controller import KeymapPanelController


class KeymapStatusTextTest(unittest.TestCase):
    @staticmethod
    def _controller(label, *, hook_active=True, custom_input_enabled=True):
        app = SimpleNamespace(
            data={},
            keymap_service=SimpleNamespace(
                get_active_keymap_label=Mock(return_value=label),
            ),
            hook=SimpleNamespace(
                hook_active=hook_active,
                custom_input_enabled=custom_input_enabled,
            ),
        )
        controller = KeymapPanelController.__new__(KeymapPanelController)
        controller._app = app
        return controller

    def test_get_active_keymap_text_preserves_all_four_outputs(self):
        cases = (
            ("Main", False, True, "Main（フック停止中）"),
            ("Main", True, False, "Main（一時停止）"),
            ("Main", True, True, "Main"),
            ("", False, False, "（なし）"),
        )
        for label, hook_active, custom_input_enabled, expected in cases:
            with self.subTest(label=label, hook_active=hook_active,
                              custom_input_enabled=custom_input_enabled):
                controller = self._controller(
                    label,
                    hook_active=hook_active,
                    custom_input_enabled=custom_input_enabled,
                )
                self.assertEqual(controller.get_active_keymap_text(), expected)

    def test_get_active_keymap_name_returns_name_or_none_label(self):
        for label, expected in (("Main", "Main"), ("", "（なし）")):
            with self.subTest(label=label):
                controller = self._controller(label)
                self.assertEqual(controller.get_active_keymap_name(), expected)


if __name__ == "__main__":
    unittest.main()
