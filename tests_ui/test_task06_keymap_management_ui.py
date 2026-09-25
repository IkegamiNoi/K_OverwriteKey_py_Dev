import copy
import unittest
from unittest.mock import patch

from keyseq.application.input_router import SelectKeymapAction
from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.dialogs import KeymapEditDialog


def make_runtime(*, one_keymap=False, switch_keys=None):
    keymaps = [
        {
            "id": "km1",
            "label": "Main",
            "mappings": {"a": "z"},
            "triggers": [
                {"key": "f1", "label": "Map A", "suppress": True, "actions": [
                    {"type": "text", "value": "A one"},
                    {"type": "text", "value": "A two"},
                ]},
                {"key": "f2", "label": "A second", "actions": []},
            ],
        },
        {
            "id": "km2",
            "label": "Other",
            "mappings": {"b": "c"},
            "triggers": [
                {"key": "f1", "label": "Map B", "suppress": True, "actions": [
                    {"type": "text", "value": "B one"},
                    {"type": "text", "value": "B two"},
                ]},
                {"key": "f3", "label": "B second", "actions": []},
            ],
        },
    ]
    if one_keymap:
        keymaps = keymaps[:1]
    return {
        "keymaps": keymaps,
        "active_keymap_id": "km1",
        "keymap_switch_keys": {"f9": "km2"} if switch_keys is None else dict(switch_keys),
        "hook_stop_key": "f12",
        "hook_toggle_key": "f11",
    }


class Task06KeymapManagementUiTest(unittest.TestCase):
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
        self.app.state.run_to_end_key = None
        self.app.state.run_to_end_paused = False
        self.app._dialog_result = None
        self.app.dirty_tracker.set_dirty(False)
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()

    def tearDown(self):
        window = self.app.layout.keyboard_window
        if window is not None:
            window._handle_close()
        self.app.data = self.original_data
        self.app.state.reset_indices()
        self.app.state.run_to_end_key = None
        self.app.state.run_to_end_paused = False
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()
        self.app.dirty_tracker.set_dirty(False)

    def test_list_and_direct_switch_redraw_views_without_marking_config_dirty(self):
        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(1)
        keymap_list.activate(1)
        self.app.keymap_panel.on_keymap_list_select()

        self.assertEqual(self.app.data["active_keymap_id"], "km2")
        self.assertFalse(self.app.dirty_tracker.is_dirty)
        self.assertIn("Map B", self.app.full_view.trigger_box.trigger_list.get(0))
        self.assertIn("B one", self.app.full_view.action_list.get(0))
        self.assertIn("Map B", self.app.compact_view.trigger_box.trigger_list.get(0))

        self.app.layout.open_keyboard_window()
        window = self.app.layout.keyboard_window
        self.assertEqual(window._display_map["b"], "c")
        self.app.action_executor.execute_router_action(SelectKeymapAction("km1"))
        self.assertEqual(self.app.data["active_keymap_id"], "km1")
        self.assertFalse(self.app.dirty_tracker.is_dirty)
        self.assertIn("Map A", self.app.full_view.trigger_box.trigger_list.get(0))
        self.assertIn("A one", self.app.full_view.action_list.get(0))
        self.assertEqual(window._display_map["a"], "z")

    def test_select_button_is_absent(self):
        box = self.app.full_view.keymap_box
        self.assertFalse(hasattr(box, "keymap_select_btn"))
        self.assertFalse(hasattr(self.app.keymap_panel, "select_keymap"))

    def test_running_or_paused_run_to_end_blocks_switch_and_active_delete(self):
        status_before = self.app.ui_vars.status_var.get()
        self.app.state.run_to_end_key = "f1"
        self.app.state.run_to_end_paused = False
        self.app.action_executor.execute_router_action(SelectKeymapAction("km2"))
        self.assertEqual(self.app.data["active_keymap_id"], "km1")
        self.app.state.run_to_end_paused = True
        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(1)
        keymap_list.activate(1)
        self.app.keymap_panel.on_keymap_list_select()
        self.assertEqual(self.app.data["active_keymap_id"], "km1")
        self.assertEqual(keymap_list.curselection(), (0,))
        self.assertEqual(self.app.ui_vars.flash_message_var.get(), self.app.keymap_panel.SWITCH_BLOCKED_MESSAGE)
        self.assertEqual(self.app.ui_vars.status_var.get(), status_before)

        self.app.action_executor.execute_router_action(SelectKeymapAction("km2"))
        self.assertEqual(self.app.data["active_keymap_id"], "km1")
        self.assertEqual(self.app.ui_vars.flash_message_var.get(), self.app.keymap_panel.SWITCH_BLOCKED_MESSAGE)
        self.assertEqual(self.app.ui_vars.status_var.get(), status_before)
        with patch("keyseq.presentation.controllers.keymap_panel_controller.messagebox.askyesno") as ask:
            self.app.keymap_panel.delete_keymap()
            ask.assert_not_called()
        self.assertEqual(len(self.app.data["keymaps"]), 2)

        self.app.state.run_to_end_key = None
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(1)
        keymap_list.activate(1)
        self.app.keymap_panel.on_keymap_list_select()
        self.assertEqual(self.app.data["active_keymap_id"], "km2")

    def test_add_prompts_for_missing_switch_keys_and_requires_new_switch_key(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={})
        )
        self.app.trigger_panel.refresh_triggers()
        dialog_results = [
            _DialogResult({"key": "f8", "label": "Main updated"}),
            _DialogResult({"key": "f6", "label": "Other updated"}),
            _DialogResult({"key": "f7", "label": ""}),
        ]
        with patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ) as showerror, patch(
            "keyseq.presentation.controllers.keymap_panel_controller.KeymapEditDialog",
            side_effect=dialog_results,
        ) as edit_dialog:
            self.app.keymap_panel.add_keymap()
        self.assertEqual(edit_dialog.call_count, 3)
        self.assertEqual(showerror.call_count, 2)
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km1"), "f8")
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km2"), "f6")
        added = self.app.data["keymaps"][-1]
        self.assertEqual(added["label"], "")
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, added["id"]), "f7")

        before_count = len(self.app.data["keymaps"])
        with patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ) as showerror, patch(
            "keyseq.presentation.controllers.keymap_panel_controller.KeymapEditDialog",
            return_value=_DialogResult(None),
        ):
            self.app.keymap_panel.add_keymap()
        showerror.assert_not_called()
        self.assertEqual(len(self.app.data["keymaps"]), before_count)

    def test_addition_dialog_retries_empty_key_and_cancel_aborts(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={"f8": "km1", "f9": "km2"})
        )
        dialogs = []

        def enter_empty_then_valid(dialog):
            dialogs.append(dialog)
            dialog.key_var.set("")
            dialog._ok()
            self.assertIsNone(dialog.result)
            self.assertTrue(dialog.winfo_exists())
            dialog.key_var.set("f7")
            dialog._ok()

        with patch.object(KeymapEditDialog, "wait_window", new=enter_empty_then_valid), patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ) as showerror, patch(
            "keyseq.presentation.controllers.keymap_panel_controller.KeymapEditDialog", wraps=KeymapEditDialog
        ) as edit_dialog:
            self.app.keymap_panel.add_keymap()
        self.assertEqual(len(dialogs), 1)
        edit_dialog.assert_called_once()
        self.assertEqual(len(self.app.data["keymaps"]), 3)
        added = self.app.data["keymaps"][-1]
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, added["id"]), "f7")
        showerror.assert_called_once()
        self.assertIs(showerror.call_args.kwargs["parent"], dialogs[0])

        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={"f8": "km1", "f9": "km2"})
        )
        before = copy.deepcopy(self.app.data)

        def cancel_after_empty(dialog):
            dialog.key_var.set("")
            dialog._ok()
            self.assertIsNone(dialog.result)
            self.assertTrue(dialog.winfo_exists())
            dialog.destroy()

        with patch.object(KeymapEditDialog, "wait_window", new=cancel_after_empty), patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ) as showerror:
            self.app.keymap_panel.add_keymap()
        showerror.assert_called_once()
        self.assertEqual(self.app.data, before)

    def test_missing_existing_switch_dialog_retries_empty_and_duplicate_keys(self):
        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime(switch_keys={}))
        dialogs = []
        key_attempts = [("", "f8"), ("f8", "f6"), ("", "f7")]

        def enter_retry_values(dialog):
            dialogs.append(dialog)
            for index, key in enumerate(key_attempts[len(dialogs) - 1]):
                dialog.key_var.set(key)
                dialog._ok()
                if index == 0:
                    self.assertIsNone(dialog.result)
                    self.assertTrue(dialog.winfo_exists())

        with patch.object(KeymapEditDialog, "wait_window", new=enter_retry_values), patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ) as showerror:
            self.app.keymap_panel.add_keymap()

        self.assertEqual(len(dialogs), 3)
        self.assertEqual(showerror.call_count, 5)
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km1"), "f8")
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km2"), "f6")
        added = self.app.data["keymaps"][-1]
        self.assertEqual(
            self.app.keymap_service.find_switch_key_for_keymap(self.app.data, added["id"]), "f7"
        )
        # 入力エラー（ダイアログ表示中）はダイアログを親にする。設定ダイアログを開く前の
        # 「<名前> に切替キーを設定してください」はダイアログがまだ無いので対象外。
        validation_calls = [call for call in showerror.call_args_list if call.args[0] == "設定できません"]
        self.assertEqual(len(validation_calls), 3)
        for call in validation_calls:
            self.assertIn(call.kwargs.get("parent"), dialogs)

    def test_keymap_edit_dialog_validation_controls_close_and_preserves_default(self):
        invalid = KeymapEditDialog(self.app, "追加", validate=lambda _values: False)
        invalid._ok()
        self.assertIsNone(invalid.result)
        self.assertTrue(invalid.winfo_exists())
        invalid.destroy()

        accepted_values = []
        valid = KeymapEditDialog(self.app, "追加", validate=lambda values: accepted_values.append(values) or True)
        valid.key_var.set("f7")
        valid.label_var.set(" Extra ")
        valid._ok()
        self.assertEqual(valid.result, {"key": "f7", "label": "Extra"})
        self.assertEqual(accepted_values, [valid.result])
        self.assertFalse(valid.winfo_exists())

        unchanged = KeymapEditDialog(self.app, "変更", initial_key="f8", initial_label="Main")
        unchanged._ok()
        self.assertEqual(unchanged.result, {"key": "f8", "label": "Main"})
        self.assertFalse(unchanged.winfo_exists())

    def test_add_cancel_after_existing_key_prompt_does_not_add_keymap(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={"f9": "km1"})
        )
        before = copy.deepcopy(self.app.data)
        with patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ), patch(
            "keyseq.presentation.controllers.keymap_panel_controller.KeymapEditDialog",
            return_value=_DialogResult(None),
        ):
            self.app.keymap_panel.add_keymap()
        self.assertEqual(self.app.data, before)

    def test_individual_load_uses_add_rules_and_cancel_preserves_runtime(self):
        loaded = {"id": "km3", "label": "Loaded", "mappings": {"c": "d"}, "triggers": []}
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={"f9": "km1"})
        )
        dialog_results = [
            _DialogResult({"key": "f8", "label": "Other"}),
            _DialogResult({"key": "f7", "label": "Loaded"}),
        ]
        with patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.filedialog.askopenfilename",
            return_value="loaded.json",
        ), patch.object(self.app.keymap_io, "_load_keymap", return_value=copy.deepcopy(loaded)), patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ), patch(
            "keyseq.presentation.controllers.keymap_panel_controller.KeymapEditDialog",
            side_effect=dialog_results,
        ), patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.messagebox.showinfo"
        ):
            self.app.keymap_io.load_keymap_file()
        self.assertEqual(len(self.app.data["keymaps"]), 3)
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km2"), "f8")
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km3"), "f7")
        self.assertEqual(self.app.data["active_keymap_id"], "km1")

        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={"f9": "km1"})
        )
        before = copy.deepcopy(self.app.data)
        with patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.filedialog.askopenfilename",
            return_value="loaded.json",
        ), patch.object(self.app.keymap_io, "_load_keymap", return_value=copy.deepcopy(loaded)), patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ), patch(
            "keyseq.presentation.controllers.keymap_panel_controller.KeymapEditDialog",
            return_value=_DialogResult(None),
        ):
            self.app.keymap_io.load_keymap_file()
        self.assertEqual(self.app.data, before)

    def test_edit_cannot_clear_switch_key_with_two_maps_but_can_with_one(self):
        with patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ) as showerror:
            changed = self.app.keymap_panel.apply_keymap_edit(
                self.app.data["keymaps"][0], new_label="Main", new_key=""
            )
        self.assertFalse(changed)
        showerror.assert_called_once()
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km2"), "f9")

        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f9": "km1"})
        )
        changed = self.app.keymap_panel.apply_keymap_edit(
            self.app.data["keymaps"][0], new_label="Main", new_key=""
        )
        self.assertTrue(changed)
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km1"), "")

    def test_delete_is_disabled_for_one_map_and_warns_about_dirty_children(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f9": "km1"})
        )
        self.app.trigger_panel.refresh_triggers()
        self.assertEqual(str(self.app.full_view.keymap_box.keymap_delete_btn.cget("state")), "disabled")
        with patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ) as showerror:
            self.app.keymap_panel.delete_keymap()
        showerror.assert_called_once()
        self.assertEqual(len(self.app.data["keymaps"]), 1)

        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime())
        target = self.app.data["keymaps"][1]
        target["_trigger_set_dirty"] = True
        target["triggers"][0][self.app.config_service.INTERNAL_SEQUENCE_DIRTY] = True
        self.app.trigger_panel.refresh_triggers()
        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(1)
        keymap_list.activate(1)
        self.app.keymap_panel.on_keymap_list_select()
        with patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.askyesno",
            return_value=False,
        ) as confirm:
            self.app.keymap_panel.delete_keymap()
        self.assertIn("未保存", confirm.call_args.args[1])
        self.assertIn("破棄", confirm.call_args.args[1])

    def test_execution_position_is_independent_for_same_key_in_each_trigger_list(self):
        with patch.object(self.app.input_gateway, "write_text"):
            self.app.sequence_runner.handle_key("f1")
        self.assertEqual(self.app._indices.get("f1"), 1)
        self.app.trigger_panel.set_selected_trigger_index(1)

        self.app.keymap_panel.activate_keymap_by_id("km2")
        self.assertEqual(self.app._indices.get("f1", 0), 0)
        self.assertEqual(self.app._selected_trigger_idx, 0)
        with patch.object(self.app.input_gateway, "write_text"):
            self.app.sequence_runner.handle_key("f1")
        self.assertEqual(self.app._indices.get("f1"), 1)
        self.app.trigger_panel.set_selected_trigger_index(1)

        self.app.keymap_panel.activate_keymap_by_id("km1")
        self.assertEqual(self.app._indices.get("f1"), 1)
        self.assertEqual(self.app._selected_trigger_idx, 1)

    def test_unsaved_nonactive_sequence_edit_survives_switching(self):
        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(1)
        keymap_list.activate(1)
        self.app.keymap_panel.on_keymap_list_select()
        with patch(
            "keyseq.presentation.controllers.trigger_panel_controller.ActionDialog",
            side_effect=lambda *_args, **_kwargs: _ActionDialogResult(self.app),
        ):
            self.app.trigger_panel.add_action()
        target = self.app.data["keymaps"][1]["triggers"][0]
        self.assertEqual(target["actions"][-1]["value"], "unsaved")
        self.assertTrue(target[self.app.config_service.INTERNAL_SEQUENCE_DIRTY])

        self.app.keymap_panel.activate_keymap_by_id("km1")
        self.app.keymap_panel.activate_keymap_by_id("km2")
        self.assertEqual(target["actions"][-1]["value"], "unsaved")
        self.assertTrue(target[self.app.config_service.INTERNAL_SEQUENCE_DIRTY])


class _DialogResult:
    def __init__(self, result):
        self.result = result

    def wait_window(self):
        return None


class _ActionDialogResult:
    def __init__(self, app):
        self.app = app

    def wait_window(self):
        self.app._dialog_result = {"type": "text", "value": "unsaved"}


if __name__ == "__main__":
    unittest.main()
