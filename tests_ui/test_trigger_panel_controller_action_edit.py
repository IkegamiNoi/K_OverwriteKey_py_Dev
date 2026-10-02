"""アクションの追加・編集・削除・移動を検証する。"""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation.controllers.trigger_panel import TriggerPanelController
from keyseq.presentation.controllers.trigger_panel import action_edit as action_edit_module


class _Dialog:
    def __init__(self, app, *, result=None, append_to_end=True, **kwargs):
        self.app = app
        self.result = result
        self.append_to_end = append_to_end
        self.kwargs = kwargs

    def wait_window(self):
        self.app._dialog_result = self.result


class _ActionListbox:
    def __init__(self):
        self.items = []
        self.selection = []

    def delete(self, _first, _last):
        self.items.clear()

    def insert(self, _index, item):
        self.items.append(item)

    def selection_clear(self, _first, _last):
        self.selection.clear()

    def selection_set(self, index):
        self.selection = [int(index)]

    def selection_anchor(self, _index):
        pass

    def curselection(self):
        return tuple(self.selection)

    def activate(self, _index):
        pass

    def see(self, _index):
        pass


class TriggerPanelActionEditTest(unittest.TestCase):
    def setUp(self):
        self.trigger = {"key": "a", "actions": [
            {"type": "hotkey", "keys": ["x"]},
            {"type": "text", "text": "second"},
        ]}
        self.app = SimpleNamespace(
            data={"active_keymap_id": "main", "keymaps": [{
                "id": "main", "triggers": [self.trigger],
            }]},
            state=SimpleNamespace(
                counters={"running": 3},
                loop_iterations_for=lambda _trigger_set_id, _key: {},
            ),
            _active_trigger_set_id=lambda: "main",
            _selected_trigger_idx=0,
            _indices={"a": 1},
            _dialog_result=None,
            config_root="C:/config",
            sequence_runner=SimpleNamespace(reset_loop_frames=Mock()),
            mark_sequence_dirty=Mock(),
            _set_flash_message=Mock(),
        )
        self.controller = TriggerPanelController(self.app)
        self.controller.refresh_actions = Mock()
        self.showinfo = patch.object(action_edit_module.messagebox, "showinfo").start()
        self.addCleanup(patch.stopall)

    def set_selection(self, index):
        patcher = patch.object(self.controller, "selected_action_index", return_value=index)
        patcher.start()
        self.addCleanup(patcher.stop)

    def install_dialog(self, *, result=None, append_to_end=True):
        dialog = _Dialog(self.app, result=result, append_to_end=append_to_end)
        patcher = patch.object(action_edit_module, "ActionDialog", return_value=dialog)
        factory = patcher.start()
        self.addCleanup(patcher.stop)
        return factory, dialog

    def add_call_targets(self):
        self.app.data["keymaps"][0]["triggers"].extend([
            {"key": "b", "label": "Back target", "actions": [
                {"type": "system", "op": "back"},
            ]},
            {"key": "c", "label": "", "actions": []},
        ])

    def assert_call_dialog_options(self, factory):
        kwargs = factory.call_args.kwargs
        self.assertEqual(kwargs["call_candidates"], [("b", "Back target"), ("c", "")])
        self.assertEqual(kwargs["call_check"]("b"), "戻す・先頭へのトリガーは呼び出せません")

    def test_add_inserts_after_selected_and_preserves_next_action(self):
        self.set_selection(0)
        next_action = self.trigger["actions"][1]
        self.app.state.counters = {"running": 3, "z_state": 0}
        self.trigger["actions"][0]["counter"] = "sequence"
        self.app.data["keymaps"][0]["triggers"].append({"key": "b", "actions": [
            {"type": "file_line", "counter": "running"},
            {"type": "system", "counter": "alpha"},
            {"type": "system", "counter": "sequence"},
        ]})
        self.app.data["keymaps"].append({"id": "inactive", "triggers": [
            {"key": "c", "actions": [{"type": "system", "counter": "inactive_only"}]},
        ]})
        factory, dialog = self.install_dialog(
            result={"type": "text", "text": "new"}, append_to_end=False
        )
        action_list = _ActionListbox()
        self.app.full_view = SimpleNamespace(action_list=action_list)
        self.app._programmatic_action_select = False
        self.app._find_trigger_by_key = lambda _key: self.trigger
        self.controller.refresh_actions = TriggerPanelController.refresh_actions.__get__(
            self.controller, TriggerPanelController
        )
        self.controller.sync_suppress_checkbox = Mock()
        self.controller.sync_run_to_end_ui = Mock()
        self.controller.update_status = Mock()

        self.controller.add_action()

        self.assertEqual([a.get("text", a.get("keys")) for a in self.trigger["actions"]],
                         [["x"], "new", "second"])
        self.assertEqual(self.app._indices["a"], 2)
        self.assertIs(self.trigger["actions"][self.app._indices["a"]], next_action)
        self.assertEqual(action_list.selection, [2])
        self.assertEqual(len(action_list.items), 3)
        self.app.mark_sequence_dirty.assert_called_once_with(self.trigger)
        factory.assert_called_once()
        self.assertEqual(factory.call_args.kwargs["mode"], "add")
        self.assertEqual(factory.call_args.kwargs["counter_names"],
                         ["alpha", "running", "sequence", "z_state"])
        self.assertEqual(factory.call_args.kwargs["config_root"], "C:/config")
        self.assertFalse(dialog.append_to_end)

    def test_add_defaults_to_end_when_no_action_is_selected(self):
        self.set_selection(None)
        self.install_dialog(result={"type": "text", "text": "new"})

        self.controller.add_action()

        self.assertEqual(self.trigger["actions"][-1], {"type": "text", "text": "new"})
        self.assertEqual(self.app._indices["a"], 1)

    def test_add_dialog_receives_call_candidates_without_owner_and_check(self):
        self.add_call_targets()
        self.set_selection(None)
        factory, _dialog = self.install_dialog()

        self.controller.add_action()

        self.assert_call_dialog_options(factory)

    def test_edit_dialog_receives_call_candidates_without_owner_and_check(self):
        self.add_call_targets()
        self.set_selection(0)
        factory, _dialog = self.install_dialog()

        self.controller.edit_action()

        self.assert_call_dialog_options(factory)

    def test_add_with_append_off_and_no_selection_still_uses_end(self):
        self.set_selection(None)
        self.install_dialog(result={"type": "text", "text": "new"}, append_to_end=False)

        self.controller.add_action()

        self.assertEqual(self.trigger["actions"][-1], {"type": "text", "text": "new"})
        self.assertEqual(self.app._indices["a"], 1)

    def test_add_standalone_control_to_nonempty_sequence_is_rejected(self):
        self.set_selection(None)
        self.install_dialog(result={"type": "system", "op": "back"})
        before = list(self.trigger["actions"])

        self.controller.add_action()

        self.assertEqual(self.trigger["actions"], before)
        self.showinfo.assert_called_once_with(
            "追加", "戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。"
        )
        self.app.mark_sequence_dirty.assert_not_called()

    def test_add_regular_row_to_sequence_with_standalone_control_is_rejected(self):
        self.set_selection(None)
        self.trigger["actions"] = [{"type": "system", "op": "rewind"}]
        self.install_dialog(result={"type": "text", "text": "extra"})

        self.controller.add_action()

        self.assertEqual(self.trigger["actions"], [{"type": "system", "op": "rewind"}])
        self.showinfo.assert_called_once_with(
            "追加", "戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。"
        )
        self.app.mark_sequence_dirty.assert_not_called()

    def test_edit_to_standalone_control_requires_one_row_sequence(self):
        self.set_selection(0)
        self.install_dialog(result={"type": "system", "op": "back"})
        before = list(self.trigger["actions"])

        self.controller.edit_action()

        self.assertEqual(self.trigger["actions"], before)
        self.showinfo.assert_called_once_with(
            "編集", "戻す・先頭へは、出力シーケンスにそれ 1 つだけで登録してください。"
        )
        self.app.mark_sequence_dirty.assert_not_called()

    def test_edit_single_row_to_standalone_control_is_allowed(self):
        self.trigger["actions"] = [{"type": "text", "text": "only"}]
        self.set_selection(0)
        self.install_dialog(result={"type": "system", "op": "rewind"})

        self.controller.edit_action()

        self.assertEqual(self.trigger["actions"], [{"type": "system", "op": "rewind"}])
        self.showinfo.assert_not_called()

    def test_add_loop_inserts_a_pair_and_depth_overflow_is_rejected(self):
        self.set_selection(0)
        self.install_dialog(result={
            "type": "system", "op": "loop_start", "count": 2,
            "infinite": False, "label": "pair",
        }, append_to_end=False)
        self.controller.add_action()
        self.assertEqual(self.trigger["actions"][1:3], [
            {"type": "system", "op": "loop_start", "count": 2,
             "infinite": False, "label": "pair"},
            {"type": "system", "op": "loop_end", "label": ""},
        ])

        self.trigger["actions"] = [
            {"type": "system", "op": "loop_start", "count": 1, "infinite": False, "label": ""}
            for _ in range(9)
        ] + [
            {"type": "system", "op": "loop_end", "label": ""}
            for _ in range(9)
        ]
        self.set_selection(8)
        self.install_dialog(result={
            "type": "system", "op": "loop_start", "count": 1,
            "infinite": False, "label": "",
        }, append_to_end=False)
        before = list(self.trigger["actions"])

        self.controller.add_action()

        self.assertEqual(self.trigger["actions"], before)
        self.showinfo.assert_called_once()
        self.assertIn("9 段", self.showinfo.call_args.args[1])

    def test_editing_loop_end_updates_its_start_configuration(self):
        start = {"type": "system", "op": "loop_start", "count": 2,
                 "infinite": False, "label": "old"}
        end = {"type": "system", "op": "loop_end", "label": ""}
        self.trigger["actions"] = [start, {"type": "text", "text": "inside"}, end]
        self.set_selection(2)
        factory, _dialog = self.install_dialog(result={
            "type": "system", "op": "loop_start", "count": 4,
            "infinite": True, "label": "new",
        })

        self.controller.edit_action()

        self.assertEqual(self.trigger["actions"][0]["count"], 4)
        self.assertTrue(self.trigger["actions"][0]["infinite"])
        self.assertEqual(self.trigger["actions"][0]["label"], "new")
        self.assertEqual(end, {"type": "system", "op": "loop_end", "label": ""})
        self.assertEqual(factory.call_args.kwargs["initial"], {
            "type": "system", "op": "loop_start", "count": 2,
            "infinite": False, "label": "old",
        })
        self.assertEqual(factory.call_args.kwargs["mode"], "edit_loop")

    def test_editing_loop_start_uses_its_own_configuration(self):
        start = {"type": "system", "op": "loop_start", "count": 2,
                 "infinite": False, "label": "old"}
        end = {"type": "system", "op": "loop_end", "label": ""}
        self.trigger["actions"] = [start, end]
        self.set_selection(0)
        factory, _dialog = self.install_dialog(result={
            "type": "system", "op": "loop_start", "count": 3,
            "infinite": False, "label": "changed",
        })

        self.controller.edit_action()

        self.assertEqual(self.trigger["actions"][0]["count"], 3)
        self.assertEqual(self.trigger["actions"][0]["label"], "changed")
        self.assertEqual(end, {"type": "system", "op": "loop_end", "label": ""})
        self.assertEqual(factory.call_args.kwargs["initial"], {
            "type": "system", "op": "loop_start", "count": 2,
            "infinite": False, "label": "old",
        })
        self.assertEqual(factory.call_args.kwargs["mode"], "edit_loop")

    def test_malformed_loop_cannot_be_edited(self):
        self.trigger["actions"] = [{"type": "system", "op": "loop_end", "label": ""}]
        self.set_selection(0)
        factory = patch.object(action_edit_module, "ActionDialog").start()
        self.addCleanup(patch.stopall)

        self.controller.edit_action()

        factory.assert_not_called()
        self.showinfo.assert_called_once()
        self.assertIn("対応が崩れている", self.showinfo.call_args.args[1])

    def test_deleting_paired_loop_confirms_and_removes_only_pair(self):
        self.trigger["actions"] = [
            {"type": "system", "op": "loop_start", "count": 2,
             "infinite": False, "label": ""},
            {"type": "text", "text": "keep"},
            {"type": "system", "op": "loop_end", "label": ""},
        ]
        self.set_selection(0)
        with patch.object(action_edit_module.messagebox, "askyesno", return_value=True) as ask:
            self.controller.delete_action()

        self.assertEqual(self.trigger["actions"], [{"type": "text", "text": "keep"}])
        self.assertIn("中の行は残ります", ask.call_args.args[1])

    def test_loop_row_cannot_move_across_another_loop_row(self):
        self.trigger["actions"] = [
            {"type": "system", "op": "loop_start", "count": 1,
             "infinite": False, "label": ""},
            {"type": "system", "op": "loop_end", "label": ""},
            {"type": "text", "text": "after"},
        ]
        self.set_selection(0)
        before = list(self.trigger["actions"])

        self.controller.move_action(1)

        self.assertEqual(self.trigger["actions"], before)
        self.app.mark_sequence_dirty.assert_not_called()


if __name__ == "__main__":
    unittest.main()
