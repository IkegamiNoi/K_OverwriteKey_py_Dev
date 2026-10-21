import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tkinter import messagebox

from keyseq.presentation.dialogs.action_dialog import ActionDialog


class ActionDialogMouseScrollTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()
        cls.root.update_idletasks()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        self.root.hook = SimpleNamespace(suspend_hook_for_dialog=Mock())
        self.root.config_service = Mock()
        self.root.data = {"hotkey_presets": []}
        self.root.input_gateway = SimpleNamespace(validate_key_name=Mock())
        self.root._dialog_result = None
        patcher = patch.object(messagebox, "showerror")
        self.showerror = patcher.start()
        self.addCleanup(patcher.stop)
        self.dialogs = []
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

    def test_mouse_scroll_is_available_in_every_dialog_context(self) -> None:
        for mode in (None, "add", "edit"):
            with self.subTest(mode=mode):
                dialog = self.make_dialog(mode=mode)
                values = dialog.type_combo.cget("values")
                self.assertIn("mouse_scroll", values)
                self.assertEqual(values[values.index("mouse_click") + 1], "mouse_scroll")

    def test_fields_are_shown_only_for_mouse_scroll(self) -> None:
        dialog = self.make_dialog()
        fields = dialog.mouse_scroll_fields
        self.assertEqual(fields.frame.winfo_manager(), "")
        dialog.type_var.set("mouse_scroll")
        dialog._sync_capture_ui()
        self.assertEqual(fields.frame.winfo_manager(), "grid")
        self.assertEqual(dialog.key_hold_fields.frame.winfo_manager(), "")
        dialog.type_var.set("key_hold")
        dialog._sync_capture_ui()
        self.assertEqual(fields.frame.winfo_manager(), "")
        self.assertEqual(dialog.key_hold_fields.frame.winfo_manager(), "grid")
        dialog.type_var.set("text")
        dialog._sync_capture_ui()
        self.assertEqual(fields.frame.winfo_manager(), "")

    def test_unit_controls_entry_states_and_unselected_keeps_both_enabled(self) -> None:
        dialog = self.make_dialog()
        fields = dialog.mouse_scroll_fields
        self.assertEqual(str(fields.amount_notch_entry.cget("state")), "normal")
        self.assertEqual(str(fields.amount_delta_entry.cget("state")), "disabled")
        fields.unit_var.set("delta")
        fields.sync_amount()
        self.assertEqual(str(fields.amount_notch_entry.cget("state")), "disabled")
        self.assertEqual(str(fields.amount_delta_entry.cget("state")), "normal")
        fields.unit_var.set("")
        fields.sync_amount()
        self.assertEqual(str(fields.amount_notch_entry.cget("state")), "normal")
        self.assertEqual(str(fields.amount_delta_entry.cget("state")), "normal")

    def test_coordinate_controls_follow_checkbox_and_capture_callback(self) -> None:
        capture = Mock()
        with patch.object(ActionDialog, "_capture_mouse_position", new=lambda _self, *args: capture(*args)):
            dialog = self.make_dialog()
        fields = dialog.mouse_scroll_fields
        self.assertEqual(str(fields.x_entry.cget("state")), "disabled")
        self.assertEqual(str(fields.y_entry.cget("state")), "disabled")
        self.assertEqual(str(fields.capture_button.cget("state")), "disabled")
        fields.coordinates_var.set(True)
        fields.sync_coordinates()
        self.assertEqual(str(fields.x_entry.cget("state")), "normal")
        self.assertEqual(str(fields.y_entry.cget("state")), "normal")
        self.assertEqual(str(fields.capture_button.cget("state")), "normal")
        fields.capture_button.invoke()
        capture.assert_called_once_with(fields.x_var, fields.y_var, fields.capture_button, fields.capture_hint)
        fields.coordinates_var.set(False)
        dialog._set_mouse_capture_state("normal")
        self.assertEqual(str(fields.capture_button.cget("state")), "disabled")

    def test_load_normalizes_unit_amount_direction_and_coordinates(self) -> None:
        cases = (
            ({"type": "mouse_scroll", "amount": 3}, "notch", "3", "120"),
            ({"type": "mouse_scroll", "unit": " DELTA ", "amount": "3"}, "delta", "1", "3"),
            ({"type": "mouse_scroll", "unit": "   ", "amount": 3.0}, "notch", "3", "120"),
            ({"type": "mouse_scroll", "unit": "bad", "amount": 3.0}, "", "3", "3"),
        )
        for initial, unit, notch, delta in cases:
            with self.subTest(initial=initial):
                fields = self.make_dialog(initial, mode="edit").mouse_scroll_fields
                self.assertEqual(fields.unit_var.get(), unit)
                self.assertEqual((fields.amount_notch_var.get(), fields.amount_delta_var.get()), (notch, delta))

        for raw_amount, expected in ((3.0, "3"), ("3", "3"), ("bad", "bad"), ("2.7", "2.7")):
            with self.subTest(amount=raw_amount):
                fields = self.make_dialog({
                    "type": "mouse_scroll", "unit": "notch", "amount": raw_amount,
                    "direction": "sideways",
                }, mode="edit").mouse_scroll_fields
                self.assertEqual(fields.amount_notch_var.get(), expected)
                self.assertEqual(fields.direction_var.get(), "下")

        fields = self.make_dialog({
            "type": "mouse_scroll", "unit": "delta", "amount": 60,
            "direction": "right", "x": "12", "y": "bad",
        }, mode="edit").mouse_scroll_fields
        self.assertEqual(fields.direction_var.get(), "右")
        self.assertTrue(fields.coordinates_var.get())
        self.assertEqual((fields.x_var.get(), fields.y_var.get()), ("12", "bad"))
        self.assertEqual(str(fields.x_entry.cget("state")), "normal")

    def test_load_without_amount_leaves_selected_amount_empty_and_ok_rejects(self) -> None:
        cases = (
            ({"type": "mouse_scroll", "unit": "notch"}, "notch", "", "120"),
            ({"type": "mouse_scroll", "unit": "delta"}, "delta", "1", ""),
            ({"type": "mouse_scroll"}, "notch", "", "120"),
            ({"type": "mouse_scroll", "unit": ""}, "notch", "", "120"),
            ({"type": "mouse_scroll", "unit": "invalid"}, "", "", ""),
        )
        for initial, unit, notch, delta in cases:
            with self.subTest(initial=initial):
                dialog = self.make_dialog(initial, mode="edit")
                fields = dialog.mouse_scroll_fields
                self.assertEqual(fields.unit_var.get(), unit)
                self.assertEqual(
                    (fields.amount_notch_var.get(), fields.amount_delta_var.get()),
                    (notch, delta),
                )
                dialog.action_label_var.set("changed")
                error_count = self.showerror.call_count
                dialog.on_ok()
                self.assertIsNone(self.root._dialog_result)
                self.assertEqual(self.showerror.call_count, error_count + 1)
                expected_error = "量は整数に変換できる値" if unit else "単位を選んで"
                self.assertIn(expected_error, self.showerror.call_args.args[1])

    def test_mouse_scroll_capture_button_stays_disabled_during_mouse_capture(self) -> None:
        dialog = self.make_dialog()
        fields = dialog.mouse_scroll_fields
        fields.coordinates_var.set(True)
        fields.sync_coordinates()

        dialog.type_var.set("mouse_click")
        dialog._set_mouse_capture_state("disabled")
        self.assertEqual(str(dialog.mouse_capture_btn.cget("state")), "disabled")
        self.assertEqual(str(fields.capture_button.cget("state")), "disabled")

        dialog.type_var.set("mouse_scroll")
        dialog._sync_capture_ui()
        self.assertEqual(str(fields.capture_button.cget("state")), "disabled")

        fields.coordinates_var.set(False)
        fields.sync_coordinates()
        fields.coordinates_var.set(True)
        fields.sync_coordinates()
        self.assertEqual(str(fields.capture_button.cget("state")), "disabled")

        dialog._set_mouse_capture_state("normal")
        self.assertEqual(str(fields.capture_button.cget("state")), "normal")

    def test_ok_saves_normalized_action_with_and_without_coordinates(self) -> None:
        dialog = self.make_dialog()
        fields = dialog.mouse_scroll_fields
        dialog.type_var.set("mouse_scroll")
        fields.direction_var.set("左")
        fields.unit_var.set("delta")
        fields.amount_delta_var.set("60")
        dialog.action_label_var.set("horizontal")
        dialog.on_ok()
        self.assertEqual(self.root._dialog_result, {
            "type": "mouse_scroll", "direction": "left", "unit": "delta", "amount": 60,
            "label": "horizontal",
        })

        dialog = self.make_dialog()
        fields = dialog.mouse_scroll_fields
        dialog.type_var.set("mouse_scroll")
        fields.direction_var.set("上")
        fields.amount_notch_var.set("3")
        fields.coordinates_var.set(True)
        fields.sync_coordinates()
        fields.x_var.set("100")
        fields.y_var.set("200")
        dialog.on_ok()
        self.assertEqual(self.root._dialog_result, {
            "type": "mouse_scroll", "direction": "up", "unit": "notch", "amount": 3,
            "label": "", "x": 100, "y": 200,
        })

    def test_ok_rejects_unselected_unit_range_and_incomplete_coordinates(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("mouse_scroll")
        dialog.mouse_scroll_fields.unit_var.set("")
        dialog.on_ok()
        self.assertIn("単位を選んで", self.showerror.call_args.args[1])
        self.assertIsNone(self.root._dialog_result)

        invalid_unit = self.make_dialog({
            "type": "mouse_scroll", "direction": "down", "unit": "unknown", "amount": 3,
        }, mode="edit")
        invalid_unit.on_ok()
        self.assertIn("単位を選んで", self.showerror.call_args.args[1])
        self.assertIsNone(self.root._dialog_result)

        dialog = self.make_dialog()
        dialog.type_var.set("mouse_scroll")
        dialog.mouse_scroll_fields.amount_notch_var.set("101")
        dialog.on_ok()
        self.assertIn("1〜100", self.showerror.call_args.args[1])

        dialog = self.make_dialog()
        dialog.type_var.set("mouse_scroll")
        dialog.mouse_scroll_fields.coordinates_var.set(True)
        dialog.mouse_scroll_fields.sync_coordinates()
        dialog.mouse_scroll_fields.x_var.set("10")
        dialog.on_ok()
        self.assertIn("X/Y は両方", self.showerror.call_args.args[1])

    def test_editing_integral_float_amount_saves_integer_after_label_change(self) -> None:
        dialog = self.make_dialog({
            "type": "mouse_scroll", "direction": "down", "unit": "notch", "amount": 3.0,
        }, mode="edit")
        dialog.action_label_var.set("changed")
        dialog.on_ok()
        self.assertEqual(self.root._dialog_result["amount"], 3)
        self.assertEqual(self.root._dialog_result["label"], "changed")

    def test_hidden_mouse_scroll_focus_moves_to_type_combo(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("mouse_scroll")
        dialog._sync_capture_ui()
        dialog.mouse_scroll_fields.direction_combo.focus_set()
        dialog.update()
        dialog.type_var.set("text")
        dialog._sync_capture_ui()
        dialog.update()
        self.assertIs(dialog.focus_lastfor(), dialog.type_combo)

    def test_mouse_scroll_initial_focus_is_type_combo(self) -> None:
        dialog = self.make_dialog({
            "type": "mouse_scroll", "direction": "down", "unit": "notch", "amount": 1,
        }, mode="edit")
        self.assertIs(dialog._initial_focus_widget(), dialog.type_combo)


if __name__ == "__main__":
    unittest.main()
