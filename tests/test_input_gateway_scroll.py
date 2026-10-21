from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from keyseq.infrastructure import input_gateway


class InputGatewayScrollTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = input_gateway.InputGateway()

    def test_build_wheel_inputs_sets_axis_flag_signed_data_and_count(self) -> None:
        vertical = input_gateway._build_wheel_inputs(True, (-120, 120))
        self.assertEqual(len(vertical), 2)
        self.assertEqual(vertical[0].type, input_gateway._INPUT_MOUSE)
        self.assertEqual(vertical[0].mi.dwFlags, input_gateway._MOUSEEVENTF_WHEEL)
        self.assertEqual(vertical[0].mi.mouseData, 0xFFFFFF88)
        horizontal = input_gateway._build_wheel_inputs(False, (60,))
        self.assertEqual(len(horizontal), 1)
        self.assertEqual(horizontal[0].mi.dwFlags, input_gateway._MOUSEEVENTF_HWHEEL)
        self.assertEqual(horizontal[0].mi.mouseData, 60)

    def test_scroll_moves_only_when_position_is_given_and_sends_once(self) -> None:
        send_input = Mock(side_effect=[2, 1])
        with patch.object(self.gateway, "move_cursor") as move_cursor, \
             patch.object(input_gateway, "_send_input_api", return_value=send_input):
            self.gateway.scroll_mouse(
                vertical=True, deltas=(-120, 120), position=(10, 20),
            )
            self.gateway.scroll_mouse(vertical=False, deltas=(60,), position=None)
        move_cursor.assert_called_once_with(10, 20)
        self.assertEqual(send_input.call_count, 2)
        count, events, size = send_input.call_args.args
        self.assertEqual(count, 1)
        self.assertEqual(size, input_gateway.ctypes.sizeof(input_gateway._INPUT))
        self.assertEqual(events[0].mi.dwFlags, input_gateway._MOUSEEVENTF_HWHEEL)

    def test_scroll_sends_all_deltas_in_one_call(self) -> None:
        send_input = Mock(return_value=3)
        with patch.object(input_gateway, "_send_input_api", return_value=send_input):
            self.gateway.scroll_mouse(
                vertical=True, deltas=(120, 120, 60), position=None,
            )
        args = send_input.call_args.args
        self.assertEqual(args[0], 3)
        self.assertEqual([args[1][index].mi.mouseData for index in range(3)], [120, 120, 60])

    def test_empty_deltas_do_not_call_sendinput(self) -> None:
        with patch.object(self.gateway, "move_cursor") as move_cursor, \
             patch.object(input_gateway, "_send_input_api") as send_api:
            self.gateway.scroll_mouse(vertical=True, deltas=(), position=(1, 2))
        move_cursor.assert_called_once_with(1, 2)
        send_api.assert_not_called()

    def test_partial_send_raises_oserror(self) -> None:
        send_input = Mock(return_value=1)
        with patch.object(input_gateway, "_send_input_api", return_value=send_input), \
             patch.object(input_gateway.ctypes, "get_last_error", return_value=5):
            with self.assertRaises(OSError) as caught:
                self.gateway.scroll_mouse(
                    vertical=True, deltas=(120, 120), position=None,
                )
        self.assertEqual(caught.exception.errno, 5)


if __name__ == "__main__":
    unittest.main()
