"""Unit tests for saving the scroll direction preference."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from keyseq.domain.mouse_scroll import ScrollInvert
from keyseq.presentation.app import App


class FakeBooleanVar:
    def __init__(self, value=False):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class ScrollInvertSettingTests(unittest.TestCase):
    def _fake_app(self, saved=None, selected=(False, False), current=None, write_result=True):
        vertical = FakeBooleanVar(selected[0])
        horizontal = FakeBooleanVar(selected[1])
        startup_io = SimpleNamespace(write_startup=Mock(return_value=write_result))
        app = SimpleNamespace(
            _startup_settings={"scroll_invert": saved},
            _scroll_invert=current or ScrollInvert(),
            ui_vars=SimpleNamespace(
                scroll_invert_vertical_var=vertical,
                scroll_invert_horizontal_var=horizontal,
            ),
            startup_io=startup_io,
        )
        return app, vertical, horizontal, startup_io.write_startup

    def _run(self, app):
        App.set_scroll_invert(app)

    def test_same_as_saved_does_not_write_or_replace_current_value(self):
        current = ScrollInvert(vertical=True)
        app, _vertical, _horizontal, write_startup = self._fake_app(
            saved={"vertical": False}, selected=(False, False), current=current,
        )

        self._run(app)

        write_startup.assert_not_called()
        self.assertIs(app._scroll_invert, current)

    def test_selected_values_are_saved_with_both_axes_and_become_current(self):
        app, _vertical, _horizontal, write_startup = self._fake_app(
            saved={}, selected=(True, False),
        )

        self._run(app)

        write_startup.assert_called_once_with(
            {"scroll_invert": {"vertical": True, "horizontal": False}},
        )
        self.assertEqual(app._scroll_invert, ScrollInvert(vertical=True))

    def test_invalid_saved_value_is_compared_after_coercion(self):
        app, _vertical, _horizontal, write_startup = self._fake_app(
            saved="x", selected=(False, False),
        )

        self._run(app)

        write_startup.assert_not_called()

    def test_failed_save_restores_saved_values_and_keeps_current_value(self):
        current = ScrollInvert(horizontal=True)
        app, vertical, horizontal, write_startup = self._fake_app(
            saved={"vertical": True}, selected=(False, True), current=current, write_result=False,
        )

        self._run(app)

        write_startup.assert_called_once_with(
            {"scroll_invert": {"vertical": False, "horizontal": True}},
        )
        self.assertTrue(vertical.get())
        self.assertFalse(horizontal.get())
        self.assertIs(app._scroll_invert, current)

    def test_does_not_touch_configuration_dirty_state(self):
        app, _vertical, _horizontal, write_startup = self._fake_app(
            saved={}, selected=(True, False),
        )

        self._run(app)

        write_startup.assert_called_once_with(
            {"scroll_invert": {"vertical": True, "horizontal": False}},
        )
        self.assertEqual(app._scroll_invert, ScrollInvert(vertical=True))


if __name__ == "__main__":
    unittest.main()
