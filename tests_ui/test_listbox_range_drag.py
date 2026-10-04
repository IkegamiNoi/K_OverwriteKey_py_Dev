"""UI coverage for the Listbox range selection and reorder helper."""

import tkinter as tk
import unittest
from unittest.mock import Mock

from keyseq.presentation.listbox_range_drag import bind_listbox_range_drag
from keyseq.presentation.listbox_utils import listbox_mouse_button_is_down


class ListboxRangeDragTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.geometry("320x240")

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.box = tk.Listbox(self.root, height=8)
        self.box.pack(fill="both", expand=True)
        self.items = [f"row {i}" for i in range(8)]
        for item in self.items:
            self.box.insert(tk.END, item)
        self.moves = []
        self.commits = []
        self.on_move = Mock(side_effect=lambda *args: self.moves.append(args) or True)
        self.controller = bind_listbox_range_drag(
            self.box, on_move=self.on_move, on_commit=lambda box: self.commits.append(box)
        )
        self.root.update()

    def tearDown(self):
        self.box.destroy()
        self.root.update_idletasks()

    def _xy(self, row):
        self.root.update_idletasks()
        x, y, width, height = self.box.bbox(row)
        return x + width // 2, y + height // 2

    def _press(self, row, *, state=0):
        x, y = self._xy(row)
        self.box.focus_force()
        self.box.event_generate("<ButtonPress-1>", x=x, y=y, state=state)
        self.root.update_idletasks()
        return x, y

    def _motion(self, row, *, shift=False):
        x, y = self._xy(row)
        self.box.event_generate("<B1-Motion>", x=x, y=y, state=0x100 | (0x1 if shift else 0))
        self.root.update_idletasks()

    def _release(self, row, *, state=0):
        x, y = self._xy(row)
        self.box.event_generate("<ButtonRelease-1>", x=x, y=y, state=state)
        self.root.update()

    def _click(self, row, *, state=0):
        self._press(row, state=state)
        self._release(row, state=state)

    def test_shift_click_and_shift_drag_select_contiguous_ranges(self):
        self._click(1)
        self._click(4, state=0x1)
        self.assertEqual(tuple(self.box.curselection()), (1, 2, 3, 4))
        self.assertEqual(int(self.box.index(tk.ACTIVE)), 4)

        x, y = self._xy(2)
        self.box.event_generate("<ButtonPress-1>", x=x, y=y, state=0x1)
        self.box.event_generate("<B1-Motion>", x=x, y=self._xy(6)[1], state=0x101)
        self._release(6, state=0x1)
        self.assertEqual(tuple(self.box.curselection()), (1, 2, 3, 4, 5, 6))
        self.assertEqual(self.moves, [])
        self.assertGreaterEqual(len(self.commits), 2)

    def test_shift_arrows_extend_from_anchor_and_commit_after_idle(self):
        self._click(2)
        before = len(self.commits)
        self.box.event_generate("<KeyPress-Down>", state=0x1)
        self.root.update()
        self.assertEqual(tuple(self.box.curselection()), (2, 3))
        self.assertEqual(int(self.box.index(tk.ACTIVE)), 3)
        self.assertEqual(len(self.commits), before + 1)
        self.box.event_generate("<KeyPress-Up>", state=0x1)
        self.root.update()
        self.assertEqual(tuple(self.box.curselection()), (2,))

    def test_control_click_does_not_make_a_disjoint_selection(self):
        self._click(1)
        self._click(5, state=0x4)
        self.assertEqual(tuple(self.box.curselection()), (5,))

    def test_plain_arrow_selects_one_row_and_updates_anchor_without_commit(self):
        self._click(1)
        self._click(3, state=0x1)
        self.commits.clear()
        self.box.event_generate("<KeyPress-Down>")
        self.root.update()
        self.assertEqual(tuple(self.box.curselection()), (4,))
        self.assertEqual(int(self.box.index(tk.ANCHOR)), 4)
        self.assertEqual(self.commits, [])
        self.box.event_generate("<KeyPress-Up>", state=0x1)
        self.root.update()
        self.assertEqual(tuple(self.box.curselection()), (3, 4))

    def test_blocked_selection_keys_leave_range_and_active_unchanged(self):
        self._click(1)
        self._click(3, state=0x1)
        self.commits.clear()
        for keysym, state in (("slash", 0x4), ("backslash", 0x4),
                              ("Home", 0x5), ("End", 0x5),
                              ("Home", 0x1), ("End", 0x1)):
            with self.subTest(keysym=keysym, state=state):
                self.box.event_generate("<KeyPress>", keysym=keysym, state=state)
                self.root.update()
                self.assertEqual(tuple(self.box.curselection()), (1, 2, 3))
                self.assertEqual(int(self.box.index(tk.ACTIVE)), 3)
        self.assertEqual(self.commits, [])

    def test_shift_arrow_at_edge_does_not_move_and_commits_after_idle(self):
        self._click(0)
        self.commits.clear()
        self.box.event_generate("<KeyPress-Up>", state=0x1)
        self.assertEqual(self.commits, [])
        self.root.update_idletasks()
        self.assertEqual(tuple(self.box.curselection()), (0,))
        self.assertEqual(int(self.box.index(tk.ACTIVE)), 0)
        self.assertEqual(len(self.commits), 1)

    def test_press_inside_range_keeps_preview_then_release_collapses(self):
        self._click(1)
        self._click(4, state=0x1)
        self._press(3)
        self.assertEqual(tuple(self.box.curselection()), (1, 2, 3, 4))
        self._release(3)
        self.assertEqual(tuple(self.box.curselection()), (3,))

    def test_selection_commit_waits_for_release(self):
        self._press(2)
        self.assertEqual(self.commits, [])
        self._release(2)
        self.assertEqual(len(self.commits), 1)

    def test_single_row_drag_previews_without_changing_caller_data(self):
        before = list(self.items)
        self.box.itemconfigure(1, background="#123456", foreground="#abcdef",
                               selectbackground="#234567", selectforeground="#fedcba")
        self._press(1)
        self.assertTrue(listbox_mouse_button_is_down(self.box))
        self._motion(5)
        self.assertEqual(
            self.box.get(0, tk.END),
            ("row 0", "row 2", "row 3", "row 4", "row 5", "row 1", "row 6", "row 7"),
        )
        self.assertEqual(self.box.itemcget(5, "background"), "#123456")
        self.assertEqual(self.box.itemcget(5, "foreground"), "#abcdef")
        self.assertEqual(self.box.itemcget(5, "selectbackground"), "#234567")
        self.assertEqual(self.box.itemcget(5, "selectforeground"), "#fedcba")
        self.assertEqual(self.items, before)
        self.assertEqual(self.moves, [])
        self._release(5)
        self.assertEqual(self.moves, [(1, 1, 5)])
        self.assertFalse(listbox_mouse_button_is_down(self.box))
        self.assertEqual(self.commits, [])

    def test_range_drag_reports_block_and_target_and_marks_preview(self):
        self._click(1)
        self._click(3, state=0x1)
        self.commits.clear()
        self._press(2)
        self._motion(6)
        self.assertEqual(tuple(self.box.curselection()), (5, 6, 7))
        self.assertEqual(self.moves, [])
        self._release(6)
        self.assertEqual(self.moves, [(1, 3, 5)])
        self.assertEqual(self.commits, [])

    def test_dragging_from_middle_of_range_preserves_pressed_row_offset(self):
        self._click(1)
        self._click(3, state=0x1)
        self._press(2)
        self._motion(4)
        self.assertEqual(
            tuple(self.box.get(0, tk.END)),
            ("row 0", "row 4", "row 5", "row 1", "row 2", "row 3", "row 6", "row 7"),
        )
        self.assertEqual(tuple(self.box.curselection()), (3, 4, 5))
        self._release(4)
        self.assertEqual(self.moves, [(1, 3, 3)])

    def test_unchanged_and_refused_moves_do_not_commit_drag(self):
        self._press(2)
        self._motion(3)
        self._motion(2)
        self._release(2)
        self.assertEqual(self.moves, [])
        self.assertEqual(tuple(self.box.curselection()), (2,))
        self.assertEqual(self.commits, [])

        self.on_move.side_effect = lambda *args: self.moves.append(args) or False
        self._click(1)
        self._click(3, state=0x1)
        self.commits.clear()
        self._press(2)
        self._motion(6)
        self._release(6)
        self.assertEqual(self.moves, [(1, 3, 5)])
        self.assertEqual(tuple(self.box.curselection()), (1, 2, 3))

    def test_refused_drag_outside_previous_range_restores_new_single_selection(self):
        self._click(1)
        self._click(3, state=0x1)
        self.on_move.return_value = False
        self.on_move.side_effect = None
        self._press(6)
        self._motion(2)
        self._release(2)
        self.on_move.assert_called_once_with(6, 6, 2)
        self.assertEqual(tuple(self.box.curselection()), (6,))
        self.assertEqual(int(self.box.index(tk.ACTIVE)), 6)

    def test_escape_restores_preview_and_suppresses_dialog_binding(self):
        escaped = []
        self.root.bind("<Escape>", lambda _event: escaped.append(True))
        original = tuple(self.box.get(0, tk.END))
        self.box.itemconfigure(1, background="#123456")
        self._press(1)
        self._motion(5)
        self.box.event_generate("<Escape>")
        self.root.update()
        self.assertEqual(tuple(self.box.get(0, tk.END)), original)
        self.assertEqual(self.box.itemcget(1, "background"), "#123456")
        self.assertEqual(tuple(self.box.curselection()), (1,))
        self.assertEqual(escaped, [])
        self._release(5)
        self.assertEqual(self.moves, [])
        self.assertEqual(self.commits, [])

        self.box.event_generate("<Escape>")
        self.root.update()
        self.assertEqual(escaped, [True])

    def test_is_dragging_and_cancel_drag_restore_preview(self):
        original = tuple(self.box.get(0, tk.END))
        self.assertFalse(self.controller.is_dragging())
        self._press(1)
        self._motion(5)
        self.assertTrue(self.controller.is_dragging())

        self.controller.cancel_drag()

        self.assertFalse(self.controller.is_dragging())
        self.assertEqual(tuple(self.box.get(0, tk.END)), original)
        self.assertEqual(tuple(self.box.curselection()), (1,))
        self._release(5)
        self.assertEqual(self.moves, [])

    def test_bind_escape_false_leaves_escape_unbound_on_listbox(self):
        self.box.destroy()
        self.box = tk.Listbox(self.root, height=8)
        self.box.pack(fill="both", expand=True)
        for item in self.items:
            self.box.insert(tk.END, item)
        self.controller = bind_listbox_range_drag(
            self.box, on_move=self.on_move, bind_escape=False
        )
        self.root.update()

        self.assertFalse(self.box.bind("<Escape>"))

    def test_drag_autoscrolls_when_pointer_is_outside(self):
        self.box.configure(height=3)
        self.box.pack_configure(fill="x", expand=False)
        self.root.update_idletasks()
        initial_top = self.box.yview()[0]
        x, _y = self._press(1)
        self._motion(2)
        self.box.event_generate("<B1-Motion>", x=x, y=self.box.winfo_height() + 5, state=0x100)
        self.root.after(180, self.root.quit)
        self.root.mainloop()
        self.assertGreater(self.box.yview()[0], initial_top)
        self.box.event_generate(
            "<ButtonRelease-1>", x=x, y=self.box.winfo_height() + 5, state=0x100
        )

    def test_can_start_drag_false_leaves_rows_in_place(self):
        self.box.destroy()
        self.box = tk.Listbox(self.root, height=8)
        self.box.pack(fill="both", expand=True)
        for item in self.items:
            self.box.insert(tk.END, item)
        bind_listbox_range_drag(self.box, on_move=self.on_move, can_start_drag=lambda: False)
        self.root.update()
        self._press(1)
        self._motion(5)
        self._release(5)
        self.assertEqual(tuple(self.box.get(0, tk.END)), tuple(self.items))
        self.assertEqual(self.moves, [])


if __name__ == "__main__":
    unittest.main()
