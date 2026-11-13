from __future__ import annotations

import ast
from dataclasses import fields
import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from keyseq.infrastructure.os_backend import (
    AppIdentity, Capabilities, ImeBackend, KeyboardBackend, KeySend, MouseBackend,
    OsBackend, TkKeyTranslator, WindowBackend, get_backend,
)
from keyseq.domain.default_profile import (
    MACOS_DEFAULT_PROFILE,
    WINDOWS_DEFAULT_PROFILE,
)


class OsBackendContractTests(unittest.TestCase):
    def test_os_backend_fields_include_profile_with_windows_constructor_default(self) -> None:
        self.assertEqual(
            [field.name for field in fields(OsBackend)],
            [
                "capabilities", "ime", "window", "tk_keys", "app", "keyboard",
                "mouse", "default_profile", "queued_hook_dispatch",
            ],
        )
        legacy_constructor = OsBackend(
            Capabilities(True, True, True, True), Mock(), Mock(), Mock(), Mock(), Mock(), Mock()
        )
        self.assertIs(legacy_constructor.default_profile, WINDOWS_DEFAULT_PROFILE)
        self.assertFalse(legacy_constructor.queued_hook_dispatch)

    def test_macos_stub_contracts_and_factory(self) -> None:
        from keyseq.infrastructure.os_backend.macos.backend import (
            MacAppIdentity, MacImeBackend, MacKeyboardBackend, MacMouseBackend,
            MacTkKeyTranslator, MacWindowBackend, create_backend,
        )

        for protocol, implementation in (
            (ImeBackend, MacImeBackend), (WindowBackend, MacWindowBackend),
            (TkKeyTranslator, MacTkKeyTranslator), (AppIdentity, MacAppIdentity),
            (KeyboardBackend, MacKeyboardBackend), (MouseBackend, MacMouseBackend),
        ):
            expected = {n: m for n, m in protocol.__dict__.items() if callable(m) and not n.startswith("_")}
            actual = {n: m for n, m in implementation.__dict__.items() if callable(m) and not n.startswith("_")}
            self.assertEqual(set(actual), set(expected))
            for name in expected:
                self.assertEqual(list(inspect.signature(actual[name]).parameters), list(inspect.signature(expected[name]).parameters))
        backend = create_backend()
        self.assertEqual(backend.capabilities, Capabilities(False, False, False, False))
        self.assertIs(backend.default_profile, MACOS_DEFAULT_PROFILE)
        self.assertTrue(backend.queued_hook_dispatch)
        self.assertIsInstance(backend.keyboard, MacKeyboardBackend)
        with patch("keyseq.infrastructure.os_backend.macos.backend.EventTap") as tap_factory:
            handle = backend.keyboard.register_global_hook(lambda _event: None)
            backend.keyboard.unregister_hook(handle)
        tap_factory.return_value.start.assert_called_once_with()
        tap_factory.return_value.stop.assert_called_once_with()

    def test_get_backend_creates_macos_stub(self) -> None:
        from keyseq.infrastructure.os_backend.macos.backend import MacKeyboardBackend
        with patch("keyseq.infrastructure.os_backend.sys.platform", "darwin"), patch("keyseq.infrastructure.os_backend._backend", None):
            self.assertIsInstance(get_backend().keyboard, MacKeyboardBackend)

    def test_windows_backend_matches_ime_protocol(self) -> None:
        if sys.platform != "win32": self.skipTest("Windows implementation")
        from keyseq.infrastructure.os_backend.windows.backend import WindowsImeBackend
        protocol = {name: member for name, member in ImeBackend.__dict__.items() if callable(member) and not name.startswith("_")}
        implementation = {name: member for name, member in WindowsImeBackend.__dict__.items() if callable(member) and not name.startswith("_")}
        self.assertEqual(set(implementation), set(protocol))
        for name in protocol:
            self.assertEqual(list(inspect.signature(implementation[name]).parameters), list(inspect.signature(protocol[name]).parameters))

    def test_windows_backends_match_new_protocols(self) -> None:
        if sys.platform != "win32": self.skipTest("Windows implementation")
        from keyseq.infrastructure.os_backend.windows.backend import WindowsAppIdentity, WindowsTkKeyTranslator, WindowsWindowBackend
        from keyseq.infrastructure.os_backend.windows.keyboard_backend import WindowsKeyboardBackend
        from keyseq.infrastructure.os_backend.windows.mouse_backend import WindowsMouseBackend
        for protocol, implementation in (
            (WindowBackend, WindowsWindowBackend),
            (TkKeyTranslator, WindowsTkKeyTranslator),
            (AppIdentity, WindowsAppIdentity),
            (KeyboardBackend, WindowsKeyboardBackend),
            (MouseBackend, WindowsMouseBackend),
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
            Capabilities(True, True, True, True), Mock(), Mock(), Mock(), Mock(), Mock(), Mock()
        )
        # macos のスタブは標準ライブラリだけなので、どの OS でも patch 先を import できる
        with patch("keyseq.infrastructure.os_backend.sys.platform", "darwin"), patch("keyseq.infrastructure.os_backend._backend", None), patch(
            "keyseq.infrastructure.os_backend.macos.backend.create_backend", return_value=created
        ) as create:
            self.assertIs(get_backend(), created)
            self.assertIs(get_backend(), created)
            create.assert_called_once_with()

    def test_backend_factory_assembles_all_windows_adapters(self) -> None:
        if sys.platform != "win32": self.skipTest("Windows implementation")
        from keyseq.infrastructure.os_backend.windows.backend import WindowsAppIdentity, WindowsImeBackend, WindowsTkKeyTranslator, WindowsWindowBackend
        from keyseq.infrastructure.os_backend.windows.keyboard_backend import WindowsKeyboardBackend
        from keyseq.infrastructure.os_backend.windows.mouse_backend import WindowsMouseBackend
        with patch("keyseq.infrastructure.os_backend.windows.backend.ime_control"), \
             patch("keyseq.infrastructure.os_backend.windows.backend.own_ime_status"):
            from keyseq.infrastructure.os_backend.windows.backend import create_backend

            backend = create_backend()
        self.assertIsInstance(backend.ime, WindowsImeBackend)
        self.assertIs(backend.default_profile, WINDOWS_DEFAULT_PROFILE)
        self.assertFalse(backend.queued_hook_dispatch)
        self.assertIsInstance(backend.window, WindowsWindowBackend)
        self.assertIsInstance(backend.tk_keys, WindowsTkKeyTranslator)
        self.assertIsInstance(backend.app, WindowsAppIdentity)
        self.assertIsInstance(backend.keyboard, WindowsKeyboardBackend)
        self.assertIsInstance(backend.mouse, WindowsMouseBackend)

    def test_key_send_and_new_contracts_are_public_exports(self) -> None:
        from keyseq.infrastructure import os_backend

        for name in ("KeySend", "KeyboardBackend", "MouseBackend"):
            with self.subTest(name=name):
                self.assertIn(name, os_backend.__all__)
                self.assertIs(getattr(os_backend, name), globals()[name])
        self.assertEqual(list(inspect.signature(KeySend).parameters), ["kind", "values", "key"])

    def test_app_loads_backend_before_tk_initialization(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "keyseq/presentation/app.py").read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        app_class = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "App")
        init = next(node for node in app_class.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
        backend_calls = [
            node for node in ast.walk(init)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "get_backend"
        ]
        super_calls = [
            node for node in ast.walk(init)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "__init__" and isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Name) and node.func.value.func.id == "super"
        ]
        self.assertTrue(backend_calls)
        self.assertTrue(super_calls)
        self.assertLess(min(node.lineno for node in backend_calls), min(node.lineno for node in super_calls))

    def test_non_windows_platform_raises(self) -> None:
        with patch("keyseq.infrastructure.os_backend.sys.platform", "linux"), patch("keyseq.infrastructure.os_backend._backend", None):
            with self.assertRaises(RuntimeError):
                get_backend()

    def test_window_id_is_converted_and_failures_return_safe_values(self) -> None:
        if sys.platform != "win32": self.skipTest("Windows implementation")
        from keyseq.infrastructure.os_backend.windows.backend import WindowsImeBackend
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
        if sys.platform != "win32": self.skipTest("Windows implementation")
        from keyseq.infrastructure.os_backend.windows.backend import WindowsWindowBackend
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
        if sys.platform != "win32": self.skipTest("Windows implementation")
        from keyseq.infrastructure.os_backend.windows.backend import WindowsAppIdentity, WindowsTkKeyTranslator
        with patch("keyseq.infrastructure.os_backend.windows.backend.win32_window.vk_to_scan_code", return_value=30) as scan, \
             patch("keyseq.infrastructure.os_backend.windows.backend.win32_window.vk_to_char", return_value="a") as char, \
             patch("keyseq.infrastructure.os_backend.windows.backend.tk_key_translator.numpad_name_from_tk_event", return_value="num enter") as numpad, \
             patch("keyseq.infrastructure.os_backend.windows.backend.win32_window.set_app_user_model_id", return_value=True) as identity, \
             patch("keyseq.infrastructure.os_backend.windows.backend.app_relaunch.relaunch_app", return_value=None) as relaunch:
            translator = WindowsTkKeyTranslator()
            app = WindowsAppIdentity()
            self.assertEqual(translator.vk_to_scan_code(65), 30)
            self.assertEqual(translator.vk_to_char(65), "a")
            self.assertEqual(translator.numpad_name(13, 0x40000), "num enter")
            self.assertTrue(app.apply_process_identity("keyseq.app"))
            self.assertIsNone(app.relaunch("C:/work"))
        scan.assert_called_once_with(65)
        char.assert_called_once_with(65)
        numpad.assert_called_once_with(13, 0x40000)
        identity.assert_called_once_with("keyseq.app")
        relaunch.assert_called_once_with("C:/work")


if __name__ == "__main__":
    unittest.main()
