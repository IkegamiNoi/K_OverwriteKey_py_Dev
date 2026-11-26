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


class FlashUnderlayTest(unittest.TestCase):
    def setUp(self):
        self.app = SimpleNamespace(
            _flash_message="",
            _flash_underlay="",
            _flash_after_id=None,
            _compact_mode=False,
            ui_vars=SimpleNamespace(
                flash_message_var=Mock(),
                flash_message_full_var=Mock(),
            ),
            after=Mock(return_value="flash-timer"),
            after_cancel=Mock(),
            _update_file_status=Mock(),
        )
        for name in (
            "_status_bar_text", "_write_status_bar_text", "_refresh_status_bar", "_show_flash_area",
            "set_flash_underlay", "_set_flash_message", "_clear_flash_message",
        ):
            setattr(self.app, name, getattr(App, name).__get__(self.app))

    def _assert_display(self, text):
        self.app.ui_vars.flash_message_var.set.assert_called_with(text)
        self.app.ui_vars.flash_message_full_var.set.assert_called_with(text)

    def test_underlay_displays_and_clears_without_becoming_temporary_message(self):
        self.app.set_flash_underlay("warning")
        self._assert_display("warning")
        self.assertEqual(self.app._flash_message, "")

        self.app.set_flash_underlay("")
        self._assert_display("")
        self.assertEqual(self.app._flash_underlay, "")

    def test_temporary_message_expires_back_to_underlay(self):
        self.app.set_flash_underlay("warning")
        self.app.after.reset_mock()

        self.app._set_flash_message("added")

        self._assert_display("added")
        self.assertEqual(self.app._flash_message, "added")
        self.app.after.assert_called_once_with(4000, self.app._clear_flash_message)
        self.app.after.call_args.args[1]()
        self._assert_display("warning")
        self.assertEqual(self.app._flash_message, "")
        self.assertIsNone(self.app._flash_after_id)

    def test_empty_message_cancels_timer_and_restores_underlay(self):
        self.app.set_flash_underlay("warning")
        self.app.after.reset_mock()
        self.app._set_flash_message("added")
        self.app.after.assert_called_once()
        self.app.after.reset_mock()
        self.app.after_cancel.reset_mock()

        self.app._set_flash_message("")

        self._assert_display("warning")
        self.assertEqual(self.app._flash_message, "")
        self.app.after_cancel.assert_called_once_with("flash-timer")
        self.app.after.assert_not_called()

    def test_changing_underlay_preserves_temporary_message_until_clear(self):
        self.app._set_flash_message("running", auto_clear=False)
        for underlay in ("new warning", ""):
            with self.subTest(underlay=underlay):
                self.app.set_flash_underlay(underlay)
                self._assert_display("running")
                self.assertEqual(self.app._flash_message, "running")
                self.assertEqual(self.app._flash_underlay, underlay)
        self.app._clear_flash_message()
        self._assert_display("")

    def test_persistent_message_cancels_existing_timer_without_rescheduling(self):
        self.app.set_flash_underlay("warning")
        self.app.after.reset_mock()
        self.app._set_flash_message("added")
        self.app.after.assert_called_once()
        self.app.after.reset_mock()
        self.app.after_cancel.reset_mock()

        self.app._set_flash_message("running", auto_clear=False)

        self._assert_display("running")
        self.app.after_cancel.assert_called_once_with("flash-timer")
        self.app.after.assert_not_called()
        self.app._clear_flash_message()
        self._assert_display("warning")

    def test_status_refresh_uses_temporary_message_then_underlay(self):
        self.app.set_flash_underlay("warning")
        self.app._set_flash_message("running", auto_clear=False)
        self.app._update_file_status.reset_mock()

        self.app._refresh_status_bar()

        self.app._update_file_status.assert_called_once_with()
        self._assert_display("running")
        self.app._clear_flash_message()
        self.app._refresh_status_bar()
        self._assert_display("warning")
        self.assertEqual(self.app._flash_message, "")


if __name__ == "__main__":
    unittest.main()
