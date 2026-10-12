"""偽の画面・入力を使い、実際の Tk 窓と予約済み操作を確認する。"""
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.input_router import GridKeyAction, InputRoute
from keyseq.application.keymap_service import KeymapService
from keyseq.presentation.controllers.hook_controller import HookController
from keyseq.presentation.controllers.layout_controller import LayoutController
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
        self.assertIn("クリック透過", self.app._set_flash_message.call_args.args[0])

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
        self.app.input_gateway.move_cursor.side_effect = None
        self.execute(key)
        self.app.input_gateway.click_at.side_effect = RuntimeError("click failed")
        with self.assertLogs("keyseq.presentation.screen_grid.screen_grid_controller", "ERROR"):
            self.execute("enter")
        self.assertIn("click failed", self.app._set_flash_message.call_args.args[0])
        self.monitors.side_effect = RuntimeError("enumeration failed")
        with self.assertLogs("keyseq.presentation.screen_grid.screen_grid_controller", "ERROR"):
            self.execute("tab")
        self.assertIn("enumeration failed", self.app._set_flash_message.call_args.args[0])
        self.assertTrue(self.app.hook.hook_active)

    def test_layout_refresh_during_startup_without_screen_grid(self):
        layout = LayoutController.__new__(LayoutController)
        layout._app = SimpleNamespace()
        layout.keyboard_window = None
        layout.refresh_keyboard_window()


if __name__ == "__main__":
    unittest.main()
