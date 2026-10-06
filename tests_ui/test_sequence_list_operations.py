"""UI-facing tests for selection and block edits in the action list."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation.controllers.trigger_panel import action_edit as action_edit_module
from keyseq.presentation.controllers.trigger_panel import TriggerPanelController


class _Listbox:
    def __init__(self):
        self.items = []
        self.selection = []
        self.active = 0
        self.anchor = 0

    def delete(self, _first, _last):
        self.items.clear()

    def insert(self, _index, item):
        self.items.append(item)

    def itemconfigure(self, *_args, **_kwargs):
        pass

    def selection_clear(self, _first, _last):
        self.selection.clear()

    def selection_set(self, first, last=None):
        first = int(first)
        last = first if last is None or last == "end" else int(last)
        self.selection = list(range(first, last + 1))

    def selection_anchor(self, index):
        self.anchor = int(index)

    def activate(self, index):
        self.active = int(index)

    def see(self, _index):
        pass

    def curselection(self):
        return tuple(self.selection)

    def size(self):
        return len(self.items)

    def index(self, index):
        if index == "active":
            return self.active
        if index == "anchor":
            return self.anchor
        return int(index)


def _action(label):
    return {"type": "text", "value": label}


class SequenceListOperationsTest(unittest.TestCase):
    def setUp(self):
        self.actions = [_action(label) for label in "ABCD"]
        self.rows = tuple(self.actions)
        self.trigger = {"key": "a", "actions": self.actions}
        self.listbox = _Listbox()
        self.app = SimpleNamespace(
            data={"active_keymap_id": "main", "keymaps": [{"id": "main", "triggers": [self.trigger]}]},
            full_view=SimpleNamespace(
                action_list=self.listbox,
                sequence_box=SimpleNamespace(
                    action_range_drag=SimpleNamespace(last_commit_extended=False),
                ),
            ),
            _selected_trigger_idx=0,
            _indices={"a": 1},
            _programmatic_action_select=False,
            focus_get=lambda: self.listbox,
            _active_trigger_set_id=lambda: "main",
            _find_trigger_by_key=lambda key: self.trigger if key == "a" else None,
            state=SimpleNamespace(loop_iterations_for=Mock(return_value={}), counters={}),
            sequence_runner=SimpleNamespace(
                reset_loop_frames=Mock(),
                is_running_chain_callee=Mock(return_value=False),
            ),
            list_clipboard=SimpleNamespace(paste=Mock(return_value=[_action("paste")])),
            mark_sequence_dirty=Mock(),
            _set_flash_message=Mock(),
        )
        self.controller = TriggerPanelController(self.app)
        self.controller.sync_suppress_checkbox = Mock()
        self.controller.sync_run_to_end_ui = Mock()
        self.controller.update_status = Mock()

    def select(self, start, end=None):
        self.listbox.selection = list(range(start, (end if end is not None else start) + 1))
        self.listbox.active = self.listbox.selection[-1]
        self.listbox.anchor = start

    def test_refresh_marks_next_action_and_allows_independent_range_selection(self):
        self.controller.refresh_actions()
        self.assertEqual(self.listbox.items[0], "　 01. [text] A")
        self.assertEqual(self.listbox.items[1], "▶ 02. [text] B")
        self.assertEqual(self.listbox.items[2], "　 03. [text] C")

        self.controller.refresh_actions(select=(0, 2))
        self.assertEqual(self.listbox.curselection(), (0, 1, 2))
        self.assertEqual(self.listbox.active, 2)
        self.assertEqual(self.app._indices["a"], 1)

    def test_run_to_end_terminal_index_marks_first_row_as_next(self):
        self.trigger["run_to_end"] = True
        self.app._indices["a"] = len(self.actions)

        self.controller.refresh_actions()

        self.assertTrue(self.listbox.items[0].startswith("▶ "))
        self.assertTrue(self.listbox.items[1].startswith("　 "))

    def test_set_next_action_index_moves_next_action_marker(self):
        self.assertTrue(self.controller.set_next_action_index(2))

        self.assertEqual(self.app._indices["a"], 2)
        self.assertTrue(self.listbox.items[2].startswith("▶ "))
        self.app.sequence_runner.reset_loop_frames.assert_called_once_with("a")

    def test_set_next_action_index_same_index_does_not_change_index(self):
        self.assertFalse(self.controller.set_next_action_index(1))

        self.assertEqual(self.app._indices["a"], 1)
        self.app.sequence_runner.reset_loop_frames.assert_not_called()
        self.controller.update_status.assert_called_once_with()

    def test_set_next_action_index_out_of_range_does_nothing(self):
        self.assertFalse(self.controller.set_next_action_index(len(self.actions)))

        self.assertEqual(self.app._indices["a"], 1)
        self.app.sequence_runner.reset_loop_frames.assert_not_called()
        self.controller.update_status.assert_not_called()

    def test_set_next_action_index_ignores_ineffective_trigger(self):
        self.app.data["keymaps"][0]["triggers"].append(
            {"key": "a", "actions": [_action("duplicate")]}
        )
        self.app._selected_trigger_idx = 1

        self.assertFalse(self.controller.set_next_action_index(0))

        self.assertEqual(self.app._indices["a"], 1)
        self.app.sequence_runner.reset_loop_frames.assert_not_called()
        self.controller.update_status.assert_not_called()

    def test_drag_move_preserves_next_action_identity_and_selects_moved_block(self):
        next_action = self.actions[1]
        self.assertTrue(self.controller.on_action_list_move(1, 2, 2))

        self.assertEqual(self.trigger["actions"], [self.rows[0], self.rows[3], self.rows[1], self.rows[2]])
        self.assertIs(self.trigger["actions"][self.app._indices["a"]], next_action)
        self.assertEqual(self.listbox.curselection(), (2, 3))
        self.app.sequence_runner.reset_loop_frames.assert_called_once_with("a")
        self.app.mark_sequence_dirty.assert_called_once_with(self.trigger)

    def test_running_chain_callee_rejects_click_and_sequence_list_edits(self):
        self.app.sequence_runner.is_running_chain_callee.return_value = True
        before = list(self.trigger["actions"])
        self.select(2)

        self.controller.on_action_list_mouse_release(self.listbox)
        self.assertFalse(self.controller.on_action_list_move(1, 1, 0))
        self.controller.move_action(-1)
        self.controller.paste_actions()
        self.controller.duplicate_action()

        self.assertEqual(self.app._indices["a"], 1)
        self.assertEqual(self.trigger["actions"], before)
        self.assertEqual(self.app._set_flash_message.call_count, 5)
        for call in self.app._set_flash_message.call_args_list:
            self.assertEqual(
                call.args[0],
                "連続実行中は呼び出し先を変更できません（一時停止してから操作してください）",
            )
        self.app.sequence_runner.reset_loop_frames.assert_not_called()
        self.app.mark_sequence_dirty.assert_not_called()

    def test_paused_chain_callee_still_accepts_sequence_list_move(self):
        # is_running_chain_callee=False also covers a paused run: paused edits are
        # accepted and a later resume uses the reordered actions.
        self.app.sequence_runner.is_running_chain_callee.return_value = False

        self.assertTrue(self.controller.on_action_list_move(1, 1, 0))

        self.assertEqual(self.trigger["actions"], [self.rows[1], self.rows[0], self.rows[2], self.rows[3]])
        self.app._set_flash_message.assert_not_called()

    def test_running_caller_itself_still_accepts_click_position_change(self):
        # The application query excludes the run-to-end key itself.
        self.trigger["run_to_end"] = True
        self.app.sequence_runner.is_running_chain_callee.return_value = False
        self.select(2)

        self.controller.on_action_list_mouse_release(self.listbox)

        self.assertEqual(self.app._indices["a"], 2)
        self.app.sequence_runner.reset_loop_frames.assert_called_once_with("a")
        self.app._set_flash_message.assert_not_called()

    def test_move_up_moves_selected_block_and_keeps_next_action(self):
        next_action = self.rows[3]
        self.app._indices["a"] = 3
        self.select(2, 3)

        self.controller.move_action(-1)

        self.assertEqual(self.trigger["actions"], [self.rows[0], self.rows[2], self.rows[3], self.rows[1]])
        self.assertIs(self.trigger["actions"][self.app._indices["a"]], next_action)
        self.assertEqual(self.listbox.curselection(), (1, 2))

    def test_move_down_moves_selected_block_and_keeps_next_action(self):
        next_action = self.rows[1]
        self.select(1, 2)

        self.controller.move_action(1)

        self.assertEqual(self.trigger["actions"], [self.rows[0], self.rows[3], self.rows[1], self.rows[2]])
        self.assertIs(self.trigger["actions"][self.app._indices["a"]], next_action)
        self.assertEqual(self.listbox.curselection(), (2, 3))

    def test_loop_pair_cannot_be_split_by_drag_and_reports_reason(self):
        start = {"type": "system", "op": "loop_start", "count": 2}
        end = {"type": "system", "op": "loop_end"}
        self.trigger["actions"] = [start, end, _action("tail")]
        before = list(self.trigger["actions"])

        self.assertFalse(self.controller.on_action_list_move(1, 1, 0))

        self.assertEqual(self.trigger["actions"], before)
        self.app._set_flash_message.assert_called_once()
        self.assertIn("ループの始まりと終わりの組が変わるため移動できません", self.app._set_flash_message.call_args.args[0])
        self.app.mark_sequence_dirty.assert_not_called()

    def test_loop_markers_cannot_cross_with_move_up_or_down(self):
        start = {"type": "system", "op": "loop_start", "count": 2}
        end = {"type": "system", "op": "loop_end"}
        self.trigger["actions"] = [start, end, _action("tail")]
        before = list(self.trigger["actions"])

        self.app._indices["a"] = 0
        self.select(0)
        self.controller.move_action(1)
        self.app._indices["a"] = 1
        self.select(1)
        self.controller.move_action(-1)

        self.assertEqual(self.trigger["actions"], before)
        self.app.mark_sequence_dirty.assert_not_called()
        self.app.sequence_runner.reset_loop_frames.assert_not_called()

    def test_move_at_boundary_is_a_no_op(self):
        self.app._indices["a"] = 0
        self.select(0)

        self.controller.move_action(-1)

        self.assertEqual(self.trigger["actions"], list(self.rows))
        self.app.mark_sequence_dirty.assert_not_called()
        self.app.sequence_runner.reset_loop_frames.assert_not_called()

    def test_complete_loop_can_move_as_a_block_past_another_loop(self):
        loop_a = [
            {"type": "system", "op": "loop_start", "count": 2, "label": "A"},
            _action("inside A"),
            {"type": "system", "op": "loop_end", "label": "A"},
        ]
        between = _action("between")
        loop_b = [
            {"type": "system", "op": "loop_start", "count": 3, "label": "B"},
            _action("inside B"),
            {"type": "system", "op": "loop_end", "label": "B"},
        ]
        self.trigger["actions"] = loop_a + [between] + loop_b
        self.app._indices["a"] = 1

        self.assertTrue(self.controller.on_action_list_move(0, 2, 2))

        self.assertEqual(self.trigger["actions"], [between, loop_b[0]] + loop_a + loop_b[1:])
        self.assertIs(self.trigger["actions"][self.app._indices["a"]], loop_a[1])

    def test_range_delete_confirms_once_counts_pair_expansion_and_marks_dirty(self):
        start = {"type": "system", "op": "loop_start", "count": 2}
        middle = _action("middle")
        end = {"type": "system", "op": "loop_end"}
        tail = _action("tail")
        all_actions = [start, middle, end, tail]
        self.trigger["actions"] = all_actions
        self.app._indices["a"] = 3
        self.select(0, 1)
        with patch.object(action_edit_module.messagebox, "askyesno", return_value=True) as ask:
            self.controller.delete_action()

        self.assertIn("選択した 3 行を削除しますか？", ask.call_args.args[1])
        self.assertIn("中の行は残ります", ask.call_args.args[1])
        ask.assert_called_once()
        self.assertEqual(self.trigger["actions"], [tail])
        self.assertIs(self.trigger["actions"][self.app._indices["a"]], tail)
        self.app.mark_sequence_dirty.assert_called_once_with(self.trigger)

    def test_single_row_and_single_loop_pair_keep_existing_confirmation_wording(self):
        with patch.object(action_edit_module.messagebox, "askyesno", return_value=False) as ask:
            self.select(0)
            self.controller.delete_action()
            self.assertEqual(ask.call_args.args[1], "選択した行を削除しますか？")

            start = {"type": "system", "op": "loop_start", "count": 2}
            end = {"type": "system", "op": "loop_end"}
            self.trigger["actions"] = [start, _action("inside"), end]
            self.select(0)
            self.controller.delete_action()
            self.assertIn("ループの始まりと終わりを削除します", ask.call_args.args[1])

    def test_delete_preserves_next_action_when_it_survives(self):
        actions = list(self.trigger["actions"])
        next_action = actions[3]
        self.select(1, 2)
        self.app._indices["a"] = 3
        with patch.object(action_edit_module.messagebox, "askyesno", return_value=True):
            self.controller.delete_action()

        self.assertEqual(self.trigger["actions"], [actions[0], actions[3]])
        self.assertEqual(self.app._indices["a"], 1)
        self.assertIs(self.trigger["actions"][1], next_action)

    def test_delete_falls_back_to_numeric_position_when_next_action_is_removed(self):
        actions = list(self.trigger["actions"])
        self.select(1, 2)
        self.app._indices["a"] = 2
        with patch.object(action_edit_module.messagebox, "askyesno", return_value=True):
            self.controller.delete_action()

        # The removed next row leaves its numeric position to normal refresh correction.
        self.assertEqual(self.app._indices["a"], 0)
        self.assertIs(self.trigger["actions"][0], actions[0])

    def test_editing_a_row_from_range_collapses_selection_to_that_row(self):
        actions = list(self.trigger["actions"])
        self.select(1, 3)
        self.app._dialog_result = _action("edited")
        dialog = Mock()
        dialog.wait_window.side_effect = lambda: None
        with patch.object(action_edit_module, "ActionDialog", return_value=dialog):
            self.controller.edit_action()

        self.assertEqual(self.trigger["actions"][3]["value"], "edited")
        self.assertEqual(self.listbox.curselection(), (3,))
        self.assertIs(self.trigger["actions"][1], actions[1])

    def test_shift_commits_leave_next_index_unchanged_and_plain_input_syncs_it(self):
        self.app.full_view.sequence_box = SimpleNamespace(
            action_range_drag=SimpleNamespace(last_commit_extended=True)
        )
        self.select(0, 2)
        with patch.object(self.controller, "on_action_list_select") as select_action:
            self.controller.on_action_list_mouse_release(self.listbox)
        select_action.assert_not_called()
        self.assertEqual(self.app._indices["a"], 1)
        self.assertEqual(self.listbox.curselection(), (0, 1, 2))

        self.app.full_view.sequence_box.action_range_drag.last_commit_extended = False
        self.select(2)
        with patch.object(self.controller, "on_action_list_select") as select_action:
            self.controller.on_action_list_mouse_release(self.listbox)
        select_action.assert_called_once_with(prefer_selection=True)

    def test_shift_key_release_does_not_collapse_selection(self):
        self.select(1, 3)
        event = SimpleNamespace(widget=self.listbox, keysym="Down", state=0x1)
        self.controller.on_action_list_focus_index_change(event)
        self.assertEqual(self.listbox.curselection(), (1, 2, 3))
        self.assertEqual(self.app._indices["a"], 1)


if __name__ == "__main__":
    unittest.main()
