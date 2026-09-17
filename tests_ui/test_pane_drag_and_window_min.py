"""境界線ドラッグ・ウィンドウ最小幅・省略表示との切替を実際の Tk で確認する（フック開始なし）。"""
import tkinter as tk
import unittest
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.presentation import app as app_module
from keyseq.presentation import theme
from keyseq.presentation.pane_width_rules import SASH_WIDTH, PaneWidths


class PaneDragAndWindowMinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        base_sizes = dict(theme._BASE_FONT_SIZES)
        cls.addClassCleanup(cls._restore_base_sizes, base_sizes)
        for target, name, value in (
            (app_module.StartupIo, "write_startup", True),
            (app_module.ConfigService, "save_startup", None),
        ):
            patcher = patch.object(target, name, return_value=value)
            patcher.start()
            cls.addClassCleanup(patcher.stop)
        loader = patch.object(app_module.ConfigService, "load_startup", return_value={})
        loader.start()
        try:
            cls.app = App()
        finally:
            loader.stop()
        cls.addClassCleanup(cls._destroy_app)
        cls.app.update()
        cls.released_minsize = cls._probe_released_minsize()

    @classmethod
    def _probe_released_minsize(cls) -> tuple[int, int]:
        # Windows の Tk は minsize(1, 1) 後もシステム下限（例 120）を返すため、解除後の値を実測する。
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
        self.keymap, self.trigger, self.sequence = (
            self.view.keymap_box, self.view.trigger_box, self.view.sequence_box,
        )
        self.boxes = (self.keymap, self.trigger, self.sequence)
        self.app.update()
        self.saved = {
            "geometry": self.app.geometry(), "delta": self.app._ui_font_delta_pt,
            "minsize": self.app.wm_minsize(), "desired": self.layout.desired,
            "min_widths": self.layout.min_widths, "pending": self.layout._remeasure_pending,
            "options": [
                {name: self.panes.panecget(box, name) for name in ("width", "minsize")}
                for box in self.boxes
            ],
        }
        writer = patch.object(self.app.startup_io, "write_startup", return_value=True)
        writer.start()
        self.addCleanup(writer.stop)
        # addCleanup は setUp 内の失敗時にも実行され、書込パッチより先に復元する。
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        saved = self.saved
        try:
            if self.app._compact_mode:
                self.app.show_full_view()
            self.layout.desired = saved["desired"]
            self.app._apply_font_delta(saved["delta"])
        finally:
            self.layout.min_widths = saved["min_widths"]
            self.layout._remeasure_pending = saved["pending"]
            self.layout._drag = None
            self.app.minsize(*saved["minsize"])
            self.app.geometry(saved["geometry"])
            for box, options in zip(self.boxes, saved["options"]):
                self.panes.paneconfigure(box, **options)
            self.app.update()
            self.app.pane_layout.cancel_window_width_save()

    def _widen(self, delta: int = 200) -> None:
        self.app.geometry(f"{self.app.winfo_width() + delta}x{self.app.winfo_height()}")
        self.app.update()

    def _widths(self) -> list[int]:
        return [box.winfo_width() for box in self.boxes]

    def _drag(self, sash: int, dx: int, button: int = 1) -> None:
        x = self.panes.sash_coord(sash)[0] + SASH_WIDTH // 2
        y = self.panes.winfo_height() // 2
        self.panes.event_generate(f"<Button-{button}>", x=x, y=y)
        self.panes.event_generate(f"<B{button}-Motion>", x=x + dx, y=y)
        self.app.update()
        self.panes.event_generate(f"<ButtonRelease-{button}>", x=x + dx, y=y)
        self.app.update()

    def _expected_window_min(self) -> int:
        extra = self.app.winfo_width() - self.panes.winfo_width()
        return max(
            self.keymap.winfo_width() + self.sequence.winfo_width()
            + self.layout.min_widths.trigger + 2 * SASH_WIDTH + extra,
            self.layout.header_window_width,
        )

    def test_01_sash0_right_limit_keeps_sequence_and_window(self) -> None:
        self._widen()
        keymap, _, sequence = self._widths()
        window = self.app.winfo_width()
        self._drag(0, 2000)
        self.assertGreater(self.keymap.winfo_width(), keymap)
        self.assertEqual(self.sequence.winfo_width(), sequence)
        self.assertEqual(self.app.winfo_width(), window)
        self.assertEqual(self.trigger.winfo_width(), self.layout.min_widths.trigger)

    def test_02_sash1_left_limit_keeps_keymap_and_window(self) -> None:
        self._widen()
        keymap, _, sequence = self._widths()
        window = self.app.winfo_width()
        self._drag(1, -2000)
        self.assertGreater(self.sequence.winfo_width(), sequence)
        self.assertEqual(self.keymap.winfo_width(), keymap)
        self.assertEqual(self.app.winfo_width(), window)
        self.assertEqual(self.trigger.winfo_width(), self.layout.min_widths.trigger)

    def test_03_sash0_left_limit_stops_at_keymap_min(self) -> None:
        sequence = self.sequence.winfo_width()
        self._drag(0, -2000)
        self.assertEqual(self.keymap.winfo_width(), self.layout.min_widths.keymap)
        self.assertEqual(self.sequence.winfo_width(), sequence)

    def test_04_middle_button_does_not_move_sash(self) -> None:
        self._widen()
        widths = self._widths()
        desired = self.layout.desired
        self._drag(0, 60, button=2)
        self._drag(1, -60, button=2)
        self.assertEqual(self._widths(), widths)
        self.assertEqual(self.layout.desired, desired)

    def test_05_drag_updates_only_dragged_side_desired(self) -> None:
        self._widen()
        before = self.layout.desired
        self._drag(0, -30)
        self.assertEqual(self.layout.desired.keymap, self.keymap.winfo_width())
        self.assertNotEqual(self.layout.desired.keymap, before.keymap)
        self.assertEqual(self.layout.desired.sequence, before.sequence)
        after_drag = self.layout.desired
        x = self.trigger.winfo_x() + self.trigger.winfo_width() // 2
        y = self.panes.winfo_height() // 2
        self.panes.event_generate("<Button-1>", x=x, y=y)
        self.panes.event_generate("<ButtonRelease-1>", x=x, y=y)
        self.app.update()
        self.assertEqual(self.layout.desired, after_drag)

    def test_06_blocked_drag_keeps_desired_below_minimum(self) -> None:
        self._widen()
        below = self.layout.min_widths.keymap - 20
        self.layout.desired = PaneWidths(keymap=below, sequence=self.layout.desired.sequence)
        self.layout.apply_layout()
        self.app.update()
        self.assertEqual(self.keymap.winfo_width(), self.layout.min_widths.keymap)
        self._drag(0, -50)
        self.assertEqual(self.layout.desired.keymap, below)
        sequence = self.layout.desired.sequence
        self._drag(1, -30)
        self.assertEqual(self.layout.desired.keymap, below)
        self.assertNotEqual(self.layout.desired.sequence, sequence)

    def test_07_window_min_width_keeps_side_panes(self) -> None:
        expected = self._expected_window_min()
        self.assertEqual(self.app.wm_minsize()[0], expected)
        keymap, _, sequence = self._widths()
        self.app.geometry(f"{expected - 100}x{self.app.winfo_height()}")
        self.app.update()
        self.assertEqual(self.keymap.winfo_width(), keymap)
        self.assertEqual(self.sequence.winfo_width(), sequence)

    def test_08_compact_view_releases_window_min(self) -> None:
        expected = self._expected_window_min()
        self.app.show_compact_view()
        self.app.update()
        self.assertEqual(self.app.wm_minsize(), self.released_minsize)
        self.assertEqual(self.app.winfo_width(), 270)
        self.app.show_full_view()
        self.app.update()
        self.assertEqual(self.app.wm_minsize()[0], expected)

    def test_09_font_change_in_compact_view_defers_remeasure(self) -> None:
        self.app._apply_font_delta(0)
        self.app.update()
        keymap_min = self.layout.min_widths.keymap
        self.app.show_compact_view()
        self.app.update()
        self.app._apply_font_delta(2)
        self.app.update()
        self.assertEqual(self.app.wm_minsize(), self.released_minsize)
        self.assertEqual(self.app.winfo_width(), 270)
        self.app.show_full_view()
        self.app.update()
        self.assertGreater(self.layout.min_widths.keymap, keymap_min)
        self.assertEqual(self.app.wm_minsize()[0], self._expected_window_min())

    def test_10_font_change_in_full_view_raises_display_not_desired(self) -> None:
        self.app._apply_font_delta(0)
        self.app.update()
        self.layout.desired = PaneWidths(
            keymap=self.layout.min_widths.keymap, sequence=self.layout.min_widths.sequence,
        )
        self.layout.apply_layout()
        self.app.update()
        desired = self.layout.desired
        self.app._apply_font_delta(2)
        self.app.update()
        mins = self.layout.min_widths
        self.assertEqual(self.layout.desired, desired)
        self.assertGreater(mins.keymap, desired.keymap)
        self.assertEqual(self.keymap.winfo_width(), mins.keymap)
        self.assertGreaterEqual(self.sequence.winfo_width(), mins.sequence)

    def test_11_screen_overflow_shrinks_sequence_first(self) -> None:
        screen = self.app.winfo_width() + 150
        desired = PaneWidths(
            keymap=self.layout.desired.keymap, sequence=self.layout.desired.sequence + 1000,
        )
        self.layout.desired = desired
        with patch.object(self.app, "winfo_screenwidth", return_value=screen), \
                patch.object(self.app, "geometry", wraps=self.app.geometry) as geometry:
            self.layout.apply_layout()
            self.app.update()
        widths = [int(str(call.args[0]).split("x")[0]) for call in geometry.call_args_list if call.args]
        self.assertTrue(widths)
        self.assertTrue(all(width <= screen for width in widths), widths)
        self.assertEqual(self.keymap.winfo_width(), max(desired.keymap, self.layout.min_widths.keymap))
        self.assertLess(self.sequence.winfo_width(), desired.sequence)
        self.assertGreaterEqual(self.sequence.winfo_width(), self.layout.min_widths.sequence)
        self.assertEqual(self.layout.desired, desired)

    def test_12_drag_after_screen_shrink_uses_displayed_window_min(self) -> None:
        mins = self.layout.min_widths
        extra = self.app.winfo_width() - self.panes.winfo_width()
        desired = PaneWidths(mins.keymap + 80, mins.sequence + 1000)
        screen = desired.keymap + mins.sequence + 60 + mins.trigger + 2 * SASH_WIDTH + extra
        self.layout.desired = desired
        with patch.object(self.app, "winfo_screenwidth", return_value=screen):
            self.layout.apply_layout()
            self.app.update()
            keymap, _, sequence = self._widths()
            self.assertEqual(keymap, desired.keymap)
            self.assertLess(sequence, desired.sequence)
            self.assertGreater(sequence, mins.sequence)
            self._drag(0, -30)
            self.assertEqual(self.keymap.winfo_width(), keymap - 30)
            self.assertEqual(self.sequence.winfo_width(), sequence)
            self.assertEqual(self.layout.desired.sequence, desired.sequence)
            self.assertEqual(self.app.wm_minsize()[0], self._expected_window_min())


if __name__ == "__main__":
    unittest.main()
