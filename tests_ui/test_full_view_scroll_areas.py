import unittest
from unittest.mock import patch

from keyseq.presentation import app as app_module, theme
from keyseq.presentation.app import App
from keyseq.presentation.controllers.pane_layout.pane_measure import measure_min_widths


class FullViewScrollAreasTest(unittest.TestCase):
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
        self.saved = (
            self.app.geometry(), self.app.wm_minsize(), self.app._ui_font_delta_pt,
        )
        self.addCleanup(self._restore)
        self.app.pane_layout.cancel_window_width_save()

    def _restore(self) -> None:
        geometry, minsize, delta = self.saved
        self.app._apply_font_delta(delta)
        self.app.minsize(*minsize)
        self.app.geometry(geometry)
        self.app.update()
        self.app.pane_layout.cancel_window_width_save()

    def _set_height(self, height: int) -> None:
        self.app.geometry(f"{self.app.winfo_width()}x{height}")
        self.app.update()

    def _reduced_height(self) -> int:
        return max(2, self.app.pane_layout.window_min_height - 150)

    def _set_font(self, delta: int) -> None:
        self.app._apply_font_delta(delta)
        self.app.update()

    def test_default_and_minimum_height_fit_without_scrollbars(self) -> None:
        for height in (self.app.winfo_height(), self.app.pane_layout.window_min_height):
            with self.subTest(height=height):
                self._set_height(height)
                for box in self.boxes:
                    area = box.scroll_area
                    area.sync()
                    self.assertFalse(area.scrollbar_shown)
                    self.assertGreaterEqual(
                        int(float(area.canvas.itemcget(area._content_window, "height"))),
                        area.content.winfo_reqheight(),
                    )

    def test_scroll_area_request_sizes_match_content(self) -> None:
        for box in self.boxes:
            box.scroll_area.sync()
            self.assertEqual(
                box.scroll_area.canvas.winfo_reqheight(),
                box.scroll_area.content.winfo_reqheight(),
            )
            self.assertEqual(
                box.scroll_area.canvas.winfo_reqwidth(),
                box.scroll_area.content.winfo_reqwidth(),
            )
        self.assertEqual(self.app.wm_minsize()[1], self.app.pane_layout.window_min_height)
        self.assertEqual(measure_min_widths(self.app), self.app.pane_layout.min_widths)

    def test_too_short_window_scrolls_only_overflowing_boxes_to_the_bottom(self) -> None:
        self.app.minsize(1, 1)
        self._set_height(self._reduced_height())
        mapped_scroll_areas = [
            box.scroll_area for box in self.boxes
            if box.scroll_area.scrollbar_shown and box.scroll_area.canvas.winfo_ismapped()
        ]
        self.assertTrue(mapped_scroll_areas, "Reduced height must leave a mapped overflowing pane")
        endings = (
            self.view.keymap_box.scroll_area.content.winfo_children()[-1].winfo_children()[-1],
            self.view.trigger_box.suppress_chk,
            self.view.sequence_box.select_before_run_chk,
        )
        for box, ending in zip(self.boxes, endings):
            area = box.scroll_area
            area.sync()
            if area.content.winfo_reqheight() > area.canvas.winfo_height():
                self.assertTrue(area.scrollbar_shown)
                area.canvas.yview_moveto(1)
                self.app.update()
                top = area.canvas.winfo_rooty()
                bottom = top + area.canvas.winfo_height()
                self.assertLess(ending.winfo_rooty(), bottom)
                self.assertGreater(ending.winfo_rooty() + ending.winfo_height(), top)
            else:
                self.assertFalse(area.scrollbar_shown)

    def test_restoring_height_hides_scrollbars_and_resets_to_top(self) -> None:
        self.app.minsize(1, 1)
        self._set_height(self._reduced_height())
        overflowing = [
            box.scroll_area for box in self.boxes
            if box.scroll_area.scrollbar_shown
        ]
        self.assertTrue(overflowing, "Reduced height must show at least one scrollbar")
        self.assertTrue(any(area.canvas.winfo_ismapped() for area in overflowing))
        for box in self.boxes:
            box.scroll_area.sync()
            if box.scroll_area.scrollbar_shown:
                box.scroll_area.canvas.yview_moveto(1)
        self._set_height(self.app.pane_layout.window_min_height)
        for box in self.boxes:
            area = box.scroll_area
            area.sync()
            self.assertFalse(area.scrollbar_shown)
            self.assertEqual(area.canvas.yview()[0], 0)

    def test_wheel_scrolls_containers_but_not_lists_or_delay_value(self) -> None:
        self.app.minsize(1, 1)
        self._set_height(self._reduced_height())
        areas = [box.scroll_area for box in self.boxes]
        for area in areas:
            area.sync()
        scrollable = next((area for area in areas if area.scrollbar_shown), None)
        if scrollable is None:
            self.fail("No full-view pane overflowed at the reduced height")
        self.assertTrue(scrollable.canvas.winfo_ismapped())
        sequence = self.view.sequence_box
        before = scrollable.canvas.yview()
        scrollable.content.winfo_children()[-1].event_generate("<MouseWheel>", delta=-120)
        self.app.update()
        self.assertNotEqual(scrollable.canvas.yview(), before)
        list_area = sequence.scroll_area if sequence.scroll_area.scrollbar_shown else scrollable
        listing = next(
            box.keymap_listbox if box is self.view.keymap_box else
            box.trigger_list if box is self.view.trigger_box else box.action_list
            for box in self.boxes
            if box.scroll_area is list_area
        )
        before = list_area.canvas.yview()
        listing.event_generate("<MouseWheel>", delta=-120)
        self.app.update()
        self.assertEqual(list_area.canvas.yview(), before)
        before_delay = self.app.ui_vars.run_to_end_delay_var.get()
        sequence.run_to_end_delay_entry.event_generate("<MouseWheel>", delta=-120)
        self.app.update()
        self.assertEqual(self.app.ui_vars.run_to_end_delay_var.get(), before_delay)

    def test_measurement_does_not_reschedule_forever(self) -> None:
        area = self.view.keymap_box.scroll_area
        with patch.object(area, "_measure_scroll_area", wraps=area._measure_scroll_area) as measure:
            area.sync()
            self.app.update()
            settled_count = measure.call_count
            for _ in range(20):
                self.app.update()
            self.assertEqual(measure.call_count, settled_count)
            self.assertFalse(area._measure_pending)

    def test_font_minus_three_and_plus_three_keep_fit_invariants(self) -> None:
        for delta in (-3, 3):
            with self.subTest(delta=delta):
                self._set_font(delta)
                self._set_height(self.app.pane_layout.window_min_height)
                for box in self.boxes:
                    area = box.scroll_area
                    area.sync()
                    self.assertFalse(area.scrollbar_shown)
                    self.assertEqual(area.canvas.winfo_reqheight(), area.content.winfo_reqheight())
                    self.assertEqual(area.canvas.winfo_reqwidth(), area.content.winfo_reqwidth())
