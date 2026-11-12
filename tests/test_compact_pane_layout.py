import unittest
from unittest.mock import ANY, Mock, call

from keyseq.presentation.controllers.compact_pane_layout import CompactPaneLayout


class CompactPaneLayoutTests(unittest.TestCase):
    def test_install_schedules_layout_when_panes_are_mapped(self) -> None:
        app = Mock()
        panes = app.compact_view.trigger_box.trigger_panes
        panes.winfo_ismapped.return_value = False
        layout = CompactPaneLayout(app)

        layout.install()

        panes.bind.assert_has_calls([
            call("<Configure>", layout._on_configure, add="+"),
            call("<Map>", ANY, add="+"),
        ])
        app.after_idle.assert_not_called()
        on_map = next(args.args[1] for args in panes.bind.call_args_list
                      if args.args[0] == "<Map>")
        panes.winfo_ismapped.return_value = True
        on_map(object())
        on_map(object())

        app.after_idle.assert_called_once_with(layout._apply_height)
        self.assertEqual(layout.layout_id, app.after_idle.return_value)
