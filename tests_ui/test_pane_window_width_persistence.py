"""ウィンドウ幅の復元・保存とドラッグ間引きを実際の Tk で確認する。"""
import unittest
from unittest.mock import Mock, call, patch

from keyseq.presentation import app as app_module, theme
from keyseq.presentation.app import App
from keyseq.presentation.pane_width_rules import (
    DEFAULT_WINDOW_WIDTH, PANE_WIDTHS_KEY, SASH_WIDTH, WINDOW_WIDTH_KEY,
)


class WindowAppFixture:
    startup = {}
    screen_width = 1920
    measure_defaults = False

    @classmethod
    def setUpClass(cls) -> None:
        sizes = dict(theme._BASE_FONT_SIZES)
        cls.addClassCleanup(cls._restore_sizes, sizes)
        for target, name, value in (
            (app_module.StartupIo, "write_startup", True),
            (app_module.ConfigService, "save_startup", None),
            (App, "winfo_screenwidth", cls.screen_width),
        ):
            patcher = patch.object(target, name, return_value=value)
            mocked = patcher.start()
            cls.addClassCleanup(patcher.stop)
            if name == "write_startup":
                cls.writer = mocked
        if cls.measure_defaults:
            with patch.object(app_module.ConfigService, "load_startup", return_value={}):
                probe = App()
            try:
                probe.update()
                cls.default_desired = probe.pane_layout.desired
                cls.default_trigger_width = probe.full_view.trigger_box.winfo_width()
            finally:
                probe.destroy()
        with patch.object(app_module.ConfigService, "load_startup", return_value=dict(cls.startup)):
            cls.app = App()
        cls.addClassCleanup(cls.app.destroy)
        cls.app.update()

    @staticmethod
    def _restore_sizes(sizes: dict) -> None:
        theme._BASE_FONT_SIZES.clear()
        theme._BASE_FONT_SIZES.update(sizes)


class StartupAssertions:
    expected_width = DEFAULT_WINDOW_WIDTH

    def test_restored_width_without_write(self) -> None:
        self.assertEqual(self.app.winfo_width(), self.expected_width)
        self.writer.assert_not_called()


class SavedWidthStartupTest(StartupAssertions, WindowAppFixture, unittest.TestCase):
    startup = {WINDOW_WIDTH_KEY: 1000}
    expected_width = 1000
    measure_defaults = True

    def test_defaults_use_default_window_basis(self) -> None:
        self.assertEqual(self.app.pane_layout.desired, self.default_desired)
        self.assertEqual(self.app.full_view.trigger_box.winfo_width() - self.default_trigger_width, 220)
        self.writer.assert_not_called()


class ClampedWidthStartupTest(StartupAssertions, WindowAppFixture, unittest.TestCase):
    startup = {WINDOW_WIDTH_KEY: 2000}
    screen_width = 1000
    expected_width = 1000

    def test_close_does_not_overwrite_clamped_width(self) -> None:
        with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True), \
                patch.object(self.app.hook, "begin_shutdown"), \
                patch.object(self.app.hook, "stop_hook"), patch.object(self.app, "destroy") as destroy:
            self.app.on_close()
        self.writer.assert_not_called()
        destroy.assert_called_once_with()


class BoolWidthStartupTest(StartupAssertions, WindowAppFixture, unittest.TestCase):
    startup = {WINDOW_WIDTH_KEY: True}


class StringWidthStartupTest(StartupAssertions, WindowAppFixture, unittest.TestCase):
    startup = {WINDOW_WIDTH_KEY: "900"}


class ZeroWidthStartupTest(StartupAssertions, WindowAppFixture, unittest.TestCase):
    startup = {WINDOW_WIDTH_KEY: 0}


class WindowWidthPersistenceTest(WindowAppFixture, unittest.TestCase):
    def setUp(self) -> None:
        self.layout = self.app.pane_layout
        self.panes = self.app.full_view.panes
        self.saved = (
            self.app.geometry(), self.layout.desired, self.layout._auto_window_width,
            dict(self.app._startup_settings), self.app._full_geometry,
        )
        self.addCleanup(self._restore)
        self.writer.reset_mock(side_effect=True)

    def _restore(self) -> None:
        geometry, desired, auto, startup, full_geometry = self.saved
        self.writer.side_effect = None
        self.layout._cancel_motion()
        self.layout._drag = None
        self.app._compact_mode = False
        self.app._full_geometry = full_geometry
        self.app._startup_settings = startup
        self.layout.desired = desired
        self.app._apply_font_delta(0)
        self.layout.apply_layout()
        self.app.geometry(geometry)
        self.app.update()
        self.layout._auto_window_width = auto

    def _resize(self, extra: int = 220) -> int:
        self.app.geometry(f"{self.app.winfo_width() + extra}x{self.app.winfo_height()}")
        self.app.update()
        return self.app.winfo_width()

    def _close(self, confirm: bool = True) -> Mock:
        trace = Mock()
        trace.attach_mock(self.writer, "write")
        with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=confirm) as ask, \
                patch.object(self.app.hook, "begin_shutdown") as begin, \
                patch.object(self.app.hook, "stop_hook") as stop, \
                patch.object(self.app, "destroy") as destroy, \
                patch.object(self.layout, "window_width_to_save", wraps=self.layout.window_width_to_save) as width:
            for name, mocked in (("confirm", ask), ("width", width), ("begin", begin),
                                 ("stop", stop), ("destroy", destroy)):
                trace.attach_mock(mocked, name)
            self.close_trace = trace
            self.app.on_close()
        return trace

    def test_resized_width_saved_after_stop_before_destroy(self) -> None:
        width = self._resize()
        trace = self._close()
        self.assertEqual(trace.mock_calls, [
            call.confirm("終了"), call.width(), call.begin(), call.stop(),
            call.write({WINDOW_WIDTH_KEY: width}), call.destroy(),
        ])

    def test_unchanged_width_not_saved(self) -> None:
        trace = self._close()
        self.writer.assert_not_called()
        trace.destroy.assert_called_once_with()

    def test_already_saved_width_not_saved(self) -> None:
        self.app._startup_settings[WINDOW_WIDTH_KEY] = self._resize()
        self._close()
        self.writer.assert_not_called()

    def test_zoomed_width_not_saved(self) -> None:
        self._resize()
        with patch.object(self.app, "wm_state", return_value="zoomed"):
            self._close()
        self.writer.assert_not_called()

    def test_cancel_does_not_shutdown_or_save(self) -> None:
        self._resize()
        self.assertEqual(self._close(False).mock_calls, [call.confirm("終了")])

    def test_save_exception_still_destroys(self) -> None:
        self._resize()
        self.writer.side_effect = RuntimeError("save failed")
        with self.assertRaisesRegex(RuntimeError, "save failed"):
            self._close()
        self.assertEqual(self.close_trace.mock_calls[-1], call.destroy())
        self.assertLess(self.close_trace.mock_calls.index(call.stop()),
                        next(i for i, entry in enumerate(self.close_trace.mock_calls) if entry[0] == "write"))

    def test_compact_uses_full_geometry_width(self) -> None:
        width = self._resize()
        self.app._full_geometry = self.app.geometry()
        self.app._compact_mode = True
        self._close()
        self.writer.assert_called_once_with({WINDOW_WIDTH_KEY: width})

    def test_unavailable_or_automatic_compact_width_not_saved(self) -> None:
        self.app._compact_mode = True
        for geometry in (None, "invalid", f"{self.layout._auto_window_width}x820-10+20"):
            with self.subTest(geometry=geometry):
                self.app._full_geometry = geometry
                self.assertIsNone(self.layout.window_width_to_save())

    def test_width_before_initial_layout_not_saved(self) -> None:
        self.layout._auto_window_width = None
        self.assertIsNone(self.layout.window_width_to_save())

    def test_font_growth_is_not_saved(self) -> None:
        self.app.geometry(f"{self.app.wm_minsize()[0]}x{self.app.winfo_height()}")
        self.app.update()
        before = self.app.winfo_width()
        self.app._apply_font_delta(3)
        self.app.update()
        self.assertGreater(self.app.winfo_width(), before)
        self.writer.reset_mock()
        self._close()
        self.writer.assert_not_called()

    def test_font_without_growth_preserves_manual_width(self) -> None:
        width = self._resize(800)
        self.app._apply_font_delta(1)
        self.app.update()
        self.assertEqual(self.app.winfo_width(), width)
        self.writer.reset_mock()
        self._close()
        self.writer.assert_called_once_with({WINDOW_WIDTH_KEY: width})

    def _press(self) -> tuple[int, int]:
        x = self.panes.sash_coord(0)[0] + SASH_WIDTH // 2
        y = self.panes.winfo_height() // 2
        self.panes.event_generate("<Button-1>", x=x, y=y)
        self.assertIsNotNone(self.layout._drag)
        return x, y

    def _drag(self) -> None:
        x, y = self._press()
        self.panes.event_generate("<B1-Motion>", x=x - 10, y=y)
        self.panes.event_generate("<ButtonRelease-1>", x=x - 10, y=y)
        self.app.update()

    def test_drag_includes_manual_window_width_in_one_write(self) -> None:
        width = self._resize()
        self._drag()
        desired = self.layout.desired
        self.writer.assert_called_once_with({
            PANE_WIDTHS_KEY: {"keymap": desired.keymap, "sequence": desired.sequence},
            WINDOW_WIDTH_KEY: width,
        })

    def test_drag_omits_automatic_window_width(self) -> None:
        self._drag()
        self.writer.assert_called_once()
        payload = self.writer.call_args.args[0]
        self.assertIn(PANE_WIDTHS_KEY, payload)
        self.assertNotIn(WINDOW_WIDTH_KEY, payload)

    def test_motion_burst_applies_only_last_position(self) -> None:
        before = self.app.full_view.keymap_box.winfo_width()
        x, y = self._press()
        with patch.object(self.panes, "paneconfigure", wraps=self.panes.paneconfigure) as configure:
            for dx in range(2, 12, 2):
                self.panes.event_generate("<B1-Motion>", x=x - dx, y=y)
            configure.assert_not_called()
            self.app.update_idletasks()
            configure.assert_called_once_with(self.app.full_view.keymap_box, width=before - 10)
        self.assertEqual(self.app.full_view.keymap_box.winfo_width(), before - 10)

    def test_release_flushes_pending_motion(self) -> None:
        before = self.app.full_view.keymap_box.winfo_width()
        self._drag()
        self.assertEqual(self.app.full_view.keymap_box.winfo_width(), before - 10)
        self.assertEqual(self.layout.desired.keymap, before - 10)
        self.assertIsNone(self.layout._motion_id)

    def test_new_non_sash_press_cancels_motion(self) -> None:
        before = self.app.full_view.keymap_box.winfo_width()
        x, y = self._press()
        with patch.object(self.panes, "paneconfigure", wraps=self.panes.paneconfigure) as configure:
            self.panes.event_generate("<B1-Motion>", x=x - 10, y=y)
            self.panes.event_generate("<Button-1>", x=1, y=y)
            self.app.update()
            configure.assert_not_called()
        self.assertEqual(self.app.full_view.keymap_box.winfo_width(), before)
        self.writer.assert_not_called()
