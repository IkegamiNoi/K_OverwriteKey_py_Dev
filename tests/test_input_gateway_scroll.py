from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from keyseq.infrastructure import input_gateway
from keyseq.infrastructure.os_backend.windows import mouse_backend, send_input as send_input_api


class InputGatewayScrollTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gateway = input_gateway.InputGateway()
        patcher = patch.object(input_gateway, "get_backend", return_value=type("Backend", (), {"mouse": mouse_backend.WindowsMouseBackend()})())
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_build_wheel_inputs_sets_axis_flag_signed_data_and_count(self) -> None:
        vertical = mouse_backend._build_wheel_inputs(True, (-120, 120))
        self.assertEqual(len(vertical), 2)
        self.assertEqual(vertical[0].type, send_input_api._INPUT_MOUSE)
        self.assertEqual(vertical[0].mi.dwFlags, mouse_backend._MOUSEEVENTF_WHEEL)
        self.assertEqual(vertical[0].mi.mouseData, 0xFFFFFF88)
        horizontal = mouse_backend._build_wheel_inputs(False, (60,))
        self.assertEqual(len(horizontal), 1)
        self.assertEqual(horizontal[0].mi.dwFlags, mouse_backend._MOUSEEVENTF_HWHEEL)
        self.assertEqual(horizontal[0].mi.mouseData, 60)

    def test_scroll_moves_only_when_position_is_given_and_sends_once(self) -> None:
        send_input = Mock(side_effect=[2, 1])
        with patch.object(mouse_backend.WindowsMouseBackend, "move_cursor") as move_cursor, \
             patch.object(mouse_backend, "_send_input_api", return_value=send_input):
            self.gateway.scroll_mouse(
                vertical=True, deltas=(-120, 120), position=(10, 20),
            )
            self.gateway.scroll_mouse(vertical=False, deltas=(60,), position=None)
        move_cursor.assert_called_once_with(10, 20)
        self.assertEqual(send_input.call_count, 2)
        count, events, size = send_input.call_args.args
        self.assertEqual(count, 1)
        self.assertEqual(size, send_input_api.ctypes.sizeof(send_input_api._INPUT))
        self.assertEqual(events[0].mi.dwFlags, mouse_backend._MOUSEEVENTF_HWHEEL)

    def test_scroll_sends_all_deltas_in_one_call(self) -> None:
        send_input = Mock(return_value=3)
        with patch.object(mouse_backend, "_send_input_api", return_value=send_input):
            self.gateway.scroll_mouse(
                vertical=True, deltas=(120, 120, 60), position=None,
            )
        args = send_input.call_args.args
        self.assertEqual(args[0], 3)
        self.assertEqual([args[1][index].mi.mouseData for index in range(3)], [120, 120, 60])

    def test_empty_deltas_do_not_call_sendinput(self) -> None:
        with patch.object(mouse_backend.WindowsMouseBackend, "move_cursor") as move_cursor, \
             patch.object(mouse_backend, "_send_input_api") as send_api:
            self.gateway.scroll_mouse(vertical=True, deltas=(), position=(1, 2))
        move_cursor.assert_called_once_with(1, 2)
        send_api.assert_not_called()

    def test_partial_send_raises_oserror(self) -> None:
        send_input = Mock(return_value=1)
        with patch.object(mouse_backend, "_send_input_api", return_value=send_input), \
             patch.object(send_input_api.ctypes, "get_last_error", return_value=5, create=True):
            with self.assertRaises(OSError) as caught:
                self.gateway.scroll_mouse(
                    vertical=True, deltas=(120, 120), position=None,
                )
        self.assertEqual(caught.exception.errno, 5)

    def test_build_click_inputs_normalizes_virtual_desktop_and_orders_events(self) -> None:
        events = mouse_backend._build_click_inputs(0, 50, "right", 2, (-100, -50, 201, 101))
        self.assertEqual(len(events), 5)
        self.assertEqual(events[0].mi.dwFlags, 0xC001)
        self.assertEqual((events[0].mi.dx, events[0].mi.dy), (32768, 65535))
        self.assertEqual([event.mi.dwFlags for event in events[1:]], [8, 16, 8, 16])
        self.assertTrue(all((event.mi.dx, event.mi.dy) == (0, 0) for event in events[1:]))

    def test_click_sends_all_events_once_and_partial_send_raises(self) -> None:
        send_input = Mock(return_value=3)
        with patch.object(mouse_backend, "_virtual_screen", return_value=(0, 0, 100, 100)), \
             patch.object(mouse_backend, "_send_input_api", return_value=send_input):
            self.gateway.click_mouse(10, 20, "left", 1)
        send_input.assert_called_once()
        self.assertEqual(send_input.call_args.args[0], 3)
        self.assertEqual(send_input.call_args.args[1][0].mi.dwFlags, 0xC001)

        send_input = Mock(return_value=1)
        with patch.object(mouse_backend, "_virtual_screen", return_value=(0, 0, 100, 100)), \
             patch.object(mouse_backend, "_send_input_api", return_value=send_input), \
             patch.object(send_input_api.ctypes, "get_last_error", return_value=5, create=True):
            with self.assertRaises(OSError):
                self.gateway.click_mouse(10, 20, "left", 1)

    def test_click_rejects_unsupported_button(self) -> None:
        with self.assertRaises(ValueError):
            mouse_backend._build_click_inputs(0, 0, "side", 1, (0, 0, 1, 1))


if __name__ == "__main__":
    unittest.main()
