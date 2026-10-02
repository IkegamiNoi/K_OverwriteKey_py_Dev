"""プリセット編集内での範囲操作と、確定・破棄の UI 契約。"""

import copy
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.dialogs.preset_manager import PresetManagerDialog
from keyseq.presentation.listbox_range_drag import select_range


class PresetManagerRangeDragTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(StartupIo, "load_startup_and_config"):
            cls.app = App()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.original_data = self.app.data
        self.presets = [
            {"label": f"Preset {i}", "value": f"ctrl+{i}"}
            for i in range(1, 6)
        ]
        self.app.data = {
            **self.original_data,
            "hotkey_presets": copy.deepcopy(self.presets),
            "hotkey_presets_individual": True,
        }
        self.dialog = PresetManagerDialog(self.app)
        self.app.update()
        self.listbox = self.dialog.listbox
        self.addCleanup(self._restore)

    def _restore(self):
        if self.dialog.winfo_exists():
            self.dialog.destroy()
        self.app.update()
        self.app.data = self.original_data

    def _xy(self, row):
        self.app.update_idletasks()
        x, y, width, height = self.listbox.bbox(row)
        return x + width // 2, y + height // 2

    def _event(self, sequence, row, state=0):
        x, y = self._xy(row)
        self.listbox.event_generate(sequence, x=x, y=y, state=state)
        self.app.update_idletasks()

    def _start_drag(self, start, end, target):
        select_range(self.listbox, start, end)
        self.listbox.focus_force()
        self._event("<ButtonPress-1>", start)
        self._event("<B1-Motion>", target, 0x100)

    def _finish_drag(self, target):
        self._event("<ButtonRelease-1>", target)
        self.app.update()

    def test_range_drag_only_changes_working_list_until_ok(self):
        self._start_drag(1, 2, 3)
        self.assertEqual(self.dialog._temp, self.presets)
        self.assertEqual(self.app.data["hotkey_presets"], self.presets)
        self._finish_drag(3)
        expected = [self.presets[i] for i in (0, 3, 4, 1, 2)]
        self.assertEqual(self.dialog._temp, expected)
        self.assertEqual(tuple(self.listbox.curselection()), (3, 4))
        self.assertEqual(self.app.data["hotkey_presets"], self.presets)
        with patch.object(self.app, "save_hotkey_presets", return_value=True) as save:
            self.dialog.on_ok()
        save.assert_called_once()
        self.assertEqual(save.call_args.args, (expected,))
        self.assertEqual(save.call_args.kwargs["loaded_presets"], self.presets)
        self.assertTrue(save.call_args.kwargs["individual"])
        self.assertFalse(self.dialog.winfo_exists())

    def test_cancel_discards_range_drag(self):
        self._start_drag(1, 2, 3)
        self._finish_drag(3)
        with patch.object(self.app, "save_hotkey_presets") as save:
            self.dialog.destroy()
        save.assert_not_called()
        self.assertEqual(self.app.data["hotkey_presets"], self.presets)

    def test_ok_commits_range_changes_to_runtime(self):
        select_range(self.listbox, 1, 2)
        self.dialog.move(1)
        expected = copy.deepcopy(self.dialog._temp)
        service = self.app.config_service
        with patch.object(service, "resolve_hotkey_presets_save_path", return_value=""), \
                patch.object(service, "individual_hotkey_presets_save_rejection_reason",
                             return_value=None), \
                patch.object(service, "describe_individual_hotkey_presets_overwrite",
                             return_value={"conflict": False}), \
                patch.object(self.app.hotkey_presets_io, "write_presets",
                             return_value=True) as write:
            self.dialog.on_ok()
        write.assert_called_once_with(expected, stored_path="")
        self.assertEqual(self.app.data["hotkey_presets"], expected)
        self.assertIsNot(self.app.data["hotkey_presets"], self.dialog._temp)
        self.assertFalse(self.dialog.winfo_exists())

    def test_up_down_move_whole_range_and_stop_at_edges(self):
        select_range(self.listbox, 1, 3)
        self.dialog.move(-1)
        expected = [self.presets[i] for i in (1, 2, 3, 0, 4)]
        self.assertEqual(self.dialog._temp, expected)
        self.assertEqual(tuple(self.listbox.curselection()), (0, 1, 2))
        self.dialog.move(-1)
        self.assertEqual(self.dialog._temp, expected)
        self.dialog.move(1)
        self.dialog.move(1)
        expected = [self.presets[i] for i in (0, 4, 1, 2, 3)]
        self.assertEqual(self.dialog._temp, expected)
        self.assertEqual(tuple(self.listbox.curselection()), (2, 3, 4))
        self.dialog.move(1)
        self.assertEqual(self.dialog._temp, expected)

    def test_delete_range_confirms_once_with_count(self):
        select_range(self.listbox, 1, 3)
        with patch("keyseq.presentation.dialogs.preset_manager.messagebox.askyesno",
                   return_value=True) as confirm:
            self.dialog.delete()
        confirm.assert_called_once_with("確認", "選択した 3 件のプリセットを削除しますか？")
        self.assertEqual(self.dialog._temp, [self.presets[0], self.presets[4]])
        self.assertEqual(self.app.data["hotkey_presets"], self.presets)

    def test_delete_single_keeps_prompt_and_declined_delete_keeps_range(self):
        select_range(self.listbox, 2, 2)
        with patch("keyseq.presentation.dialogs.preset_manager.messagebox.askyesno",
                   return_value=False) as confirm:
            self.dialog.delete()
        confirm.assert_called_once_with("確認", "選択したプリセットを削除しますか？")
        self.assertEqual(self.dialog._temp, self.presets)
        self.assertEqual(tuple(self.listbox.curselection()), (2,))

    def test_edit_uses_active_row_and_preserves_range(self):
        select_range(self.listbox, 1, 3, active=2)
        editor = Mock(result={"label": "Changed", "value": "ctrl+9"})
        with patch("keyseq.presentation.dialogs.preset_manager.PresetDialog",
                   return_value=editor) as factory, patch.object(
                       self.app, "validate_hotkey", return_value=(None, "ctrl+9")):
            self.dialog.edit()
        self.assertEqual(factory.call_args.kwargs["initial_label"], "Preset 3")
        self.assertEqual(self.dialog._temp[2]["label"], "Changed")
        self.assertEqual(tuple(self.listbox.curselection()), (1, 2, 3))
        self.assertEqual(int(self.listbox.index(tk.ACTIVE)), 2)

    def test_edit_immediately_after_add_targets_the_added_row(self):
        add_dialog = Mock(result={"label": "Added", "value": "ctrl+9"})
        edit_dialog = Mock(result={"label": "Edited", "value": "ctrl+0"})
        with patch("keyseq.presentation.dialogs.preset_manager.PresetDialog",
                   side_effect=[add_dialog, edit_dialog]) as factory, patch.object(
                       self.app,
                       "validate_hotkey",
                       side_effect=[(None, "ctrl+9"), (None, "ctrl+0")],
                   ):
            self.dialog.add()
            self.dialog.edit()

        self.assertEqual(factory.call_args_list[1].kwargs["initial_label"], "Added")
        self.assertEqual(self.dialog._temp[-1]["label"], "Edited")

    def test_double_click_edits_active_row_only(self):
        select_range(self.listbox, 1, 3, active=3)
        editor = Mock(result=None)
        with patch("keyseq.presentation.dialogs.preset_manager.PresetDialog",
                   return_value=editor) as factory:
            self.assertEqual(self.dialog._on_double_click(), "break")
        self.assertEqual(factory.call_args.kwargs["initial_label"], "Preset 4")
        self.assertEqual(self.dialog._temp, self.presets)

    def test_escape_cancels_drag_without_closing_then_idle_escape_closes(self):
        before = self.listbox.get(0, tk.END)
        self._start_drag(1, 2, 3)
        self.listbox.event_generate("<Escape>")
        self.app.update()
        self.assertTrue(self.dialog.winfo_exists())
        self.assertEqual(self.listbox.get(0, tk.END), before)
        self.assertEqual(tuple(self.listbox.curselection()), (1, 2))
        self._finish_drag(3)
        self.assertEqual(self.dialog._temp, self.presets)
        self.listbox.event_generate("<Escape>")
        self.app.update()
        self.assertFalse(self.dialog.winfo_exists())

    def test_no_selection_keeps_existing_guidance(self):
        self.listbox.selection_clear(0, tk.END)
        with patch("keyseq.presentation.dialogs.preset_manager.messagebox.showinfo") as info:
            self.dialog.move(1)
            self.dialog.delete()
            self.dialog.edit()
        self.assertEqual([call.args for call in info.call_args_list], [
            ("移動", "移動したい行を選択してください。"),
            ("削除", "削除したい行を選択してください。"),
            ("編集", "編集したい行を選択してください。"),
        ])
        self.assertEqual(self.dialog._temp, self.presets)


if __name__ == "__main__":
    unittest.main()
