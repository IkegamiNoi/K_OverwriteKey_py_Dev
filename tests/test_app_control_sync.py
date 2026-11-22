import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.app_state import AppState
from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo


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
            state=AppState(),
        )

        App._sync_control_vars_from_data(app)

        app.layout.reload_keyboard_layouts.assert_called_once_with()
        app.layout.sync_keyboard_layout_controls.assert_not_called()


class CounterStartsSyncTest(unittest.TestCase):
    def setUp(self):
        self.app = SimpleNamespace(
            data={},
            state=AppState(),
            ui_vars=Mock(),
            layout=Mock(),
            config_service=Mock(),
            config_root="C:/config",
            dirty_tracker=Mock(),
            trigger_panel=Mock(),
            discard_retained_hook_keys=Mock(),
            _refresh_key_overlap_report=Mock(),
            _set_flash_message=Mock(),
        )
        self.app._sync_control_vars_from_data = lambda: App._sync_control_vars_from_data(self.app)
        self.app.state.set_counter_starts({"old": 8})
        self.app.state.counters["running"] = 13
        self.io = KeymapSetIo(self.app)

    def test_sync_control_vars_replaces_counter_starts_and_preserves_current_values(self):
        for data, expected in (
            ({"counter_starts": {"alpha": -2}}, {"alpha": -2}),
            ({"counter_starts": {}}, {}),
            ({}, {}),
        ):
            with self.subTest(data=data):
                self.app.data = data
                self.app._sync_control_vars_from_data()
                self.assertEqual(self.app.state.counters.starts, expected)
                self.assertEqual(dict(self.app.state.counters), {"running": 13})
        self.app.dirty_tracker.set_dirty.assert_not_called()

    def test_loaded_profile_syncs_counter_starts(self):
        self.app.data = {"counter_starts": {"loaded": -3}}

        self.io.apply_loaded_data_to_ui()

        self.assertEqual(self.app.state.counters.starts, {"loaded": -3})
        self.assertEqual(dict(self.app.state.counters), {"running": 13})

    def test_new_profile_clears_previous_counter_starts(self):
        self.app.config_service.new_base_data.return_value = {"keymaps": []}
        self.app.config_service.normalize_runtime_data.side_effect = lambda data: data

        self.io._start_new_data()

        self.assertEqual(self.app.state.counters.starts, {})
        self.assertEqual(dict(self.app.state.counters), {"running": 13})
        self.app.trigger_panel.refresh_actions.assert_called_once_with()

    def test_restore_sample_settings_replaces_previous_counter_starts(self):
        for sample, expected in (
            ({"keymaps": [], "counter_starts": {"sample": 4}}, {"sample": 4}),
            ({"keymaps": []}, {}),
        ):
            with self.subTest(sample=sample):
                self.app.state.set_counter_starts({"old": 8})
                self.app.trigger_panel.refresh_actions.reset_mock()
                self.app.config_service.new_default_data.return_value = sample
                with patch.object(self.io, "confirm_save_if_dirty", return_value=True), patch(
                    "keyseq.presentation.controllers.config_io.keymap_set_io.messagebox.askyesno",
                    return_value=True,
                ):
                    self.io.restore_default()
                self.assertEqual(self.app.state.counters.starts, expected)
                self.assertEqual(dict(self.app.state.counters), {"running": 13})
                self.app.trigger_panel.refresh_actions.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
