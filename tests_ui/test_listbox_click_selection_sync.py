"""回帰テスト: Listbox のクリック/ドラッグ中は状態を保留し、解放時に同期する。"""

import unittest
from unittest.mock import Mock, patch

from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.startup_io import StartupIo


def make_runtime():
    return {
        "keymaps": [
            {
                "id": f"km{number}",
                "label": f"Map {number}",
                "mappings": {},
                "triggers": [
                    {
                        "key": f"f{trigger_number}",
                        "label": f"Trigger {trigger_number}",
                        "actions": [
                            {"type": "text", "value": "one"},
                            {"type": "text", "value": "two"},
                            {"type": "text", "value": "three"},
                        ],
                    }
                    for trigger_number in range(1, 4)
                ],
            }
            for number in range(1, 4)
        ],
        "active_keymap_id": "km1",
        "keymap_switch_keys": {},
        "hook_stop_key": "f12",
        "hook_toggle_key": "f11",
    }


class ListboxClickSelectionSyncTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(StartupIo, "load_startup_and_config"):
            cls.app = App()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.original_data = self.app.data
        self.original_selected_trigger_idx = self.app._selected_trigger_idx
        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime())
        self.app.state.reset_indices()
        self.app._selected_trigger_idx = 0
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()
        self.app.update()
        self.addCleanup(self._restore_app)

    def _restore_app(self):
        self.app.data = self.original_data
        self.app._selected_trigger_idx = self.original_selected_trigger_idx
        self.app.state.reset_indices()
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()

    def _row_xy(self, listbox, row):
        self.app.update_idletasks()
        x, y, width, height = listbox.bbox(row)
        return x + width // 2, y + height // 2

    def _press(self, listbox, row):
        x, y = self._row_xy(listbox, row)
        listbox.focus_force()
        listbox.event_generate("<ButtonPress-1>", x=x, y=y)
        self.app.update_idletasks()
        return x, y

    def _motion(self, listbox, row):
        x, y = self._row_xy(listbox, row)
        listbox.event_generate("<B1-Motion>", x=x, y=y, state=0x100)
        self.app.update_idletasks()

    def _release(self, listbox, row):
        x, y = self._row_xy(listbox, row)
        listbox.event_generate("<ButtonRelease-1>", x=x, y=y)
        self.app.update()

    def _click(self, listbox, row):
        self._press(listbox, row)
        self._release(listbox, row)

    def _assert_row_synced(self, listbox, row):
        self.assertEqual(tuple(listbox.curselection()), (row,))
        self.assertEqual(int(listbox.index("active")), row)

    def test_trigger_click_selects_row_and_updates_selected_trigger(self):
        listbox = self.app.full_view.trigger_box.trigger_list

        self._click(listbox, 1)

        self._assert_row_synced(listbox, 1)
        self.assertEqual(self.app.trigger_panel.selected_trigger_index(), 1)

    def test_sequence_click_selects_row_and_updates_next_execution_index(self):
        listbox = self.app.full_view.action_list

        self._click(listbox, 1)

        self._assert_row_synced(listbox, 1)
        self.assertEqual(self.app._indices["f1"], 1)

    def test_keymap_click_selects_row_and_activates_keymap(self):
        listbox = self.app.full_view.keymap_box.keymap_listbox

        self._click(listbox, 1)

        self._assert_row_synced(listbox, 1)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km2")

    def test_rejected_keymap_click_restores_selection_and_active_row(self):
        listbox = self.app.full_view.keymap_box.keymap_listbox
        with patch.object(self.app.state, "can_switch_keymap", return_value=False):
            self._click(listbox, 1)

        self._assert_row_synced(listbox, 0)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km1")

    def test_sequence_drag_commits_only_the_row_released(self):
        listbox = self.app.full_view.action_list
        original_reset = self.app.sequence_runner.reset_loop_frames
        reset = Mock(wraps=original_reset)
        self.app.sequence_runner.reset_loop_frames = reset
        self.addCleanup(setattr, self.app.sequence_runner, "reset_loop_frames", original_reset)

        self._press(listbox, 0)
        self._motion(listbox, 1)
        self.assertEqual(tuple(listbox.curselection()), (1,))
        self.assertEqual(self.app._indices["f1"], 0)
        reset.assert_not_called()
        self._motion(listbox, 2)
        self.assertEqual(tuple(listbox.curselection()), (2,))
        self.assertEqual(self.app._indices["f1"], 0)
        reset.assert_not_called()
        self._release(listbox, 2)

        self._assert_row_synced(listbox, 2)
        self.assertEqual(self.app._indices["f1"], 2)
        reset.assert_called_once_with("f1")

    def test_keymap_drag_commits_only_the_row_released(self):
        listbox = self.app.full_view.keymap_box.keymap_listbox
        original_activate = self.app.keymap_panel.activate_keymap_by_id
        activate = Mock(wraps=original_activate)
        self.app.keymap_panel.activate_keymap_by_id = activate
        self.addCleanup(setattr, self.app.keymap_panel, "activate_keymap_by_id", original_activate)

        self._press(listbox, 0)
        self._motion(listbox, 1)
        self.assertEqual(tuple(listbox.curselection()), (1,))
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km1")
        activate.assert_not_called()
        self._motion(listbox, 2)
        self.assertEqual(tuple(listbox.curselection()), (2,))
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km1")
        activate.assert_not_called()
        self._release(listbox, 2)

        self._assert_row_synced(listbox, 2)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km3")
        activate.assert_called_once()
        self.assertEqual(activate.call_args.args[0], "km3")

    def test_drag_back_to_original_keymap_keeps_active_keymap(self):
        listbox = self.app.full_view.keymap_box.keymap_listbox
        original_activate = self.app.keymap_panel.activate_keymap_by_id
        activate = Mock(wraps=original_activate)
        self.app.keymap_panel.activate_keymap_by_id = activate
        self.addCleanup(setattr, self.app.keymap_panel, "activate_keymap_by_id", original_activate)

        self._press(listbox, 0)
        self._motion(listbox, 1)
        self._motion(listbox, 0)
        self._release(listbox, 0)

        self._assert_row_synced(listbox, 0)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km1")
        activate.assert_not_called()

    def test_shift_click_keeps_selection_and_active_row_together(self):
        listbox = self.app.full_view.trigger_box.trigger_list
        x, y = self._row_xy(listbox, 2)
        listbox.focus_force()
        listbox.event_generate("<ButtonPress-1>", x=x, y=y, state=0x1)
        listbox.event_generate("<ButtonRelease-1>", x=x, y=y, state=0x1)
        self.app.update()

        selection = tuple(listbox.curselection())
        self.assertEqual(len(selection), 1)
        self.assertEqual(int(listbox.index("active")), selection[0])
        self.assertEqual(self.app.trigger_panel.selected_trigger_index(), selection[0])

    def test_key_release_keeps_active_row_authoritative_for_sequence(self):
        listbox = self.app.full_view.action_list
        listbox.focus_force()
        self.app.update()
        listbox.selection_clear(0, "end")
        listbox.selection_set(0)
        listbox.activate(1)

        listbox.event_generate("<KeyRelease>", keysym="Down")
        self.app.update_idletasks()

        self._assert_row_synced(listbox, 1)
        self.assertEqual(self.app._indices["f1"], 1)


if __name__ == "__main__":
    unittest.main()
