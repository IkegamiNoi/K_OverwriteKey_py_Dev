"""偽のモニタを使って枠編集窓の操作を確認する。"""
import copy
import tkinter as tk
from tkinter import ttk
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.application.screen_grid_session import MonitorInfo
from keyseq.domain.screen_grid import (
    DEFAULT_OPS, GRID_OPS, GridCell, GridRow, TopLayout, default_top_layout,
    set_cell_key, top_layout_to_json,
)
from keyseq.presentation.dialogs.grid_editor_window import GridEditorWindow


class GridEditorWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()
        cls.monitors = [
            MonitorInfo("primary", (0, 0, 100, 100), True),
            MonitorInfo("secondary", (100, 0, 200, 100), False),
        ]

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.root = self.__class__.root
        self.monitors = self.__class__.monitors

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
        editor.panel.sub_keys = values[:cols * int(editor.panel.rows_var.get())]
        for index, key in enumerate(editor.panel.sub_keys):
            editor.panel.sub_key_buttons[index].configure(text=key)

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

        editor.panel.buttons["段の追加"].invoke()
        self.assertEqual(len(editor.layout.rows), 4)
        editor.panel.buttons["列の追加"].invoke()
        self.assertEqual(len(editor.layout.rows[0].cells), 5)
        editor.panel.buttons["列の削除"].invoke()
        self.assertEqual(len(editor.layout.rows[0].cells), 4)
        editor.panel.buttons["段の削除"].invoke()
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

    @staticmethod
    def crosshair_centers(editor):
        """Return the crosshair lines and the centers where a horizontal and a vertical arm cross."""
        lines = editor.canvas.find_withtag("crosshair")
        horizontal, vertical = [], []
        for item in lines:
            x1, y1, x2, y2 = editor.canvas.coords(item)
            (horizontal if y1 == y2 else vertical).append((x1, y1, x2, y2))
        centers = {
            (int(vx1), int(hy1))
            for hx1, hy1, hx2, _hy2 in horizontal
            for vx1, vy1, _vx2, vy2 in vertical
            if hx1 <= vx1 <= hx2 and vy1 <= hy1 <= vy2
        }
        return lines, centers

    def assert_crosshair_centers(self, editor, cells):
        expected = {
            ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)
            for row_index, col_index in cells
            for rect, _key in [editor.cell_rects()[row_index][col_index]]
        }
        lines, centers = self.crosshair_centers(editor)
        self.assertEqual(centers, expected)
        self.assertEqual(len(lines), len(expected) * 2)

    def test_row_boundary_crosshairs_follow_related_cells_and_disappear_on_release(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        rows = editor.cell_rects()
        boundary = rows[0][0][0][3]
        related = {(row, col) for row in (0, 1) for col in range(len(rows[row]))}
        editor.on_press(SimpleNamespace(x=50, y=boundary))
        self.assertEqual(editor._drag, ("row", 0))
        self.assert_crosshair_centers(editor, related)
        labels = {
            editor.canvas.itemcget(item, "text")
            for item in editor.canvas.find_all()
            if editor.canvas.type(item) == "text"
        }
        related_keys = {rows[row][col][1] for row, col in related}
        other_keys = {key for row in rows for _rect, key in row} - related_keys
        self.assertTrue(related_keys.isdisjoint(labels))
        self.assertTrue(other_keys.issubset(labels))

        # 境界を動かさずに離すと、関係した枠の文字が戻る（動かすと文字が収まらない枠が出るため先に確かめる）。
        editor.on_release()
        labels = {
            editor.canvas.itemcget(item, "text")
            for item in editor.canvas.find_all()
            if editor.canvas.type(item) == "text"
        }
        self.assertTrue(related_keys.issubset(labels))

        editor.on_press(SimpleNamespace(x=50, y=boundary))
        editor.on_drag(SimpleNamespace(x=50, y=boundary + 11))
        self.assert_crosshair_centers(editor, related)
        editor.on_release()
        self.assertEqual(len(editor.canvas.find_withtag("crosshair")), 0)

    def test_cell_boundary_crosshairs_follow_moved_cells(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        rect = editor.cell_rects()[0][0][0]
        x, y = rect[2], (rect[1] + rect[3]) // 2
        related = {(0, 0), (0, 1)}
        editor.on_press(SimpleNamespace(x=x, y=y))
        self.assertEqual(editor._drag, ("cell", 0, 0))
        self.assert_crosshair_centers(editor, related)

        editor.on_drag(SimpleNamespace(x=x + 10, y=y))
        self.assert_crosshair_centers(editor, related)
        editor.on_release()
        self.assertEqual(len(editor.canvas.find_withtag("crosshair")), 0)

    def test_left_top_labels_remain_during_drag_and_cell_selection_has_no_crosshair(self):
        editor = self.open_editor(grid={"label_position": "top_left"})
        self.addCleanup(editor.destroy)
        rows = editor.cell_rects()
        editor.on_press(SimpleNamespace(x=50, y=rows[0][0][0][3]))
        labels = {
            editor.canvas.itemcget(item, "text")
            for item in editor.canvas.find_all()
            if editor.canvas.type(item) == "text"
        }
        self.assertTrue({key for row in rows for _rect, key in row}.issubset(labels))
        self.assertGreater(len(editor.canvas.find_withtag("crosshair")), 0)
        editor.on_release()

        rect = editor.cell_rects()[0][0][0]
        editor.on_press(SimpleNamespace(x=(rect[0] + rect[2]) // 2,
                                        y=(rect[1] + rect[3]) // 2))
        self.assertIsNone(editor._drag)
        self.assertEqual(len(editor.canvas.find_withtag("crosshair")), 0)

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

    def test_changing_subdivision_counts_rebuilds_key_buttons(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        editor.panel.rows_var.set("2")
        self.assertEqual(len(editor.panel.sub_key_buttons), 6)
        editor.panel.cols_var.set("4")
        self.assertEqual(len(editor.panel.sub_key_buttons), 8)

    def test_one_by_one_subdivision_keeps_existing_key_arrangement(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        editor.panel.rows_var.set("1")
        original_rows = editor.panel.sub_rows
        original_cols = editor.panel.sub_cols
        original_keys = list(editor.panel.sub_keys)
        original_buttons = list(editor.panel.sub_key_buttons)

        editor.panel.cols_var.set("1")

        self.assertEqual((editor.panel.sub_rows, editor.panel.sub_cols),
                         (original_rows, original_cols))
        self.assertEqual(editor.panel.sub_keys, original_keys)
        self.assertEqual(editor.panel.sub_key_buttons, original_buttons)
        with patch("keyseq.presentation.dialogs.grid_editor_window.messagebox.showerror") as showerror:
            editor.accept()
        showerror.assert_called_once()
        self.assertTrue(editor.winfo_exists())
        self.assertIsNone(editor.result)

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
        self.assertEqual(str(editor.panel.buttons["段の追加"].cget("state")), "normal")
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

    def test_label_position_check_redraws_and_is_saved_only_when_on(self):
        for initial, toggle, expected in ((None, True, "top_left"),
                                           ({"label_position": "top_left"}, False, "top_left"),
                                           ({"label_position": "top_left"}, True, "center")):
            with self.subTest(initial=initial, toggle=toggle):
                editor = self.open_editor(grid=initial)
                with patch("keyseq.presentation.dialogs.grid_editor_window.draw_cell_label") as draw:
                    if toggle:
                        editor.panel.label_position_check.invoke()
                    else:
                        editor.draw()
                self.assertEqual(editor.label_position, expected)
                self.assertTrue(draw.called)
                self.assertTrue(all(call.kwargs["position"] == expected for call in draw.call_args_list))
                editor.accept()
                if expected == "top_left":
                    self.assertEqual(editor.result["label_position"], expected)
                else:
                    self.assertNotIn("label_position", editor.result)

    def test_sub_buttons_capture_symbols_and_names_with_spaces_exclusively(self):
        editor = GridEditorWindow(
            self.root, grid=None, monitors=self.monitors, start_monitor_id="primary",
            reserved=set(), key_name_from_event=lambda event: event.name,
        )
        self.addCleanup(editor.destroy)
        for index, key in enumerate((".", "num 1")):
            editor.panel.sub_key_buttons[index].invoke()
            self.assertIsNone(editor.selected)
            self.assertEqual(editor.panel.sub_selected, index)
            self.assertEqual(editor.panel.sub_key_buttons[index].cget("relief"), tk.SUNKEN)
            editor.on_key(SimpleNamespace(name=key))
            self.assertEqual(editor.panel.sub_key_buttons[index].cget("text"), key)
        editor.on_key(SimpleNamespace(name="right shift"))
        self.assertEqual(editor.panel.sub_key_rows()[0][1], "num 1")
        editor.on_key(SimpleNamespace(name="esc"))
        self.assertIsNone(editor.panel.sub_selected)
        self.assertTrue(editor.winfo_exists())
        editor.panel.sub_key_buttons[0].invoke()
        self.select_cell(editor)
        self.assertIsNone(editor.panel.sub_selected)
        self.assertEqual(editor.selected, (0, 0))
        editor.accept()
        self.assertEqual(editor.result["sub"]["keys"][:2], [".", "num 1"])

    def test_sub_count_changes_replace_buttons_and_clear_sub_selection(self):
        from keyseq.domain.screen_grid import auto_fill_sub_keys

        editor = self.open_editor(reserved={"q"})
        self.addCleanup(editor.destroy)
        old_buttons = list(editor.panel.sub_key_buttons)
        old_buttons[0].invoke()
        editor.panel.rows_var.set("2")
        self.assertIsNone(editor.panel.sub_selected)
        self.assertEqual(len(editor.panel.sub_key_buttons), 6)
        self.assertTrue(all(not button.winfo_exists() for button in old_buttons))
        editor.panel.cols_var.set("4")
        self.assertEqual([button.cget("text") for button in editor.panel.sub_key_buttons],
                         list(auto_fill_sub_keys(2, 4, {"q"})))
        self.assertFalse(any(isinstance(child, tk.Entry)
                             for child in editor.panel.sub_keys_frame.winfo_children()))

    def test_count_spinbox_key_input_does_not_change_selected_grid_or_sub_key(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        top_key = editor.layout.rows[0].cells[0].key
        sub_key = editor.panel.sub_keys[0]
        for spinbox in editor.panel.count_spinboxes:
            spinbox.focus_force()
            spinbox.event_generate("<KeyPress>", keysym="x")
        self.assertEqual(editor.layout.rows[0].cells[0].key, top_key)
        self.assertEqual(editor.selected, (0, 0))
        editor.panel.sub_key_buttons[0].invoke()
        for spinbox in editor.panel.count_spinboxes:
            spinbox.focus_force()
            spinbox.event_generate("<KeyPress>", keysym="y")
        self.assertEqual(editor.panel.sub_keys[0], sub_key)

    def test_typing_sub_key_with_empty_column_count_uses_built_layout(self):
        editor = GridEditorWindow(
            self.root, grid=None, monitors=self.monitors, start_monitor_id="primary",
            reserved=set(), key_name_from_event=lambda event: event.name,
        )
        self.addCleanup(editor.destroy)
        editor.panel.sub_key_buttons[4].invoke()
        editor.panel.cols_var.set("")
        editor.on_key(SimpleNamespace(name="num 1"))
        self.assertEqual(editor.panel.sub_keys[4], "num 1")
        self.assertEqual(editor.panel.sub_key_buttons[4].cget("text"), "num 1")

    def test_switch_and_first_map_reapply_editor_then_panel_stacking(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        calls = []
        with patch.object(editor, "wm_attributes", side_effect=lambda *args: calls.append(("editor", args))), \
                patch.object(editor, "lift", side_effect=lambda: calls.append(("editor", "lift"))), \
                patch.object(editor.panel, "wm_attributes", side_effect=lambda *args: calls.append(("panel", args))), \
                patch.object(editor.panel, "lift", side_effect=lambda: calls.append(("panel", "lift"))), \
                patch.object(editor, "after_idle", side_effect=lambda callback: callback()):
            for action in (lambda: editor.switch_monitor("secondary"), editor._on_first_map):
                calls.clear()
                editor._first_map_seen = False
                action()
                self.assertEqual(calls, [("editor", ("-topmost", True)), ("editor", "lift"),
                                         ("panel", ("-topmost", True)), ("panel", "lift")])

    def test_subdivision_rows_require_column_count_and_accept_punctuation_keys(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        editor.panel.rows_var.set("2")
        editor.panel.cols_var.set("2")
        editor.panel.sub_keys = ["a", ",", "x"]
        for index, key in enumerate(editor.panel.sub_keys):
            editor.panel.sub_key_buttons[index].configure(text=key)
        with patch("keyseq.presentation.dialogs.grid_editor_window.messagebox.showerror") as showerror:
            editor.accept()
        self.assertIn("細分化・段 2: キーは 2 個にしてください", showerror.call_args.args[1])
        self.assertTrue(editor.winfo_exists())
        editor.panel.sub_keys = ["a", ",", "/", "."]
        for index, key in enumerate(editor.panel.sub_keys):
            editor.panel.sub_key_buttons[index].configure(text=key)
        editor.accept()
        self.assertEqual(editor.result["sub"]["keys"], ["a", ",", "/", "."])


    def test_operation_buttons_show_default_and_customized_grid_values(self):
        editor = self.open_editor()
        self.assertEqual(tuple(editor.panel.op_key_buttons), GRID_OPS)
        self.assertEqual(
            {name: button.cget("text") for name, button in editor.panel.op_key_buttons.items()},
            dict(DEFAULT_OPS),
        )

        custom = {name: f"f{index + 1}" for index, name in enumerate(GRID_OPS)}
        editor.destroy()
        editor = self.open_editor(grid={"ops": custom})
        self.addCleanup(editor.destroy)
        self.assertEqual(
            {name: button.cget("text") for name, button in editor.panel.op_key_buttons.items()},
            custom,
        )

    def test_operation_key_selection_is_exclusive_and_kept_after_typing(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        original_top_key = editor.layout.rows[0].cells[0].key
        editor.panel.op_key_buttons["deepen"].invoke()
        self.assertIsNone(editor.selected)
        self.assertIsNone(editor.panel.sub_selected)
        self.assertEqual(editor.panel.op_selected, "deepen")
        editor.on_key(SimpleNamespace(keysym="g", char="g", state=0))
        self.assertEqual(editor.ops["deepen"], "g")
        self.assertEqual(editor.panel.op_key_buttons["deepen"].cget("text"), "g")
        self.assertEqual(editor.panel.op_selected, "deepen")
        self.assertEqual(editor.layout.rows[0].cells[0].key, original_top_key)

        editor.panel.sub_key_buttons[0].invoke()
        self.assertIsNone(editor.panel.op_selected)
        self.assertIsNone(editor.selected)
        editor.panel.op_key_buttons["back"].invoke()
        self.assertIsNone(editor.panel.sub_selected)
        self.select_cell(editor)
        self.assertIsNone(editor.panel.op_selected)
        self.assertIsNone(editor.panel.sub_selected)
        self.assertIsNotNone(editor.selected)

    def test_escape_clears_operation_selection_before_closing(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        editor.panel.op_key_buttons["deepen"].invoke()

        editor.on_escape()

        self.assertIsNone(editor.panel.op_selected)
        self.assertTrue(editor.winfo_exists())
        self.assertIsNone(editor.result)

    def test_reset_operation_keys_restores_defaults_and_result_omits_defaults(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        editor.ops["deepen"] = "g"
        editor.panel.update_op_buttons()
        editor.panel.op_key_buttons["deepen"].invoke()
        reset = next(child for child in editor.panel.ops_frame.winfo_children()
                     if isinstance(child, ttk.Button) and child.cget("text") == "操作キーを既定に戻す")
        reset.invoke()
        self.assertEqual(editor.ops, dict(DEFAULT_OPS))
        self.assertIsNone(editor.panel.op_selected)
        editor.accept()
        self.assertNotIn("ops", editor.result)

    def test_accept_saves_custom_operations_and_rejects_conflicts(self):
        custom = {name: f"f{index + 1}" for index, name in enumerate(GRID_OPS)}
        editor = self.open_editor()
        editor.ops = dict(custom)
        editor.accept()
        self.assertEqual(editor.result["ops"], custom)

        cases = (
            ("duplicate", "deepen", "f2", {"ops": custom}, set()),
            ("reserved", "deepen", "f9", None, {"f9"}),
            ("fixed esc", "deepen", "esc", None, set()),
            ("fixed num enter", "click", "num enter", None, set()),
            ("current frame", "deepen", "t", {"monitors": {"primary": top_layout_to_json(
                TopLayout((GridRow(1.0, (GridCell(1.0, "t"),)),)))}}, set()),
            ("default frame", "deepen", "r", {"monitors": {
                "primary": top_layout_to_json(TopLayout((GridRow(1.0, (GridCell(1.0, "g"),)),))),
                "secondary": top_layout_to_json(TopLayout((GridRow(1.0, (GridCell(1.0, "h"),)),))),
            }}, set()),
            ("subdivision", "deepen", "m", {"sub": {"rows": 2, "cols": 2,
                "keys": ["m", "n", "b", "v"]}}, set()),
        )
        for reason, operation, key, initial, reserved in cases:
            with self.subTest(reason=reason):
                editor = self.open_editor(grid=initial, reserved=reserved)
                editor.ops[operation] = key
                with patch("keyseq.presentation.dialogs.grid_editor_window.messagebox.showerror") as showerror:
                    editor.accept()
                showerror.assert_called_once()
                self.assertTrue(editor.winfo_exists())
                self.assertIsNone(editor.result)
                editor.destroy()

        editor = self.open_editor()
        editor.ops["deepen"] = "h"
        editor._replace(set_cell_key(editor.layout, 0, 0, "h"))
        with patch("keyseq.presentation.dialogs.grid_editor_window.messagebox.showerror") as showerror:
            editor.accept()
        showerror.assert_called_once()
        self.assertTrue(editor.winfo_exists())
        editor.destroy()

    def test_split_and_refill_skip_custom_operation_keys_and_default_key_can_be_used(self):
        editor = self.open_editor()
        self.addCleanup(editor.destroy)
        editor.ops["deepen"] = "t"
        editor.selected = (0, 0)
        editor.add_cell()
        self.assertNotIn("t", [cell.key for row in editor.layout.rows for cell in row.cells])
        editor.reassign()
        self.assertNotIn("t", [cell.key for row in editor.layout.rows for cell in row.cells])

        editor.panel.op_key_buttons["deepen"].invoke()
        editor.panel.rows_var.set("2")
        self.assertIsNone(editor.panel.op_selected)
        self.assertNotIn("t", editor.panel.sub_keys)
        editor.panel.op_key_buttons["deepen"].invoke()
        editor.switch_monitor("secondary")
        self.assertIsNone(editor.panel.op_selected)
        editor.panel.op_key_buttons["deepen"].invoke()
        editor.reset_monitor()
        self.assertIsNone(editor.panel.op_selected)
        editor.ops["deepen"] = "g"
        editor._replace(set_cell_key(editor.layout, 0, 0, "space"))
        editor.accept()
        self.assertEqual(editor.result["monitors"]["secondary"]["rows"][0]["cells"][0]["key"], "space")


if __name__ == "__main__":
    unittest.main()
