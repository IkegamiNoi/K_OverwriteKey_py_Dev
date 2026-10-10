from __future__ import annotations

import unittest

from keyseq.application.held_inputs import HeldInputs


class FakeInputGateway:
    """記録だけを行い、実際のキーやマウス入力は送らない gateway。"""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.failures: dict[tuple, Exception] = {}
        self.on_press_key = None
        self.on_mouse_down = None
        self.identities = {
            "ctrl": (29, False),
            "left ctrl": (29, False),
            "right ctrl": (29, True),
        }

    def key_identity(self, key: str) -> tuple[int, bool]:
        return self.identities.get(key, (ord(key[0]), False))

    def _record(self, call: tuple) -> None:
        self.calls.append(call)
        error = self.failures.get(call)
        if error is not None:
            raise error

    def press_key(self, key: str) -> None:
        call = ("press_key", key)
        self.calls.append(call)
        if self.on_press_key is not None:
            self.on_press_key(key)
        error = self.failures.get(call)
        if error is not None:
            raise error

    def release_key(self, key: str) -> None:
        self._record(("release_key", key))

    def mouse_down(self, button: str, x=None, y=None) -> None:
        call = ("mouse_down", button, x, y)
        self.calls.append(call)
        if self.on_mouse_down is not None:
            self.on_mouse_down(button)
        error = self.failures.get(call)
        if error is not None:
            raise error

    def mouse_up(self, button: str, x=None, y=None) -> None:
        self._record(("mouse_up", button, x, y))


class HeldInputsTests(unittest.TestCase):
    def test_display_names_localize_all_mouse_buttons_in_press_order(self) -> None:
        gateway = FakeInputGateway()
        held = HeldInputs(gateway)
        held.press_mouse("f1", "right")
        held.press_key("f1", "shift")
        held.press_mouse("f1", "middle")
        held.press_mouse("f1", "left")
        self.assertEqual(held.display_names, ("マウス右", "shift", "マウス中", "マウス左"))

    def setUp(self) -> None:
        self.gateway = FakeInputGateway()
        self.guard_calls: list[str] = []
        self.changes: list[tuple[str, ...]] = []
        self.held = HeldInputs(
            self.gateway,
            enter_send_guard=lambda: self.guard_calls.append("enter"),
            exit_send_guard=lambda: self.guard_calls.append("exit"),
            on_change=self.changes.append,
        )

    def test_press_records_before_sending_and_uses_send_guard(self) -> None:
        observed: list[tuple[str, ...]] = []
        self.gateway.on_press_key = lambda _key: observed.append(
            self.held.display_names
        )

        self.held.press_key("trigger", "a")

        self.assertEqual(observed, [("a",)])
        self.assertEqual(self.gateway.calls, [("press_key", "a")])
        self.assertEqual(self.guard_calls, ["enter", "exit"])
        self.assertEqual(self.held.display_names, ("a",))

    def test_failed_press_compensates_and_preserves_original_error(self) -> None:
        send_error = RuntimeError("press failed")
        compensation_error = OSError("release failed")
        self.gateway.failures[("press_key", "a")] = send_error
        self.gateway.failures[("release_key", "a")] = compensation_error
        observed: list[tuple[str, ...]] = []
        self.gateway.on_press_key = lambda _key: observed.append(
            self.held.display_names
        )

        with self.assertRaises(RuntimeError) as caught:
            self.held.press_key("trigger", "a")

        self.assertIs(caught.exception, send_error)
        self.assertEqual(observed, [("a",)])
        self.assertEqual(self.gateway.calls, [
            ("press_key", "a"), ("release_key", "a"),
        ])
        self.assertEqual(self.held.display_names, ("a",))
        self.assertEqual(self.changes, [("a",)])
        self.gateway.failures.clear()
        self.assertEqual(self.held.release_all(), [])
        self.assertEqual(self.held.display_names, ())

    def test_mouse_press_records_before_sending_and_compensates_failure(self) -> None:
        send_error = RuntimeError("mouse down failed")
        self.gateway.failures[("mouse_down", "left", 10, 20)] = send_error
        observed: list[tuple[str, ...]] = []
        self.gateway.on_mouse_down = lambda _button: observed.append(
            self.held.display_names
        )

        with self.assertRaises(RuntimeError) as caught:
            self.held.press_mouse("trigger", "left", (10, 20))

        self.assertIs(caught.exception, send_error)
        self.assertEqual(observed, [("マウス左",)])
        self.assertEqual(self.gateway.calls, [
            ("mouse_down", "left", 10, 20), ("mouse_up", "left", None, None),
        ])
        self.assertEqual(self.held.display_names, ())

    def test_release_key_sends_even_when_identity_is_not_held(self) -> None:
        self.held.release_key("a")

        self.assertEqual(self.gateway.calls, [("release_key", "a")])
        self.assertEqual(self.held.display_names, ())
        self.assertEqual(self.guard_calls, ["enter", "exit"])
        self.assertEqual(self.changes, [])

    def test_explicit_release_failure_keeps_record_for_retry(self) -> None:
        self.held.press_key("owner", "a")
        release_error = RuntimeError("release failed")
        self.gateway.failures[("release_key", "a")] = release_error

        with self.assertRaises(RuntimeError) as caught:
            self.held.release_key("a")

        self.assertIs(caught.exception, release_error)
        self.assertEqual(self.held.display_names, ("a",))
        self.gateway.failures.clear()
        self.held.release_key("a")
        self.assertEqual(self.held.display_names, ())

    def test_explicit_mouse_release_failure_keeps_record_for_retry(self) -> None:
        self.held.press_mouse("owner", "left")
        release_error = RuntimeError("mouse release failed")
        self.gateway.failures[("mouse_up", "left", None, None)] = release_error

        with self.assertRaises(RuntimeError) as caught:
            self.held.release_mouse("left")

        self.assertIs(caught.exception, release_error)
        self.assertEqual(self.held.display_names, ("マウス左",))
        self.gateway.failures.clear()
        self.held.release_mouse("left")
        self.assertEqual(self.held.display_names, ())

    def test_aliases_share_identity_but_left_and_right_keys_do_not(self) -> None:
        self.held.press_key("one", "ctrl")
        self.held.press_key("two", "left ctrl")
        self.held.press_key("three", "right ctrl")

        self.assertEqual(self.held.display_names, ("left ctrl", "right ctrl"))
        self.assertEqual(
            self.held.release_owner("one"),
            [],
        )
        self.assertEqual(self.held.display_names, ("left ctrl", "right ctrl"))
        self.assertEqual(self.held.release_owner("two"), [])
        self.assertEqual(self.held.display_names, ("right ctrl",))
        self.assertEqual(self.held.release_owner("three"), [])
        self.assertEqual(self.gateway.calls[-2:], [
            ("release_key", "left ctrl"), ("release_key", "right ctrl"),
        ])

    def test_owner_overwrite_keeps_first_press_order(self) -> None:
        self.held.press_key("first-owner", "a")
        self.held.press_key("second-owner", "b")
        self.held.press_key("updated-owner", "a")

        self.assertEqual(self.held.display_names, ("a", "b"))
        self.assertEqual(self.held.release_owner("first-owner"), [])
        self.assertEqual(self.held.release_owner("updated-owner"), [])
        self.assertEqual(self.held.release_owner("second-owner"), [])
        self.assertEqual(self.gateway.calls[-2:], [
            ("release_key", "a"), ("release_key", "b"),
        ])

    def test_release_owner_collects_errors_and_continues(self) -> None:
        mouse_error = RuntimeError("mouse release failed")
        self.gateway.failures[("mouse_up", "left", None, None)] = mouse_error
        self.held.press_mouse("owner", "left", (10, 20))
        self.held.press_key("owner", "b")
        self.held.press_key("other", "c")

        errors = self.held.release_owner("owner")

        self.assertEqual(errors, [mouse_error])
        self.assertEqual(self.gateway.calls[-2:], [
            ("mouse_up", "left", None, None), ("release_key", "b"),
        ])
        self.assertEqual(self.held.display_names, ("マウス左", "c"))
        self.gateway.failures.clear()
        self.assertEqual(self.held.release_owner("owner"), [])
        self.assertEqual(self.held.display_names, ("c",))

    def test_release_all_collects_errors_and_continues(self) -> None:
        key_error = RuntimeError("key release failed")
        self.gateway.failures[("release_key", "a")] = key_error
        self.held.press_key("first", "a")
        self.held.press_mouse("second", "right")
        self.held.press_key("third", "b")

        errors = self.held.release_all()

        self.assertEqual(errors, [key_error])
        self.assertEqual(self.gateway.calls[-3:], [
            ("release_key", "a"), ("mouse_up", "right", None, None),
            ("release_key", "b"),
        ])
        self.assertEqual(self.held.display_names, ("a",))
        self.gateway.failures.clear()
        self.assertEqual(self.held.release_all(), [])
        self.assertEqual(self.gateway.calls[-1], ("release_key", "a"))
        self.assertEqual(self.held.display_names, ())

    def test_suspend_and_resume_keyboard_preserve_set_and_skip_mouse(self) -> None:
        self.held.press_key("owner", "a")
        self.held.press_mouse("owner", "left", (10, 20))
        initial_names = self.held.display_names
        initial_calls = len(self.gateway.calls)

        self.held.suspend_keyboard()
        self.assertEqual(self.held.display_names, initial_names)
        self.assertEqual(self.gateway.calls[initial_calls:], [("release_key", "a")])

        suspended_calls = len(self.gateway.calls)
        self.held.resume_keyboard()
        self.assertEqual(self.held.display_names, initial_names)
        self.assertEqual(self.gateway.calls[suspended_calls:], [("press_key", "a")])
        self.assertEqual(self.guard_calls, ["enter", "exit"] * 3)

    def test_suspend_keyboard_continues_after_key_release_error(self) -> None:
        release_error = RuntimeError("release failed")
        self.gateway.failures[("release_key", "a")] = release_error
        self.held.press_key("owner", "a")
        self.held.press_key("owner", "b")
        self.held.press_mouse("owner", "left")
        before_suspend = len(self.gateway.calls)

        with self.assertRaises(RuntimeError) as caught:
            self.held.suspend_keyboard()

        self.assertIs(caught.exception, release_error)
        self.assertEqual(self.gateway.calls[before_suspend:], [
            ("release_key", "a"), ("release_key", "b"),
        ])
        self.assertEqual(self.held.display_names, ("a", "b", "マウス左"))

    def test_resume_keyboard_compensates_failed_repress(self) -> None:
        self.held.press_key("owner", "a")
        self.held.suspend_keyboard()
        send_error = RuntimeError("repress failed")
        self.gateway.failures[("press_key", "a")] = send_error

        with self.assertRaises(RuntimeError) as caught:
            self.held.resume_keyboard()

        self.assertIs(caught.exception, send_error)
        self.assertEqual(self.gateway.calls[-2:], [
            ("press_key", "a"), ("release_key", "a"),
        ])
        self.assertEqual(self.held.display_names, ())

    def test_resume_continues_after_failure_and_keeps_later_owner(self) -> None:
        self.held.press_key("first-owner", "a")
        self.held.press_key("second-owner", "b")
        self.held.suspend_keyboard()
        send_error = RuntimeError("first repress failed")
        self.gateway.failures[("press_key", "a")] = send_error
        before_resume = len(self.gateway.calls)

        with self.assertRaises(RuntimeError) as caught:
            self.held.resume_keyboard()

        self.assertIs(caught.exception, send_error)
        self.assertEqual(self.gateway.calls[before_resume:], [
            ("press_key", "a"), ("release_key", "a"), ("press_key", "b"),
        ])
        self.assertEqual(self.held.display_names, ("b",))
        self.gateway.failures.clear()
        self.assertEqual(self.held.release_owner("second-owner"), [])
        self.assertEqual(self.gateway.calls[-1], ("release_key", "b"))
        self.assertEqual(self.held.display_names, ())

    def test_change_callback_receives_ordered_display_names(self) -> None:
        self.held.press_key("owner", "a")
        self.held.press_mouse("owner", "left")
        self.held.release_key("missing")
        self.held.release_mouse("missing")
        self.held.release_key("a")
        self.held.release_mouse("left")

        self.assertEqual(self.changes, [
            ("a",), ("a", "マウス左"), ("マウス左",), (),
        ])


if __name__ == "__main__":
    unittest.main()
