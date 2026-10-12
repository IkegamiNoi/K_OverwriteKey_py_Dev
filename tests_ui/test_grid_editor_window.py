"""偽のモニタを使って枠編集窓の操作を確認する。"""
import copy
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.application.screen_grid_session import MonitorInfo
from keyseq.domain.screen_grid import default_top_layout, set_cell_key, top_layout_to_json
from keyseq.presentation.dialogs.grid_editor_window import GridEditorWindow


class GridEditorWindowTest(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.monitors = [
            MonitorInfo("primary", (0, 0, 100, 100), True),
            MonitorInfo("secondary", (100, 0, 200, 100), False),
        ]

    def open_editor(self, *, grid=None, start="primary", reserved=None):
        return GridEditorWindow(
            self.root, grid=grid, monitors=self.monitors,
            start_monitor_id=start, reserved=set() if reserved is None else reserved,
        )

    @staticmethod
    def select_cell(editor, row=0, col=0):
        rect = editor.cell_rects()[row][col][0]
        editor.on_press(SimpleNamespace(
            x=(rect[0] + rect[2]) // 2, y=(rect[1] + rect[3]) // 2,
        ))

    @staticmethod
    def set_sub_keys(editor, keys):
        values = keys.split()
        cols = int(editor.panel.cols_var.get())
        for row, variable in enumerate(editor.panel.sub_key_vars):
            variable.set(" ".join(values[row * cols:(row + 1) * cols]))

    def test_opens_on_start_monitor_and_switches_between_two_monitors(self):
        editor = self.open_editor(start="secondary")
        self.addCleanup(editor.destroy)
        self.assertEqual(editor.monitor.id, "secondary")
        self.assertEqual(editor.panel.monitor_combo.current(), 1)

        editor.panel.monitor_combo.current(0)
        editor.panel.monitor_combo.event_generate("<<ComboboxSelected>>")
        self.root.update()
        self.assertEqual(editor.monitor.id, "primary")
        self.assertEqual(editor.panel.monitor_combo.current(), 0)

    def test_selecting_cell_and_typing_assigns_its_key(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        self.select_cell(editor, 1, 2)
        self.assertEqual(editor.selected, (1, 2))

        editor.on_key(SimpleNamespace(keysym="y", char="y", state=0))
        self.assertEqual(editor.layout.rows[1].cells[2].key, "y")

    def test_escape_clears_selection_first_and_cancels_when_unselected(self):
        editor = self.open_editor()
        self.select_cell(editor)
        editor.on_escape()
        self.assertIsNone(editor.selected)
        self.assertTrue(editor.winfo_exists())
        self.assertIsNone(editor.result)

        editor.on_escape()
        self.root.update_idletasks()
        self.assertFalse(editor.winfo_exists())
        self.assertIsNone(editor.result)

    def test_panel_buttons_split_and_delete_selected_row_and_cell(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        self.select_cell(editor)

        editor.panel.buttons["行の追加"].invoke()
        self.assertEqual(len(editor.layout.rows), 4)
        editor.panel.buttons["列の追加"].invoke()
        self.assertEqual(len(editor.layout.rows[0].cells), 5)
        editor.panel.buttons["列の削除"].invoke()
        self.assertEqual(len(editor.layout.rows[0].cells), 4)
        editor.panel.buttons["行の削除"].invoke()
        self.assertEqual(len(editor.layout.rows), 3)

    def test_row_and_cell_boundaries_move_by_drag(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        original_rows = tuple(row.h for row in editor.layout.rows)
        editor.on_press(SimpleNamespace(x=50, y=33))
        self.assertEqual(editor._drag, ("row", 0))
        editor.on_drag(SimpleNamespace(x=50, y=44))
        self.assertNotEqual(tuple(row.h for row in editor.layout.rows), original_rows)
        editor.on_release()

        original_widths = tuple(cell.w for cell in editor.layout.rows[0].cells)
        editor.on_press(SimpleNamespace(x=25, y=10))
        self.assertEqual(editor._drag, ("cell", 0, 0))
        editor.on_drag(SimpleNamespace(x=34, y=10))
        self.assertNotEqual(tuple(cell.w for cell in editor.layout.rows[0].cells), original_widths)
        editor.on_release()

    def test_switching_and_accepting_records_edited_monitor_only(self):
        original = {
            "monitors": {"primary": top_layout_to_json(default_top_layout())},
            "sub": {"rows": 2, "cols": 2, "keys": ["q", "w", "a", "s"]},
        }
        editor = self.open_editor(grid=original)
        editor.panel.monitor_combo.current(1)
        editor.panel.monitor_combo.event_generate("<<ComboboxSelected>>")
        self.root.update()
        self.assertEqual(editor.monitor.id, "secondary")
        self.select_cell(editor)
        editor.on_key(SimpleNamespace(keysym="y", char="y", state=0))
        editor.accept()

        self.assertIn("primary", editor.result["monitors"])
        self.assertEqual(editor.result["monitors"]["primary"], original["monitors"]["primary"])
        self.assertIn("secondary", editor.result["monitors"])
        self.assertEqual(editor.result["monitors"]["secondary"]["rows"][0]["cells"][0]["key"], "y")

    def test_reset_removes_monitor_record_and_accept_keeps_it_removed(self):
        grid = {"monitors": {
            "primary": top_layout_to_json(default_top_layout()),
            "secondary": top_layout_to_json(default_top_layout()),
        }}
        editor = self.open_editor(grid=grid, start="secondary")
        editor.reset_monitor()
        self.assertNotIn("secondary", editor._records)
        editor.accept()
        self.assertNotIn("secondary", editor.result["monitors"])
        self.assertIn("primary", editor.result["monitors"])

    def test_unedited_monitor_is_not_added_to_records(self):
        editor = self.open_editor(start="secondary")
        editor.accept()
        self.assertNotIn("secondary", editor.result["monitors"])

    def test_changing_subdivision_counts_rebuilds_one_key_entry_per_row(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        editor.panel.sub_key_vars[0].set("invalid")
        editor.panel.rows_var.set("2")
        self.assertEqual(len(editor.panel.sub_key_vars), 2)
        self.assertEqual(sum(len(var.get().split()) for var in editor.panel.sub_key_vars), 6)
        editor.panel.cols_var.set("4")
        self.assertEqual(len(editor.panel.sub_key_vars), 2)
        self.assertEqual(sum(len(var.get().split()) for var in editor.panel.sub_key_vars), 8)
        self.assertNotIn("invalid", " ".join(var.get() for var in editor.panel.sub_key_vars))

    def test_ok_rejects_reserved_and_duplicate_sub_keys_without_closing(self):
        cases = (("f9 w a s", {"f9"}), ("q q a s", set()))
        for keys, reserved in cases:
            with self.subTest(keys=keys):
                editor = self.open_editor(reserved=reserved)
                editor.panel.rows_var.set("2")
                editor.panel.cols_var.set("2")
                self.set_sub_keys(editor, keys)
                with patch(
                    "keyseq.presentation.dialogs.grid_editor_window.messagebox.showerror"
                ) as showerror:
                    editor.accept()
                showerror.assert_called_once()
                self.assertTrue(editor.winfo_exists())
                self.assertIsNone(editor.result)
                editor.destroy()

    def test_ok_rejects_reserved_and_duplicate_top_keys_with_monitor_id(self):
        cases = (("reserved", {"y"}), ("duplicate", set()))
        for failure, reserved in cases:
            with self.subTest(failure=failure):
                editor = self.open_editor(reserved=reserved)
                key = "y" if failure == "reserved" else "a"
                editor._replace(set_cell_key(editor.layout, 0, 0, key))
                with patch(
                    "keyseq.presentation.dialogs.grid_editor_window.messagebox.showerror"
                ) as showerror:
                    editor.accept()
                showerror.assert_called_once()
                self.assertIn("primary", showerror.call_args.args[1])
                self.assertTrue(editor.winfo_exists())
                editor.destroy()

    def test_ok_rejects_empty_top_key_without_closing(self):
        editor = self.open_editor()
        editor._replace(set_cell_key(editor.layout, 0, 0, ""))
        with patch(
            "keyseq.presentation.dialogs.grid_editor_window.messagebox.showerror"
        ) as showerror:
            editor.accept()
        showerror.assert_called_once()
        self.assertTrue(editor.winfo_exists())
        self.assertIsNone(editor.result)
        editor.destroy()

    def test_initial_grid_is_deep_copied_until_accept(self):
        grid = {
            "monitors": {"primary": top_layout_to_json(default_top_layout())},
            "sub": {"rows": 2, "cols": 2, "keys": ["q", "w", "a", "s"]},
        }
        original = copy.deepcopy(grid)
        editor = self.open_editor(grid=grid)
        self.select_cell(editor)
        editor.on_key(SimpleNamespace(keysym="y", char="y", state=0))
        self.set_sub_keys(editor, "z x c v")

        self.assertEqual(grid, original)
        editor.destroy()

    def test_key_event_resolver_is_used_for_grid_keys(self):
        editor = GridEditorWindow(
            self.root, grid=None, monitors=self.monitors, start_monitor_id="primary",
            reserved=set(), key_name_from_event=lambda _event: ".",
        )
        self.addCleanup(editor.destroy)
        editor.on_key(SimpleNamespace(keysym="period", keycode=190, state=0))
        self.assertEqual(editor.layout.rows[0].cells[0].key, ".")

    def test_boundary_cursor_changes_for_row_and_cell_boundaries(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        editor.on_motion(SimpleNamespace(x=50, y=33))
        self.assertEqual(editor.canvas.cget("cursor"), "sb_v_double_arrow")
        editor.on_motion(SimpleNamespace(x=25, y=10))
        self.assertEqual(editor.canvas.cget("cursor"), "sb_h_double_arrow")
        editor.on_motion(SimpleNamespace(x=5, y=5))
        self.assertEqual(editor.canvas.cget("cursor"), "")

    def test_editor_starts_with_top_left_cell_selected(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        self.assertEqual(editor.selected, (0, 0))
        self.assertEqual(str(editor.panel.buttons["行の追加"].cget("state")), "normal")
        self.assertIn("キーを押す", editor.panel.hint.cget("text"))

    def test_first_map_reapplies_monitor_geometry_once(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        with patch.object(editor, "after_idle", side_effect=lambda callback: callback()), patch.object(
            editor, "switch_monitor", wraps=editor.switch_monitor
        ) as switch_monitor, patch.object(editor, "attributes", wraps=editor.attributes) as attributes:
            editor._first_map_seen = False
            editor._on_first_map()
            editor._on_first_map()
        switch_monitor.assert_called_once_with("primary")
        attributes.assert_called_once_with("-alpha", 0.5)

    def test_subdivision_rows_require_column_count_and_accept_punctuation_keys(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        editor.panel.rows_var.set("2")
        editor.panel.cols_var.set("2")
        editor.panel.sub_key_vars[0].set("a ,")
        editor.panel.sub_key_vars[1].set("x")
        with patch("keyseq.presentation.dialogs.grid_editor_window.messagebox.showerror") as showerror:
            editor.accept()
        self.assertIn("細分化・行 2: キーは 2 個にしてください", showerror.call_args.args[1])
        self.assertTrue(editor.winfo_exists())
        editor.panel.sub_key_vars[1].set("/ .")
        editor.accept()
        self.assertEqual(editor.result["sub"]["keys"], ["a", ",", "/", "."])


if __name__ == "__main__":
    unittest.main()
