import tkinter as tk
import unittest
from math import ceil
from tkinter import ttk
from unittest.mock import patch

from keyseq.presentation import app as app_module, theme
from keyseq.presentation.app import App
from keyseq.presentation.controllers.pane_layout.pane_measure import (
    measure_main_area_basis_height,
    measure_min_widths,
    measure_window_min_height,
)


class FullViewMinSizeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        base_sizes = dict(theme._BASE_FONT_SIZES)
        cls.addClassCleanup(cls._restore_base_sizes, base_sizes)
        for target, name, value in (
            (app_module.StartupIo, "write_startup", True),
            (app_module.ConfigService, "save_startup", None),
            (app_module.ConfigService, "load_startup", {}),
        ):
            patcher = patch.object(target, name, return_value=value)
            mock = patcher.start()
            cls.addClassCleanup(patcher.stop)
            if name == "write_startup":
                cls.writer = mock
        cls.app = App()
        cls.addClassCleanup(cls._destroy_app)
        cls.app.update()

    @classmethod
    def _restore_base_sizes(cls, sizes: dict[str, int]) -> None:
        theme._BASE_FONT_SIZES.clear()
        theme._BASE_FONT_SIZES.update(sizes)

    @classmethod
    def _destroy_app(cls) -> None:
        try:
            cls.app.pane_layout.cancel_window_width_save()
            cls.app.update()
        finally:
            cls.app.destroy()

    def setUp(self) -> None:
        self.view = self.app.full_view
        self.boxes = (self.view.keymap_box, self.view.trigger_box, self.view.sequence_box)
        self.saved = (self.app.geometry(), self.app.wm_minsize(), self.app._ui_font_delta_pt)
        self.addCleanup(self._restore)
        self.app.pane_layout.cancel_window_width_save()

    def _restore(self) -> None:
        geometry, minsize, delta = self.saved
        self.app._apply_font_delta(delta)
        self.app.minsize(*minsize)
        self.app.geometry(geometry)
        self.app.update()
        self.app.pane_layout.cancel_window_width_save()

    def _set_font(self, delta: int) -> None:
        self.app._apply_font_delta(delta)
        self.app.update()

    def _current_min_height_formula(self) -> int:
        self.app.update_idletasks()
        height = self.app.winfo_reqheight()
        variable = str(self.app.ui_vars.flash_message_var)
        pending = list(self.app.winfo_children())
        label = None
        while pending:
            widget = pending.pop()
            if isinstance(widget, ttk.Label) and str(widget.cget("textvariable")) == variable:
                label = widget
                break
            pending.extend(widget.winfo_children())
        if label is not None:
            other_heights = [
                child.winfo_reqheight() for child in label.master.winfo_children()
                if isinstance(child, ttk.Label) and child is not label
            ]
            if other_heights:
                height -= max(0, label.winfo_reqheight() - max(other_heights))
        return height

    def _ending_widget(self, box: ttk.LabelFrame) -> tk.Widget:
        if box is self.view.keymap_box:
            return box.scroll_area.content.winfo_children()[-1].winfo_children()[-1]
        if box is self.view.trigger_box:
            return box.suppress_chk
        return box.select_before_run_chk

    def test_minimum_height_formula_and_scrollbar_widths_at_each_font(self) -> None:
        for delta in (-3, 0, 3):
            with self.subTest(font_delta=delta):
                self._set_font(delta)
                layout = self.app.pane_layout
                current_height = self._current_min_height_formula()
                panes_height = self.view.panes.winfo_reqheight()
                basis_height = measure_main_area_basis_height(self.app)
                expected_basis_height = max(
                    box.winfo_reqheight() - box.scroll_area.winfo_reqheight()
                    + box.scroll_area.content.winfo_reqheight()
                    for box in self.boxes
                )
                self.assertEqual(basis_height, expected_basis_height)
                expected_height = current_height - panes_height + ceil(basis_height / 2)
                self.assertEqual(layout.window_min_height, measure_window_min_height(self.app))
                self.assertEqual(layout.window_min_height, expected_height)
                self.assertEqual(self.app.wm_minsize()[1], expected_height)
                self.assertLess(expected_height, current_height)

                original_widths = tuple(
                    box.scroll_area.scrollbar.winfo_reqwidth() for box in self.boxes
                )
                width_patchers = [
                    patch.object(box.scroll_area.scrollbar, "winfo_reqwidth", return_value=0)
                    for box in self.boxes
                ]
                for patcher in width_patchers:
                    patcher.start()
                try:
                    before_scrollbar = measure_min_widths(self.app)
                finally:
                    for patcher in reversed(width_patchers):
                        patcher.stop()
                measured = measure_min_widths(self.app)
                self.assertEqual(measured.keymap, before_scrollbar.keymap + original_widths[0])
                self.assertEqual(measured.trigger, before_scrollbar.trigger + original_widths[1])
                self.assertEqual(measured.sequence, before_scrollbar.sequence + original_widths[2])
                self.assertEqual(measured, layout.min_widths)

    def test_minimum_geometry_keeps_widths_and_bottom_controls_reachable(self) -> None:
        for delta in (-3, 0, 3):
            with self.subTest(font_delta=delta):
                self._set_font(delta)
                window_width = self.app.wm_minsize()[0]
                window_height = self.app.pane_layout.window_min_height
                self.app.minsize(1, 1)
                self.app.geometry(f"{window_width}x{window_height}")
                self.app.update()
                overflows = []
                for box in self.boxes:
                    area = box.scroll_area
                    area.sync()
                    inner_width = area.winfo_width()
                    self.assertLessEqual(
                        area.scrollbar.winfo_x() + area.scrollbar.winfo_width(), inner_width,
                    )
                    self.assertGreaterEqual(
                        area.scrollbar.winfo_width(), area.scrollbar.winfo_reqwidth(),
                    )
                    for widget in self._width_sensitive_widgets(area.content):
                        self.assertGreaterEqual(widget.winfo_width(), widget.winfo_reqwidth(), str(widget))
                    if area.content.winfo_reqheight() > area.canvas.winfo_height():
                        overflows.append(area)
                        self.assertTrue(area.scrollbar_shown)
                        area.canvas.yview_moveto(1)
                        self.app.update()
                        ending = self._ending_widget(box)
                        top = area.canvas.winfo_rooty()
                        bottom = top + area.canvas.winfo_height()
                        self.assertLess(ending.winfo_rooty(), bottom)
                        self.assertGreater(ending.winfo_rooty() + ending.winfo_height(), top)
                    else:
                        self.assertFalse(area.scrollbar_shown)
                self.assertTrue(overflows, "Minimum height must leave at least one pane scrollable")

    def _width_sensitive_widgets(self, parent: tk.Misc):
        for child in parent.winfo_children():
            if isinstance(child, (tk.Button, tk.Checkbutton, ttk.Button, ttk.Checkbutton, tk.Entry, ttk.Entry)):
                yield child
            yield from self._width_sensitive_widgets(child)

    def test_current_minimum_height_has_no_pane_scrollbars(self) -> None:
        for delta in (-3, 0, 3):
            with self.subTest(font_delta=delta):
                self._set_font(delta)
                current_height = self._current_min_height_formula()
                self.app.geometry(f"{self.app.winfo_width()}x{current_height}")
                self.app.update()
                for box in self.boxes:
                    box.scroll_area.sync()
                    self.assertFalse(box.scroll_area.scrollbar_shown)


if __name__ == "__main__":
    unittest.main()
