"""key_hold 編集欄の作成・編集・検証。実際のキーやマウスは操作しない。"""
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tkinter import messagebox

from keyseq.presentation.dialogs.action_dialog import ActionDialog
from tests_ui.escape_delivery import acquire_focus


class FakeInputGateway:
    def __init__(self) -> None:
        self.validated: list[str] = []
        self.invalid_names: set[str] = set()

    def validate_key_name(self, key_name: str) -> None:
        self.validated.append(key_name)
        if key_name in self.invalid_names:
            raise ValueError("unknown key")


class ActionDialogKeyHoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Tk はクラスで 1 つだけ作る（テストごとに作り直すと、後のモジュールのフォーカスが取れなくなる）。
        cls.root = tk.Tk()
        cls.root.update_idletasks()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        self.root.hook = SimpleNamespace(suspend_hook_for_dialog=Mock())
        self.root.config_service = Mock()
        self.root.data = {"hotkey_presets": []}
        self.root.input_gateway = FakeInputGateway()
        self.root._dialog_result = None
        self.showerror_patcher = patch.object(messagebox, "showerror")
        self.showerror = self.showerror_patcher.start()
        self.addCleanup(self.showerror_patcher.stop)
        self.dialogs: list[ActionDialog] = []
        self.addCleanup(self.cleanup_windows)

    def cleanup_windows(self) -> None:
        for dialog in self.dialogs:
            if dialog.winfo_exists():
                dialog.grab_release()
                dialog.destroy()
        self.root.update()

    def make_dialog(self, initial: dict | None = None, mode: str | None = "add") -> ActionDialog:
        dialog = ActionDialog(self.root, "アクション", initial=initial, mode=mode)
        self.dialogs.append(dialog)
        self.root.update_idletasks()
        return dialog

    def test_key_action_records_one_tk_key_and_builds_down_action(self) -> None:
        dialog = self.make_dialog(mode=None)
        self.assertIn("key_hold", dialog.type_combo.cget("values"))
        dialog.type_var.set("key_hold")
        dialog._sync_capture_ui()
        fields = dialog.key_hold_fields
        fields.start_recording()
        # Tk へ渡るイベントを直接渡す。OS のキー入力は送らない。
        fields._on_key_press(SimpleNamespace(keysym="Shift_L"))
        self.assertFalse(fields.recording)
        self.assertEqual(fields.key_var.get(), "left shift")
        dialog.action_label_var.set("selection")
        dialog.on_ok()
        self.assertEqual(self.root._dialog_result, {
            "type": "key_hold", "edge": "down", "value": "left shift", "label": "selection",
        })
        self.assertEqual(self.root.input_gateway.validated, ["left shift"])

    def test_key_hold_recording_preserves_modifier_sides(self) -> None:
        cases = (
            ("Control_R", "right ctrl"),
            ("Shift_R", "right shift"),
            ("Alt_L", "left alt"),
            ("Alt_R", "right alt"),
            ("Control_L", "left ctrl"),
            ("Shift_L", "left shift"),
            ("Super_L", "left windows"),
            ("Win_R", "right windows"),
        )
        for keysym, expected in cases:
            with self.subTest(keysym=keysym):
                dialog = self.make_dialog(mode=None)
                fields = dialog.key_hold_fields
                fields.start_recording()
                fields._on_key_press(SimpleNamespace(keysym=keysym))
                self.assertEqual(fields.key_var.get(), expected)
                dialog.type_var.set("key_hold")
                dialog.on_ok()
                self.assertEqual(self.root._dialog_result["value"], expected)
                self.assertEqual(self.root.input_gateway.validated[-1], expected)

    def test_key_hold_is_available_in_every_dialog_context(self) -> None:
        for mode in (None, "add", "edit"):
            with self.subTest(mode=mode):
                dialog = self.make_dialog(mode=mode)
                self.assertIn("key_hold", dialog.type_combo.cget("values"))

    def test_escape_stops_key_recording_without_closing_or_recording_escape(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("key_hold")
        dialog._sync_capture_ui()
        fields = dialog.key_hold_fields
        fields.start_recording()
        acquire_focus(self.root, dialog)  # Escape はフォーカスのある窓へ届くため
        dialog.event_generate("<Escape>")
        dialog.update()
        self.assertTrue(dialog.winfo_exists())
        self.assertFalse(fields.recording)
        self.assertEqual(fields.key_var.get(), "")

    def test_mouse_default_button_is_left(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("key_hold")
        dialog._sync_capture_ui()
        fields = dialog.key_hold_fields
        fields.target_var.set("マウスのボタン")
        fields.sync_target()
        self.assertEqual(fields.button_var.get(), "左")
        dialog.on_ok()
        self.assertEqual(self.root._dialog_result["button"], "left")

    def test_mouse_capture_button_passes_its_coordinate_controls(self) -> None:
        capture = Mock()
        with patch.object(ActionDialog, "_capture_mouse_position", new=lambda _self, *args: capture(*args)):
            dialog = self.make_dialog()
        dialog.type_var.set("key_hold")
        dialog._sync_capture_ui()
        fields = dialog.key_hold_fields
        fields.target_var.set("マウスのボタン")
        fields.sync_target()
        fields.coordinates_var.set(True)
        fields.sync_coordinates()
        fields.capture_button.invoke()
        capture.assert_called_once_with(
            fields.x_var, fields.y_var, fields.capture_button, fields.capture_hint,
        )

    def test_changing_target_stops_key_recording(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("key_hold")
        dialog._sync_capture_ui()
        fields = dialog.key_hold_fields
        fields.start_recording()
        fields.target_var.set("マウスのボタン")
        fields.sync_target()
        self.assertFalse(fields.recording)

    def test_mouse_action_without_coordinates(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("key_hold")
        dialog._sync_capture_ui()
        fields = dialog.key_hold_fields
        fields.target_var.set("マウスのボタン")
        fields.sync_target()
        fields.edge_var.set("離す")
        fields.button_var.set("右")
        dialog.action_label_var.set("release right")
        dialog.on_ok()
        self.assertEqual(self.root._dialog_result, {
            "type": "key_hold", "edge": "up", "button": "right", "label": "release right",
        })

    def test_mouse_action_with_coordinates(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("key_hold")
        dialog._sync_capture_ui()
        fields = dialog.key_hold_fields
        fields.target_var.set("マウスのボタン")
        fields.sync_target()
        fields.button_var.set("中")
        fields.coordinates_var.set(True)
        fields.sync_coordinates()
        fields.x_var.set("100")
        fields.y_var.set("200")
        dialog.on_ok()
        self.assertEqual(self.root._dialog_result, {
            "type": "key_hold", "edge": "down", "button": "middle",
            "x": 100, "y": 200, "label": "",
        })

    def test_edit_loads_key_mouse_and_coordinates(self) -> None:
        key_dialog = self.make_dialog({
            "type": "key_hold", "edge": "up", "value": "CTRL", "label": "key label",
        }, mode="edit")
        self.assertEqual(key_dialog.key_hold_fields.edge_var.get(), "離す")
        self.assertEqual(key_dialog.key_hold_fields.key_var.get(), "CTRL")
        key_dialog.on_ok()
        self.assertEqual(self.root._dialog_result, {
            "type": "key_hold", "edge": "up", "value": "ctrl", "label": "key label",
        })

        mouse_dialog = self.make_dialog({
            "type": "key_hold", "edge": "down", "button": "left", "x": 30, "y": 40,
        }, mode="edit")
        fields = mouse_dialog.key_hold_fields
        self.assertEqual(fields.target_var.get(), "マウスのボタン")
        self.assertEqual(fields.button_var.get(), "左")
        self.assertTrue(fields.coordinates_var.get())
        self.assertEqual((fields.x_var.get(), fields.y_var.get()), ("30", "40"))
        mouse_dialog.on_ok()
        self.assertEqual(self.root._dialog_result, {
            "type": "key_hold", "edge": "down", "button": "left",
            "x": 30, "y": 40, "label": "",
        })

    def test_invalid_key_name_and_incomplete_coordinates_keep_dialog_open(self) -> None:
        invalid_key = self.make_dialog()
        invalid_key.type_var.set("key_hold")
        invalid_key._sync_capture_ui()
        invalid_key.key_hold_fields.key_var.set("not-a-key")
        self.root.input_gateway.invalid_names.add("not-a-key")
        invalid_key.on_ok()
        self.assertTrue(invalid_key.winfo_exists())
        self.assertIn("キー名が不正です", self.showerror.call_args.args[1])

        incomplete = self.make_dialog()
        incomplete.type_var.set("key_hold")
        incomplete._sync_capture_ui()
        fields = incomplete.key_hold_fields
        fields.target_var.set("マウスのボタン")
        fields.sync_target()
        fields.coordinates_var.set(True)
        fields.sync_coordinates()
        fields.x_var.set("10")
        incomplete.on_ok()
        self.assertTrue(incomplete.winfo_exists())
        self.assertIn("X/Y は両方", self.showerror.call_args.args[1])

    def test_empty_composite_key_and_invalid_coordinates_are_rejected(self) -> None:
        for value in ("", "ctrl+shift", "a,b"):
            with self.subTest(value=value):
                dialog = self.make_dialog()
                dialog.type_var.set("key_hold")
                dialog._sync_capture_ui()
                dialog.key_hold_fields.key_var.set(value)
                dialog.on_ok()
                self.assertTrue(dialog.winfo_exists())
        invalid_coordinates = self.make_dialog()
        invalid_coordinates.type_var.set("key_hold")
        invalid_coordinates._sync_capture_ui()
        fields = invalid_coordinates.key_hold_fields
        fields.target_var.set("マウスのボタン")
        fields.sync_target()
        fields.coordinates_var.set(True)
        fields.sync_coordinates()
        fields.x_var.set("ten")
        fields.y_var.set("20")
        invalid_coordinates.on_ok()
        self.assertTrue(invalid_coordinates.winfo_exists())
        self.assertIn("整数", self.showerror.call_args.args[1])

    def test_invalid_existing_edge_and_button_are_rejected(self) -> None:
        for initial in (
            {"type": "key_hold", "edge": "side", "value": "shift"},
            {"type": "key_hold", "edge": "down", "button": "extra"},
        ):
            with self.subTest(initial=initial):
                dialog = self.make_dialog(initial, mode="edit")
                dialog.on_ok()
                self.assertTrue(dialog.winfo_exists())
                self.assertIsNone(self.root._dialog_result)


if __name__ == "__main__":
    unittest.main()
