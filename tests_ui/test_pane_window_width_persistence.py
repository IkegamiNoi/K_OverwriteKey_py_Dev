"""ウィンドウ幅の復元・保存とドラッグ間引きを実際の Tk で確認する。"""
import unittest
import tkinter as tk
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from keyseq.presentation import app as app_module, theme
from keyseq.presentation.app import App
from keyseq.presentation.controllers.pane_layout.pane_layout_controller import (
    PaneLayoutController, WINDOW_WIDTH_SAVE_DELAY_MS,
)
from keyseq.presentation.pane_width_rules import (
    DEFAULT_WINDOW_WIDTH, PANE_WIDTHS_KEY, SASH_WIDTH, WINDOW_WIDTH_KEY,
)


class WindowWidthSchedulingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = Mock()
        self.layout = PaneLayoutController(self.app)

    def test_width_burst_leaves_only_last_reservation(self) -> None:
        pending = {}

        def reserve(delay, callback):
            token = f"width-{self.app.after.call_count}"
            pending[token] = callback
            return token

        self.app.after.side_effect = reserve
        self.app.after_cancel.side_effect = pending.pop
        for width in (800, 900, 1000):
            self.layout._on_window_configure(SimpleNamespace(widget=self.app, width=width))
        self.assertEqual(WINDOW_WIDTH_SAVE_DELAY_MS, 500)
        self.assertEqual(self.app.after.call_args_list, [call(500, self.layout._save_window_width)] * 3)
        self.assertEqual(self.app.after_cancel.call_args_list, [call("width-1"), call("width-2")])
        self.assertEqual(list(pending), [self.layout._width_save_id])
        self.app.wm_state.assert_not_called()
        pending.pop(self.layout._width_save_id)()
        self.assertIsNone(self.layout._width_save_id)

    def test_height_or_position_change_does_not_reschedule(self) -> None:
        self.layout._on_window_configure(SimpleNamespace(widget=self.app, width=800, height=600, x=0))
        pending = self.layout._width_save_id
        self.app.after.reset_mock()
        self.layout._on_window_configure(SimpleNamespace(widget=self.app, width=800, height=700, x=20))
        self.app.after.assert_not_called()
        self.app.after_cancel.assert_not_called()
        self.assertEqual(self.layout._width_save_id, pending)

    def test_child_configure_is_ignored(self) -> None:
        self.layout._on_window_configure(SimpleNamespace(widget=Mock(), width=900))
        self.app.after.assert_not_called()
        self.app.after_cancel.assert_not_called()
        self.assertIsNone(self.layout._last_window_width)


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
                probe.pane_layout.cancel_window_width_save()
                probe.destroy()
        with patch.object(app_module.ConfigService, "load_startup", return_value=dict(cls.startup)):
            cls.app = App()
        cls.addClassCleanup(cls.app.destroy)
        cls.addClassCleanup(cls.app.pane_layout.cancel_window_width_save)
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

    def test_save_does_not_overwrite_clamped_width(self) -> None:
        self.app.pane_layout.cancel_window_width_save()
        self.app.pane_layout._save_window_width()
        self.writer.assert_not_called()


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
        self.layout.cancel_window_width_save()

    def _save_width(self) -> None:
        # 実時間を待たずに予約を実行し、Tk 側に古い予約を残さない。
        self.layout.cancel_window_width_save()
        self.layout._save_window_width()
        self.assertIsNone(self.layout._width_save_id)

    def _resize(self, extra: int = 220) -> int:
        self.app.geometry(f"{self.app.winfo_width() + extra}x{self.app.winfo_height()}")
        self.app.update()
        return self.app.winfo_width()

    def _close(self, confirm: bool = True, stop_error: Exception | None = None) -> Mock:
        trace = Mock()
        trace.attach_mock(self.writer, "write")
        with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=confirm) as ask, \
                patch.object(self.app.hook, "begin_shutdown") as begin, \
                patch.object(self.app.hook, "stop_hook", side_effect=stop_error) as stop, \
                patch.object(self.app, "destroy") as destroy, \
                patch.object(self.layout, "cancel_window_width_save",
                             wraps=self.layout.cancel_window_width_save) as cancel:
            for name, mocked in (("confirm", ask), ("cancel", cancel), ("begin", begin),
                                 ("stop", stop), ("destroy", destroy)):
                trace.attach_mock(mocked, name)
            self.close_trace = trace
            self.app.on_close()
        return trace

    def test_close_cancels_pending_save_without_writing(self) -> None:
        self._resize()
        pending = self.layout._width_save_id
        self.assertIsNotNone(pending)
        trace = self._close()
        self.assertEqual(trace.mock_calls, [
            call.confirm("終了"), call.cancel(), call.begin(), call.stop(), call.destroy(),
        ])
        self.assertIsNone(self.layout._width_save_id)
        self.assertNotIn(pending, self.app.tk.call("after", "info"))
        self.writer.assert_not_called()

    def test_resized_width_saved(self) -> None:
        width = self._resize()
        self._save_width()
        self.writer.assert_called_once_with({WINDOW_WIDTH_KEY: width})

    def test_automatic_width_not_saved(self) -> None:
        self._save_width()
        self.writer.assert_not_called()

    def test_already_saved_width_not_saved(self) -> None:
        self.app._startup_settings[WINDOW_WIDTH_KEY] = self._resize()
        self._save_width()
        self.writer.assert_not_called()
        self.assertIsNone(self.layout._auto_window_width)

    def test_non_normal_width_not_saved_or_invalidated(self) -> None:
        auto = self.layout._auto_window_width
        self._resize()
        for state in ("zoomed", "iconic"):
            with self.subTest(state=state), patch.object(self.app, "wm_state", return_value=state):
                self._save_width()
                self.assertEqual(self.layout._auto_window_width, auto)
        self.app.geometry(f"{auto}x{self.app.winfo_height()}")
        self.app.update()
        self._save_width()
        self.writer.assert_not_called()

    def test_cancel_does_not_shutdown_or_save(self) -> None:
        self._resize()
        pending = self.layout._width_save_id
        self.assertIsNotNone(pending)
        self.assertEqual(self._close(False).mock_calls, [call.confirm("終了")])
        self.assertEqual(self.layout._width_save_id, pending)
        self.assertIn(pending, self.app.tk.call("after", "info"))

    def test_stop_exception_still_destroys(self) -> None:
        self._resize()
        with self.assertRaisesRegex(RuntimeError, "stop failed"):
            self._close(stop_error=RuntimeError("stop failed"))
        self.assertEqual(self.close_trace.mock_calls[-1], call.destroy())
        self.assertIsNone(self.layout._width_save_id)
        self.writer.assert_not_called()

    def test_compact_width_not_saved_or_invalidated(self) -> None:
        auto = self.layout._auto_window_width
        self._resize()
        self.app._full_geometry = self.app.geometry()
        self.app._compact_mode = True
        self._save_width()
        self.writer.assert_not_called()
        self.assertEqual(self.layout._auto_window_width, auto)

    def test_width_before_initial_layout_not_saved(self) -> None:
        auto = self.layout._auto_window_width
        self._resize()
        self.layout.desired = None
        self._save_width()
        self.writer.assert_not_called()
        self.assertEqual(self.layout._auto_window_width, auto)

    def test_return_to_original_automatic_width_is_saved(self) -> None:
        auto = self.layout._auto_window_width
        width = self._resize()
        self._save_width()
        self.assertIsNone(self.layout._auto_window_width)
        self.app._startup_settings[WINDOW_WIDTH_KEY] = width
        self.app.geometry(f"{auto}x{self.app.winfo_height()}")
        self.app.update()
        self._save_width()
        self.assertEqual(self.writer.call_args_list, [
            call({WINDOW_WIDTH_KEY: width}), call({WINDOW_WIDTH_KEY: auto}),
        ])

    def test_destroyed_app_does_not_save(self) -> None:
        with patch.object(self.app, "wm_state", side_effect=tk.TclError("destroyed")):
            self._save_width()
        self.writer.assert_not_called()

    def test_font_growth_is_not_saved(self) -> None:
        self.app.geometry(f"{self.app.wm_minsize()[0]}x{self.app.winfo_height()}")
        self.app.update()
        before = self.app.winfo_width()
        self.app._apply_font_delta(3)
        self.app.update()
        self.assertGreater(self.app.winfo_width(), before)
        self.writer.reset_mock()
        self._save_width()
        self.writer.assert_not_called()

    def test_font_without_growth_preserves_manual_width(self) -> None:
        width = self._resize(800)
        self.app._apply_font_delta(1)
        self.app.update()
        self.assertEqual(self.app.winfo_width(), width)
        self.writer.reset_mock()
        self._save_width()
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

    def test_drag_omits_manual_window_width(self) -> None:
        self._resize()
        self._drag()
        desired = self.layout.desired
        self.writer.assert_called_once_with({
            PANE_WIDTHS_KEY: {"keymap": desired.keymap, "sequence": desired.sequence},
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
