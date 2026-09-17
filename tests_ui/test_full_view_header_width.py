"""ヘッダ幅を含む最小幅と表示切替を実際の Tk で確認する（暫定仕様17）。"""
import unittest
from unittest.mock import patch

from keyseq.presentation import app as app_module, theme
from keyseq.presentation.app import App
from keyseq.presentation.hook_button_texts import CAPTURE_ACTIVE_TEXT, CAPTURE_IDLE_TEXT
from keyseq.presentation.pane_width_rules import (
    PaneWidths, SASH_WIDTH, window_min_width_after_drag,
)


class FullViewHeaderWidthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sizes = dict(theme._BASE_FONT_SIZES)
        cls.addClassCleanup(cls._restore_sizes, sizes)
        for target, name, value in (
            (app_module.ConfigService, "load_startup", {}),
            (app_module.StartupIo, "write_startup", True),
            (app_module.ConfigService, "save_startup", None),
        ):
            patcher = patch.object(target, name, return_value=value)
            mocked = patcher.start()
            cls.addClassCleanup(patcher.stop)
            if name == "write_startup":
                cls.writer = mocked
        cls.app = App()
        cls.addClassCleanup(cls._destroy_app)
        cls.app.update()

    @staticmethod
    def _restore_sizes(sizes: dict[str, int]) -> None:
        theme._BASE_FONT_SIZES.clear()
        theme._BASE_FONT_SIZES.update(sizes)

    @classmethod
    def _destroy_app(cls) -> None:
        try:
            cls.app.pane_layout.cancel_window_width_save()
        finally:
            cls.app.destroy()

    def setUp(self) -> None:
        self.layout = self.app.pane_layout
        self.view = self.app.full_view
        self.button = self.app.stop_key_capture._capture_btn
        self.app.update()
        self.saved_geometry = self.app.geometry()
        self.saved_full_geometry = self.app._full_geometry
        self.saved_compact_mode = self.app._compact_mode
        self.saved_desired = self.layout.desired
        self.saved_auto_width = self.layout._auto_window_width
        self.saved_text = self.button.cget("text")
        self.addCleanup(self._restore)
        self.layout.cancel_window_width_save()
        self.writer.reset_mock()

    def _restore(self) -> None:
        try:
            self.app.stop_key_capture.stop(cancel=True)
            self.layout._cancel_motion()
            self.layout._drag = None
            if self.app._compact_mode:
                self.app.show_full_view()
            self.button.configure(text=self.saved_text)
            self.layout.desired = self.saved_desired
            self.app._apply_font_delta(0)
            self.layout.apply_layout()
            self.app.geometry(self.saved_geometry)
            self.app.update()
            self.app._compact_mode = self.saved_compact_mode
            self.app._full_geometry = self.saved_full_geometry
            self.layout._auto_window_width = self.saved_auto_width
        finally:
            self.layout.cancel_window_width_save()

    def _set_font(self, delta: int) -> None:
        self.app._apply_font_delta(delta)
        self.app.update()

    def test_header_and_each_frame_fit_at_minimum_width(self) -> None:
        for delta in (-3, 0, 3):
            self._set_font(delta)
            for text in (CAPTURE_IDLE_TEXT, CAPTURE_ACTIVE_TEXT):
                with self.subTest(delta=delta, text=text):
                    self.button.configure(text=text)
                    self.app.geometry(f"1x{self.app.winfo_height()}")
                    self.app.update()
                    for widget in (
                        self.view.header_area, self.view.hook_frame,
                        self.view.display_frame, self.view.file_frame,
                    ):
                        self.assertGreaterEqual(widget.winfo_width(), widget.winfo_reqwidth())

    def test_window_minimum_includes_header_at_each_font(self) -> None:
        for delta in (-3, 0, 3):
            with self.subTest(delta=delta):
                self._set_font(delta)
                self.assertEqual(self.app.wm_minsize()[0], self.layout._plan().window_min_width)
                self.assertGreaterEqual(self.app.wm_minsize()[0], self.layout.header_window_width)

    def test_capture_keeps_header_requested_width(self) -> None:
        capture = self.app.stop_key_capture
        for delta in (-3, 0, 3):
            with self.subTest(delta=delta):
                self._set_font(delta)
                before = self.view.header_area.winfo_reqwidth()
                try:
                    capture.start()
                    self.app.update_idletasks()
                    self.assertTrue(capture.capturing)
                    self.assertEqual(self.view.header_area.winfo_reqwidth(), before)
                finally:
                    capture.stop(cancel=True)

    def test_font_restore_lowers_minimum_without_shrinking_window(self) -> None:
        original_minimum = self.app.wm_minsize()[0]
        self._set_font(3)
        larger_minimum = self.app.wm_minsize()[0]
        larger_width = self.app.winfo_width()
        self.assertGreater(larger_minimum, original_minimum)
        self._set_font(0)
        self.assertLess(self.app.wm_minsize()[0], larger_minimum)
        self.assertEqual(self.app.winfo_width(), larger_width)

    def test_compact_font_change_defers_header_measurement(self) -> None:
        self._set_font(3)
        larger_minimum = self.app.wm_minsize()[0]
        larger_header = self.layout.header_window_width
        self._set_font(0)
        original_header = self.layout.header_window_width
        self.app.show_compact_view()
        self.app.update()
        compact_minimum = self.app.wm_minsize()
        self._set_font(3)
        self.assertEqual(self.app.wm_minsize(), compact_minimum)
        self.assertEqual(self.layout.header_window_width, original_header)
        self.app.show_full_view()
        self.app.update()
        self.assertEqual(self.layout.header_window_width, larger_header)
        self.assertEqual(self.app.wm_minsize()[0], larger_minimum)

    def test_drag_minimum_preserves_sides_when_screen_is_smaller(self) -> None:
        panes = self.view.panes
        self.app.geometry(f"{self.app.winfo_width() + 600}x{self.app.winfo_height()}")
        self.app.update()
        before = self.view.sequence_box.winfo_width()
        with patch.object(App, "winfo_screenwidth", return_value=1):
            x = panes.sash_coord(1)[0] + SASH_WIDTH // 2
            y = panes.winfo_height() // 2
            panes.event_generate("<Button-1>", x=x, y=y)
            panes.event_generate("<B1-Motion>", x=x - 400, y=y)
            self.app.update()
            panes.event_generate("<ButtonRelease-1>", x=x - 400, y=y)
            self.app.update()
            displayed = PaneWidths(
                self.view.keymap_box.winfo_width(), self.view.sequence_box.winfo_width(),
            )
            self.assertGreater(displayed.sequence, before)
            extra = self.app.winfo_width() - panes.winfo_width()
            expected = window_min_width_after_drag(
                displayed, self.layout.min_widths, 2 * SASH_WIDTH,
                extra, self.layout.header_window_width,
            )
            # 縮小規則を誤って通す実装との差が出る条件であることも確認する。
            self.assertGreater(expected, self.layout._plan(displayed).window_min_width)
            self.assertEqual(self.app.wm_minsize()[0], expected)
            self.app.geometry(f"{expected}x{self.app.winfo_height()}")
            self.app.update()
            self.assertEqual(self.view.keymap_box.winfo_width(), displayed.keymap)
            self.assertEqual(self.view.sequence_box.winfo_width(), displayed.sequence)

    def test_automatic_startup_width_is_not_saved(self) -> None:
        self.assertEqual(self.app.winfo_width(), self.layout._auto_window_width)
        self.layout.cancel_window_width_save()
        self.layout._save_window_width()
        self.writer.assert_not_called()
