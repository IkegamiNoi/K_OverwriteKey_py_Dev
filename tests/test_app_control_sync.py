import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from keyseq.presentation.app import App


class AppControlSyncTest(unittest.TestCase):
    def test_sync_control_vars_reloads_keyboard_layouts(self):
        app = SimpleNamespace(
            data={
                "hook_stop_key": "f12",
                "hook_toggle_key": "f11",
                "hook_keys_individual": True,
                "select_before_run": True,
                "keyboard_show_physical_key_labels": True,
            },
            ui_vars=SimpleNamespace(
                stop_key_var=Mock(),
                toggle_key_var=Mock(),
                hook_keys_individual_var=Mock(),
                select_before_run_var=Mock(),
                keyboard_show_physical_key_labels_var=Mock(),
            ),
            layout=Mock(),
        )

        App._sync_control_vars_from_data(app)

        app.layout.reload_keyboard_layouts.assert_called_once_with()
        app.layout.sync_keyboard_layout_controls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
