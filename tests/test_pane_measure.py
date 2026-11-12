import unittest
from unittest.mock import Mock, patch

from keyseq.presentation.controllers.pane_layout import pane_measure


class PaneMeasureTests(unittest.TestCase):
    def test_fit_height_uses_full_main_area_basis(self) -> None:
        app = Mock()
        app.winfo_reqheight.return_value = 700
        app.full_view.panes.winfo_reqheight.return_value = 400
        with patch.object(pane_measure, "_sync_full_view_scroll_areas"), \
                patch.object(pane_measure, "_find_flash_message_label", return_value=None), \
                patch.object(pane_measure, "measure_main_area_basis_height") as basis:
            for height, minimum, fit in ((500, 550, 800), (501, 551, 801)):
                with self.subTest(height=height):
                    basis.return_value = height
                    self.assertEqual(pane_measure.measure_window_min_height(app), minimum)
                    self.assertEqual(pane_measure.measure_window_fit_height(app), fit)
