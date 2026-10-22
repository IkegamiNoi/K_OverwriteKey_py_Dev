import unittest

from keyseq.domain.config import format_action_list_item
from keyseq.domain.key_hold import (
    MODIFIER_KEY_NAMES,
    KeyHoldSpec,
    format_key_hold_value,
    held_display_name,
    is_modifier_key,
    is_repeat_enabled,
    parse_key_hold,
    wants_repeat,
)


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


class KeyRepeatDomainTests(unittest.TestCase):
    def test_modifier_names_and_normalization(self):
        self.assertEqual(len(MODIFIER_KEY_NAMES), 24)
        for name in MODIFIER_KEY_NAMES:
            with self.subTest(name=name):
                self.assertTrue(is_modifier_key(name))
                self.assertTrue(is_modifier_key(f"  {name.upper()}  "))
        for name in ("a", "enter", "menu"):
            with self.subTest(name=name):
                self.assertFalse(is_modifier_key(name))

    def test_modifier_names_with_underscores(self):
        for name in ("left_shift", "right_ctrl", "LEFT_WINDOWS"):
            with self.subTest(name=name):
                self.assertTrue(is_modifier_key(name))

    def test_wants_repeat_requires_boolean_true(self):
        for action, expected in (
            ({"repeat": True}, True),
            ({"repeat": False}, False),
            ({}, False),
            ({"repeat": "true"}, False),
            ({"repeat": 1}, False),
        ):
            with self.subTest(action=action):
                self.assertIs(wants_repeat(action), expected)

    def test_repeat_enabled_only_for_valid_non_modifier_keyboard_down(self):
        self.assertTrue(is_repeat_enabled({"edge": "down", "value": "a", "repeat": True}))
        disabled_actions = (
            {"edge": "up", "value": "a", "repeat": True},
            {"edge": "down", "button": "left", "repeat": True},
            {"edge": "down", "value": "ctrl", "repeat": True},
            {"edge": "down", "value": "control", "repeat": True},
            {"edge": "down", "value": "a"},
            {"edge": "invalid", "value": "a", "repeat": True},
            {"edge": "down", "value": "a+b", "repeat": True},
        )
        for action in disabled_actions:
            with self.subTest(action=action):
                self.assertFalse(is_repeat_enabled(action))


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

    def test_repeat_marker_is_shown_only_for_repeat_enabled_rows(self):
        self.assertEqual(
            format_key_hold_value({"edge": "down", "value": "a", "repeat": True}),
            "[押す] a （リピート）",
        )
        for action in (
            {"edge": "down", "value": "a"},
            {"edge": "up", "value": "a", "repeat": True},
            {"edge": "down", "value": "shift", "repeat": True},
            {"edge": "down", "button": "left", "repeat": True},
            {"edge": "bad", "value": "a", "repeat": True},
        ):
            with self.subTest(action=action):
                self.assertNotIn("（リピート）", format_key_hold_value(action))

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
        self.assertEqual(
            format_action_list_item(
                4, {"type": "key_hold", "edge": "down", "value": "a", "repeat": True}
            ),
            "05. [押す] a （リピート）",
        )
