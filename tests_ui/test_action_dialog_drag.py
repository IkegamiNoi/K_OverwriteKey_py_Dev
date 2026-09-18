"""ドラッグの入力・生成停止・座標取得 UI を検証する。"""
import unittest
from tkinter import messagebox
from unittest.mock import patch

from pynput import mouse

from keyseq.presentation.app import App
from keyseq.presentation.dialogs.action_dialog import ActionDialog


class ActionDialogDragTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.app.update()
        cls.app.destroy()

    def setUp(self) -> None:
        self.app.update()
        self.app._dialog_result = None
        patcher = patch.object(messagebox, "showerror")
        self.showerror = patcher.start()
        self.addCleanup(patcher.stop)
        for name in ("start", "stop"):
            patcher = patch.object(self.app.hook_coordinator, name)
            patcher.start()
            self.addCleanup(patcher.stop)

    def cleanup_window(self, dialog: ActionDialog) -> None:
        if dialog.winfo_exists():
            dialog.grab_release()
            dialog.destroy()
        self.app.update()

    def make_dialog(self, initial: dict | None = None) -> ActionDialog:
        dialog = ActionDialog(self.app, title="ドラッグ設定", initial=initial)
        self.addCleanup(self.cleanup_window, dialog)
        if initial is None:
            dialog.type_var.set("mouse_click")
            dialog.mouse_x_var.set("100")
            dialog.mouse_y_var.set("200")
            dialog.mouse_btn_var.set("right")
            dialog.mouse_clicks_var.set("3")
            dialog.action_label_var.set("範囲選択")
        dialog._sync_capture_ui()
        return dialog

    def enable_drag(self, dialog: ActionDialog) -> None:
        dialog.mouse_drag_var.set(True)
        dialog.mouse_to_x_var.set("400")
        dialog.mouse_to_y_var.set("500")
        dialog.mouse_drag_speed_var.set("750")
        dialog._sync_drag_ui()

    def test_drag_off_dict(self) -> None:
        dialog = self.make_dialog()
        dialog.on_ok()
        self.assertEqual(self.app._dialog_result, {
            "type": "mouse_click", "x": 100, "y": 200, "button": "right",
            "clicks": 3, "label": "範囲選択",
        })
        self.showerror.assert_not_called()

    def test_drag_on_dict(self) -> None:
        dialog = self.make_dialog()
        self.enable_drag(dialog)
        dialog.on_ok()
        self.assertEqual(self.app._dialog_result, {
            "type": "mouse_click", "x": 100, "y": 200, "button": "right",
            "clicks": 1, "label": "範囲選択", "drag": True,
            "to_x": 400, "to_y": 500, "drag_speed": 750,
        })
        self.showerror.assert_not_called()

    def test_restore_drag_then_save_off(self) -> None:
        initial = {"type": "mouse_click", "x": 100, "y": 200, "button": "right",
                   "clicks": 1, "label": "範囲選択", "drag": True,
                   "to_x": 400, "to_y": 500, "drag_speed": 750}
        dialog = self.make_dialog(initial)
        self.assertTrue(dialog.mouse_drag_var.get())
        for variable, expected in (
            (dialog.mouse_x_var, "100"), (dialog.mouse_y_var, "200"),
            (dialog.mouse_to_x_var, "400"), (dialog.mouse_to_y_var, "500"),
            (dialog.mouse_drag_speed_var, "750"), (dialog.mouse_btn_var, "right"),
            (dialog.mouse_clicks_var, "1"), (dialog.action_label_var, "範囲選択"),
        ):
            self.assertEqual(variable.get(), expected)
        dialog.mouse_drag_var.set(False)
        dialog._sync_drag_ui()
        dialog.on_ok()
        self.assertEqual(self.app._dialog_result, {
            "type": "mouse_click", "x": 100, "y": 200, "button": "right",
            "clicks": 1, "label": "範囲選択",
        })
        self.assertTrue(initial["drag"])

    def test_release_coordinates_required_and_integer(self) -> None:
        for x, y in (("", "500"), ("400", ""), ("abc", "500"), ("400", "abc")):
            with self.subTest(x=x, y=y):
                dialog = self.make_dialog()
                self.enable_drag(dialog)
                dialog.mouse_to_x_var.set(x)
                dialog.mouse_to_y_var.set(y)
                self.showerror.reset_mock()
                dialog.on_ok()
                self.showerror.assert_called_once()
                self.assertEqual(self.showerror.call_args.args[0], "入力エラー")
                self.assertIsNone(self.app._dialog_result)
                self.assertTrue(dialog.winfo_exists())
                self.cleanup_window(dialog)

    def test_invalid_speed_uses_default(self) -> None:
        for speed in ("", "abc", "0", "-1"):
            with self.subTest(speed=speed):
                dialog = self.make_dialog()
                self.enable_drag(dialog)
                dialog.mouse_drag_speed_var.set(speed)
                dialog.on_ok()
                self.assertEqual(self.app._dialog_result["drag_speed"], 1000)
        self.showerror.assert_not_called()

    def test_drag_ui_toggle(self) -> None:
        dialog = self.make_dialog()
        self.assertEqual(dialog.mouse_drag_speed_var.get(), "1000")
        for enabled in (True, False):
            dialog.mouse_drag_var.set(enabled)
            dialog._sync_drag_ui()
            self.assertEqual(str(dialog.mouse_clicks_entry.cget("state")),
                             "disabled" if enabled else "normal")
            self.assertEqual(dialog.mouse_x_label.cget("text"), "掴む位置 X" if enabled else "X")
            self.assertEqual(dialog.mouse_y_label.cget("text"), "掴む位置 Y" if enabled else "Y")
            for widget in dialog._drag_widgets:
                self.assertEqual(bool(widget.grid_info()), enabled)

    def test_coordinate_capture_is_exclusive_and_restores_buttons(self) -> None:
        dialog = self.make_dialog()
        self.enable_drag(dialog)
        for target in ("start", "end"):
            with self.subTest(target=target), patch.object(mouse, "Listener") as listener:
                button = dialog.mouse_capture_btn if target == "start" else dialog.mouse_to_capture_btn
                button.invoke()
                for capture_button in (dialog.mouse_capture_btn, dialog.mouse_to_capture_btn):
                    self.assertTrue(capture_button.instate(["disabled"]))
                    capture_button.invoke()
                listener.assert_called_once()
                self.assertTrue(listener.return_value.daemon)
                listener.return_value.start.assert_called_once_with()
                on_click = listener.call_args.kwargs["on_click"]
                self.assertTrue(on_click(12, 34, mouse.Button.left, False))
                self.assertFalse(on_click(12, 34, mouse.Button.left, True))
                self.app.update()
                for capture_button in (dialog.mouse_capture_btn, dialog.mouse_to_capture_btn):
                    self.assertEqual(str(capture_button.cget("state")), "normal")
                x_var, y_var = ((dialog.mouse_x_var, dialog.mouse_y_var) if target == "start"
                                else (dialog.mouse_to_x_var, dialog.mouse_to_y_var))
                self.assertEqual((x_var.get(), y_var.get()), ("12", "34"))


if __name__ == "__main__":
    unittest.main()
