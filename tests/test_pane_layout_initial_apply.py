import unittest
from unittest.mock import Mock, patch

from keyseq.presentation.controllers.pane_layout.pane_layout_controller import (
    PaneLayoutController,
)


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


if __name__ == "__main__":
    unittest.main()
