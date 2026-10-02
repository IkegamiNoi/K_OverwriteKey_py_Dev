import unittest
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.application.sequence_steps import LoopFrame
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.controllers.trigger_panel import trigger_panel_controller as panel_module
from tests_ui.test_trigger_effective_row import _DialogResult, make_runtime


class TriggerEffectiveRowTransitionUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(StartupIo, "load_startup_and_config"):
            cls.app = App()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.original_data = self.app.data
        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime())
        self.rows[0]["actions"] = [{"type": "text", "value": "first"}]
        self.rows[1]["actions"] = [{"type": "text", "value": "shadow"}]
        self.rows[0]["actions"] *= 3
        self.app._indices = {"f1": 2}
        self.app._selected_trigger_idx = 1
        self.app.state.run_to_end_key = None
        self.app.state.run_to_end_paused = False
        self.app.state.pending_steps.clear()
        identity = self.app._active_trigger_set_id()
        self.history = [object()]
        self.frames = [LoopFrame(start=0, iteration=2)]
        self.deferred = [("count", "+1")]
        self.app.state.history_for(identity)["f1"] = self.history
        self.app.state.loop_frames_for(identity)["f1"] = self.frames
        self.app.state.deferred_counters_for(identity)["f1"] = self.deferred
        self.app.state.last_trigger = (identity, "f1")
        self.app.trigger_panel.refresh_triggers()

    def tearDown(self):
        self.app.state.run_to_end_key = None
        self.app.state.run_to_end_paused = False
        self.app.sequence_runner.cancel_pending_waits()
        self.app.state.reset_indices()
        self.app.data = self.original_data
        self.app._indices = {}
        self.app._selected_trigger_idx = 0
        self.app._compact_mode = False
        self.app.trigger_panel.refresh_triggers()
        self.app.dirty_tracker.set_dirty(False)

    @property
    def rows(self):
        return self.app.data["keymaps"][0]["triggers"]

    def delete_selected(self):
        with patch.object(panel_module.messagebox, "askyesno", return_value=True):
            self.app.trigger_panel.delete_trigger()

    def test_gray_row_deletion_preserves_effective_position_and_history(self):
        self.app.state.run_to_end_key = "f1"
        with patch.object(self.app.sequence_runner, "cancel_pending_wait") as cancel, \
             patch.object(self.app.sequence_runner, "has_active_execution") as active:
            self.delete_selected()
        self.assertEqual(self.app._indices["f1"], 2)
        self.assertIs(self.app.state.history_for(self.app._active_trigger_set_id())["f1"], self.history)
        self.assertIs(self.app.state.loop_frames_for(self.app._active_trigger_set_id())["f1"], self.frames)
        cancel.assert_not_called()
        active.assert_not_called()

    def test_last_row_deletion_keeps_existing_cleanup_without_replacement_guard(self):
        del self.rows[1]
        self.app._selected_trigger_idx = 0
        self.app.state.run_to_end_key = "f1"
        with patch.object(self.app.sequence_runner, "has_active_execution") as active:
            self.delete_selected()
        active.assert_not_called()
        self.assertNotIn("f1", self.app._indices)
        self.assertNotIn("f1", self.app.state.history_for(self.app._active_trigger_set_id()))

    def test_effective_deletion_replaces_row_and_clears_state(self):
        self.app._selected_trigger_idx = 0
        successor = self.rows[1]
        self.delete_selected()
        identity = self.app._active_trigger_set_id()
        self.assertIs(self.rows[0], successor)
        self.assertEqual(self.app._indices["f1"], 0)
        self.assertNotIn("f1", self.app.state.history_for(identity))
        self.assertNotIn("f1", self.app.state.loop_frames_for(identity))
        self.assertNotIn("f1", self.app.state.deferred_counters_for(identity))
        self.assertIsNone(self.app.state.last_trigger)

    def test_active_and_paused_replacements_are_rejected_before_mutation(self):
        self.app._selected_trigger_idx = 0
        original = list(self.rows)
        for paused in (False, True):
            for operation in ("delete", "rename"):
                with self.subTest(paused=paused, operation=operation):
                    self.app.state.run_to_end_key = "f1"
                    self.app.state.run_to_end_paused = paused
                    with patch.object(self.app, "_set_flash_message") as flash, \
                         patch.object(panel_module, "TriggerDialog", return_value=_DialogResult({
                             "key": "f2", "label": "Changed",
                         })), \
                         patch.object(self.app.dirty_tracker, "mark_trigger_set_dirty") as dirty:
                        if operation == "delete":
                            self.delete_selected()
                        else:
                            self.app.trigger_panel.rename_trigger()
                    self.assertEqual(self.rows, original)
                    self.assertEqual(self.rows[0]["key"], "f1")
                    self.assertEqual(self.rows[0]["label"], "First")
                    self.assertEqual(self.app._indices["f1"], 2)
                    flash.assert_called_once()
                    self.assertIn("f1", flash.call_args.args[0])
                    self.assertIn("実行中", flash.call_args.args[0])
                    dirty.assert_not_called()

    def test_effective_rename_transfers_state_before_old_key_cleanup(self):
        self.app._selected_trigger_idx = 0
        with patch.object(panel_module, "TriggerDialog", return_value=_DialogResult({
            "key": "f2", "label": "Changed",
        })):
            self.app.trigger_panel.rename_trigger()
        identity = self.app._active_trigger_set_id()
        self.assertEqual(self.app._indices["f2"], 2)
        self.assertEqual(self.app._indices["f1"], 0)
        self.assertIs(self.app.state.history_for(identity)["f2"], self.history)
        self.assertNotIn("f1", self.app.state.history_for(identity))
        self.assertIs(self.app.state.loop_frames_for(identity)["f2"], self.frames)
        self.assertIs(self.app.state.deferred_counters_for(identity)["f2"], self.deferred)
        self.assertEqual(self.app.state.last_trigger, (identity, "f2"))
        self.assertEqual(self.rows[2]["actions"][0]["target"], "f2")

    def test_gray_selection_has_own_actions_no_pointer_or_runtime_changes(self):
        panel = self.app.trigger_panel
        listing = self.app.full_view.action_list
        panel.set_selected_trigger_index(1)
        self.assertIn("shadow", listing.get(0))
        self.assertTrue(all("▶" not in row for row in listing.get(0, "end")))
        listing.selection_set(0)
        with patch.object(self.app.sequence_runner, "reset_loop_frames") as reset:
            panel.on_action_list_select()
            panel.on_action_list_focus_index_change(SimpleNamespace(state=0, keysym="Down"))
            panel.select_next_action_row("f1")
        reset.assert_not_called()
        self.assertEqual(self.app._indices["f1"], 2)
        self.assertIs(self.app.state.history_for(self.app._active_trigger_set_id())["f1"], self.history)
        self.assertNotIn("選択中の次:", self.app.ui_vars.status_var.get())
        self.app._compact_mode = True
        panel.update_status()
        self.assertNotIn("次:", self.app.ui_vars.status_var.get())
        self.assertEqual(panel.get_next_action_summary("f1"), "")


if __name__ == "__main__":
    unittest.main()
