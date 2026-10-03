"""Full-view trigger range operations and selection integration."""

import unittest
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.controllers.trigger_panel import trigger_list_edit as edit_module
from keyseq.presentation.list_clipboard import CLIP_ACTIONS, CLIP_TRIGGERS
from keyseq.presentation.listbox_range_drag import select_range
from tests_ui.click_time import next_click_time


def make_runtime():
    return {
        "keymaps": [{
            "id": "main", "label": "Main", "mappings": {},
            "triggers": [
                {"key": key, "label": label, "suppress": False,
                 "run_to_end": False, "run_to_end_delay_ms": 123,
                 "actions": [{"type": "text", "value": label}] * 3}
                for key, label in zip(("f1", "f2", "F1", "f3"), ("a", "a (2)", "", "a"))
            ],
        }],
        "active_keymap_id": "main", "hook_stop_key": "f12",
        "hook_toggle_key": "f11", "keymap_switch_keys": {},
    }


class TriggerListOperationsTest(unittest.TestCase):
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
        self.app.state.reset_indices()
        self.app._indices = {"f1": 2, "f2": 1, "f3": 0}
        self.app._compact_mode = False
        self.app._selected_trigger_idx = 0
        self.panel = self.app.trigger_panel
        self.listbox = self.app.full_view.trigger_box.trigger_list
        self.panel.sync_trigger_selection_to_views()
        self.panel.refresh_triggers()
        self.app.list_clipboard.clear()
        self.app.dirty_tracker.set_dirty(False)
        self.app.update()

    def tearDown(self):
        self.app.sequence_runner.cancel_pending_waits()
        self.app.state.reset_indices()
        self.app.data = self.original_data
        self.app._selected_trigger_idx = 0
        self.app._compact_mode = False
        self.app.list_clipboard.clear()
        self.panel.sync_trigger_selection_to_views()
        self.panel.refresh_triggers()
        self.app.dirty_tracker.set_dirty(False)

    @property
    def rows(self):
        return self.app.data["keymaps"][0]["triggers"]

    def select(self, start, end, *, active=None):
        select_range(self.listbox, start, end, active=active)
        self.panel.on_trigger_list_mouse_release(self.listbox)

    def seed_frames(self):
        identity = self.app._active_trigger_set_id()
        self.app.state.loop_frames_for(identity)["f1"] = [object()]
        return identity

    def test_move_selects_block_and_refreshes_overlap_hook_and_keyboard(self):
        before = list(self.rows)
        with patch.object(self.app, "_refresh_key_overlap_report", wraps=self.app._refresh_key_overlap_report) as overlap, \
             patch.object(self.app.layout, "refresh_keyboard_window") as keyboard, \
             patch.object(self.app.hook, "hook_active", True), \
             patch.object(self.app.hook, "start_hook") as hook, \
             patch.object(self.app.dirty_tracker, "mark_trigger_set_dirty") as dirty:
            self.assertTrue(self.panel.on_trigger_list_move(0, 1, 2))
        self.assertEqual(self.rows, before[2:] + before[:2])
        self.assertEqual(tuple(self.listbox.curselection()), (2, 3))
        self.assertEqual(self.panel.selected_trigger_index(), 3)
        overlap.assert_called_once()
        keyboard.assert_called_once()
        hook.assert_called_once()
        dirty.assert_called_once()

    def test_unchanged_move_does_not_mark_dirty_or_refresh(self):
        with patch.object(self.app.dirty_tracker, "mark_trigger_set_dirty") as dirty, \
             patch.object(self.panel, "refresh_triggers") as refresh:
            self.assertTrue(self.panel.on_trigger_list_move(0, 1, 0))
        dirty.assert_not_called()
        refresh.assert_not_called()

    def test_replacement_move_clears_only_replaced_key_state(self):
        identity = self.seed_frames()
        with patch.object(self.app.sequence_runner, "has_active_execution", return_value=False):
            self.assertTrue(self.panel.on_trigger_list_move(2, 2, 0))
        self.assertEqual(self.app._indices["f1"], 0)
        self.assertEqual(self.app._indices["f2"], 1)
        self.assertNotIn("f1", self.app.state.loop_frames_for(identity))

    def test_active_replacement_move_is_rejected_before_mutation(self):
        before = list(self.rows)
        with patch.object(self.app.sequence_runner, "has_active_execution", return_value=True), \
             patch.object(self.app, "_set_flash_message") as flash, \
             patch.object(self.app.dirty_tracker, "mark_trigger_set_dirty") as dirty:
            self.assertFalse(self.panel.on_trigger_list_move(2, 2, 0))
        self.assertEqual(self.rows, before)
        self.assertEqual(self.app._indices["f1"], 2)
        self.assertIn("実行中", flash.call_args.args[0])
        dirty.assert_not_called()

    def test_range_delete_confirms_once_and_clears_replaced_and_removed_keys(self):
        identity = self.seed_frames()
        survivors = self.rows[2:]
        self.select(0, 1)
        with patch.object(edit_module.messagebox, "askyesno", return_value=True) as confirm, \
             patch.object(self.app.sequence_runner, "has_active_execution", return_value=False), \
             patch.object(self.app.dirty_tracker, "mark_trigger_set_dirty") as dirty:
            self.panel.delete_trigger()
        confirm.assert_called_once_with("確認", "トリガー 2 件を削除しますか？")
        self.assertEqual(self.rows, survivors)
        self.assertEqual(tuple(self.listbox.curselection()), (1,))
        self.assertEqual(self.app._indices["f1"], 0)
        self.assertNotIn("f2", self.app._indices)
        self.assertNotIn("f1", self.app.state.loop_frames_for(identity))
        dirty.assert_called_once()

    def test_active_replacement_range_delete_and_cancel_leave_rows_unchanged(self):
        self.select(0, 1)
        before = list(self.rows)
        with patch.object(edit_module.messagebox, "askyesno", return_value=True), \
             patch.object(self.app.sequence_runner, "has_active_execution", return_value=True), \
             patch.object(self.app, "_set_flash_message") as flash, \
             patch.object(self.app.dirty_tracker, "mark_trigger_set_dirty") as dirty:
            self.panel.delete_trigger()
        self.assertEqual(self.rows, before)
        self.assertIn("実行中", flash.call_args.args[0])
        self.assertEqual(tuple(self.listbox.curselection()), (0, 1))
        dirty.assert_not_called()
        with patch.object(edit_module.messagebox, "askyesno", return_value=False):
            self.panel.delete_trigger()
        self.assertEqual(self.rows, before)

    def test_copy_paste_detaches_numbers_labels_and_marks_new_sequences_dirty(self):
        for row in self.rows:
            row.update({"_source_path": "old.json", "_reference": "old", "_dirty": True})
        self.select(0, 3)
        self.assertEqual(self.panel.copy_triggers(), "break")
        self.rows[0]["actions"][0]["value"] = "edited after copy"
        with patch.object(self.app, "mark_sequence_dirty") as dirty:
            self.assertEqual(self.panel.paste_triggers(), "break")
        pasted = self.rows[4:]
        self.assertEqual([row["label"] for row in pasted], ["a (3)", "a (4)", "", "a (5)"])
        self.assertEqual(tuple(self.listbox.curselection()), (4, 5, 6, 7))
        self.assertEqual(self.panel.selected_trigger_index(), 7)
        self.assertEqual(dirty.call_count, 4)
        self.assertEqual([call.args[0] for call in dirty.call_args_list], pasted)
        self.assertTrue(all(not key.startswith("_") for row in pasted for key in row))
        self.assertEqual(pasted[0]["actions"][0]["value"], "a")
        self.assertFalse(pasted[0]["suppress"])
        self.assertEqual(pasted[0]["run_to_end_delay_ms"], 123)
        self.assertIsNot(pasted[0]["actions"], self.rows[0]["actions"])
        self.assertIn("上のトリガーと重複", self.listbox.get(4))
        self.assertEqual(self.listbox.itemcget(4, "foreground"), "#888888")

    def test_paste_marks_real_new_rows_unsaved(self):
        self.select(0, 0)
        self.panel.copy_triggers()
        self.panel.paste_triggers()
        self.assertTrue(self.rows[-1][self.app.config_service.INTERNAL_SEQUENCE_DIRTY])
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

    def test_empty_or_wrong_clipboard_kind_is_a_no_op_and_handlers_break(self):
        for kind in (None, CLIP_ACTIONS):
            with self.subTest(kind=kind):
                if kind is not None:
                    self.app.list_clipboard.copy(kind, [{"type": "text", "value": "x"}])
                with patch.object(self.app.dirty_tracker, "mark_trigger_set_dirty") as dirty:
                    self.assertEqual(self.panel.paste_triggers(), "break")
                self.assertEqual(len(self.rows), 4)
                dirty.assert_not_called()
        self.listbox.selection_clear(0, "end")
        self.app._selected_trigger_idx = 1
        self.assertEqual(self.panel.copy_triggers(), "break")
        self.assertEqual(self.app.list_clipboard.paste(CLIP_TRIGGERS)[0]["key"], "f2")

    def test_paste_into_another_keymap_uses_destination_labels_and_accepts_conflicts(self):
        self.select(0, 0)
        self.panel.copy_triggers()
        self.app.data["keymaps"].append({
            "id": "other", "label": "Other", "mappings": {"f1": "a"},
            "triggers": [],
        })
        self.app.data["active_keymap_id"] = "other"
        self.app.data["hook_stop_key"] = "f1"
        self.panel.paste_triggers()
        target = self.app.data["keymaps"][1]["triggers"]
        self.assertEqual(target[0]["label"], "a")
        self.assertIn("停止キーと重複", self.listbox.get(0))

    def test_refresh_preserves_range_active_row_and_compact_stays_single(self):
        self.select(0, 2, active=0)
        self.panel.refresh_triggers()
        self.assertEqual(tuple(self.listbox.curselection()), (0, 1, 2))
        self.assertEqual(int(self.listbox.index("active")), 0)
        self.assertIs(self.panel.selected_trigger(), self.rows[0])
        compact = self.app.compact_view.trigger_box.trigger_list
        self.assertEqual(tuple(compact.curselection()), (0,))
        self.app._compact_mode = True
        self.panel.refresh_triggers()
        self.assertEqual(tuple(self.listbox.curselection()), (0,))
        self.assertEqual(tuple(compact.curselection()), (0,))

    def test_execution_selects_single_effective_row(self):
        self.select(0, 3)
        self.panel.select_trigger_by_key("f1")
        self.assertEqual(tuple(self.listbox.curselection()), (0,))
        self.assertEqual(self.panel.selected_trigger_index(), 0)

    def test_backward_shift_selection_keeps_original_anchor_after_refresh(self):
        self.select(2, 2)
        self.listbox.focus_force()
        self.listbox.event_generate("<Shift-Up>")
        self.app.update()
        self.assertEqual(tuple(self.listbox.curselection()), (1, 2))
        self.assertEqual(self.panel.selected_trigger_index(), 1)
        self.assertEqual(int(self.listbox.index("anchor")), 2)
        self.panel.refresh_triggers()
        self.assertEqual(int(self.listbox.index("anchor")), 2)
        self.listbox.event_generate("<Shift-Up>")
        self.app.update()
        self.assertEqual(tuple(self.listbox.curselection()), (0, 1, 2))
        self.assertEqual(self.panel.selected_trigger_index(), 0)

    def test_mouse_drag_moves_data_on_release_and_escape_restores_preview(self):
        before = list(self.rows)
        self.listbox.focus_force()
        self.app.update_idletasks()
        x, y, width, height = self.listbox.bbox(1)
        x, y = x + width // 2, y + height // 2
        _, target_y, _, target_height = self.listbox.bbox(3)
        target_y += target_height // 2
        self.listbox.event_generate("<ButtonPress-1>", time=next_click_time(), x=x, y=y)
        self.listbox.event_generate("<B1-Motion>", x=x, y=target_y, state=0x100)
        self.app.update_idletasks()
        self.assertEqual(self.rows, before)
        self.listbox.event_generate("<Escape>")
        self.listbox.event_generate("<ButtonRelease-1>", x=x, y=target_y)
        self.app.update()
        self.assertEqual(self.rows, before)
        self.listbox.event_generate("<ButtonPress-1>", time=next_click_time(), x=x, y=y)
        self.listbox.event_generate("<B1-Motion>", x=x, y=target_y, state=0x100)
        self.listbox.event_generate("<ButtonRelease-1>", x=x, y=target_y)
        self.app.update()
        self.assertEqual(self.rows, [before[0], before[2], before[3], before[1]])
        self.assertEqual(tuple(self.listbox.curselection()), (3,))
        self.assertEqual(self.app._indices["f1"], 2)
        self.assertEqual(self.app._indices["f2"], 1)

    def test_shift_mouse_selection_commits_active_row_only_after_release(self):
        self.app.update_idletasks()
        x, y, width, height = self.listbox.bbox(2)
        self.listbox.focus_force()
        self.listbox.event_generate("<ButtonPress-1>", time=next_click_time(), x=x + width // 2,
                                    y=y + height // 2, state=0x1)
        self.app.update_idletasks()
        self.assertEqual(self.panel.selected_trigger_index(), 0)
        self.listbox.event_generate("<ButtonRelease-1>", x=x + width // 2,
                                    y=y + height // 2, state=0x1)
        self.app.update()
        self.assertEqual(tuple(self.listbox.curselection()), (0, 1, 2))
        self.assertEqual(self.panel.selected_trigger_index(), 2)

    def test_clipboard_shortcuts_are_bound_to_trigger_list_in_both_cases(self):
        for sequence in ("<Control-c>", "<Control-C>", "<Control-v>", "<Control-V>"):
            self.assertTrue(self.listbox.bind(sequence))
