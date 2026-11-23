"""key_hold 編集欄の作成・編集・検証。実際のキーやマウスは操作しない。"""
import tkinter as tk
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tkinter import messagebox

from keyseq.presentation.dialogs.action_dialog import ActionDialog
from keyseq.application.hotkey_service import HotkeyService
from tests_ui.escape_delivery import acquire_focus
from keyseq.shared.i18n import fix_language

fix_language("ja")


class FakeInputGateway:
    def __init__(self) -> None:
        self.validated: list[str] = []
        self.invalid_names: set[str] = set()
        self.rejected_names: set[str] = set()

    def accepts_key_name(self, key_name: str) -> bool:
        return key_name.lower() not in self.rejected_names

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
        self.root.validate_hotkey = HotkeyService(
            validate_key_name=self.root.input_gateway.validate_key_name
        ).validate
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
        self.assertIn("押下・解放", dialog.type_combo.cget("values"))
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
            "repeat": True,
        })
        self.assertEqual(self.root.input_gateway.validated, ["left shift"])

    @unittest.skipUnless(sys.platform == "win32", "Windows の Tk keycode（VK）を前提にする")
    def test_key_hold_recording_distinguishes_numpad_digit(self) -> None:
        dialog = self.make_dialog(mode=None)
        fields = dialog.key_hold_fields
        fields.start_recording()
        fields._on_key_press(SimpleNamespace(keysym="End", keycode=97, state=0))
        self.assertEqual(fields.key_var.get(), "num 1")

    @unittest.skipUnless(sys.platform == "win32", "Windows の Tk keycode（VK）を前提にする")
    def test_hotkey_recording_distinguishes_numpad_digit(self) -> None:
        dialog = self.make_dialog(mode=None)
        dialog._start_recording()

        dialog._on_key_press(SimpleNamespace(keysym="End", keycode=97, state=0))

        self.assertEqual(dialog.value_var.get(), "num 1")
        self.assertFalse(dialog._recording)

    @unittest.skipUnless(sys.platform == "win32", "Windows の修飾キー名を確認する")
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

    def test_key_hold_recording_uses_mac_command_and_option_sides(self) -> None:
        from keyseq.infrastructure.os_backend.macos.keyboard_backend import MacKeyboardBackend
        from keyseq.infrastructure.os_backend.macos.tk_key_translator import MacTkKeyTranslator

        backend = SimpleNamespace(tk_keys=MacTkKeyTranslator(MacKeyboardBackend()))
        with patch("keyseq.presentation.tk_keys.get_backend", return_value=backend):
            for keysym, expected in (
                ("Meta_L", "left command"), ("Meta_R", "right command"),
                ("Alt_L", "left option"), ("Alt_R", "right option"),
            ):
                with self.subTest(keysym=keysym):
                    dialog = self.make_dialog(initial={"type": "key_hold", "edge": "down", "value": "a"}, mode=None)
                    fields = dialog.key_hold_fields
                    fields.start_recording()
                    fields._on_key_press(SimpleNamespace(keysym=keysym))
                    self.assertEqual(fields.key_var.get(), expected)
                    dialog.on_ok()
                    self.assertEqual(self.root._dialog_result["value"], expected)
                    self.assertEqual(self.root.input_gateway.validated[-1], expected)

    def test_key_hold_is_available_in_every_dialog_context(self) -> None:
        for mode in (None, "add", "edit"):
            with self.subTest(mode=mode):
                dialog = self.make_dialog(mode=mode)
                self.assertIn("押下・解放", dialog.type_combo.cget("values"))

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
        self.assertIn("キー名が正しくありません", self.showerror.call_args.args[1])

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
        self.assertIn("X/Yは両方", self.showerror.call_args.args[1])

    def test_hotkey_recording_collects_mac_modifiers_in_existing_order(self) -> None:
        dialog = self.make_dialog(mode=None)
        dialog._start_recording()
        event = SimpleNamespace(keysym="", keycode=0, state=0)
        with patch(
            "keyseq.presentation.dialogs.action_dialog.resolve_modified_char_key_name",
            return_value="",
        ), patch(
            "keyseq.presentation.dialogs.action_dialog.normalize_tk_key_event",
            side_effect=["command", "option", "esc"],
        ):
            for _ in range(2):
                self.assertEqual(dialog._on_key_press(event), "break")
                self.assertTrue(dialog._recording)
            self.assertEqual(dialog.value_var.get(), "option+command")
            dialog._on_key_press(event)
        self.assertEqual(dialog.value_var.get(), "option+command+esc")
        self.assertFalse(dialog._recording)

    def test_hotkey_rejects_other_os_modifier_and_unknown_normal_name(self) -> None:
        self.root.input_gateway.rejected_names.add("left command")
        rejected = self.make_dialog()
        rejected.type_var.set("hotkey")
        rejected._sync_capture_ui()
        rejected.value_var.set("left command+a")
        rejected.on_ok()
        self.assertTrue(rejected.winfo_exists())
        self.assertIn("不明なキー名", self.showerror.call_args.args[1])

        self.root.input_gateway.invalid_names.add("unknown-normal-name")
        unknown = self.make_dialog()
        unknown.type_var.set("hotkey")
        unknown._sync_capture_ui()
        unknown.value_var.set("unknown-normal-name+a")
        self.root._dialog_result = None
        unknown.on_ok()
        self.assertTrue(unknown.winfo_exists())
        self.assertIsNone(self.root._dialog_result)

    def test_key_hold_still_uses_backend_validation_for_unknown_and_other_os_names(self) -> None:
        self.root.input_gateway.rejected_names.add("left command")
        self.root.input_gateway.invalid_names.add("left command")
        dialog = self.make_dialog()
        dialog.type_var.set("key_hold")
        dialog._sync_capture_ui()
        dialog.key_hold_fields.key_var.set("left command")

        dialog.on_ok()

        self.assertTrue(dialog.winfo_exists())
        self.assertIn("left command", self.root.input_gateway.validated)
        self.assertIn("キー名が正しくありません", self.showerror.call_args.args[1])

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

    def test_repeat_control_is_visible_only_for_down_key_and_keeps_its_value(self) -> None:
        dialog = self.make_dialog()
        fields = dialog.key_hold_fields
        dialog.type_var.set("key_hold")
        dialog._sync_capture_ui()
        self.assertEqual(fields.repeat_var.get(), True)
        self.assertEqual(fields.repeat_frame.winfo_manager(), "grid")

        fields.repeat_var.set(False)
        fields.edge_var.set("離す")
        fields.edge_combo.event_generate("<<ComboboxSelected>>")
        self.assertEqual(fields.repeat_frame.winfo_manager(), "")
        fields.edge_var.set("押す")
        fields.edge_combo.event_generate("<<ComboboxSelected>>")
        fields.target_var.set("マウスのボタン")
        fields.target_combo.event_generate("<<ComboboxSelected>>")
        self.assertEqual(fields.repeat_frame.winfo_manager(), "")
        fields.target_var.set("キー")
        fields.target_combo.event_generate("<<ComboboxSelected>>")
        self.assertEqual(fields.repeat_frame.winfo_manager(), "grid")
        self.assertFalse(fields.repeat_var.get())

    def test_repeat_initial_values_for_new_and_existing_rows(self) -> None:
        cases = (
            (None, True),
            ({"type": "text", "value": "a"}, True),
            ({"type": "key_hold", "edge": "up", "value": "a"}, True),
            ({"type": "key_hold", "edge": "down", "button": "left"}, True),
            ({"type": "key_hold", "edge": "down", "value": "a"}, False),
            ({"type": "key_hold", "edge": "down", "value": "a", "repeat": False}, False),
            ({"type": "key_hold", "edge": "down", "value": "a", "repeat": True}, True),
        )
        for initial, expected in cases:
            with self.subTest(initial=initial):
                dialog = self.make_dialog(initial, mode="edit" if initial else "add")
                self.assertEqual(dialog.key_hold_fields.repeat_var.get(), expected)

    def test_repeat_is_saved_only_for_down_key_rows(self) -> None:
        down = self.make_dialog()
        down.type_var.set("key_hold")
        down._sync_capture_ui()
        down.key_hold_fields.key_var.set("a")
        down.key_hold_fields.repeat_var.set(False)
        down.on_ok()
        self.assertEqual(self.root._dialog_result["repeat"], False)

        up = self.make_dialog({"type": "key_hold", "edge": "up", "value": "a"}, mode="edit")
        up.on_ok()
        self.assertNotIn("repeat", self.root._dialog_result)

        mouse = self.make_dialog()
        mouse.type_var.set("key_hold")
        mouse._sync_capture_ui()
        mouse.key_hold_fields.target_var.set("マウスのボタン")
        mouse.key_hold_fields.sync_target()
        mouse.on_ok()
        self.assertNotIn("repeat", self.root._dialog_result)

    def test_hotkey_is_saved_normalized(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("hotkey")
        dialog._sync_capture_ui()
        dialog.value_var.set("Ctrl+ A")

        dialog.on_ok()

        self.assertEqual(self.root._dialog_result["value"], "ctrl+a")

    def test_hotkey_rejects_invalid_syntax(self) -> None:
        for value in ("ctrl++a", "ctrl+ctrl+a"):
            with self.subTest(value=value):
                self.root._dialog_result = None
                dialog = self.make_dialog()
                dialog.type_var.set("hotkey")
                dialog._sync_capture_ui()
                dialog.value_var.set(value)

                dialog.on_ok()

                self.assertTrue(dialog.winfo_exists())
                self.assertIsNone(self.root._dialog_result)

    def test_text_value_is_not_normalized(self) -> None:
        dialog = self.make_dialog()
        dialog.type_var.set("text")
        dialog._sync_capture_ui()
        dialog.value_var.set("Ctrl+ A")

        dialog.on_ok()

        self.assertEqual(self.root._dialog_result["value"], "Ctrl+ A")


if __name__ == "__main__":
    unittest.main()
