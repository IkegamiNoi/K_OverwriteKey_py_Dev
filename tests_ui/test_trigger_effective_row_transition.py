import unittest
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.application.sequence_steps import LoopFrame
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.controllers.trigger_panel import action_edit as action_edit_module
from keyseq.presentation.controllers.trigger_panel import trigger_panel_controller as panel_module
from keyseq.presentation.list_clipboard import CLIP_ACTIONS
from tests_ui.test_trigger_effective_row import _DialogResult, make_runtime


class _ActionDialogResult:
    def __init__(self, app, result):
        self.app = app
        self.result = result
        self.append_to_end = True

    def wait_window(self):
        self.app._dialog_result = self.result


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
        with patch.object(self.app.sequence_runner, "has_active_execution") as active, \
             patch.object(self.app.sequence_runner, "cancel_pending_wait") as cancel:
            self.delete_selected()
        identity = self.app._active_trigger_set_id()
        active.assert_not_called()
        cancel.assert_called_once_with("f1")
        self.assertNotIn("f1", self.app._indices)
        self.assertNotIn("f1", self.app.state.history_for(identity))
        self.assertNotIn("f1", self.app.state.loop_frames_for(identity))
        self.assertNotIn("f1", self.app.state.deferred_counters_for(identity))

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

    def test_gray_sequence_edits_leave_effective_runtime_state_untouched(self):
        panel = self.app.trigger_panel
        edit = panel._action_edit
        operations = ("add", "duplicate", "paste", "edit", "delete", "move")
        for operation in operations:
            with self.subTest(operation=operation):
                self.rows[1]["actions"] = [
                    {"type": "text", "value": value} for value in ("one", "two", "three")
                ]
                self.app._selected_trigger_idx = 1
                with patch.object(panel, "selected_action_index", return_value=0), \
                     patch.object(panel, "refresh_actions"), \
                     patch.object(self.app.sequence_runner, "reset_loop_frames") as reset:
                    if operation in ("add", "edit"):
                        result = {"type": "text", "value": "changed"}
                        with patch.object(action_edit_module, "ActionDialog", return_value=
                                          _ActionDialogResult(self.app, result)):
                            getattr(edit, f"{operation}_action")()
                    elif operation == "duplicate":
                        edit.duplicate_action()
                    elif operation == "paste":
                        self.app.list_clipboard.copy(CLIP_ACTIONS, [
                            {"type": "text", "value": "pasted"},
                        ])
                        edit.paste_actions()
                    elif operation == "delete":
                        with patch.object(action_edit_module.messagebox, "askyesno", return_value=True):
                            edit.delete_action()
                    else:
                        edit.move_action_range(0, 0, 1)
                    reset.assert_not_called()
                identity = self.app._active_trigger_set_id()
                self.assertEqual(self.app._indices["f1"], 2)
                self.assertIs(self.app.state.history_for(identity)["f1"], self.history)
                self.assertIs(self.app.state.loop_frames_for(identity)["f1"], self.frames)
                self.assertIs(self.app.state.deferred_counters_for(identity)["f1"], self.deferred)

    def test_effective_sequence_edit_still_resets_loop_frames(self):
        self.app._selected_trigger_idx = 0
        with patch.object(self.app.trigger_panel, "selected_action_index", return_value=None), \
             patch.object(self.app.trigger_panel, "refresh_actions"), \
             patch.object(action_edit_module, "ActionDialog", return_value=
                          _ActionDialogResult(self.app, {"type": "text", "value": "added"})), \
             patch.object(self.app.sequence_runner, "reset_loop_frames") as reset:
            self.app.trigger_panel.add_action()
        reset.assert_called_once_with("f1")

    def test_stop_overlap_label_edit_is_allowed_but_key_change_is_rejected(self):
        self.app._selected_trigger_idx = 3
        with patch.object(panel_module, "TriggerDialog", return_value=_DialogResult({
            "key": "f12", "label": "Edited stop overlap",
        })), patch.object(panel_module.messagebox, "showerror") as showerror, \
             patch.object(self.app.trigger_service, "is_stop_key_conflict", wraps=
                          self.app.trigger_service.is_stop_key_conflict) as stop_conflict:
            self.app.trigger_panel.rename_trigger()
        self.assertEqual(self.rows[3]["label"], "Edited stop overlap")
        stop_conflict.assert_not_called()
        showerror.assert_not_called()

        del self.rows[3]
        self.app._selected_trigger_idx = 2
        with patch.object(panel_module, "TriggerDialog", return_value=_DialogResult({
            "key": "f12", "label": "Changed key",
        })), patch.object(panel_module.messagebox, "showerror") as showerror:
            self.app.trigger_panel.rename_trigger()
        self.assertEqual(self.rows[2]["key"], "caller")
        showerror.assert_called_once()

    def test_renamed_gray_row_refreshes_sequence_marker_when_it_becomes_effective(self):
        self.app._selected_trigger_idx = 1
        with patch.object(panel_module, "TriggerDialog", return_value=_DialogResult({
            "key": "f2", "label": "Now effective",
        })):
            self.app.trigger_panel.rename_trigger()
        self.assertEqual(self.rows[1]["key"], "f2")
        self.assertIn("▶", self.app.full_view.action_list.get(0))

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
