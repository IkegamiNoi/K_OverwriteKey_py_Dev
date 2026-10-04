"""UI-facing checks for sequence duplication and the in-app list clipboard."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
from keyseq.presentation.controllers.trigger_panel import action_edit as action_edit_module
from keyseq.presentation.controllers.trigger_panel import TriggerPanelController
from keyseq.presentation.list_clipboard import CLIP_ACTIONS, ListClipboard


class _Listbox:
    def __init__(self):
        self.selection = []

    def curselection(self):
        return tuple(self.selection)


def _action(value):
    return {"type": "text", "value": value}


class SequenceCopyPasteTest(unittest.TestCase):
    def setUp(self):
        self.first = {"key": "a", "actions": [_action("A"), _action("B"), _action("C")]}
        self.second = {"key": "b", "actions": [_action("X")]}
        self.listbox = _Listbox()
        self.app = SimpleNamespace(
            data={"active_keymap_id": "main", "keymaps": [{"id": "main", "triggers": [self.first, self.second]}]},
            full_view=SimpleNamespace(action_list=self.listbox),
            list_clipboard=ListClipboard(),
            _selected_trigger_idx=0,
            _indices={"a": 1, "b": 0},
            sequence_runner=SimpleNamespace(reset_loop_frames=Mock()),
            mark_sequence_dirty=Mock(),
        )
        self.controller = TriggerPanelController(self.app)
        self.controller.refresh_actions = Mock()
        self.controller.selected_action_index = Mock(return_value=0)

    def test_duplicate_appends_selected_range_without_touching_clipboard(self):
        self.app.list_clipboard.copy(CLIP_ACTIONS, [_action("kept")])
        self.listbox.selection = [1, 2]
        next_action = self.first["actions"][1]

        self.controller.duplicate_action()

        actions = self.first["actions"]
        self.assertEqual([item["value"] for item in actions], ["A", "B", "C", "B", "C"])
        self.assertIsNot(actions[1], actions[3])
        self.assertIsNot(actions[2], actions[4])
        self.assertIs(actions[self.app._indices["a"]], next_action)
        self.assertEqual(self.app.list_clipboard.paste(CLIP_ACTIONS), [_action("kept")])
        self.controller.refresh_actions.assert_called_once_with(select=(3, 4))
        self.app.sequence_runner.reset_loop_frames.assert_called_once_with("a")
        self.app.mark_sequence_dirty.assert_called_once_with(self.first)

    def test_duplicate_completes_selected_loop_range(self):
        start = {"type": "system", "op": "loop_start", "count": 3, "label": "L1"}
        first = _action("T1")
        second = _action("T2")
        end = {"type": "system", "op": "loop_end", "label": "L1"}
        self.first["actions"] = [start, first, second, end]
        self.listbox.selection = [2, 3]

        self.controller.duplicate_action()

        actions = self.first["actions"]
        self.assertEqual(len(actions), 7)
        self.assertEqual(actions[4]["op"], "loop_start")
        self.assertEqual(actions[4]["count"], 3)
        self.assertEqual(actions[5]["value"], "T2")
        self.assertEqual(actions[6]["op"], "loop_end")
        self.assertIsNot(actions[4], start)
        self.assertIsNot(actions[5], second)
        self.assertIsNot(actions[6], end)
        self.controller.refresh_actions.assert_called_once_with(select=(4, 6))

    def test_copy_completes_loop_and_pastes_detached_pair_to_another_trigger(self):
        start = {"type": "system", "op": "loop_start", "count": 2, "label": "L1"}
        body = _action("B")
        end = {"type": "system", "op": "loop_end", "label": "L1"}
        self.first["actions"] = [start, body, end]
        self.listbox.selection = [0]

        self.assertEqual(self.controller.copy_actions(), "break")
        start["count"] = 9
        end["label"] = "edited"
        stored = self.app.list_clipboard.paste(CLIP_ACTIONS)
        self.assertEqual([item.get("op") for item in stored], ["loop_start", "loop_end"])
        self.assertEqual(stored[0]["count"], 2)
        self.assertEqual(stored[1]["label"], "L1")

        self.app._selected_trigger_idx = 1
        self.assertEqual(self.controller.paste_actions(), "break")
        pasted = self.second["actions"][1:]
        self.assertEqual([item.get("op") for item in pasted], ["loop_start", "loop_end"])
        self.assertEqual(pasted[0]["count"], 2)
        self.assertEqual(pasted[1]["label"], "L1")

    def test_copy_then_paste_to_another_trigger_is_repeatable_and_detached(self):
        self.listbox.selection = [1]
        self.assertEqual(self.controller.copy_actions(), "break")
        self.first["actions"][1]["value"] = "edited after copy"
        self.app._selected_trigger_idx = 1
        self.listbox.selection = []

        self.assertEqual(self.controller.paste_actions(), "break")
        self.assertEqual(self.controller.paste_actions(), "break")

        self.assertEqual([item["value"] for item in self.second["actions"]], ["X", "B", "B"])
        self.assertIsNot(self.second["actions"][1], self.second["actions"][2])
        self.assertEqual(self.app.list_clipboard.paste(CLIP_ACTIONS), [_action("B")])
        self.assertEqual(self.controller.refresh_actions.call_count, 2)

    def test_copy_and_paste_preserves_step_call_flag(self):
        step_call = {"type": "system", "op": "call", "target": "f5", "step": True}
        self.first["actions"] = [step_call]
        self.listbox.selection = [0]

        self.assertEqual(self.controller.copy_actions(), "break")
        stored = self.app.list_clipboard.paste(CLIP_ACTIONS)
        self.assertEqual(stored, [step_call])
        self.assertIsNot(stored[0], step_call)

        self.app._selected_trigger_idx = 1
        self.listbox.selection = []
        self.assertEqual(self.controller.paste_actions(), "break")
        self.assertEqual(self.second["actions"][-1], step_call)

    def test_empty_selection_uses_focused_action_and_handlers_break(self):
        self.controller.selected_action_index.return_value = 2
        self.assertEqual(self.controller.copy_actions(), "break")
        self.assertEqual(self.app.list_clipboard.paste(CLIP_ACTIONS), [_action("C")])
        self.assertEqual(self.controller.paste_actions(), "break")

    def test_invalid_loop_and_standalone_appends_show_reason_without_mutating(self):
        self.listbox.selection = [1]
        self.first["actions"] = [_action("A"), {"type": "system", "op": "loop_end"}]
        with patch.object(action_edit_module.messagebox, "showinfo") as showinfo:
            self.controller.copy_actions()
            self.controller.paste_actions()

        self.assertEqual(len(self.first["actions"]), 2)
        self.assertIn("対になっていない", showinfo.call_args.args[1])
        self.app.mark_sequence_dirty.assert_not_called()

        self.app.list_clipboard.copy(CLIP_ACTIONS, [{"type": "system", "op": "back"}])
        with patch.object(action_edit_module.messagebox, "showinfo") as showinfo:
            self.controller.paste_actions()
        self.assertIn("それ 1 つだけ", showinfo.call_args.args[1])
        self.assertEqual(len(self.first["actions"]), 2)

    def test_loop_depth_violation_shows_limit(self):
        # 末尾へ貼る対は既存の閉じたループの外に付くため、深さ超過は貼る内容自体が 10 段の入れ子のときに生じる。
        self.first["actions"] = [{"type": "text", "value": "x"}]
        self.app.list_clipboard.copy(CLIP_ACTIONS, [
            *({"type": "system", "op": "loop_start", "count": 2} for _ in range(10)),
            *({"type": "system", "op": "loop_end"} for _ in range(10)),
        ])
        with patch.object(action_edit_module.messagebox, "showinfo") as showinfo:
            self.controller.paste_actions()

        self.assertEqual(len(self.first["actions"]), 1)
        self.assertIn("9 段", showinfo.call_args.args[1])

    def test_run_to_end_endpoint_stays_at_new_endpoint(self):
        self.first["run_to_end"] = True
        self.app._indices["a"] = len(self.first["actions"])
        self.app.list_clipboard.copy(CLIP_ACTIONS, [_action("copy")])

        self.controller.paste_actions()

        self.assertEqual(self.app._indices["a"], len(self.first["actions"]))


class ClipboardResetTest(unittest.TestCase):
    def test_new_config_and_loaded_data_clear_clipboard(self):
        clipboard = ListClipboard()
        clipboard.copy(CLIP_ACTIONS, [_action("stored")])
        app = SimpleNamespace(list_clipboard=clipboard)
        io = KeymapSetIo(app)
        io.confirm_save_if_dirty = Mock(return_value=True)
        new_data = {"active_keymap_id": "main", "keymaps": [{"id": "main", "triggers": []}]}
        app.config_service = SimpleNamespace(
            new_default_data=Mock(return_value=new_data),
            apply_global_defaults=Mock(),
            normalize_runtime_data=Mock(side_effect=lambda data: data),
        )
        app.dirty_tracker = SimpleNamespace(
            reset_trigger_set_state=Mock(), set_dirty=Mock(),
        )
        app.discard_retained_hook_keys = Mock()
        app._sync_control_vars_from_data = Mock()
        app.state = SimpleNamespace(reset_indices=Mock())
        app.trigger_panel = SimpleNamespace(refresh_triggers=Mock(), refresh_actions=Mock())
        app._set_flash_message = Mock()
        app.config_root = ""

        io.new_config()
        self.assertIsNone(clipboard.paste(CLIP_ACTIONS))

        clipboard.copy(CLIP_ACTIONS, [_action("stored")])
        app.data = {}
        app.dirty_tracker.sync_trigger_set_source_path_from_data = Mock()
        app.dirty_tracker.clear_individual_dirty_flags = Mock()
        app.dirty_tracker.mark_migrated_keymap_dirty = Mock()
        app._refresh_key_overlap_report = Mock()
        io.apply_loaded_data_to_ui()
        self.assertIsNone(clipboard.paste(CLIP_ACTIONS))


if __name__ == "__main__":
    unittest.main()
