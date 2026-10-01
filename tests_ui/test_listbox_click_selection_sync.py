"""回帰テスト: Listbox のクリック選択と下線行を同じ操作で同期する。"""

import unittest
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.startup_io import StartupIo


def make_runtime():
    return {
        "keymaps": [
            {
                "id": "km1",
                "label": "Main",
                "mappings": {},
                "triggers": [
                    {
                        "key": "f1",
                        "label": "First",
                        "actions": [
                            {"type": "text", "value": "one"},
                            {"type": "text", "value": "two"},
                        ],
                    },
                    {"key": "f2", "label": "Second", "actions": []},
                ],
            },
            {
                "id": "km2",
                "label": "Other",
                "mappings": {},
                "triggers": [
                    {"key": "f3", "label": "Third", "actions": []},
                ],
            },
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
        self.addCleanup(self._restore_app)

    def _restore_app(self):
        self.app.data = self.original_data
        self.app._selected_trigger_idx = self.original_selected_trigger_idx
        self.app.state.reset_indices()
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()

    def _click_row_in_tk_order(self, listbox, row):
        """Model Listbox Button-1 selection/virtual event followed by release activation."""
        listbox.focus_force()
        self.app.update()
        listbox.selection_clear(0, "end")
        listbox.selection_set(row)
        listbox.event_generate("<<ListboxSelect>>")
        listbox.activate(row)
        self.app.update_idletasks()

    def _assert_row_synced(self, listbox, row):
        self.assertEqual(tuple(listbox.curselection()), (row,))
        self.assertEqual(int(listbox.index("active")), row)

    def test_trigger_click_selects_row_and_updates_selected_trigger(self):
        listbox = self.app.full_view.trigger_box.trigger_list

        self._click_row_in_tk_order(listbox, 1)

        self._assert_row_synced(listbox, 1)
        self.assertEqual(self.app.trigger_panel.selected_trigger_index(), 1)

    def test_sequence_click_selects_row_and_updates_next_execution_index(self):
        listbox = self.app.full_view.action_list

        self._click_row_in_tk_order(listbox, 1)

        self._assert_row_synced(listbox, 1)
        self.assertEqual(self.app._indices["f1"], 1)

    def test_keymap_click_selects_row_and_activates_keymap(self):
        listbox = self.app.full_view.keymap_box.keymap_listbox

        self._click_row_in_tk_order(listbox, 1)

        self._assert_row_synced(listbox, 1)
        self.assertEqual(self.app.keymap_service.get_active_keymap_id(self.app.data), "km2")

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
