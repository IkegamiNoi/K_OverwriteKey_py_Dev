import copy
import os
import tempfile
import unittest
from unittest.mock import patch

from keyseq.application.input_router import SelectKeymapAction
from keyseq.application.screen_grid_session import MonitorInfo
from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.dialogs import KeymapEditDialog, KeymapSwitchBatchDialog


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
        with patch.object(self.app.input_gateway, "release_send"), patch.object(
            self.app.input_gateway, "mouse_up"
        ):
            self.app.held_inputs.release_all()
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

    def test_loading_and_restoring_reset_all_keymap_trigger_positions(self):
        original_path = self.app.keymap_set_path
        self.addCleanup(setattr, self.app, "keymap_set_path", original_path)
        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime())
        other_id = self.app.keymap_service.get_trigger_set_id(self.app.data, "km2")
        self.app.state.indices_for(other_id)["f1"] = 1
        loaded = self.app.config_service.normalize_runtime_data(make_runtime())
        io = KeymapSetIo(self.app)

        with patch.object(
            self.app.config_service,
            "load_runtime_data_from_keymap_set_path",
            return_value=loaded,
        ), patch.object(io, "apply_loaded_data_to_ui"), patch.object(
            self.app.dirty_tracker, "set_dirty"
        ), patch.object(self.app.dirty_tracker, "sync_dirty_state"), patch.object(
            self.app.keymap_set_history_io, "record", return_value=(True, "")
        ), patch.object(io, "notify_migrated_legacy_trigger_set"), patch.object(
            self.app, "_set_flash_message"
        ), patch(
            "keyseq.presentation.controllers.config_io.keymap_set_io.messagebox.showinfo"
        ):
            self.assertEqual(io.load_keymap_set_path("loaded.json"), "ok")

        self.assertEqual(self.app.state.indices_for(other_id).get("f1", 0), 0)

        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime())
        self.app.state.indices_for(other_id)["f1"] = 1
        with patch(
            "keyseq.presentation.controllers.config_io.keymap_set_io.messagebox.askyesno",
            return_value=True,
        ), patch.object(self.app, "_set_flash_message"):
            io.restore_default()
        self.assertEqual(self.app.state.indices_for(other_id).get("f1", 0), 0)

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

    def test_running_blocks_switch_but_paused_run_is_discarded_to_switch_or_delete(self):
        self.app.state.run_to_end_key = "f1"
        self.app.state.run_to_end_paused = False
        self.app.action_executor.execute_router_action(SelectKeymapAction("km2"))
        self.assertEqual(self.app.data["active_keymap_id"], "km1")
        self.app.state.run_to_end_paused = True
        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(1)
        keymap_list.activate(1)
        with patch("keyseq.presentation.app.messagebox.askokcancel") as confirm:
            self.app.keymap_panel.on_keymap_list_select()
        confirm.assert_not_called()
        self.assertEqual(self.app.data["active_keymap_id"], "km2")
        self.assertIsNone(self.app.state.run_to_end_key)
        self.assertIn("一時停止中の実行を破棄しました(f1)",
                      self.app.ui_vars.flash_message_var.get())

        self.app.state.run_to_end_key = "f1"
        self.app.state.run_to_end_paused = True
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(1)
        keymap_list.activate(1)
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.askyesno",
            return_value=True,
        ) as ask_delete, patch("keyseq.presentation.app.messagebox.askokcancel") as confirm:
            self.app.keymap_panel.delete_keymap()
        ask_delete.assert_called_once()
        confirm.assert_not_called()
        self.assertEqual(len(self.app.data["keymaps"]), 1)

    def test_discard_notifies_without_dialog(self):
        self.app.state.run_to_end_key = "f1"
        self.app.state.run_to_end_paused = True
        with patch("keyseq.presentation.app.messagebox.askokcancel") as ask:
            self.assertEqual(self.app.sequence_runner.discard_paused(), ("f1",))
        ask.assert_not_called()
        self.assertIn("一時停止中の実行を破棄しました(f1)",
                      self.app.ui_vars.flash_message_var.get())
        self.assertFalse(self.app.state.run_to_end_paused)

    def test_switching_to_active_keymap_keeps_paused_runs(self):
        self.app.state.run_to_end_key = "f1"
        self.app.state.run_to_end_paused = True
        with patch("keyseq.presentation.app.messagebox.askokcancel") as ask:
            self.assertTrue(self.app.keymap_panel.activate_keymap_by_id("km1"))
        ask.assert_not_called()
        self.assertTrue(self.app.state.run_to_end_paused)

    def test_switch_releases_held_keyboard_key_but_same_map_keeps_it(self):
        with patch.object(self.app.input_gateway, "press_send"), patch.object(
            self.app.input_gateway, "release_send"
        ) as release_send:
            self.app.held_inputs.press_key("f1", "shift")
            self.assertTrue(self.app.keymap_panel.activate_keymap_by_id("km1"))
            self.assertEqual(self.app.held_inputs.display_names, ("shift",))
            release_send.assert_not_called()

            self.assertTrue(self.app.keymap_panel.activate_keymap_by_id("km2"))

        self.assertEqual(self.app.held_inputs.display_names, ())
        release_send.assert_called_once()
        self.assertEqual(release_send.call_args.args[0].key, "shift")

    def test_active_delete_uses_only_delete_confirmation(self):
        self.app.state.run_to_end_key = "f1"
        self.app.state.run_to_end_paused = True
        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(0)
        keymap_list.activate(0)

        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.askyesno",
            return_value=False,
        ) as ask_delete, patch("keyseq.presentation.app.messagebox.askokcancel") as confirm:
            self.app.keymap_panel.delete_keymap()
        ask_delete.assert_called_once()
        confirm.assert_not_called()
        self.assertEqual(len(self.app.data["keymaps"]), 2)
        self.assertTrue(self.app.state.run_to_end_paused)

        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.askyesno",
            return_value=True,
        ), patch("keyseq.presentation.app.messagebox.askokcancel") as confirm, patch.object(
            self.app.input_gateway, "press_send"
        ), patch.object(self.app.input_gateway, "release_send") as release_send:
            self.app.held_inputs.press_key("f1", "shift")
            self.app.keymap_panel.delete_keymap()
        confirm.assert_not_called()
        self.assertEqual(len(self.app.data["keymaps"]), 1)
        self.assertFalse(self.app.state.run_to_end_paused)
        self.assertEqual(self.app.held_inputs.display_names, ())
        release_send.assert_called_once()
        self.assertEqual(release_send.call_args.args[0].key, "shift")

    def test_add_prompts_for_missing_switch_keys_and_requires_new_switch_key(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={})
        )
        self.app.trigger_panel.refresh_triggers()
        dialog_result = _DialogResult([
            {"key": "f8", "label": "Main updated"},
            {"key": "f6", "label": "Other updated"},
            {"key": "f7", "label": ""},
        ])
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog",
            return_value=dialog_result,
        ) as batch_dialog, patch.object(
            self.app.keymap_panel, "activate_keymap_by_id", wraps=self.app.keymap_panel.activate_keymap_by_id
        ) as activate:
            self.app.keymap_panel.add_keymap()
        batch_dialog.assert_called_once()
        rows = batch_dialog.call_args.kwargs["rows"]
        self.assertEqual([row[0] for row in rows], ["既存", "既存", "新規"])
        self.assertEqual([row[1] for row in rows[:2]], ["Main", "Other"])
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km1"), "f8")
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km2"), "f6")
        added = self.app.data["keymaps"][-1]
        self.assertEqual(rows[2][1], added["id"])
        self.assertEqual(added["label"], "")
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, added["id"]), "f7")
        self.assertEqual(self.app.data["active_keymap_id"], "km1")
        activate.assert_not_called()

    def test_add_batch_cancel_changes_nothing(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={})
        )
        before = copy.deepcopy(self.app.data)
        self.app.dirty_tracker.set_dirty(False)
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog",
            return_value=_DialogResult(None),
        ) as batch_dialog, patch.object(
            self.app.keymap_panel, "activate_keymap_by_id", wraps=self.app.keymap_panel.activate_keymap_by_id
        ) as activate:
            self.app.keymap_panel.add_keymap()
        batch_dialog.assert_called_once()
        self.assertEqual(self.app.data, before)
        self.assertFalse(self.app.dirty_tracker.has_unsaved_changes())
        self.assertEqual(self.app.data["active_keymap_id"], "km1")
        activate.assert_not_called()

    def test_batch_ok_updates_existing_and_new_without_switching_active_map(self):
        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime(switch_keys={}))
        self.app.dirty_tracker.set_dirty(False)
        result = _DialogResult([
            {"key": "f8", "label": "Main batch"},
            {"key": "f6", "label": "Other batch"},
            {"key": "f7", "label": "Added batch"},
        ])
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog",
            return_value=result,
        ), patch.object(
            self.app.keymap_panel, "activate_keymap_by_id", wraps=self.app.keymap_panel.activate_keymap_by_id
        ) as activate:
            self.app.keymap_panel.add_keymap()

        self.assertEqual(self.app.data["active_keymap_id"], "km1")
        self.assertEqual([item["label"] for item in self.app.data["keymaps"]], [
            "Main batch", "Other batch", "Added batch",
        ])
        self.assertEqual(
            [self.app.keymap_service.find_switch_key_for_keymap(self.app.data, keymap_id)
             for keymap_id in ("km1", "km2", self.app.data["keymaps"][-1]["id"])],
            ["f8", "f6", "f7"],
        )
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())
        self.assertTrue(all(item[self.app.config_service.INTERNAL_KEYMAP_DIRTY]
                            for item in self.app.data["keymaps"]))
        activate.assert_not_called()

    def test_batch_retries_duplicate_key_then_commits_all_rows_once(self):
        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime(switch_keys={}))
        before = copy.deepcopy(self.app.data)
        self.app.dirty_tracker.set_dirty(False)
        dialogs = []

        def enter_duplicate_then_correct(dialog):
            dialogs.append(dialog)
            dialog._ok()
            self.assertIsNone(dialog.result)
            self.assertTrue(dialog.winfo_exists())
            self.assertEqual(self.app.data, before)
            for variable, value in zip(dialog.key_vars, ("f8", "f8", "f7")):
                variable.set(value)
            dialog._ok()
            self.assertIsNone(dialog.result)
            self.assertTrue(dialog.winfo_exists())
            self.assertEqual(self.app.data, before)
            dialog.key_vars[1].set("f6")
            dialog._ok()

        with patch.object(KeymapSwitchBatchDialog, "wait_window", new=enter_duplicate_then_correct), patch(
            "keyseq.presentation.dialogs.keymap_switch_batch_dialog.messagebox.showerror"
        ) as showerror, patch.object(
            self.app.keymap_panel, "activate_keymap_by_id", wraps=self.app.keymap_panel.activate_keymap_by_id
        ) as activate:
            self.app.keymap_panel.add_keymap()

        self.assertEqual(len(dialogs), 1)
        self.assertEqual(showerror.call_count, 2)
        self.assertTrue(all(call.kwargs.get("parent") is dialogs[0] for call in showerror.call_args_list))
        self.assertEqual(len(self.app.data["keymaps"]), 3)
        self.assertEqual(
            [self.app.keymap_service.find_switch_key_for_keymap(self.app.data, keymap_id)
             for keymap_id in ("km1", "km2", self.app.data["keymaps"][-1]["id"])],
            ["f8", "f6", "f7"],
        )
        self.assertEqual(self.app.data["active_keymap_id"], "km1")
        activate.assert_not_called()

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
        self.assertEqual(valid.result, {"key": "f7", "label": "Extra", "grid_enabled": False})
        self.assertEqual(accepted_values, [valid.result])
        self.assertFalse(valid.winfo_exists())

        unchanged = KeymapEditDialog(self.app, "変更", initial_key="f8", initial_label="Main")
        unchanged._ok()
        self.assertEqual(unchanged.result, {"key": "f8", "label": "Main", "grid_enabled": False})
        self.assertFalse(unchanged.winfo_exists())

    def test_keymap_edit_dialog_grid_checkbox_initial_value_and_result(self):
        for grid, expected in (({"enabled": True}, True), ({"enabled": False}, False), (None, False)):
            with self.subTest(grid=grid):
                self.app.data["keymaps"][0].pop("grid", None)
                if grid is not None:
                    self.app.data["keymaps"][0]["grid"] = grid
                dialog_result = _DialogResult(None)
                with patch(
                    "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.KeymapEditDialog",
                    return_value=dialog_result,
                ) as edit_dialog:
                    self.app.keymap_panel.edit_selected_keymap()
                self.assertEqual(edit_dialog.call_args.kwargs["initial_grid_enabled"], expected)

                dialog = KeymapEditDialog(
                    self.app, "変更", initial_grid_enabled=expected
                )
                self.assertEqual(dialog.grid_enabled_var.get(), expected)
                dialog._ok()
                self.assertEqual(dialog.result["grid_enabled"], expected)

    def test_keymap_edit_dialog_hides_grid_editor_without_context(self):
        dialog = KeymapEditDialog(self.app, "変更")
        self.assertFalse(hasattr(dialog, "grid_editor_btn"))
        dialog.destroy()

    def test_keymap_edit_dialog_grid_editor_result_is_returned_as_draft(self):
        from types import SimpleNamespace

        monitors = [MonitorInfo("1920x1080+0+0", (0, 0, 1920, 1080), True)]
        shapes = {
            "monitors": {"m1": {"rows": [{"h": 1, "cells": [{"w": 1, "key": "a"}]}]}},
            "sub": {"rows": 1, "cols": 2, "keys": ["a", "b"]},
        }
        context = (monitors, "m1", {"f12", "f11", "f9"})
        with patch(
            "keyseq.presentation.dialogs.keymap_edit_dialog.GridEditorWindow",
            return_value=SimpleNamespace(result=shapes, wait_window=lambda: None),
        ) as editor_factory:
            dialog = KeymapEditDialog(
                self.app, "変更", initial_key="f8", grid_editor_context=lambda: context
            )
            dialog.grid_editor_btn.invoke()
            editor_factory.assert_called_once()
            self.assertEqual(editor_factory.call_args.kwargs["reserved"], {"f12", "f11", "f9", "f8"})
            dialog._ok()

        self.assertEqual(dialog.result["grid"], shapes)
        self.assertEqual(dialog.result["grid_enabled"], False)

    def test_keymap_edit_dialog_grid_editor_returns_focus_after_close(self):
        from types import SimpleNamespace

        context = ([MonitorInfo("m1", (0, 0, 100, 100), True)], "m1", set())
        for result in ({"monitors": {}}, None):
            with self.subTest(result=result):
                dialog = KeymapEditDialog(
                    self.app, "変更", grid_editor_context=lambda: context
                )
                try:
                    with patch.object(dialog.grid_editor_btn, "focus_force") as focus_force, patch(
                        "keyseq.presentation.dialogs.keymap_edit_dialog.GridEditorWindow",
                        return_value=SimpleNamespace(result=result, wait_window=lambda: None),
                    ):
                        dialog._edit_grid()
                    focus_force.assert_called_once_with()
                finally:
                    dialog.destroy()

    def test_keymap_edit_dialog_grid_editor_does_not_focus_after_dialog_destroyed(self):
        from types import SimpleNamespace

        context = ([MonitorInfo("m1", (0, 0, 100, 100), True)], "m1", set())
        dialog = KeymapEditDialog(self.app, "変更", grid_editor_context=lambda: context)
        try:
            with patch.object(dialog.grid_editor_btn, "focus_force") as focus_force, patch(
                "keyseq.presentation.dialogs.keymap_edit_dialog.GridEditorWindow",
                return_value=SimpleNamespace(
                    result=None, wait_window=lambda: dialog.destroy()
                ),
            ):
                dialog._edit_grid()
            focus_force.assert_not_called()
        finally:
            if dialog.winfo_exists():
                dialog.destroy()

    def test_grid_editor_context_excludes_edited_switch_key_but_dialog_adds_current_value(self):
        from types import SimpleNamespace

        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={"f8": "km1", "f9": "km2"})
        )
        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(0)
        keymap_list.activate(0)
        monitors = [MonitorInfo("m1", (0, 0, 100, 100), True)]
        with patch.object(self.app.screen_grid, "list_monitors", return_value=monitors), patch.object(
            self.app.input_gateway, "cursor_position", return_value=(10, 10)
        ), patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.KeymapEditDialog",
            return_value=_DialogResult(None),
        ) as edit_dialog:
            self.app.keymap_panel.edit_selected_keymap()

        context = edit_dialog.call_args.kwargs["grid_editor_context"]()
        self.assertNotIn("f8", context[2])
        self.assertIn("f9", context[2])
        with patch(
            "keyseq.presentation.dialogs.keymap_edit_dialog.GridEditorWindow",
            return_value=SimpleNamespace(result=None, wait_window=lambda: None),
        ) as editor_factory:
            dialog = KeymapEditDialog(
                self.app, "変更", initial_key="f8",
                grid_editor_context=lambda: context,
            )
            dialog.grid_editor_btn.invoke()
            self.assertIn("f8", editor_factory.call_args.kwargs["reserved"])
            self.assertIn("f9", editor_factory.call_args.kwargs["reserved"])
            dialog.destroy()

    def test_grid_editor_context_keeps_reserved_hook_keys_when_own_switch_key_matches(self):
        monitors = [MonitorInfo("m1", (0, 0, 100, 100), True)]
        with patch.object(self.app.screen_grid, "list_monitors", return_value=monitors), patch.object(
            self.app.input_gateway, "cursor_position", return_value=(10, 10)
        ):
            self.app.data = self.app.config_service.normalize_runtime_data(
                make_runtime(switch_keys={"f8": "km1", "f9": "km2"})
            )
            self.app.data["hook_stop_key"] = "f8"
            self.app.data["hook_toggle_key"] = "f7"
            _monitors, _monitor_id, reserved = self.app.keymap_panel._grid_editor_context("km1")
            self.assertIn("f8", reserved)
            self.assertIn("f7", reserved)

            self.app.data["hook_stop_key"] = "f12"
            self.app.data["hook_toggle_key"] = "f11"
            _monitors, _monitor_id, reserved = self.app.keymap_panel._grid_editor_context("km1")
            self.assertNotIn("f8", reserved)
            self.assertIn("f12", reserved)
            self.assertIn("f11", reserved)

    def test_keymap_edit_dialog_passes_grid_key_resolver_to_editor(self):
        from types import SimpleNamespace

        resolver = lambda _event: "."
        context = ([MonitorInfo("m1", (0, 0, 100, 100), True)], "m1", set())
        with patch(
            "keyseq.presentation.dialogs.keymap_edit_dialog.GridEditorWindow",
            return_value=SimpleNamespace(result=None, wait_window=lambda: None),
        ) as editor_factory:
            dialog = KeymapEditDialog(
                self.app, "変更", grid_editor_context=lambda: context,
                key_name_from_event=resolver,
            )
            dialog.grid_editor_btn.invoke()
            self.assertIs(editor_factory.call_args.kwargs["key_name_from_event"], resolver)
            dialog.destroy()

    def test_keymap_panel_resolves_grid_key_through_scan_code_with_tk_fallback(self):
        from types import SimpleNamespace

        event = SimpleNamespace(keycode=190, state=0, keysym="period")
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.win32_window.vk_to_scan_code",
            return_value=0x34,
        ) as to_scan_code, patch.object(
            self.app.layout, "resolve_key_name_from_scan_code", return_value="period-key"
        ) as resolve:
            self.assertEqual(self.app.keymap_panel._grid_key_name_from_event(event), "period-key")
        to_scan_code.assert_called_once_with(190)
        resolve.assert_called_once_with(0x34)

        module = "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.win32_window"
        with patch(f"{module}.vk_to_scan_code", return_value=None), patch(
            f"{module}.vk_to_char", return_value="."
        ) as to_char:
            self.assertEqual(self.app.keymap_panel._grid_key_name_from_event(event), ".")
        to_char.assert_called_once_with(190)

        with patch(f"{module}.vk_to_scan_code", return_value=None), patch(
            f"{module}.vk_to_char", return_value=""
        ):
            self.assertEqual(self.app.keymap_panel._grid_key_name_from_event(event), "period")

    def test_keymap_edit_dialog_grid_editor_without_monitors_reports_error(self):
        dialog = KeymapEditDialog(
            self.app, "変更", initial_key="f8", grid_editor_context=lambda: ([], "", set())
        )
        try:
            with patch("keyseq.presentation.dialogs.keymap_edit_dialog.messagebox.showerror") as error, patch(
                "keyseq.presentation.dialogs.keymap_edit_dialog.GridEditorWindow"
            ) as editor:
                dialog.grid_editor_btn.invoke()
            error.assert_called_once()
            editor.assert_not_called()
            self.assertTrue(dialog.winfo_exists())
        finally:
            dialog.destroy()

    def test_keymap_edit_dialog_grid_editor_cancel_keeps_initial_draft(self):
        from types import SimpleNamespace

        initial_grid = {
            "enabled": True,
            "monitors": {"m1": {"rows": [{"h": 1, "cells": [{"w": 1, "key": "a"}]}]}},
            "sub": {"rows": 1, "cols": 2, "keys": ["a", "b"]},
        }
        original_grid = copy.deepcopy(initial_grid)
        with patch(
            "keyseq.presentation.dialogs.keymap_edit_dialog.GridEditorWindow",
            return_value=SimpleNamespace(result=None, wait_window=lambda: None),
        ):
            dialog = KeymapEditDialog(
                self.app, "変更", initial_grid=initial_grid,
                grid_editor_context=lambda: ([MonitorInfo("m1", (0, 0, 1920, 1080), True)], "m1", set()),
            )
            dialog.grid_editor_btn.invoke()
            self.assertEqual(dialog._grid_draft, original_grid)
            dialog._ok()

        self.assertEqual(dialog.result["grid"], original_grid)

    def test_keymap_edit_grid_shapes_replace_shapes_and_mark_dirty(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f8": "km1"})
        )
        keymap = self.app.data["keymaps"][0]
        keymap["grid"] = {"enabled": True, "monitors": {"old": "layout"}, "sub": {"old": True}}
        shapes = {
            "monitors": {"new": {"rows": [{"h": 1, "cells": [{"w": 1, "key": "x"}]}]}},
            "sub": {"rows": 1, "cols": 2, "keys": ["x", "y"]},
        }
        self.app.dirty_tracker.set_dirty(False)

        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap, new_label="Main", new_key="f8", new_grid_shapes=shapes
        )

        self.assertTrue(changed)
        self.assertEqual(keymap["grid"], {"enabled": True, **shapes})
        self.assertIsNot(keymap["grid"]["monitors"], shapes["monitors"])
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

    def test_keymap_edit_grid_shapes_create_disabled_grid_when_missing(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f8": "km1"})
        )
        keymap = self.app.data["keymaps"][0]
        keymap.pop("grid", None)
        self.app.dirty_tracker.set_dirty(False)

        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap, new_label="Main", new_key="f8", new_grid_shapes={}
        )

        self.assertTrue(changed)
        self.assertEqual(keymap["grid"], {"enabled": False, "monitors": {}, "sub": {}})
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

    def test_keymap_edit_grid_ops_add_replace_remove_and_same_value(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f8": "km1"})
        )
        keymap = self.app.data["keymaps"][0]
        keymap["grid"] = {"enabled": True, "monitors": {}, "sub": {}}
        first = {"deepen": "g", "back": "h"}
        shapes = {"monitors": {}, "sub": {}, "ops": first}
        self.app.dirty_tracker.set_dirty(False)

        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap, new_label="Main", new_key="f8", new_grid_shapes=shapes
        )

        self.assertTrue(changed)
        self.assertEqual(keymap["grid"]["ops"], first)
        self.assertIsNot(keymap["grid"]["ops"], first)
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

        self.app.dirty_tracker.clear_individual_dirty_flags()
        self.app.dirty_tracker.set_dirty(False)
        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap, new_label="Main", new_key="f8",
            new_grid_shapes={"monitors": {}, "sub": {}, "ops": dict(first)},
        )
        self.assertFalse(changed)
        self.assertFalse(self.app.dirty_tracker.has_unsaved_changes())

        replacement = {"deepen": "t", "back": "y"}
        self.app.dirty_tracker.clear_individual_dirty_flags()
        self.app.dirty_tracker.set_dirty(False)
        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap, new_label="Main", new_key="f8",
            new_grid_shapes={"monitors": {}, "sub": {}, "ops": replacement},
        )
        self.assertTrue(changed)
        self.assertEqual(keymap["grid"]["ops"], replacement)
        self.assertIsNot(keymap["grid"]["ops"], replacement)
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

        self.app.dirty_tracker.clear_individual_dirty_flags()
        self.app.dirty_tracker.set_dirty(False)
        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap, new_label="Main", new_key="f8",
            new_grid_shapes={"monitors": {}, "sub": {}},
        )
        self.assertTrue(changed)
        self.assertNotIn("ops", keymap["grid"])
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

    def test_keymap_edit_grid_label_position_add_remove_marks_dirty(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f8": "km1"})
        )
        keymap = self.app.data["keymaps"][0]
        keymap["grid"] = {"enabled": True, "monitors": {}, "sub": {}}
        self.app.dirty_tracker.set_dirty(False)

        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap,
            new_label="Main",
            new_key="f8",
            new_grid_shapes={"monitors": {}, "sub": {}, "label_position": "top_left"},
        )

        self.assertTrue(changed)
        self.assertEqual(keymap["grid"]["label_position"], "top_left")
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

        self.app.dirty_tracker.set_dirty(False)
        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap,
            new_label="Main",
            new_key="f8",
            new_grid_shapes={"monitors": {}, "sub": {}},
        )

        self.assertTrue(changed)
        self.assertNotIn("label_position", keymap["grid"])
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

    def test_keymap_edit_dialog_receives_grid_and_applies_returned_shapes(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f8": "km1"})
        )
        keymap = self.app.data["keymaps"][0]
        initial_grid = {"enabled": True, "monitors": {"old": []}, "sub": {"old": 1}}
        keymap["grid"] = copy.deepcopy(initial_grid)
        shapes = {
            "monitors": {"edited": {"rows": [{"h": 1, "cells": [{"w": 1, "key": "x"}]}]}},
            "sub": {"rows": 1, "cols": 2, "keys": ["x", "y"]},
        }
        dialog_result = _DialogResult({
            "key": "f8", "label": "Main", "grid_enabled": True, "grid": shapes,
        })
        self.app.dirty_tracker.set_dirty(False)
        received = []

        with patch.object(self.app.keymap_panel, "_grid_editor_context", return_value=([], "", set())) as context, patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.KeymapEditDialog",
            side_effect=lambda *args, **kwargs: (
                received.append(copy.deepcopy(kwargs["initial_grid"])) or dialog_result
            ),
        ) as dialog_factory:
            self.app.keymap_panel.edit_selected_keymap()
            # 編集中の keymap の id を渡して予約キーから自分の切替キーを除くため、lambda で包んで渡す（task_07 L2）。
            self.assertEqual(dialog_factory.call_args.kwargs["grid_editor_context"](), ([], "", set()))
            context.assert_called_once_with(keymap["id"])

        self.assertEqual(received, [initial_grid])
        self.assertEqual(keymap["grid"], {"enabled": True, **shapes})
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

    def test_keymap_edit_cancel_does_not_apply_grid_shapes(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f8": "km1"})
        )
        keymap = self.app.data["keymaps"][0]
        original_grid = {"enabled": True, "monitors": {"saved": []}, "sub": {"x": 1}}
        keymap["grid"] = copy.deepcopy(original_grid)
        self.app.dirty_tracker.set_dirty(False)

        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.KeymapEditDialog",
            return_value=_DialogResult(None),
        ):
            self.app.keymap_panel.edit_selected_keymap()

        self.assertEqual(keymap["grid"], original_grid)
        self.assertFalse(self.app.dirty_tracker.has_unsaved_changes())

    def test_keymap_edit_grid_on_creates_default_grid_and_marks_dirty(self):
        from keyseq.domain.screen_grid import new_enabled_grid

        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f8": "km1"})
        )
        self.app.dirty_tracker.set_dirty(False)
        keymap = self.app.data["keymaps"][0]
        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap, new_label="Main", new_key="f8", new_grid_enabled=True
        )
        self.assertTrue(changed)
        self.assertEqual(keymap["grid"], new_enabled_grid())
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

    def test_keymap_edit_grid_off_keeps_grid_and_unchanged_value_does_not_touch_it(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f8": "km1"})
        )
        keymap = self.app.data["keymaps"][0]
        keymap["grid"] = {"enabled": True, "monitors": {}, "sub": {"kept": True}}
        self.app.dirty_tracker.set_dirty(False)
        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap, new_label="Main", new_key="f8", new_grid_enabled=False
        )
        self.assertTrue(changed)
        self.assertEqual(keymap["grid"], {
            "enabled": False, "monitors": {}, "sub": {"kept": True},
        })

        retained_grid = keymap["grid"]
        self.app.dirty_tracker.set_dirty(False)
        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap, new_label="Main", new_key="f8", new_grid_enabled=False
        )
        self.assertFalse(changed)
        self.assertIs(keymap["grid"], retained_grid)

    def test_keymap_edit_without_grid_value_does_not_add_grid(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(one_keymap=True, switch_keys={"f8": "km1"})
        )
        keymap = self.app.data["keymaps"][0]
        self.app.dirty_tracker.set_dirty(False)
        changed = self.app.keymap_panel.apply_keymap_edit(
            keymap, new_label="Main", new_key="f8"
        )
        self.assertFalse(changed)
        self.assertNotIn("grid", keymap)
        self.assertFalse(self.app.dirty_tracker.has_unsaved_changes())

    def test_batch_new_grid_option_is_only_passed_for_new_keymaps(self):
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={})
        )
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog",
            return_value=_DialogResult(None),
        ) as batch_dialog:
            self.app.keymap_panel._keymap_add_flow._run_batch("新規", [{"id": "km3", "label": "", "mappings": {}}])
            self.assertEqual(tuple(batch_dialog.call_args.kwargs["grid_option_rows"]), (2,))
            self.app.keymap_panel._keymap_add_flow._run_batch("読込", [{"id": "km3", "label": "", "mappings": {}}])
            self.assertEqual(batch_dialog.call_args.kwargs["grid_option_rows"], ())
            self.app.keymap_panel._keymap_add_flow._run_batch("貼り付け", [{"id": "km3", "label": "", "mappings": {}}])
            self.assertEqual(batch_dialog.call_args.kwargs["grid_option_rows"], ())

    def test_batch_new_grid_option_creates_grid_only_when_checked(self):
        from keyseq.domain.screen_grid import new_enabled_grid

        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                self.app.data = self.app.config_service.normalize_runtime_data(
                    make_runtime(switch_keys={})
                )
                result = _DialogResult([
                    {"key": "f8", "label": "Main"},
                    {"key": "f6", "label": "Other"},
                    {"key": "f7", "label": "Added", "grid_enabled": enabled},
                ])
                with patch(
                    "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog",
                    return_value=result,
                ):
                    self.app.keymap_panel._keymap_add_flow._run_batch(
                        "新規", [{"id": "km3", "label": "", "mappings": {}}]
                    )
                added = self.app.data["keymaps"][-1]
                if enabled:
                    self.assertEqual(added["grid"], new_enabled_grid())
                else:
                    self.assertNotIn("grid", added)

    def test_add_with_no_existing_keymaps_skips_batch_dialog(self):
        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime(one_keymap=True))
        self.app.data["keymaps"] = []
        self.app.data["active_keymap_id"] = None
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog"
        ) as batch_dialog:
            self.app.keymap_panel.add_keymap()
        batch_dialog.assert_not_called()
        self.assertEqual(len(self.app.data["keymaps"]), 1)

    def test_individual_load_with_no_existing_keymaps_skips_batch_dialog(self):
        loaded = {"id": "km3", "label": "Loaded", "mappings": {"c": "d"}, "triggers": []}
        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime(one_keymap=True))
        self.app.data["keymaps"] = []
        self.app.data["active_keymap_id"] = None
        with patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.filedialog.askopenfilename",
            return_value="loaded.json",
        ), patch.object(self.app.keymap_io, "_load_keymap", return_value=copy.deepcopy(loaded)), patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog"
        ) as batch_dialog, patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.messagebox.showinfo"
        ):
            self.app.keymap_io.load_keymap_file()
        batch_dialog.assert_not_called()
        self.assertEqual([item["id"] for item in self.app.data["keymaps"]], ["km3"])

    def test_individual_load_uses_add_rules_and_cancel_preserves_runtime(self):
        loaded = {"id": "km3", "label": "Loaded", "mappings": {"c": "d"}, "triggers": []}
        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={"f9": "km1"})
        )
        dialog_result = _DialogResult([
            {"key": "f8", "label": "Other"},
            {"key": "f7", "label": "Loaded"},
        ])
        with patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.filedialog.askopenfilename",
            return_value="loaded.json",
        ), patch.object(self.app.keymap_io, "_load_keymap", return_value=copy.deepcopy(loaded)), patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog",
            return_value=dialog_result,
        ) as batch_dialog, patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.messagebox.showinfo"
        ):
            self.app.keymap_io.load_keymap_file()
        batch_dialog.assert_called_once()
        self.assertEqual([row[0] for row in batch_dialog.call_args.kwargs["rows"]], ["既存", "読込"])
        self.assertEqual(len(self.app.data["keymaps"]), 3)
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km2"), "f8")
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km3"), "f7")
        self.assertEqual(self.app.data["active_keymap_id"], "km1")

        self.app.data = self.app.config_service.normalize_runtime_data(
            make_runtime(switch_keys={"f9": "km1"})
        )
        before = copy.deepcopy(self.app.data)
        self.app.dirty_tracker.set_dirty(False)
        with patch(
            "keyseq.presentation.controllers.config_io.keymap_file_io.filedialog.askopenfilename",
            return_value="loaded.json",
        ), patch.object(self.app.keymap_io, "_load_keymap", return_value=copy.deepcopy(loaded)), patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog",
            return_value=_DialogResult(None),
        ) as batch_dialog, patch.object(
            self.app.keymap_panel, "activate_keymap_by_id", wraps=self.app.keymap_panel.activate_keymap_by_id
        ) as activate:
            self.app.keymap_io.load_keymap_file()
        batch_dialog.assert_called_once()
        self.assertEqual(self.app.data, before)
        self.assertFalse(self.app.dirty_tracker.has_unsaved_changes())
        self.assertEqual(self.app.data["active_keymap_id"], "km1")
        activate.assert_not_called()

    def test_edit_cannot_clear_switch_key_with_two_maps_but_can_with_one(self):
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.showerror"
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
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.showerror"
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
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.askyesno",
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

    def test_deleting_shared_representative_preserves_trigger_list_positions(self):
        shared = self.app.data["keymaps"][0]["triggers"]
        self.app.data["keymaps"][1]["triggers"] = shared
        self.app.state.update_selected_index(1, "km1")
        self.app.state.indices_for("km1")["f1"] = 1
        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(0)
        keymap_list.activate(0)

        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.askyesno",
            return_value=True,
        ):
            self.app.keymap_panel.delete_keymap()

        self.assertEqual(self.app.data["active_keymap_id"], "km2")
        self.assertEqual(self.app._selected_trigger_idx, 1)
        self.assertEqual(self.app._indices.get("f1"), 1)

    def test_deleting_migration_target_clears_legacy_record_before_save(self):
        with tempfile.TemporaryDirectory() as directory:
            config_root = os.path.join(directory, "config")
            self.app.config_service.ensure_split_config_dirs(config_root)
            self.app.config_service.repository.save_json(
                os.path.join(config_root, "user", "trigger_sets", "old.json"),
                {"triggers": [{"key": "f8", "actions": []}]},
            )
            self.app.config_service.repository.save_json(
                os.path.join(config_root, "user", "trigger_sets", "own.json"),
                {"triggers": [{"key": "f9", "actions": []}]},
            )
            self.app.config_service.repository.save_json(
                os.path.join(config_root, "user", "keymaps", "a.json"),
                {"id": "a", "label": "A", "mappings": {}, "trigger_set_path": "user/trigger_sets/own.json"},
            )
            self.app.config_service.repository.save_json(
                os.path.join(config_root, "user", "keymaps", "b.json"),
                {"id": "b", "label": "B", "mappings": {}, "trigger_set_path": ""},
            )
            keymap_set_path = os.path.join(config_root, "user", "keymap_sets", "main.json")
            self.app.config_service.repository.save_json(keymap_set_path, {
                "keymaps": [
                    {"path": "user/keymaps/a.json", "switch_key": "1"},
                    {"path": "user/keymaps/b.json", "switch_key": "2"},
                ],
                "active_keymap_path": "user/keymaps/a.json",
                "trigger_set_path": "user/trigger_sets/old.json",
            })
            previous_root = self.app.config_root
            previous_set_path = self.app.keymap_set_path
            previous_data = self.app.data
            try:
                self.app.config_root = config_root
                self.app.keymap_set_path = keymap_set_path
                self.app.data = self.app.config_service.load_runtime_data_from_keymap_set_path(
                    keymap_set_path, config_root=config_root,
                )
                migration_id = self.app.data["_legacy_trigger_set"]["keymap_id"]
                self.assertTrue(self.app.data["_legacy_trigger_set"]["auto_created"])
                self.app.trigger_panel.refresh_triggers()
                keymap_list = self.app.full_view.keymap_box.keymap_listbox
                migration_index = next(
                    index for index, item in enumerate(self.app.data["keymaps"])
                    if item["id"] == migration_id
                )
                keymap_list.selection_clear(0, "end")
                keymap_list.selection_set(migration_index)
                keymap_list.activate(migration_index)
                with patch(
                    "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.askyesno",
                    return_value=True,
                ):
                    self.app.keymap_panel.delete_keymap()
                self.assertEqual(self.app.data["_legacy_trigger_set"], {
                    "state": "none", "path": "", "keymap_id": "",
                })
                self.assertIsNone(self.app.keymap_service.find_keymap(self.app.data, migration_id))
                self.app.config_service.save_runtime_data(
                    keymap_set_path, self.app.data, config_root=config_root,
                    migration_source_keymap_set_path=keymap_set_path,
                )
                saved_set = self.app.config_service.repository.load_json(keymap_set_path)
                self.assertEqual(saved_set["trigger_set_path"], "")
            finally:
                self.app.config_root = previous_root
                self.app.keymap_set_path = previous_set_path
                self.app.data = previous_data

    def test_new_config_creates_one_keymap(self):
        self.app.dirty_tracker.set_dirty(False)

        KeymapSetIo(self.app).new_config()

        self.assertEqual(len(self.app.data["keymaps"]), 1)
        self.assertEqual(self.app.data["active_keymap_id"], self.app.data["keymaps"][0]["id"])

    def test_unsaved_nonactive_sequence_edit_survives_switching(self):
        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(1)
        keymap_list.activate(1)
        self.app.keymap_panel.on_keymap_list_select()
        with patch(
            "keyseq.presentation.controllers.trigger_panel.action_edit.ActionDialog",
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
