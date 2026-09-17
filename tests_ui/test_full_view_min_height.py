import time
import tkinter as tk
import unittest
from unittest.mock import patch

from keyseq.presentation import app as app_module, theme
from keyseq.presentation.app import App
from keyseq.presentation.pane_width_rules import SASH_WIDTH


class FullViewMinHeightTest(unittest.TestCase):
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
        cls.released_minsize = cls._probe_released_minsize()

    @classmethod
    def _probe_released_minsize(cls) -> tuple[int, int]:
        # Windows の Tk が返すシステム下限も含めて解除値を測る。
        probe = tk.Toplevel(cls.app)
        try:
            probe.minsize(1, 1)
            probe.update_idletasks()
            return probe.wm_minsize()
        finally:
            probe.destroy()

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
        self.layout = self.app.pane_layout
        self.view = self.app.full_view
        self.panes = self.view.panes
        self.boxes = (self.view.keymap_box, self.view.trigger_box, self.view.sequence_box)
        self.app.update()
        self.saved = {
            "geometry": self.app.geometry(), "delta": self.app._ui_font_delta_pt,
            "minsize": self.app.wm_minsize(), "desired": self.layout.desired,
            "min_widths": self.layout.min_widths,
            "window_min_height": self.layout.window_min_height,
            "header_window_width": self.layout.header_window_width,
            "pending": self.layout._remeasure_pending,
            "options": [
                {name: self.panes.panecget(box, name) for name in ("width", "minsize")}
                for box in self.boxes
            ],
        }
        self.addCleanup(self._restore)
        self.layout.cancel_window_width_save()
        self.writer.reset_mock()

    def tearDown(self) -> None:
        # 各テストの操作による書き込みを、復元操作より前に検査する。
        self._assert_saved_keys()

    def _assert_saved_keys(self) -> None:
        allowed = {"full_view_pane_widths", "full_view_window_width", "ui_font_delta_pt"}
        for call in self.writer.call_args_list:
            self.assertEqual(len(call.args), 1)
            self.assertFalse(call.kwargs)
            self.assertLessEqual(set(call.args[0]), allowed)

    def _restore(self) -> None:
        saved = self.saved
        try:
            if self.app._compact_mode:
                self.app.show_full_view()
            self.layout.desired = saved["desired"]
            self.app._apply_font_delta(saved["delta"])
        finally:
            self.layout.min_widths = saved["min_widths"]
            self.layout.window_min_height = saved["window_min_height"]
            self.layout.header_window_width = saved["header_window_width"]
            self.layout._remeasure_pending = saved["pending"]
            self.layout._drag = None
            self.app.minsize(*saved["minsize"])
            self.app.geometry(saved["geometry"])
            for box, options in zip(self.boxes, saved["options"]):
                self.panes.paneconfigure(box, **options)
            self.app.update()
            self.layout.cancel_window_width_save()

    def _set_height(self, height: int) -> None:
        self.app.geometry(f"{self.app.winfo_width()}x{height}")
        self.app.update()

    def _set_font(self, delta: int) -> None:
        self.app._apply_font_delta(delta)
        self.app.update()

    def _drain_timers(self) -> None:
        # 幅保存の 500ms を超えて、after のコールバックを update で処理する。
        finished = []
        timer = self.app.after(600, lambda: finished.append(True))
        try:
            while not finished:
                self.app.update()
                time.sleep(0.01)
        finally:
            self.app.after_cancel(timer)

    def _drag(self, sash: int, dx: int) -> None:
        x = self.panes.sash_coord(sash)[0] + SASH_WIDTH // 2
        y = self.panes.winfo_height() // 2
        self.panes.event_generate("<Button-1>", x=x, y=y)
        self.panes.event_generate("<B1-Motion>", x=x + dx, y=y)
        self.app.update()
        self.panes.event_generate("<ButtonRelease-1>", x=x + dx, y=y)
        self.app.update()

    def test_minimum_height_keeps_contents_visible(self) -> None:
        for delta in (-3, 0, 3):
            with self.subTest(delta=delta):
                self._set_font(delta)
                self._set_height(1)
                self.assertEqual(self.app.winfo_height(), self.layout.window_min_height)
                self.assertEqual(self.app.wm_minsize()[1], self.layout.window_min_height)
                for child in self.app.pack_slaves():
                    self.assertTrue(child.winfo_ismapped(), str(child))
                    self.assertLessEqual(
                        child.winfo_y() + child.winfo_height(), self.app.winfo_height(),
                    )
                for box in self.boxes:
                    for child in box.winfo_children():
                        if child.winfo_manager() == "pack":
                            self.assertTrue(child.winfo_ismapped(), str(child))
                            self.assertGreaterEqual(child.winfo_height(), child.winfo_reqheight())
                            self.assertLessEqual(
                                child.winfo_y() + child.winfo_height(), box.winfo_height(),
                            )
                for listing in (
                    self.view.keymap_box.keymap_listbox, self.view.trigger_box.trigger_list,
                    self.view.sequence_box.action_list,
                ):
                    self.assertGreaterEqual(listing.winfo_height(), listing.winfo_reqheight())
                header = self.view.header_area
                self.assertGreaterEqual(header.winfo_height(), header.winfo_reqheight())

    def test_font_changes_recalculate_minimum_height(self) -> None:
        self._set_font(0)
        normal = self.layout.window_min_height
        self.assertEqual(self.app.wm_minsize()[1], normal)
        self._set_font(3)
        enlarged = self.layout.window_min_height
        self.assertGreater(enlarged, normal)
        self.assertEqual(self.app.wm_minsize()[1], enlarged)
        self._set_font(0)
        self.assertLess(self.layout.window_min_height, enlarged)
        self.assertEqual(self.app.wm_minsize()[1], self.layout.window_min_height)

    def test_font_growth_expands_only_below_minimum(self) -> None:
        self._set_font(0)
        normal = self.layout.window_min_height
        self._set_height(normal)
        self.assertEqual(self.app.winfo_height(), normal)
        self._set_font(3)
        enlarged = self.layout.window_min_height
        self.assertGreater(enlarged, normal)
        self.assertEqual(self.app.winfo_height(), enlarged)
        self._set_font(0)
        self.assertEqual(self.app.winfo_height(), enlarged)
        self._set_height(enlarged + 200)
        tall = self.app.winfo_height()
        self._set_font(3)
        self.assertGreaterEqual(tall, self.layout.window_min_height)
        self.assertEqual(self.app.winfo_height(), tall)

    def test_drag_preserves_minimum_height(self) -> None:
        self.app.geometry(f"{self.app.winfo_width() + 200}x{self.app.winfo_height()}")
        self.app.update()
        before = self.layout.desired
        self._drag(0, 40)
        self.assertNotEqual(self.layout.desired, before)
        self.assertGreater(self.layout.window_min_height, self.released_minsize[1])
        self.assertEqual(self.app.wm_minsize()[1], self.layout.window_min_height)

    def test_compact_view_releases_and_full_view_restores_minimum(self) -> None:
        self.app.show_compact_view()
        self.app.update()
        self.assertTrue(self.app._compact_mode)
        self.assertEqual(self.app.wm_minsize(), self.released_minsize)
        self.app.show_full_view()
        self.app.update()
        self.assertFalse(self.app._compact_mode)
        self.assertGreater(self.layout.window_min_height, self.released_minsize[1])
        self.assertEqual(self.app.wm_minsize()[1], self.layout.window_min_height)

    def test_font_change_ignores_multiline_flash_message_height(self) -> None:
        self.addCleanup(self.app._set_flash_message, "", auto_clear=False)
        self.app._set_flash_message("", auto_clear=False)
        self._set_font(3)
        expected = self.layout.window_min_height
        self._set_font(0)
        before = self.app.winfo_reqheight()
        self.app._set_flash_message("1行目\n2行目\n3行目", auto_clear=False)
        self.app.update()
        self.assertGreater(self.app.winfo_reqheight(), before)
        self._set_font(3)
        self.assertEqual(self.layout.window_min_height, expected)

    def test_view_round_trip_ignores_multiline_flash_message_height(self) -> None:
        self.addCleanup(self.app._set_flash_message, "", auto_clear=False)
        self.app._set_flash_message("", auto_clear=False)
        self._set_font(0)
        expected = self.layout.window_min_height
        self.app._set_flash_message("1行目\n2行目\n3行目", auto_clear=False)
        self.app.update()
        self.app.show_compact_view()
        self.app.update()
        self.app.show_full_view()
        self.app.update()
        self.assertEqual(self.layout.window_min_height, expected)

    def test_compact_font_change_measures_full_view_status_height(self) -> None:
        self._set_font(0)
        self.app.show_compact_view()
        self._set_font(3)
        self.app.show_full_view()
        restored = self.layout.window_min_height
        self.app.update()
        self.layout.apply_layout()
        self.assertEqual(self.layout.window_min_height, restored)

    def test_full_view_return_expands_height_below_new_minimum(self) -> None:
        self._set_font(0)
        normal = self.layout.window_min_height
        self._set_height(normal)
        self.assertEqual(self.app.winfo_height(), normal)
        self.app.show_compact_view()
        self._set_font(3)
        self.app.show_full_view()
        self.app.update()
        self.assertEqual(self.app.winfo_height(), self.layout.window_min_height)
        self.assertGreater(self.layout.window_min_height, normal)

    def test_height_is_not_saved(self) -> None:
        self._set_font(3)
        self._set_font(0)
        self._drain_timers()
        self.assertTrue(self.writer.called)
        self._assert_saved_keys()
        height_only_call_start_index = len(self.writer.call_args_list)
        width, height = self.app.winfo_width(), self.app.winfo_height()
        self._set_height(height + 50)
        self._drain_timers()
        self.assertEqual(self.app.winfo_width(), width)
        self.assertNotEqual(self.app.winfo_height(), height)
        for call in self.writer.call_args_list[height_only_call_start_index:]:
            self.assertNotIn("full_view_window_width", call.args[0])


if __name__ == "__main__":
    unittest.main()
