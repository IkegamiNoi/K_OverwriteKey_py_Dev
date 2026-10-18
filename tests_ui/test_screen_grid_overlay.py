"""偽の画面・入力を使い、実際の Tk 窓と予約済み操作を確認する。"""
import tkinter as tk
from tkinter import font as tkfont
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.input_router import GridKeyAction, InputRoute
from keyseq.application.keymap_service import KeymapService
from keyseq.presentation.controllers.hook_controller import HookController
from keyseq.presentation.controllers.layout_controller import LayoutController
from keyseq.presentation.screen_grid.cell_label import draw_cell_label
from keyseq.presentation.screen_grid.crosshair import draw_crosshair
from keyseq.presentation.screen_grid import ScreenGridController


class ScreenGridOverlayTest(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        monitors_patch = patch(
            "keyseq.presentation.screen_grid.screen_grid_controller."
            "win32_window.list_monitor_rects",
            return_value=[((0, -768, 1024, 0), True)],
        )
        self.monitors = monitors_patch.start()
        self.addCleanup(monitors_patch.stop)
        styles_patch = patch(
            "keyseq.presentation.screen_grid.grid_overlay_window."
            "win32_window.make_click_through_overlay", return_value=True,
        )
        self.styles = styles_patch.start()
        self.addCleanup(styles_patch.stop)
        self.app = SimpleNamespace(
            after=self.root.after,
            input_gateway=SimpleNamespace(
                cursor_position=Mock(return_value=(100, -600)),
                move_cursor=Mock(), click_at=Mock(),
            ),
            keymap_service=KeymapService(),
            data={"active_keymap_id": "on", "keymaps": [
                {"id": "on", "grid": {"enabled": True}}, {"id": "off"},
                {"id": "other", "grid": {"enabled": True}},
            ]},
            _set_flash_message=Mock(), action_executor=Mock(),
        )
        # Toplevel の親は実際の Tk。コントローラの入力だけ偽物へ差し替える。
        self.root.input_gateway = self.app.input_gateway
        self.root.keymap_service = self.app.keymap_service
        self.root.data = self.app.data
        self.root._set_flash_message = self.app._set_flash_message
        self.app.hook = HookController(self.app)
        self.root.hook = self.app.hook
        self.app.screen_grid = ScreenGridController(self.root)
        self.addCleanup(self.app.screen_grid.shutdown)
        self.layout = LayoutController.__new__(LayoutController)
        self.layout._app = self.app
        self.layout.keyboard_window = None
        self.app.hook.hook_active = True

    def sync(self):
        self.layout.refresh_keyboard_window()
        self.root.update_idletasks()

    def execute(self, key, *, shift=False, generation=None):
        if generation is None:
            generation = self.app.screen_grid.snapshot().generation
        action = GridKeyAction(key, generation, shift, False)
        self.app.hook._execute_reserved_action(action, ())

    def assert_hidden(self):
        window = self.app.screen_grid._overlay._window
        self.assertTrue(window is None or window.state() == "withdrawn")

    def test_lazy_creation_and_visibility_conditions(self):
        overlay = self.app.screen_grid._overlay
        self.app.data["active_keymap_id"] = "off"
        self.sync()
        self.assertIsNone(overlay._window)
        self.styles.assert_not_called()
        self.app.data["active_keymap_id"] = "on"
        self.sync()
        window = overlay._window
        self.assertEqual(window.state(), "normal")
        self.assertEqual((window.winfo_rootx(), window.winfo_rooty()), (0, -768))
        self.assertEqual((window.winfo_width(), window.winfo_height()), (1024, 768))
        self.styles.assert_called_once_with(window.winfo_id())
        self.assertEqual(len(self.app.screen_grid.session.view().cells), 12)
        for field, value, restored in (
            ("hook_active", False, True),
            ("custom_input_enabled", False, True),
            ("hook_suspend_count", 1, 0),
        ):
            with self.subTest(field=field):
                setattr(self.app.hook, field, value)
                self.sync()
                self.assert_hidden()
                self.assertFalse(self.app.screen_grid.snapshot().visible)
                setattr(self.app.hook, field, restored)
                self.sync()
                self.assertIs(overlay._window, window)
                self.assertEqual(window.state(), "normal")
        self.app.data["active_keymap_id"] = "off"
        self.sync()
        self.assert_hidden()

    def test_grid_actions_move_subdivide_and_click(self):
        self.sync()
        view = self.app.screen_grid.session.view()
        rect, key = view.cells[0]
        center = ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)
        self.execute(key)
        self.app.input_gateway.move_cursor.assert_called_once_with(*center)
        self.assertEqual(self.app.screen_grid.session.view().selected, 0)
        self.execute("space")
        self.assertEqual(self.app.screen_grid.session.view().level, 1)
        canvas = self.app.screen_grid._overlay._canvas
        shades = [item for item in canvas.find_all()
                  if canvas.type(item) == "rectangle" and canvas.itemcget(item, "stipple")]
        self.assertTrue(shades)
        self.execute("enter", shift=True)
        self.app.input_gateway.click_at.assert_called_once_with(*center, "right")
        self.assertEqual(self.app.screen_grid.session.view().level, 0)
        self.execute(key)
        self.execute("enter")
        self.assertEqual(self.app.input_gateway.click_at.call_args.args, (*center, "left"))
        self.app.action_executor.execute_router_action.assert_not_called()

    def test_style_is_applied_while_window_is_withdrawn_and_failure_is_reported(self):
        def fail_style(widget_id):
            window = self.root.winfo_children()[0]
            self.assertEqual(window.winfo_id(), widget_id)
            self.assertEqual(window.state(), "withdrawn")
            self.assertTrue(window.overrideredirect())
            self.assertEqual(str(window.cget("background")), "#ff00fe")
            self.assertEqual(str(window.attributes("-transparentcolor")), "#ff00fe")
            return False

        self.styles.side_effect = fail_style
        with self.assertLogs("keyseq.presentation.screen_grid.screen_grid_controller", "ERROR"):
            self.sync()
        self.assertIsNone(self.app.screen_grid._overlay._window)
        self.assertEqual(self.root.winfo_children(), [])
        self.assertFalse(self.app.screen_grid.snapshot().visible)
        self.assertFalse(self.app.screen_grid.snapshot().suppress_keys)
        self.assertIn("クリック透過", self.app._set_flash_message.call_args.args[0])
        self.assertEqual(self.app._set_flash_message.call_count, 1)

        self.sync()
        self.assertEqual(self.styles.call_count, 1)
        self.assertEqual(self.app._set_flash_message.call_count, 1)

        self.app.hook.hook_active = False
        self.sync()
        self.app.hook.hook_active = True
        self.sync()
        self.assertEqual(self.styles.call_count, 2)
        self.assertEqual(self.app._set_flash_message.call_count, 2)

    def test_stopped_paused_and_old_generation_actions_are_ignored(self):
        self.sync()
        view = self.app.screen_grid.session.view()
        key = view.cells[0][1]
        for field in ("hook_active", "custom_input_enabled"):
            with self.subTest(field=field):
                setattr(self.app.hook, field, False)
                self.execute(key)
                setattr(self.app.hook, field, True)
        self.app.hook.hook_suspend_count = 1
        self.sync()
        self.execute(key)
        self.app.hook.hook_suspend_count = 0
        self.app.data["active_keymap_id"] = "other"
        self.sync()
        self.execute(key, generation=view.generation)
        self.app.input_gateway.move_cursor.assert_not_called()
        self.app.input_gateway.click_at.assert_not_called()
        self.app.action_executor.execute_router_action.assert_not_called()

    def test_empty_monitors_leave_window_uncreated(self):
        self.monitors.return_value = []
        self.sync()
        self.assert_hidden()
        self.assertIsNone(self.app.screen_grid._overlay._window)
        self.execute("tab")
        self.execute("enter")
        self.app.input_gateway.click_at.assert_not_called()
        self.app._set_flash_message.assert_not_called()

    def test_top_left_cell_label_uses_ui_named_font_and_inset(self):
        canvas = Mock()
        ui_font = tkfont.nametofont("TkDefaultFont", root=self.root)

        draw_cell_label(
            canvas, (10, 20, 120, 60), "a", position="top_left", fill="white",
            center_font=ui_font, corner_font=ui_font,
        )

        canvas.create_text.assert_called_once()
        args, kwargs = canvas.create_text.call_args
        self.assertEqual(args, (13, 22))
        self.assertEqual(kwargs["anchor"], "nw")
        self.assertIs(kwargs["font"], ui_font)
        self.assertEqual(ui_font.name, "TkDefaultFont")

    def test_draw_crosshair_uses_two_clipped_arms_and_fixed_style(self):
        canvas = Mock()

        draw_crosshair(canvas, (10, 20, 40, 50), (25, 35), fill="#ffcc66")

        self.assertEqual(canvas.create_line.call_count, 2)
        self.assertEqual(canvas.create_line.call_args_list[0].args, (13, 35, 37, 35))
        self.assertEqual(canvas.create_line.call_args_list[1].args, (25, 23, 25, 47))
        for call in canvas.create_line.call_args_list:
            self.assertEqual(call.kwargs["fill"], "#ffcc66")
            self.assertEqual(call.kwargs["width"], 2)
            self.assertEqual(call.kwargs["tags"], "crosshair")

    def test_draw_crosshair_clips_arms_at_nearby_cell_edges(self):
        canvas = Mock()

        draw_crosshair(canvas, (10, 20, 30, 40), (11, 21), fill="gold")

        self.assertEqual(canvas.create_line.call_args_list[0].args, (10, 21, 23, 21))
        self.assertEqual(canvas.create_line.call_args_list[1].args, (11, 20, 11, 33))

    def test_draw_crosshair_skips_zero_length_arms(self):
        canvas = Mock()

        draw_crosshair(canvas, (10, 20, 10, 40), (10, 30), fill="gold")
        self.assertEqual(canvas.create_line.call_count, 1)
        self.assertEqual(canvas.create_line.call_args.args, (10, 20, 10, 39))

        canvas = Mock()
        draw_crosshair(canvas, (10, 20, 40, 20), (25, 20), fill="gold")
        self.assertEqual(canvas.create_line.call_count, 1)
        self.assertEqual(canvas.create_line.call_args.args, (13, 20, 37, 20))

    def test_font_change_redraws_visible_overlay(self):
        with patch.object(self.app.screen_grid, "_show_view") as show:
            self.app.screen_grid.on_font_changed()
        show.assert_called_once_with()

    def test_font_change_view_error_is_reported_and_does_not_escape(self):
        self.sync()
        self.assertTrue(self.app.screen_grid.snapshot().visible)
        error = RuntimeError("redraw failed")
        with patch.object(self.app.screen_grid, "_show_view", side_effect=error), patch.object(
            self.app.screen_grid, "_report_error"
        ) as report:
            self.app.screen_grid.on_font_changed()
        report.assert_called_once_with(error)
        self.assertFalse(self.app.screen_grid.snapshot().visible)

    def test_corner_label_font_is_ui_named_font(self):
        from keyseq.presentation.screen_grid.cell_label import corner_label_font

        self.assertEqual(corner_label_font(self.root).name, "TkDefaultFont")

    def test_top_left_label_has_dark_backing_and_center_has_none(self):
        from keyseq.presentation.screen_grid.cell_label import LABEL_BACKING

        ui_font = tkfont.nametofont("TkDefaultFont", root=self.root)
        width, height = ui_font.measure("a"), ui_font.metrics("linespace")
        canvas = Mock()
        calls = []
        canvas.create_rectangle.side_effect = lambda *a, **k: calls.append("rect")
        canvas.create_text.side_effect = lambda *a, **k: calls.append("text")
        draw_cell_label(canvas, (10, 20, 120, 60), "a", position="top_left", fill="white",
                        center_font=ui_font, corner_font=ui_font)
        self.assertEqual(calls, ["rect", "text"])
        args, kwargs = canvas.create_rectangle.call_args
        self.assertEqual(args, (11, 21, 13 + width + 2, 22 + height + 1))
        self.assertEqual(kwargs["fill"], LABEL_BACKING)

        canvas = Mock()
        draw_cell_label(canvas, (10, 20, 120, 60), "a", position="center", fill="white",
                        center_font=ui_font, corner_font=ui_font)
        canvas.create_rectangle.assert_not_called()
        self.assertEqual(canvas.create_text.call_args.args, (65, 40))
        self.assertEqual(canvas.create_text.call_args.kwargs["anchor"], "center")

    def test_cell_label_that_exceeds_small_cell_is_not_drawn(self):
        key = "a very long key name that cannot fit"
        ui_font = tkfont.nametofont("TkDefaultFont", root=self.root)
        rect = (0, 0, ui_font.measure(key) + 7, ui_font.metrics("linespace") + 9)

        for position in ("center", "top_left"):
            with self.subTest(position=position):
                canvas = Mock()
                draw_cell_label(
                    canvas, rect, key, position=position, fill="white",
                    center_font=ui_font, corner_font=ui_font,
                )
                canvas.create_text.assert_not_called()

    def test_cell_label_that_exceeds_cell_height_is_not_drawn(self):
        key = "a"
        ui_font = tkfont.nametofont("TkDefaultFont", root=self.root)
        rect = (0, 0, ui_font.measure(key) + 9, ui_font.metrics("linespace") + 7)

        for position in ("center", "top_left"):
            with self.subTest(position=position):
                canvas = Mock()
                draw_cell_label(
                    canvas, rect, key, position=position, fill="white",
                    center_font=ui_font, corner_font=ui_font,
                )
                canvas.create_text.assert_not_called()

    def test_overlay_draw_uses_top_left_label_position_on_real_canvas(self):
        self.app.data["keymaps"][0]["grid"]["label_position"] = "top_left"
        self.sync()
        view = self.app.screen_grid.session.view()
        canvas = self.app.screen_grid._overlay._canvas
        text_item = next(
            item for item in canvas.find_all() if canvas.type(item) == "text"
        )
        first_rect, first_key = view.cells[0]
        left, top, _right, _bottom = view.monitor.rect

        self.assertEqual(view.label_position, "top_left")
        self.assertEqual(canvas.itemcget(text_item, "text"), first_key)
        self.assertEqual(canvas.itemcget(text_item, "anchor"), "nw")
        self.assertEqual(
            tuple(canvas.coords(text_item)),
            (first_rect[0] - left + 3, first_rect[1] - top + 2),
        )

    def test_overlay_crosshair_tracks_selection_and_nudges_on_real_canvas(self):
        self.sync()
        overlay = self.app.screen_grid._overlay
        canvas = overlay._canvas
        self.assertEqual(canvas.find_withtag("crosshair"), ())

        view = self.app.screen_grid.session.view()
        self.execute(view.cells[0][1])
        view = self.app.screen_grid.session.view()
        crosshair = canvas.find_withtag("crosshair")
        self.assertEqual(len(crosshair), 2)
        left, top, _right, _bottom = view.monitor.rect
        point = (view.click_point[0] - left, view.click_point[1] - top)
        lines = [tuple(canvas.coords(item)) for item in crosshair]
        self.assertTrue(any(line[1] == point[1] and line[3] == point[1] for line in lines))
        self.assertTrue(any(line[0] == point[0] and line[2] == point[0] for line in lines))

        before = lines
        self.execute("right")
        view = self.app.screen_grid.session.view()
        crosshair = canvas.find_withtag("crosshair")
        after = [tuple(canvas.coords(item)) for item in crosshair]
        dx = view.click_point[0] - left - point[0]
        dy = view.click_point[1] - top - point[1]
        self.assertEqual(len(crosshair), 2)
        self.assertEqual(after, [
            (line[0] + dx, line[1] + dy, line[2] + dx, line[3] + dy)
            for line in before
        ])

    def test_selected_center_label_is_replaced_but_top_left_label_remains(self):
        self.sync()
        view = self.app.screen_grid.session.view()
        selected_key = view.cells[0][1]
        other_key = view.cells[1][1]
        self.execute(selected_key)
        canvas = self.app.screen_grid._overlay._canvas
        texts = [canvas.itemcget(item, "text") for item in canvas.find_all()
                 if canvas.type(item) == "text"]
        self.assertNotIn(selected_key, texts)
        self.assertIn(other_key, texts)

        self.app.data["keymaps"][0]["grid"]["label_position"] = "top_left"
        self.sync()
        texts = [canvas.itemcget(item, "text") for item in canvas.find_all()
                 if canvas.type(item) == "text"]
        self.assertIn(selected_key, texts)

    def test_enter_clears_crosshair_after_selected_click(self):
        self.sync()
        view = self.app.screen_grid.session.view()
        self.execute(view.cells[0][1])
        canvas = self.app.screen_grid._overlay._canvas
        self.assertEqual(len(canvas.find_withtag("crosshair")), 2)

        self.execute("enter")

        view = self.app.screen_grid.session.view()
        self.assertIsNone(view.selected)
        self.assertIsNone(view.click_point)
        self.assertEqual(canvas.find_withtag("crosshair"), ())

    def test_snapshot_does_not_touch_tk(self):
        self.sync()
        with patch.object(self.app.screen_grid._overlay, "show") as show:
            snapshot = self.app.screen_grid.snapshot()
        self.assertTrue(snapshot.visible)
        show.assert_not_called()

    def test_reserved_grid_action_runs_via_after(self):
        self.sync()
        view = self.app.screen_grid.session.view()
        action = GridKeyAction(view.cells[0][1], view.generation, False, False)
        self.app.layout = SimpleNamespace(
            resolve_key_name_from_scan_code=Mock(return_value=action.key),
            should_debug_special_key_event=Mock(return_value=False),
        )
        self.app.input_router = Mock()
        self.app.input_router.handle.return_value = InputRoute(actions=(action,), accept=False)
        self.app.make_only_keys = SimpleNamespace(handle=Mock(return_value=None))
        self.assertFalse(self.app.hook.on_input_event(SimpleNamespace(scan_code=1)))
        self.app.input_gateway.move_cursor.assert_not_called()
        self.root.update()
        self.app.input_gateway.move_cursor.assert_called_once()

    def test_input_and_enumeration_errors_are_reported_without_stopping_hook(self):
        self.sync()
        key = self.app.screen_grid.session.view().cells[0][1]
        self.app.input_gateway.move_cursor.side_effect = RuntimeError("move failed")
        with self.assertLogs("keyseq.presentation.screen_grid.screen_grid_controller", "ERROR"):
            self.execute(key)
        self.assertIn("move failed", self.app._set_flash_message.call_args.args[0])
        # 失敗すると枠は畳まれ（suppress しない）、表示の条件が一度偽になるまで出し直さない（task_07 M2）。
        self.assertFalse(self.app.screen_grid.snapshot().visible)
        self.app.input_gateway.move_cursor.side_effect = None
        self._reshow()
        self.execute(key)
        self.app.input_gateway.click_at.side_effect = RuntimeError("click failed")
        with self.assertLogs("keyseq.presentation.screen_grid.screen_grid_controller", "ERROR"):
            self.execute("enter")
        self.assertIn("click failed", self.app._set_flash_message.call_args.args[0])
        self.assertFalse(self.app.screen_grid.snapshot().visible)
        self._reshow()
        self.monitors.side_effect = RuntimeError("enumeration failed")
        with self.assertLogs("keyseq.presentation.screen_grid.screen_grid_controller", "ERROR"):
            self.execute("tab")
        self.assertIn("enumeration failed", self.app._set_flash_message.call_args.args[0])
        self.assertFalse(self.app.screen_grid.snapshot().visible)
        self.assertTrue(self.app.hook.hook_active)

    def test_empty_monitor_refresh_aborts_once_until_visibility_condition_turns_off(self):
        self.sync()
        self.assertTrue(self.app.screen_grid.snapshot().visible)
        self.monitors.return_value = []

        with self.assertLogs("keyseq.presentation.screen_grid.screen_grid_controller", "ERROR"):
            self.execute("tab")

        snapshot = self.app.screen_grid.snapshot()
        self.assertFalse(snapshot.visible)
        self.assertFalse(snapshot.suppress_keys)
        self.assertFalse(self.app.screen_grid.session.view().visible)
        self.assertEqual(self.app._set_flash_message.call_count, 1)
        self.assertIn("画面（モニタ）を取得できませんでした", self.app._set_flash_message.call_args.args[0])
        self.assertTrue(self.app.hook.hook_active)
        self.sync()
        self.assertFalse(self.app.screen_grid.snapshot().visible)
        self.assertEqual(self.app._set_flash_message.call_count, 1)

        self.app.hook.hook_active = False
        self.sync()
        self.monitors.return_value = [((0, -768, 1024, 0), True)]
        self.app.hook.hook_active = True
        self.sync()
        self.assertTrue(self.app.screen_grid.snapshot().visible)
        self.assertEqual(self.app._set_flash_message.call_count, 1)

    def _reshow(self):
        self.sync()
        self.assertFalse(self.app.screen_grid.snapshot().visible)
        self.app.hook.hook_active = False
        self.sync()
        self.app.hook.hook_active = True
        self.sync()
        self.assertTrue(self.app.screen_grid.snapshot().visible)

    def test_layout_refresh_during_startup_without_screen_grid(self):
        layout = LayoutController.__new__(LayoutController)
        layout._app = SimpleNamespace()
        layout.keyboard_window = None
        layout.refresh_keyboard_window()


if __name__ == "__main__":
    unittest.main()
