"""Localized choices keep action and mouse button storage codes unchanged."""

import tkinter as tk
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.domain.config import format_action_list_item
from keyseq.presentation.dialogs.action_dialog import ActionDialog
from keyseq.shared.i18n import fix_language, tr_in


class ActionDialogLabelsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def setUp(self) -> None:
        fix_language("ja")
        self.root.hook = SimpleNamespace(suspend_hook_for_dialog=Mock())
        self.root.config_service = Mock()
        self.root.data = {"hotkey_presets": []}
        self.root.input_gateway = SimpleNamespace(validate_key_name=Mock())
        self.root._dialog_result = None
        self.dialogs = []
        self.addCleanup(self.cleanup_windows)

    def cleanup_windows(self) -> None:
        for dialog in self.dialogs:
            if dialog.winfo_exists():
                dialog.grab_release()
                dialog.destroy()
        self.root.update()

    def make_dialog(self, initial=None, mode="edit") -> ActionDialog:
        dialog = ActionDialog(self.root, "Action", initial=initial, mode=mode)
        self.dialogs.append(dialog)
        return dialog

    def language(self, lang):
        if lang == "ja":
            return nullcontext()
        return patch("keyseq.presentation.dialogs.action_dialog.tr",
                     side_effect=lambda key, **params: tr_in("en", key, **params))

    def test_type_choices_and_initial_actions_show_labels(self) -> None:
        codes = ("hotkey", "text", "mouse_click", "mouse_scroll", "key_hold", "system", "file_line")
        for lang in ("ja", "en"):
            with self.subTest(lang=lang), self.language(lang):
                expected = [tr_in(lang, f"action.type.{code}") for code in codes]
                for code, label in zip(codes, expected):
                    dialog = self.make_dialog({"type": code, "value": "a"})
                    self.assertEqual(list(dialog.type_combo.cget("values")), expected)
                    self.assertEqual(dialog.type_var.get(), label)
                    self.assertEqual(dialog._action_type(), code)
                loop = self.make_dialog(mode="edit_loop")
                self.assertEqual(loop.type_var.get(), tr_in(lang, "action.type.system"))
                self.assertEqual(str(loop.type_combo.cget("state")), "disabled")

    def test_selecting_type_saves_internal_code(self) -> None:
        for lang in ("ja", "en"):
            for code in ("hotkey", "text", "mouse_scroll", "key_hold", "system", "file_line"):
                with self.subTest(lang=lang, code=code), self.language(lang):
                    dialog = self.make_dialog()
                    dialog.type_var.set(tr_in(lang, f"action.type.{code}"))
                    dialog._sync_capture_ui()
                    dialog.value_var.set("a")
                    dialog.key_hold_fields.key_var.set("a")
                    dialog.mouse_scroll_fields.amount_notch_var.set("1")
                    with patch.object(dialog.control_fields, "build_result", return_value={"type": code}) as build:
                        dialog.on_ok()
                    self.assertEqual(self.root._dialog_result["type"], code)
                    if code in ("system", "file_line"):
                        build.assert_called_once_with(code, "")

    def test_unknown_type_is_displayed_and_saved_unchanged(self) -> None:
        for lang in ("ja", "en"):
            for initial in ({"type": "Future_TYPE", "value": "data", "label": "memo", "extra": 42},
                            {"type": " future_type ", "extra": 42},
                            {"type": tr_in(lang, "action.type.text"), "extra": 42}):
                with self.subTest(lang=lang, initial=initial), self.language(lang):
                    dialog = self.make_dialog(initial)
                    self.assertEqual(dialog.type_var.get(), initial["type"])
                    dialog.on_ok()
                    self.assertEqual(self.root._dialog_result, initial)

    def test_mouse_choices_initial_values_and_saved_codes(self) -> None:
        for lang in ("ja", "en"):
            for code in ("left", "right", "middle"):
                with self.subTest(lang=lang, code=code), self.language(lang):
                    initial = {"type": "mouse_click", "x": 10, "y": 20, "button": code, "clicks": 2, "label": ""}
                    dialog = self.make_dialog(initial)
                    labels = [tr_in(lang, f"action_dialog.key_hold.button.{button}")
                              for button in ("left", "right", "middle")]
                    self.assertEqual(list(dialog.mouse_btn_combo.cget("values")), labels)
                    self.assertEqual(dialog.mouse_btn_var.get(), tr_in(lang, f"action_dialog.key_hold.button.{code}"))
                    selected = "middle" if code != "middle" else "left"
                    dialog.mouse_btn_var.set(tr_in(lang, f"action_dialog.key_hold.button.{selected}"))
                    dialog.on_ok()
                    self.assertEqual(self.root._dialog_result, dict(initial, button=selected))

    def test_selecting_a_label_replaces_a_colliding_unknown_type(self) -> None:
        for lang in ("ja", "en"):
            with self.subTest(lang=lang), self.language(lang):
                label = tr_in(lang, "action.type.text")
                dialog = self.make_dialog({"type": label})
                dialog.type_var.set(label)
                dialog._on_type_selected(None)
                dialog.value_var.set("data")
                dialog.on_ok()
                self.assertEqual(self.root._dialog_result,
                                 {"type": "text", "value": "data", "label": ""})

    def test_mouse_list_labels_and_unknown_button(self) -> None:
        for lang in ("ja", "en"):
            with self.subTest(lang=lang), patch("keyseq.domain.config.tr", side_effect=lambda key: tr_in(lang, key)):
                for code in ("left", "right", "middle", "future"):
                    label = tr_in(lang, f"domain.config.mouse_button.{code}") if code != "future" else code
                    action = {"type": "mouse_click", "x": 10, "y": 20, "button": code}
                    self.assertEqual(format_action_list_item(0, action),
                                     f"01. [click] (10, 20) {label} x1")
                    action.update(drag=True, to_x=30, to_y=40)
                    self.assertEqual(format_action_list_item(0, action),
                                     f"01. [click] (10, 20)→(30, 40) {label} 1000px/s")
