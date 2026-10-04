"""Full-view keymap range operations and selection integration."""

import copy
import unittest
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.controllers.config_io.keymap_file_io import KeymapFileIo
from keyseq.presentation.controllers.keymap_panel import keymap_list_edit as edit_module
from keyseq.presentation.dialogs import KeymapSwitchBatchDialog
from keyseq.presentation.list_clipboard import CLIP_KEYMAPS
from keyseq.presentation.listbox_range_drag import select_range
from tests_ui.click_time import next_click_time


def make_runtime():
    return {
        "keymaps": [
            {
                "id": f"km{number}",
                "label": label,
                "mappings": {f"source{number}": f"target{number}"},
                "triggers": [
                    {"key": f"f{number}", "label": "Trigger", "actions": [
                        {"type": "text", "value": f"map {number}"}
                    ]}
                ],
            }
            for number, label in enumerate(("Map", "Map (2)", "Other"), start=1)
        ],
        "active_keymap_id": "km1",
        "keymap_switch_keys": {"f7": "km1", "f8": "km2", "f9": "km3"},
        "hook_stop_key": "f12",
        "hook_toggle_key": "f11",
    }


class _DialogResult:
    def __init__(self, result):
        self.result = result

    def wait_window(self):
        pass


class KeymapListOperationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(StartupIo, "load_startup_and_config"):
            cls.app = App()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.original_data = self.app.data
        self.original_compact_mode = self.app._compact_mode
        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime())
        self.app.state.reset_indices()
        self.app._compact_mode = False
        self.app.list_clipboard.clear()
        self.app.dirty_tracker.set_dirty(False)
        self.panel = self.app.keymap_panel
        self.listbox = self.app.full_view.keymap_box.keymap_listbox
        self.panel.refresh_keymap_list_ui()
        self.app.update()
        self.addCleanup(self._restore_app)

    def _restore_app(self):
        self.app.data = self.original_data
        self.app._compact_mode = self.original_compact_mode
        self.app.state.reset_indices()
        self.app.list_clipboard.clear()
        self.panel.refresh_keymap_list_ui()
        self.app.dirty_tracker.set_dirty(False)

    def select(self, start, end, *, active=None):
        select_range(self.listbox, start, end, active=active)

    def test_shift_range_commit_activates_underline_row(self):
        self.listbox.focus_force()
        self.listbox.selection_anchor(0)
        x, y, width, height = self.listbox.bbox(2)
        self.listbox.event_generate(
            "<ButtonPress-1>", time=next_click_time(), x=x + width // 2, y=y + height // 2, state=0x1
        )
        self.listbox.event_generate(
            "<ButtonRelease-1>", x=x + width // 2, y=y + height // 2, state=0x1
        )
        self.app.update()

        self.assertEqual(tuple(self.listbox.curselection()), (0, 1, 2))
        self.assertEqual(int(self.listbox.index("active")), 2)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km3")

    def test_rejected_shift_range_restores_only_original_active_row(self):
        self.select(0, 0)
        with patch.object(self.app.state, "can_switch_keymap", return_value=False):
            self.listbox.focus_force()
            self.listbox.selection_anchor(0)
            x, y, width, height = self.listbox.bbox(2)
            self.listbox.event_generate(
                "<ButtonPress-1>", time=next_click_time(), x=x + width // 2, y=y + height // 2, state=0x1
            )
            self.listbox.event_generate(
                "<ButtonRelease-1>", x=x + width // 2, y=y + height // 2, state=0x1
            )
            self.app.update()

        self.assertEqual(tuple(self.listbox.curselection()), (0,))
        self.assertEqual(int(self.listbox.index("active")), 0)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km1")

    def test_move_preserves_active_keymap_and_selects_moved_row(self):
        before_active = self.app.keymap_service.get_active_keymap_id(self.app.data)
        with patch.object(self.app.dirty_tracker, "set_dirty", wraps=self.app.dirty_tracker.set_dirty) as dirty:
            self.assertTrue(self.panel.on_keymap_list_move(1, 1, 2))

        self.assertEqual([item["id"] for item in self.app.data["keymaps"]], ["km1", "km3", "km2"])
        self.assertEqual(tuple(self.listbox.curselection()), (2,))
        self.assertEqual(int(self.listbox.index("active")), 0)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), before_active)
        dirty.assert_called_with(True)

    def test_unchanged_move_does_not_mark_dirty_or_refresh(self):
        with patch.object(self.app.dirty_tracker, "set_dirty") as dirty, \
             patch.object(self.panel, "refresh_keymap_list_ui", wraps=self.panel.refresh_keymap_list_ui) as refresh:
            self.assertTrue(self.panel.on_keymap_list_move(0, 0, 0))
        dirty.assert_not_called()
        refresh.assert_not_called()

    def test_move_rekeys_shared_trigger_set_and_keeps_execution_state(self):
        keymaps = self.app.data["keymaps"]
        keymaps[1]["triggers"] = keymaps[0]["triggers"]
        # 実行位置 2 が再描画の正規化（アクション数で割った余り）で 0 に戻らないよう 3 つにする。
        keymaps[0]["triggers"][0]["actions"] = [
            {"type": "text", "value": str(number)} for number in range(3)
        ]
        self.app.state.keymap_indices["km1"] = {"f1": 2}
        execution_indices = self.app.state.keymap_indices["km1"]
        self.app.state.keymap_history["km1"] = {"f1": [object()]}
        history = self.app.state.keymap_history["km1"]
        with patch.object(self.app.state, "rekey_trigger_set", wraps=self.app.state.rekey_trigger_set) as rekey, \
             patch.object(
                 self.app.sequence_runner,
                 "publish_call_view",
                 wraps=self.app.sequence_runner.publish_call_view,
             ) as publish_call_view:
            self.assertTrue(self.panel.on_keymap_list_move(0, 0, 1))

        rekey.assert_called_once_with("km1", "km2")
        publish_call_view.assert_called_once_with()
        self.assertIs(self.app.state.keymap_history["km2"], history)
        self.assertNotIn("km1", self.app.state.keymap_history)
        self.assertIs(self.app.state.keymap_indices["km2"], execution_indices)
        self.assertEqual(self.app.state.keymap_indices["km2"]["f1"], 2)
        self.assertNotIn("km1", self.app.state.keymap_indices)

    def test_drag_start_and_commit_both_check_active_execution(self):
        with patch.object(self.app.sequence_runner, "has_any_active_execution", return_value=True), \
             patch.object(self.app, "_set_flash_message") as flash:
            self.assertFalse(self.panel.can_start_keymap_drag())
        self.assertIn("実行中", flash.call_args.args[0])

        with patch.object(self.app.sequence_runner, "has_any_active_execution", side_effect=(False, True)):
            self.assertTrue(self.panel.can_start_keymap_drag())
            self.assertFalse(self.panel.on_keymap_list_move(0, 0, 1))
        self.assertEqual([item["id"] for item in self.app.data["keymaps"]], ["km1", "km2", "km3"])

    def test_refused_widget_drag_restores_range_and_active_underline(self):
        self.select(0, 1, active=0)
        self.app.update_idletasks()
        x, y, width, height = self.listbox.bbox(1)
        target_x, target_y, target_width, target_height = self.listbox.bbox(2)
        with patch.object(self.app.sequence_runner, "has_any_active_execution", side_effect=(False, True)):
            self.listbox.focus_force()
            self.listbox.event_generate(
                "<ButtonPress-1>", time=next_click_time(), x=x + width // 2, y=y + height // 2
            )
            self.listbox.event_generate(
                "<B1-Motion>", x=target_x + target_width // 2,
                y=target_y + target_height // 2, state=0x100,
            )
            self.listbox.event_generate(
                "<ButtonRelease-1>", x=target_x + target_width // 2,
                y=target_y + target_height // 2,
            )
            self.app.update()

        self.assertEqual([item["id"] for item in self.app.data["keymaps"]], ["km1", "km2", "km3"])
        self.assertEqual(tuple(self.listbox.curselection()), (0, 1))
        self.assertEqual(int(self.listbox.index("active")), 0)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km1")

    def test_refused_singleton_drag_restores_selection_and_active_underline(self):
        self.select(0, 0, active=0)
        self.app.update_idletasks()
        x, y, width, height = self.listbox.bbox(1)
        target_x, target_y, target_width, target_height = self.listbox.bbox(2)
        with patch.object(self.app.sequence_runner, "has_any_active_execution", side_effect=(False, True)):
            self.listbox.focus_force()
            self.listbox.event_generate(
                "<ButtonPress-1>", time=next_click_time(), x=x + width // 2, y=y + height // 2
            )
            self.listbox.event_generate(
                "<B1-Motion>", x=target_x + target_width // 2,
                y=target_y + target_height // 2, state=0x100,
            )
            self.listbox.event_generate(
                "<ButtonRelease-1>", x=target_x + target_width // 2,
                y=target_y + target_height // 2,
            )
            self.app.update()

        self.assertEqual([item["id"] for item in self.app.data["keymaps"]], ["km1", "km2", "km3"])
        self.assertEqual(tuple(self.listbox.curselection()), (1,))
        self.assertEqual(int(self.listbox.index("active")), 0)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km1")

    def test_shift_key_release_commits_active_row(self):
        self.listbox.focus_force()
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(0)
        self.listbox.selection_anchor(0)
        self.listbox.activate(0)
        self.listbox.event_generate("<KeyPress-Down>", state=0x1)
        self.listbox.event_generate("<KeyRelease-Down>", state=0x1)
        self.app.update()

        self.assertEqual(tuple(self.listbox.curselection()), (0, 1))
        self.assertEqual(int(self.listbox.index("active")), 1)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km2")

    def test_range_delete_confirms_count_and_rejects_active_range_as_a_whole(self):
        self.select(1, 2)
        with patch.object(edit_module.messagebox, "askyesno", return_value=True) as confirm:
            self.panel.delete_keymap()
        confirm.assert_called_once()
        self.assertIn("2", confirm.call_args.args[1])
        self.assertEqual([item["id"] for item in self.app.data["keymaps"]], ["km1"])

        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime())
        self.panel.refresh_keymap_list_ui()
        self.select(0, 1)
        before = list(self.app.data["keymaps"])
        with patch.object(self.app.state, "can_switch_keymap", return_value=False), \
             patch.object(edit_module.messagebox, "askyesno", return_value=True) as confirm, \
             patch.object(self.app, "_set_flash_message"):
            self.panel.delete_keymap()
        self.assertEqual(self.app.data["keymaps"], before)
        confirm.assert_not_called()

    def test_delete_cannot_remove_every_keymap(self):
        self.app.data["keymaps"] = self.app.data["keymaps"][:2]
        self.panel.refresh_keymap_list_ui()
        self.select(0, 1)
        before = list(self.app.data["keymaps"])
        with patch.object(edit_module.messagebox, "askyesno", return_value=True) as confirm, \
             patch.object(edit_module.messagebox, "showerror") as showerror:
            self.panel.delete_keymap()
        self.assertEqual(self.app.data["keymaps"], before)
        self.assertLessEqual(confirm.call_count, 1)
        confirm.assert_not_called()
        showerror.assert_called_once()

    def test_delete_moved_singleton_range_uses_band_not_active_keymap(self):
        self.assertTrue(self.panel.on_keymap_list_move(1, 1, 2))
        self.assertEqual(tuple(self.listbox.curselection()), (2,))
        self.assertEqual(int(self.listbox.index("active")), 0)
        with patch.object(edit_module.messagebox, "askyesno", return_value=True) as confirm, \
             patch.object(
                 self.app.sequence_runner,
                 "publish_call_view",
                 wraps=self.app.sequence_runner.publish_call_view,
             ) as publish_call_view:
            self.panel.delete_keymap()

        confirm.assert_called_once()
        publish_call_view.assert_called_once_with()
        self.assertEqual([item["id"] for item in self.app.data["keymaps"]], ["km1", "km3"])
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km1")

    def test_copy_paste_uses_one_batch_numbers_labels_and_detaches_lists(self):
        self.select(0, 1)
        original_rows = [item["triggers"] for item in self.app.data["keymaps"][:2]]
        self.assertEqual(self.panel.copy_keymaps(), "break")
        copied = self.app.list_clipboard.paste(CLIP_KEYMAPS)
        self.assertEqual(len(copied), 2)
        dialog_result = _DialogResult([
            {"key": "f10", "label": "Map (3)"},
            {"key": "f6", "label": "Map (4)"},
        ])
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog",
            return_value=dialog_result,
        ) as batch_dialog, patch.object(
            self.panel, "activate_keymap_by_id", wraps=self.panel.activate_keymap_by_id
        ) as activate:
            self.assertEqual(self.panel.paste_keymaps(), "break")

        batch_dialog.assert_called_once()
        self.assertEqual(
            [row[2] for row in batch_dialog.call_args.kwargs["rows"]],
            ["Map (3)", "Map (4)"],
        )
        self.assertEqual([row[0] for row in batch_dialog.call_args.kwargs["rows"]], ["貼り付け", "貼り付け"])
        pasted = self.app.data["keymaps"][3:]
        self.assertEqual([item["label"] for item in pasted], ["Map (3)", "Map (4)"])
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km1")
        activate.assert_not_called()
        self.assertEqual(tuple(self.listbox.curselection()), (3, 4))
        self.assertEqual(int(self.listbox.index("active")), 0)
        self.assertIsNot(pasted[0]["triggers"], copied[0]["triggers"])
        self.assertIsNot(pasted[0]["triggers"], original_rows[0])
        pasted[0]["triggers"][0]["label"] = "changed"
        self.assertEqual(copied[0]["triggers"][0]["label"], "Trigger")
        self.assertEqual(original_rows[0][0]["label"], "Trigger")
        for keymap in pasted:
            self.assertTrue(keymap[self.app.config_service.INTERNAL_KEYMAP_DIRTY])
            self.assertTrue(keymap["_trigger_set_dirty"])
            for row in keymap["triggers"]:
                self.assertTrue(row[self.app.config_service.INTERNAL_SEQUENCE_DIRTY])
        self.assertTrue(self.app.dirty_tracker.has_unsaved_changes())

    def test_single_keymap_actions_target_active_after_focus_leaves_range(self):
        self.select(0, 2, active=2)
        self.panel.on_keymap_list_select()
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km3")
        self.listbox.selection_clear(0, "end")
        self.app.focus_force()
        self.app.update()
        self.assertIsNot(self.app.focus_get(), self.listbox)

        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.KeymapEditDialog",
            return_value=_DialogResult(None),
        ) as edit_dialog:
            self.panel.edit_selected_keymap()
        self.assertEqual(edit_dialog.call_args.kwargs["initial_label"], "Other")
        self.assertEqual(edit_dialog.call_args.kwargs["initial_key"], "f9")

        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.simpledialog.askstring",
            return_value=None,
        ) as askstring:
            self.panel.rename_keymap_label()
        self.assertIn("km3", askstring.call_args.args[1])

        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.askyesno",
            return_value=False,
        ) as confirm:
            self.panel.delete_keymap()
        self.assertIn("Other", confirm.call_args.args[1])

        index, keymap = KeymapFileIo(self.app).selected_keymap_for_io()
        self.assertEqual(index, 2)
        self.assertEqual(keymap["id"], "km3")

    def test_paste_batch_cancel_keeps_all_keymaps_unchanged(self):
        self.select(0, 1)
        self.panel.copy_keymaps()
        before = copy.deepcopy(self.app.data)
        before_active = self.app.data["active_keymap_id"]
        self.app.dirty_tracker.set_dirty(False)
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog",
            return_value=_DialogResult(None),
        ) as batch_dialog, patch.object(
            self.panel, "activate_keymap_by_id", wraps=self.panel.activate_keymap_by_id
        ) as activate:
            self.panel.paste_keymaps()

        batch_dialog.assert_called_once()
        self.assertEqual(self.app.data, before)
        self.assertEqual(self.app.data["active_keymap_id"], before_active)
        self.assertFalse(self.app.dirty_tracker.has_unsaved_changes())
        activate.assert_not_called()

    def test_missing_switch_keys_and_pasted_maps_share_one_dialog(self):
        self.app.data["keymap_switch_keys"] = {}
        self.select(0, 1)
        self.panel.copy_keymaps()
        candidates = [
            {"key": "f6", "label": "Map"},
            {"key": "f7", "label": "Map (2)"},
            {"key": "f8", "label": "Other"},
            {"key": "f10", "label": "Map (3)"},
            {"key": "f5", "label": "Map (4)"},
        ]
        calls = []

        def make_dialog(*args, **kwargs):
            calls.append((args, kwargs))
            return _DialogResult(candidates)

        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog",
            side_effect=make_dialog,
        ) as batch_dialog:
            self.panel.paste_keymaps()

        batch_dialog.assert_called_once()
        self.assertEqual(len(calls[0][1]["rows"]), 5)
        self.assertEqual([row[2] for row in calls[0][1]["rows"]], [
            "Map", "Map (2)", "Other", "Map (3)", "Map (4)",
        ])
        self.assertEqual([row[0] for row in calls[0][1]["rows"]], [
            "既存", "既存", "既存", "貼り付け", "貼り付け",
        ])
        for index, keymap_id in enumerate(("km1", "km2", "km3")):
            self.assertEqual(
                self.app.keymap_service.find_switch_key_for_keymap(self.app.data, keymap_id),
                ("f6", "f7", "f8")[index],
            )
        self.assertEqual([item["label"] for item in self.app.data["keymaps"][3:]], ["Map (3)", "Map (4)"])
        self.assertEqual(self.app.data["active_keymap_id"], "km1")

    def test_paste_rejects_switch_key_matching_the_pasted_map_trigger(self):
        self.app.data["keymaps"][0]["triggers"][0]["key"] = "f5"
        self.select(0, 0)
        self.panel.copy_keymaps()
        # Keep f5 only in the duplicated candidate so validation must inspect the completed state.
        self.app.data["keymaps"][0]["triggers"][0]["key"] = "f1"
        dialogs = []

        def enter_conflict_then_correct(dialog):
            dialogs.append(dialog)
            dialog.key_vars[0].set("f5")
            dialog._ok()
            self.assertIsNone(dialog.result)
            self.assertTrue(dialog.winfo_exists())
            dialog.key_vars[0].set("f10")
            dialog._ok()

        with patch.object(KeymapSwitchBatchDialog, "wait_window", new=enter_conflict_then_correct), patch(
            "keyseq.presentation.dialogs.keymap_switch_batch_dialog.messagebox.showerror"
        ) as showerror:
            self.panel.paste_keymaps()

        self.assertEqual(len(dialogs), 1)
        showerror.assert_called_once()
        self.assertEqual(len(self.app.data["keymaps"]), 4)
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(
            self.app.data, self.app.data["keymaps"][-1]["id"]
        ), "f10")

    def test_empty_or_wrong_clipboard_kind_is_a_no_op(self):
        before = list(self.app.data["keymaps"])
        self.app.list_clipboard.copy("actions", [{"type": "text", "value": "x"}])
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_add_flow.KeymapSwitchBatchDialog"
        ) as batch_dialog:
            self.assertEqual(self.panel.paste_keymaps(), "break")
            self.app.list_clipboard.clear()
            self.assertEqual(self.panel.paste_keymaps(), "break")
        self.assertEqual(self.app.data["keymaps"], before)
        batch_dialog.assert_not_called()

    def test_clipboard_shortcuts_are_bound_to_keymap_list_in_both_cases(self):
        for sequence in ("<Control-c>", "<Control-C>", "<Control-v>", "<Control-V>"):
            self.assertTrue(self.listbox.bind(sequence))


if __name__ == "__main__":
    unittest.main()
