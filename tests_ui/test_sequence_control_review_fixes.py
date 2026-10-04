"""Review regression coverage for sequence wait and selection wiring."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tkinter import messagebox

from keyseq.presentation.controllers.trigger_panel import action_edit as action_edit_module
from keyseq.presentation.controllers.trigger_panel import trigger_panel_controller as trigger_module
from keyseq.presentation.controllers.trigger_panel import trigger_row_edit as trigger_row_module
from keyseq.presentation.controllers.hook_controller import HookController
from keyseq.presentation.controllers.keymap_panel.keymap_panel_controller import KeymapPanelController
from keyseq.presentation.controllers.trigger_panel import TriggerPanelController


class SequenceControlReviewFixesTest(unittest.TestCase):
    def test_stop_hook_cancels_all_pending_waits(self):
        app = SimpleNamespace(
            sequence_runner=SimpleNamespace(stop_run_to_end=Mock(), cancel_pending_waits=Mock()),
            hook_coordinator=SimpleNamespace(stop=Mock()), key_state_manager=SimpleNamespace(clear=Mock()),
            layout=SimpleNamespace(refresh_keyboard_window=Mock()), trigger_panel=SimpleNamespace(update_status=Mock()),
        )
        controller = HookController.__new__(HookController)
        controller._app = app
        controller.hook_active = True
        controller.custom_input_enabled = False
        controller._clear_keymap_switch_in_progress = Mock()
        controller.sync_hook_toggle_buttons = Mock()
        controller.sync_trigger_toggle_buttons = Mock()

        controller.stop_hook()

        app.sequence_runner.cancel_pending_waits.assert_called_once_with()

    def test_disabling_custom_input_cancels_pending_waits(self):
        runner = SimpleNamespace(stop_run_to_end=Mock(), cancel_pending_waits=Mock())
        controller = HookController.__new__(HookController)
        controller._app = SimpleNamespace(
            sequence_runner=runner,
            trigger_panel=SimpleNamespace(refresh_actions=Mock(), update_status=Mock()),
            layout=SimpleNamespace(refresh_keyboard_window=Mock()),
        )
        controller.hook_active = True
        controller.custom_input_enabled = True
        controller._clear_keymap_switch_in_progress = Mock()
        controller.sync_trigger_toggle_buttons = Mock()

        controller.toggle_custom_input_enabled()

        runner.cancel_pending_waits.assert_called_once_with()
        self.assertFalse(controller.custom_input_enabled)

    def test_keymap_switch_cancels_waits_only_when_keymap_changes(self):
        for changed in (True, False):
            target_id = "new" if changed else "old"
            runner = SimpleNamespace(cancel_pending_waits=Mock(),
                                     discard_paused=Mock(return_value=()))
            service = SimpleNamespace(
                get_active_keymap_id=Mock(side_effect=["old", target_id]),
                set_active_keymap_id=Mock(return_value=changed), get_keymaps=Mock(return_value=[{"id": target_id}]),
            )
            app = SimpleNamespace(
                data={},
                keymap_service=service,
                state=SimpleNamespace(can_switch_keymap=Mock(return_value=True)),
                sequence_runner=runner,
                trigger_panel=SimpleNamespace(refresh_triggers=Mock(), refresh_actions=Mock(), update_status=Mock()),
                layout=SimpleNamespace(refresh_keyboard_window=Mock()),
                _set_flash_message=Mock(),
            )
            controller = KeymapPanelController.__new__(KeymapPanelController)
            controller._app = app
            controller.refresh_keymap_list_ui = Mock()
            controller.get_active_keymap_text = Mock(return_value="new")

            self.assertTrue(controller.activate_keymap_by_id(target_id, show_flash=False))

            if changed:
                runner.cancel_pending_waits.assert_called_once_with()
            else:
                runner.cancel_pending_waits.assert_not_called()

    def test_action_selection_resets_and_renders_only_when_position_changes(self):
        controller = TriggerPanelController.__new__(TriggerPanelController)
        runner = SimpleNamespace(reset_loop_frames=Mock())
        app = SimpleNamespace(
            _programmatic_action_select=False, _indices={"a": 1},
            _find_trigger_by_key=Mock(return_value={"actions": [{}, {}, {}]}),
            sequence_runner=runner, full_view=SimpleNamespace(
                action_list=SimpleNamespace(curselection=lambda: ())
            ),
        )
        controller._app = app
        controller.selected_trigger_key = Mock(return_value="a")
        controller.selected_trigger_is_effective = Mock(return_value=True)
        controller.refresh_actions = Mock()
        controller.update_status = Mock()
        with patch.object(trigger_module, "sync_listbox_selection_to_focus", return_value=1):
            controller.on_action_list_select()
        runner.reset_loop_frames.assert_not_called()
        controller.refresh_actions.assert_not_called()

        with patch.object(trigger_module, "sync_listbox_selection_to_focus", return_value=2):
            controller.on_action_list_select()
        runner.reset_loop_frames.assert_called_once_with("a")
        controller.refresh_actions.assert_called_once_with()
        self.assertEqual(app._indices["a"], 2)

    def test_delete_trigger_cancels_wait_and_forgets_history(self):
        trigger = {"key": "a", "actions": []}
        runner = SimpleNamespace(cancel_pending_wait=Mock())
        state = SimpleNamespace(
            loop_frames_for=Mock(return_value={"a": []}), forget_trigger=Mock(),
        )
        app = SimpleNamespace(
            data={"keymaps": [{"id": "main", "triggers": [trigger]}], "active_keymap_id": "main"},
            _indices={"a": 0}, state=state, sequence_runner=runner,
            _active_trigger_set_id=Mock(return_value="main"),
            dirty_tracker=SimpleNamespace(mark_trigger_set_dirty=Mock()),
            hook=SimpleNamespace(hook_active=False),
        )
        controller = TriggerPanelController.__new__(TriggerPanelController)
        controller._app = app
        controller.selected_trigger_index = Mock(return_value=0)
        controller.refresh_triggers = Mock()
        controller.refresh_actions = Mock()
        with patch.object(messagebox, "askyesno", return_value=True):
            controller.delete_trigger()
        runner.cancel_pending_wait.assert_called_once_with("a")
        state.forget_trigger.assert_called_once_with("main", "a")

    def test_rename_trigger_rekeys_runtime_history(self):
        trigger = {"key": "a", "label": "old", "actions": []}
        events = []
        service = SimpleNamespace(
            key_exists=Mock(return_value=False), is_stop_key_conflict=Mock(return_value=False),
            is_toggle_key_conflict=Mock(return_value=False),
        )
        state = SimpleNamespace(
            loop_frames_for=Mock(return_value={"a": ["frame"]}),
            rekey_trigger=Mock(side_effect=lambda *_args: events.append("rekey")),
            forget_trigger=Mock(),
        )
        app = SimpleNamespace(
            data={"keymaps": [{"id": "main", "triggers": [trigger]}], "active_keymap_id": "main"},
            _indices={"a": 1}, state=state,
            sequence_runner=SimpleNamespace(cancel_pending_wait=Mock(
                side_effect=lambda _key: events.append(tuple(app._indices)))),
            _active_trigger_set_id=Mock(return_value="main"), trigger_service=service,
            keymap_service=SimpleNamespace(get_keymap_by_switch_key=Mock(return_value=None)),
            _key_overlap_report=Mock(return_value=SimpleNamespace(active_source_keys=set())),
            dirty_tracker=SimpleNamespace(mark_trigger_set_dirty=Mock()), mark_sequence_dirty=Mock(),
            hook=SimpleNamespace(hook_active=False),
        )
        controller = TriggerPanelController.__new__(TriggerPanelController)
        controller._app = app
        controller.selected_trigger = Mock(return_value=trigger)
        controller.refresh_triggers = Mock()
        controller.refresh_actions = Mock()
        dialog = SimpleNamespace(result={"key": "b", "label": "new"}, wait_window=Mock())
        with patch.object(trigger_row_module, "TriggerDialog", return_value=dialog):
            controller.rename_trigger()
        state.rekey_trigger.assert_called_once_with("main", "a", "b")
        self.assertEqual(app._indices, {"b": 1})
        # 旧キーの待ちの取り消しは移し替えより前（task_05b 以降は共通手順が旧キーの後始末を重ねて呼ぶが、移し替え後なので無害）。
        self.assertEqual(events[:2], [("a",), "rekey"])

    def test_rename_trigger_updates_call_targets_without_changing_other_history(self):
        trigger = {"key": "z7", "label": "renamed", "actions": []}
        caller = {
            "key": "caller",
            "label": "caller",
            "actions": [{"type": "system", "op": "call", "target": " Z7 "}],
        }
        untouched = {"key": "untouched", "label": "", "actions": [{"type": "text", "value": "x"}]}
        frames = {"z7": ["renamed-frame"], "caller": ["caller-frame"], "untouched": ["untouched-frame"]}
        indices = {"z7": 2, "caller": 3, "untouched": 4}
        service = SimpleNamespace(
            key_exists=Mock(return_value=False), is_stop_key_conflict=Mock(return_value=False),
            is_toggle_key_conflict=Mock(return_value=False),
        )
        app = SimpleNamespace(
            data={"keymaps": [{"id": "main", "triggers": [trigger, caller, untouched]}], "active_keymap_id": "main"},
            _indices=indices,
            state=SimpleNamespace(loop_frames_for=Mock(return_value=frames), rekey_trigger=Mock(),
                                  forget_trigger=Mock()),
            sequence_runner=SimpleNamespace(cancel_pending_wait=Mock()),
            _active_trigger_set_id=Mock(return_value="main"), trigger_service=service,
            keymap_service=SimpleNamespace(get_keymap_by_switch_key=Mock(return_value=None)),
            _key_overlap_report=Mock(return_value=SimpleNamespace(active_source_keys=set())),
            dirty_tracker=SimpleNamespace(mark_trigger_set_dirty=Mock()), mark_sequence_dirty=Mock(),
            hook=SimpleNamespace(hook_active=False),
        )
        controller = TriggerPanelController.__new__(TriggerPanelController)
        controller._app = app
        controller.selected_trigger = Mock(return_value=trigger)
        controller.refresh_triggers = Mock()
        controller.refresh_actions = Mock()
        dialog = SimpleNamespace(result={"key": "z8", "label": "renamed"}, wait_window=Mock())

        with patch.object(trigger_row_module, "TriggerDialog", return_value=dialog):
            controller.rename_trigger()

        self.assertEqual(caller["actions"], [{"type": "system", "op": "call", "target": "z8"}])
        self.assertEqual(app.mark_sequence_dirty.call_args_list, [unittest.mock.call(caller)])
        self.assertEqual(app._indices, {"z8": 2, "caller": 3, "untouched": 4})
        self.assertEqual(frames, {"z8": ["renamed-frame"], "caller": ["caller-frame"], "untouched": ["untouched-frame"]})
        self.assertEqual(app.state.rekey_trigger.call_args.args, ("main", "z7", "z8"))

    def test_add_action_uses_position_after_dialog_wait(self):
        trigger = {"key": "f1", "actions": [{"value": "one"}, {"value": "two"}]}
        runner = SimpleNamespace(reset_loop_frames=Mock())
        app = SimpleNamespace(
            data={"keymaps": [{"id": "main", "triggers": [trigger]}], "active_keymap_id": "main"},
            _indices={"f1": 0}, _dialog_result={"type": "text", "value": "three"},
            state=SimpleNamespace(counters={}), sequence_runner=runner, config_root="",
            mark_sequence_dirty=Mock(),
        )
        controller = TriggerPanelController.__new__(TriggerPanelController)
        controller._app = app
        controller.selected_trigger = Mock(return_value=trigger)
        controller.selected_action_index = Mock(return_value=0)
        controller.refresh_actions = Mock()
        dialog = SimpleNamespace(
            append_to_end=True,
            wait_window=Mock(side_effect=lambda: app._indices.__setitem__("f1", 2)),
        )

        with patch.object(action_edit_module, "ActionDialog", return_value=dialog):
            controller.add_action()

        self.assertEqual(app._indices["f1"], 3)
        self.assertEqual(len(trigger["actions"]), 3)
        runner.reset_loop_frames.assert_called_once_with("f1")


if __name__ == "__main__":
    unittest.main()
