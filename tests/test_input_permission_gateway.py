import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.infrastructure.input_gateway import InputGateway


class InputPermissionGatewayTests(unittest.TestCase):
    def test_permission_and_failure_listener_calls_reach_keyboard_backend(self):
        keyboard = Mock()
        keyboard.input_permission_granted.return_value = False
        keyboard.open_input_permission_settings.return_value = True
        gateway = InputGateway()
        listener = Mock()
        with patch("keyseq.infrastructure.input_gateway.get_backend", return_value=SimpleNamespace(keyboard=keyboard)):
            self.assertFalse(gateway.input_permission_granted())
            self.assertTrue(gateway.open_input_permission_settings())
            gateway.set_hook_failure_listener(listener)
            gateway.set_hook_failure_listener(None)
        keyboard.input_permission_granted.assert_called_once_with()
        keyboard.open_input_permission_settings.assert_called_once_with()
        self.assertEqual([call.args for call in keyboard.set_hook_failure_listener.call_args_list], [(listener,), (None,)])
        listener.assert_not_called()
