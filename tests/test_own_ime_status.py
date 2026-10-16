from __future__ import annotations

import unittest
from unittest.mock import patch

from keyseq.infrastructure import own_ime_status


class FakeApi:
    def __init__(self) -> None:
        self.context = 22
        self.is_open = True
        self.events: list[tuple[object, ...]] = []
        self.get_error: Exception | None = None
        self.set_error: Exception | None = None

    def get_context(self, hwnd: int) -> int | None:
        self.events.append(("context", hwnd))
        return self.context

    def release_context(self, hwnd: int, context: int) -> None:
        self.events.append(("release", hwnd, context))

    def get_open_status(self, context: int) -> bool:
        self.events.append(("get", context))
        if self.get_error:
            raise self.get_error
        return self.is_open

    def set_open_status(self, context: int, is_open: bool) -> bool:
        self.events.append(("set", context, is_open))
        if self.set_error:
            raise self.set_error
        self.is_open = is_open
        return True


class OwnImeStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = FakeApi()
        self.api_patch = patch.object(own_ime_status, "_get_api", return_value=self.api)
        self.api_patch.start()
        self.addCleanup(self.api_patch.stop)

    def test_get_status_releases_context(self) -> None:
        self.assertIs(own_ime_status.get_open_status(11), True)
        self.assertEqual(self.api.events[-1], ("release", 11, 22))

    def test_set_status_releases_context(self) -> None:
        self.assertTrue(own_ime_status.set_open_status(11, False))
        self.assertFalse(self.api.is_open)
        self.assertEqual(self.api.events[-1], ("release", 11, 22))

    def test_missing_context_does_not_call_status_or_release(self) -> None:
        self.api.context = None
        self.assertIsNone(own_ime_status.get_open_status(11))
        self.assertFalse(own_ime_status.set_open_status(11, False))
        self.assertEqual(self.api.events, [("context", 11), ("context", 11)])

    def test_api_exceptions_return_safe_values_and_release(self) -> None:
        self.api.get_error = RuntimeError("read failed")
        self.assertIsNone(own_ime_status.get_open_status(11))
        self.api.get_error = None
        self.api.set_error = RuntimeError("write failed")
        self.assertFalse(own_ime_status.set_open_status(11, False))
        self.assertEqual(self.api.events.count(("release", 11, 22)), 2)

    def test_unavailable_api_returns_safe_values(self) -> None:
        with patch.object(own_ime_status, "_get_api", return_value=None):
            self.assertIsNone(own_ime_status.get_open_status(11))
            self.assertFalse(own_ime_status.set_open_status(11, False))


class OwnImeStatusUnavailableApiTests(unittest.TestCase):
    def test_non_windows_api_construction_fails(self) -> None:
        with patch.object(own_ime_status.sys, "platform", "linux"):
            with self.assertRaises(OSError):
                own_ime_status._Win32OwnImeApi()
        with patch.object(own_ime_status, "_api", own_ime_status._UNINITIALIZED):
            with patch.object(own_ime_status.sys, "platform", "linux"):
                self.assertIsNone(own_ime_status.get_open_status(11))
                self.assertFalse(own_ime_status.set_open_status(11, False))


if __name__ == "__main__":
    unittest.main()
