import unittest

from keyseq.domain.config import format_action_list_item
from keyseq.domain.key_hold import KeyHoldSpec, format_key_hold_value, held_display_name, parse_key_hold


class ParseKeyHoldTests(unittest.TestCase):
    def test_keyboard_down_up_and_normalization(self):
        self.assertEqual(
            parse_key_hold({"edge": "down", "value": "shift"}),
            KeyHoldSpec("down", None, "shift", None),
        )
        self.assertEqual(
            parse_key_hold({"edge": " UP ", "value": "  ShIfT  "}),
            KeyHoldSpec("up", None, "shift", None),
        )

    def test_rejects_invalid_edge_and_keyboard_values(self):
        invalid_actions = (
            {"edge": "side", "value": "a"},
            {"edge": 1, "value": "a"},
            {"edge": "down", "value": " "},
            {"edge": "down", "value": None},
            {"edge": "down", "value": "ctrl+a"},
            {"edge": "down", "value": "a,b"},
        )
        for action in invalid_actions:
            with self.subTest(action=action):
                self.assertIsInstance(parse_key_hold(action), str)

    def test_accepts_all_mouse_buttons(self):
        for button in ("left", "right", "middle"):
            with self.subTest(button=button):
                self.assertEqual(
                    parse_key_hold({"edge": "down", "button": button.upper()}),
                    KeyHoldSpec("down", button, None, None),
                )

    def test_rejects_invalid_mouse_button(self):
        self.assertIsInstance(parse_key_hold({"edge": "down", "button": "extra"}), str)

    def test_empty_or_non_string_button_selects_keyboard(self):
        for button in ("", "  ", None, 1):
            with self.subTest(button=button):
                self.assertEqual(
                    parse_key_hold({"edge": "down", "button": button, "value": " A ", "x": 1}),
                    KeyHoldSpec("down", None, "a", None),
                )

    def test_mouse_coordinates_convert_with_int(self):
        self.assertEqual(
            parse_key_hold({"edge": "down", "button": "left", "x": "100", "y": 10.9}),
            KeyHoldSpec("down", "left", None, (100, 10)),
        )

    def test_rejects_incomplete_or_invalid_mouse_coordinates(self):
        for action in (
            {"edge": "down", "button": "left", "x": 10},
            {"edge": "up", "button": "right", "y": 20},
            {"edge": "down", "button": "middle", "x": "bad", "y": 20},
        ):
            with self.subTest(action=action):
                self.assertIsInstance(parse_key_hold(action), str)

    def test_keyboard_ignores_coordinates(self):
        self.assertEqual(
            parse_key_hold({"edge": "up", "value": "shift", "x": "bad"}),
            KeyHoldSpec("up", None, "shift", None),
        )


class FormatKeyHoldTests(unittest.TestCase):
    def test_held_display_names(self):
        self.assertEqual(held_display_name("key", "right ctrl"), "right ctrl")
        for button, expected in (("left", "マウス左"), ("right", "マウス右"), ("middle", "マウス中")):
            with self.subTest(button=button):
                self.assertEqual(held_display_name("mouse", button), expected)

    def test_formats_keyboard_and_mouse_rows(self):
        self.assertEqual(format_key_hold_value({"edge": "down", "value": "shift"}), "[押す] shift")
        self.assertEqual(format_key_hold_value({"edge": "up", "value": "shift"}), "[離す] shift")
        self.assertEqual(format_key_hold_value({"edge": "down", "button": "left"}), "[押す] マウス左")
        self.assertEqual(
            format_key_hold_value({"edge": "down", "button": "left", "x": "100", "y": 200}),
            "[押す] マウス左 (100, 200)",
        )

    def test_formats_invalid_row_for_visibility(self):
        self.assertEqual(
            format_key_hold_value({"edge": "down", "value": "ctrl+a"}),
            "[key_hold] ctrl+a",
        )
        self.assertEqual(
            format_key_hold_value({"edge": "down", "button": "extra"}),
            "[key_hold] extra",
        )

    def test_action_list_item_uses_value_format_with_optional_label(self):
        self.assertEqual(
            format_action_list_item(0, {"type": "key_hold", "edge": "down", "value": "shift"}),
            "01. [押す] shift",
        )
        self.assertEqual(
            format_action_list_item(
                1, {"type": "key_hold", "edge": "up", "value": "shift", "label": "解除"}
            ),
            "02. [離す] shift: 解除",
        )
        self.assertEqual(
            format_action_list_item(
                2, {"type": "key_hold", "edge": "down", "button": "middle", "x": 1, "y": 2}
            ),
            "03. [押す] マウス中 (1, 2)",
        )
        self.assertEqual(
            format_action_list_item(3, {"type": "key_hold", "edge": "bad", "value": "shift"}),
            "04. [key_hold] shift",
        )
