from __future__ import annotations

import inspect
import unittest
from unittest.mock import Mock, patch

from keyseq.infrastructure.os_backend import Capabilities, ImeBackend, OsBackend, get_backend
from keyseq.infrastructure.os_backend.windows.backend import WindowsImeBackend


class OsBackendContractTests(unittest.TestCase):
    def test_windows_backend_matches_ime_protocol(self) -> None:
        protocol = {name: member for name, member in ImeBackend.__dict__.items() if callable(member) and not name.startswith("_")}
        implementation = {name: member for name, member in WindowsImeBackend.__dict__.items() if callable(member) and not name.startswith("_")}
        self.assertEqual(set(implementation), set(protocol))
        for name in protocol:
            self.assertEqual(list(inspect.signature(implementation[name]).parameters), list(inspect.signature(protocol[name]).parameters))

    def test_capabilities_require_all_values(self) -> None:
        with self.assertRaises(TypeError):
            Capabilities()  # type: ignore[call-arg]
        self.assertEqual(list(inspect.signature(Capabilities).parameters), ["click_through_window", "window_stacking", "status_icon", "ime_control"])

    def test_backend_is_cached_after_single_creation(self) -> None:
        created = OsBackend(Capabilities(True, True, True, True), Mock())
        with patch("keyseq.infrastructure.os_backend.sys.platform", "win32"), patch("keyseq.infrastructure.os_backend._backend", None), patch(
            "keyseq.infrastructure.os_backend.windows.backend.create_backend", return_value=created
        ) as create:
            self.assertIs(get_backend(), created)
            self.assertIs(get_backend(), created)
            create.assert_called_once_with()

    def test_non_windows_platform_raises(self) -> None:
        with patch("keyseq.infrastructure.os_backend.sys.platform", "darwin"), patch("keyseq.infrastructure.os_backend._backend", None):
            with self.assertRaises(RuntimeError):
                get_backend()

    def test_window_id_is_converted_and_failures_return_safe_values(self) -> None:
        backend = WindowsImeBackend()
        window = Mock()
        window.winfo_id.return_value = "42"
        with patch("keyseq.infrastructure.os_backend.windows.backend.own_ime_status.get_open_status", return_value=True) as get_status, patch(
            "keyseq.infrastructure.os_backend.windows.backend.own_ime_status.set_open_status", return_value=True
        ) as set_status:
            self.assertTrue(backend.get_own_open_status(window))
            self.assertTrue(backend.set_own_open_status(window, True))
        get_status.assert_called_once_with(42)
        set_status.assert_called_once_with(42, True)
        window.winfo_id.side_effect = RuntimeError("destroyed")
        self.assertIsNone(backend.get_own_open_status(window))
        self.assertFalse(backend.set_own_open_status(window, True))


if __name__ == "__main__":
    unittest.main()
