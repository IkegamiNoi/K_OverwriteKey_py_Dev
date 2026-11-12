import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.presentation.controllers.pane_layout import pane_layout_controller as controller_module
from keyseq.presentation.controllers.pane_layout.pane_layout_controller import (
    PaneLayoutController,
)
from keyseq.presentation.pane_width_rules import MinWidths


class PaneLayoutInitialApplyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.panes = Mock()
        self.app = Mock()
        self.app.full_view.panes = self.panes
        self.controller = PaneLayoutController(self.app)

    def test_install_schedules_initial_apply_check_once(self) -> None:
        self.controller.install()

        self.app.after_idle.assert_called_once_with(
            self.controller._apply_if_already_sized
        )

    def test_sized_panes_apply_initial_widths(self) -> None:
        self.panes.winfo_width.return_value = 2
        with patch.object(self.controller, "apply_initial_widths") as apply:
            self.controller._apply_if_already_sized()

        apply.assert_called_once_with()
        self.assertTrue(self.controller._applied)

    def test_unsized_panes_do_not_apply_initial_widths(self) -> None:
        self.panes.winfo_width.return_value = 1
        with patch.object(self.controller, "apply_initial_widths") as apply:
            self.controller._apply_if_already_sized()

        apply.assert_not_called()
        self.assertFalse(self.controller._applied)

    def test_already_applied_does_not_apply_again(self) -> None:
        self.controller._applied = True
        self.panes.winfo_width.return_value = 2
        with patch.object(self.controller, "apply_initial_widths") as apply:
            self.controller._apply_if_already_sized()

        apply.assert_not_called()

    def _apply_initial_height(self, fit: int, work_height: int, state: str = "normal") -> Mock:
        self.app.wm_state.return_value = state
        self.app.wm_maxsize.return_value = (1920, work_height)
        self.app.winfo_width.return_value = 780
        self.app._startup_settings = {}
        self.panes.winfo_width.return_value = 780
        self.app.full_view.keymap_box.winfo_reqwidth.return_value = 200
        self.app.full_view.trigger_box.winfo_reqwidth.return_value = 200
        self.controller.min_widths = MinWidths(100, 100, 100)
        with patch.object(self.controller, "_measure"), \
                patch.object(self.controller, "apply_layout") as layout, \
                patch.object(controller_module, "measure_window_fit_height", return_value=fit) as measure:
            self.controller._apply_if_already_sized()
            self.controller._apply_if_already_sized()
            self.controller._on_configure(SimpleNamespace(width=780))
        layout.assert_called_once_with()
        return measure

    def test_initial_height_fits_contents_with_default_floor_and_screen_height_cap(self) -> None:
        for fit, work_height, expected in (
            (700, 1200, 820), (950, 1200, 950), (1500, 1000, 1000), (700, 750, 750),
        ):
            with self.subTest(fit=fit, work_height=work_height):
                self.controller._applied = False
                self.app.geometry.reset_mock()
                measure = self._apply_initial_height(fit, work_height)
                self.app.geometry.assert_called_once_with(f"780x{expected}")
                measure.assert_called_once_with(self.app)
                self.app.startup_io.write_startup.assert_not_called()

    def test_initial_height_is_unchanged_when_maximized_or_minimized(self) -> None:
        for state in ("zoomed", "iconic"):
            with self.subTest(state=state):
                self.controller._applied = False
                measure = self._apply_initial_height(950, 1200, state)
                self.app.geometry.assert_not_called()
                self.app.wm_maxsize.assert_not_called()
                measure.assert_not_called()


if __name__ == "__main__":
    unittest.main()
