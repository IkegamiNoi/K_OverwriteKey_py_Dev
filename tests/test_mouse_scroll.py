from __future__ import annotations

import unittest

from keyseq.domain.config import format_action_list_item
from keyseq.domain.mouse_scroll import (
    MouseScrollSpec,
    describe_mouse_scroll,
    format_mouse_scroll_value,
    parse_mouse_scroll,
    scroll_deltas,
)


class ParseMouseScrollTests(unittest.TestCase):
    def parse(self, **values):
        return parse_mouse_scroll({"direction": "up", "amount": 1, **values})

    def test_direction_normalizes_four_directions(self) -> None:
        for direction in ("up", "down", "left", "right"):
            with self.subTest(direction=direction):
                self.assertEqual(self.parse(direction=f"  {direction.upper()} ").direction, direction)

    def test_rejects_invalid_direction(self) -> None:
        for direction in ("diagonal", "", "up down", None, 1):
            with self.subTest(direction=direction):
                self.assertIsInstance(self.parse(direction=direction), str)

    def test_unit_defaults_and_normalizes(self) -> None:
        for action in (
            {"direction": "up", "amount": 1},
            {"direction": "up", "unit": "", "amount": 1},
            {"direction": "up", "unit": "  ", "amount": 1},
        ):
            self.assertEqual(parse_mouse_scroll(action).unit, "notch")
        self.assertEqual(self.parse(unit=" Delta ").unit, "delta")

    def test_rejects_invalid_unit(self) -> None:
        for unit in ("ticks", "Notches", None, 1):
            with self.subTest(unit=unit):
                self.assertIsInstance(self.parse(unit=unit), str)

    def test_amount_conversions_and_errors(self) -> None:
        for value, expected in ((3, 3), (3.0, 3), ("3", 3), (" 3 ", 3)):
            self.assertEqual(self.parse(amount=value).amount, expected)
        for value in (2.7, True, None, "bad"):
            with self.subTest(value=value):
                self.assertIsInstance(self.parse(amount=value), str)
        self.assertIsInstance(parse_mouse_scroll({"direction": "up"}), str)

    def test_amount_ranges(self) -> None:
        for value in (0, 101):
            self.assertIsInstance(self.parse(amount=value), str)
        self.assertEqual(self.parse(unit="delta", amount=12000).amount, 12000)
        self.assertIsInstance(self.parse(unit="delta", amount=12001), str)
        self.assertIn("1〜100", self.parse(amount=101))
        self.assertIn("1〜12000", self.parse(unit="delta", amount=12001))

    def test_coordinates_require_both_convertible_values(self) -> None:
        self.assertEqual(self.parse(x="10", y=20).position, (10, 20))
        self.assertIsInstance(self.parse(x=1), str)
        self.assertIsInstance(self.parse(y=1), str)
        for value in (None, "bad"):
            with self.subTest(value=value):
                self.assertIsInstance(self.parse(x=value, y=2), str)


class ScrollDeltaTests(unittest.TestCase):
    def test_notch_and_delta_chunks(self) -> None:
        self.assertEqual(scroll_deltas(MouseScrollSpec("down", "notch", 3, None)),
                         (True, (-120, -120, -120)))
        self.assertEqual(scroll_deltas(MouseScrollSpec("up", "delta", 300, None)),
                         (True, (120, 120, 60)))
        self.assertEqual(scroll_deltas(MouseScrollSpec("up", "delta", 120, None)),
                         (True, (120,)))

    def test_four_directions_set_sign_and_axis(self) -> None:
        expected = {"up": (True, 120), "down": (True, -120),
                    "right": (False, 120), "left": (False, -120)}
        for direction, result in expected.items():
            with self.subTest(direction=direction):
                self.assertEqual(scroll_deltas(MouseScrollSpec(direction, "notch", 1, None)),
                                 (result[0], (result[1],)))


class MouseScrollFormattingTests(unittest.TestCase):
    def test_valid_and_invalid_values(self) -> None:
        self.assertEqual(format_mouse_scroll_value(
            {"direction": "down", "amount": 3}), "[スクロール] 下 3")
        self.assertEqual(format_mouse_scroll_value(
            {"direction": "right", "unit": "delta", "amount": 60}),
            "[スクロール] 右 60 (生)")
        self.assertEqual(format_mouse_scroll_value(
            {"direction": "down", "amount": 3, "x": 100, "y": 200}),
            "[スクロール] 下 3 (100, 200)")
        self.assertEqual(format_mouse_scroll_value({"direction": "bad", "amount": 1}),
                         "[mouse_scroll] bad")
        self.assertEqual(format_mouse_scroll_value({"direction": 1, "amount": 1}),
                         "[mouse_scroll]")

    def test_description_uses_string_values_and_missing_marker(self) -> None:
        self.assertEqual(describe_mouse_scroll({"direction": 1, "unit": None, "amount": 3}),
                         "direction=1 unit=None amount=3")
        self.assertEqual(describe_mouse_scroll({"direction": "up", "x": None}),
                         "direction=up unit=(なし) amount=(なし) x=None y=(なし)")

    def test_action_list_item_formats_mouse_scroll_without_type_prefix(self) -> None:
        self.assertEqual(format_action_list_item(
            0, {"type": "mouse_scroll", "direction": "down", "amount": 3}),
            "01. [スクロール] 下 3")
        self.assertEqual(format_action_list_item(
            1, {"type": "mouse_scroll", "direction": "right", "unit": "delta",
                "amount": 60, "label": " memo "}),
            "02. [スクロール] 右 60 (生): memo")


if __name__ == "__main__":
    unittest.main()
