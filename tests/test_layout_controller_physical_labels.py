import unittest
from unittest.mock import Mock, call

from keyseq.presentation.controllers.layout_controller import LayoutController


class LayoutControllerPhysicalLabelsTests(unittest.TestCase):
    def make_controller(self):
        app = Mock()
        app.data = {}
        app.ui_vars.keyboard_show_physical_key_labels_var.get.return_value = True
        controller = LayoutController.__new__(LayoutController)
        controller._app = app
        controller.refresh_keyboard_window = Mock()
        return controller, app

    def test_apply_updates_data_refreshes_and_marks_dirty(self):
        controller, app = self.make_controller()
        controller.apply_keyboard_show_physical_key_labels()
        self.assertTrue(app.data["keyboard_show_physical_key_labels"])
        controller.refresh_keyboard_window.assert_called_once_with()
        app.dirty_tracker.set_dirty.assert_called_once_with(True)

    def test_toggle_applies_before_persisting(self):
        controller, _app = self.make_controller()
        controller.persist_keyboard_layout_selection = Mock()
        events = []
        controller.apply_keyboard_show_physical_key_labels = Mock(side_effect=lambda: events.append("apply"))
        controller.persist_keyboard_layout_selection.side_effect = lambda: events.append("persist")
        controller.toggle_keyboard_show_physical_key_labels()
        self.assertEqual(events, ["apply", "persist"])


if __name__ == "__main__":
    unittest.main()
