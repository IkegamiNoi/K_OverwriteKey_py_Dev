from __future__ import annotations

import inspect
import unittest
from unittest.mock import Mock, patch

from keyseq.infrastructure.os_backend import AppIdentity, Capabilities, ImeBackend, OsBackend, TkKeyTranslator, WindowBackend, get_backend
from keyseq.infrastructure.os_backend.windows.backend import (
    WindowsAppIdentity, WindowsImeBackend, WindowsTkKeyTranslator, WindowsWindowBackend,
)


class OsBackendContractTests(unittest.TestCase):
    def test_windows_backend_matches_ime_protocol(self) -> None:
        protocol = {name: member for name, member in ImeBackend.__dict__.items() if callable(member) and not name.startswith("_")}
        implementation = {name: member for name, member in WindowsImeBackend.__dict__.items() if callable(member) and not name.startswith("_")}
        self.assertEqual(set(implementation), set(protocol))
        for name in protocol:
            self.assertEqual(list(inspect.signature(implementation[name]).parameters), list(inspect.signature(protocol[name]).parameters))

    def test_windows_backends_match_new_protocols(self) -> None:
        for protocol, implementation in (
            (WindowBackend, WindowsWindowBackend),
            (TkKeyTranslator, WindowsTkKeyTranslator),
            (AppIdentity, WindowsAppIdentity),
        ):
            with self.subTest(protocol=protocol.__name__):
                protocol_methods = {
                    name: member for name, member in protocol.__dict__.items()
                    if callable(member) and not name.startswith("_")
                }
                implementation_methods = {
                    name: member for name, member in implementation.__dict__.items()
                    if callable(member) and not name.startswith("_")
                }
                self.assertEqual(set(implementation_methods), set(protocol_methods))
                for name, method in protocol_methods.items():
                    self.assertEqual(
                        list(inspect.signature(implementation_methods[name]).parameters),
                        list(inspect.signature(method).parameters),
                    )

    def test_capabilities_require_all_values(self) -> None:
        with self.assertRaises(TypeError):
            Capabilities()  # type: ignore[call-arg]
        self.assertEqual(list(inspect.signature(Capabilities).parameters), ["click_through_window", "window_stacking", "status_icon", "ime_control"])

    def test_backend_is_cached_after_single_creation(self) -> None:
        created = OsBackend(
            Capabilities(True, True, True, True), Mock(), Mock(), Mock(), Mock()
        )
        with patch("keyseq.infrastructure.os_backend.sys.platform", "win32"), patch("keyseq.infrastructure.os_backend._backend", None), patch(
            "keyseq.infrastructure.os_backend.windows.backend.create_backend", return_value=created
        ) as create:
            self.assertIs(get_backend(), created)
            self.assertIs(get_backend(), created)
            create.assert_called_once_with()

    def test_backend_factory_assembles_all_windows_adapters(self) -> None:
        with patch("keyseq.infrastructure.os_backend.windows.backend.ime_control"), \
             patch("keyseq.infrastructure.os_backend.windows.backend.own_ime_status"):
            from keyseq.infrastructure.os_backend.windows.backend import create_backend

            backend = create_backend()
        self.assertIsInstance(backend.ime, WindowsImeBackend)
        self.assertIsInstance(backend.window, WindowsWindowBackend)
        self.assertIsInstance(backend.tk_keys, WindowsTkKeyTranslator)
        self.assertIsInstance(backend.app, WindowsAppIdentity)

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

    def test_window_backend_converts_tk_windows_before_delegation(self) -> None:
        backend = WindowsWindowBackend()
        window = Mock()
        window.wm_frame.return_value = "2a"
        window.winfo_id.return_value = 17
        with patch("keyseq.infrastructure.os_backend.windows.backend.win32_window.place_window_below", return_value=True) as place, \
             patch("keyseq.infrastructure.os_backend.windows.backend.win32_window.make_click_through_overlay", return_value=True) as overlay:
            self.assertEqual(backend.window_handle(window), 42)
            self.assertTrue(backend.place_window_below(window, 99))
            self.assertTrue(backend.make_click_through_overlay(window))
        place.assert_called_once_with(42, 99)
        overlay.assert_called_once_with(17)

    def test_translator_and_app_identity_delegate_through_modules(self) -> None:
        with patch("keyseq.infrastructure.os_backend.windows.backend.win32_window.vk_to_scan_code", return_value=30) as scan, \
             patch("keyseq.infrastructure.os_backend.windows.backend.win32_window.vk_to_char", return_value="a") as char, \
             patch("keyseq.infrastructure.os_backend.windows.backend.win32_window.set_app_user_model_id", return_value=True) as identity, \
             patch("keyseq.infrastructure.os_backend.windows.backend.app_relaunch.relaunch_app", return_value=None) as relaunch:
            translator = WindowsTkKeyTranslator()
            app = WindowsAppIdentity()
            self.assertEqual(translator.vk_to_scan_code(65), 30)
            self.assertEqual(translator.vk_to_char(65), "a")
            self.assertTrue(app.apply_process_identity("keyseq.app"))
            self.assertIsNone(app.relaunch("C:/work"))
        scan.assert_called_once_with(65)
        char.assert_called_once_with(65)
        identity.assert_called_once_with("keyseq.app")
        relaunch.assert_called_once_with("C:/work")


if __name__ == "__main__":
    unittest.main()
