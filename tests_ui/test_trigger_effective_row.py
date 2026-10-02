import unittest
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.controllers.trigger_panel import trigger_panel_controller as panel_module


class _DialogResult:
    def __init__(self, result):
        self.result = result

    def wait_window(self):
        pass


def make_runtime():
    return {
        "keymaps": [{
            "id": "main",
            "label": "Main",
            "mappings": {},
            "triggers": [
                {"key": "f1", "label": "First", "actions": [{"type": "text", "text": "first"}]},
                {"key": "F1", "label": "Shadow", "actions": [{"type": "text", "text": "shadow"}]},
                {"key": "caller", "label": "Caller", "actions": [
                    {"type": "system", "op": "call", "target": "f1"},
                ]},
                {"key": "f12", "label": "Stop overlap", "actions": []},
            ],
        }],
        "active_keymap_id": "main",
        "hook_stop_key": "f12",
        "hook_toggle_key": "",
        "keymap_switch_keys": {},
    }


class TriggerEffectiveRowUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(StartupIo, "load_startup_and_config"):
            cls.app = App()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        self.original_data = self.app.data
        self.app.data = self.app.config_service.normalize_runtime_data(make_runtime())
        self.app._indices = {"f1": 2}
        self.app._selected_trigger_idx = 1
        self.app.trigger_panel.refresh_triggers()

    def tearDown(self):
        window = self.app.layout.keyboard_window
        if window is not None:
            window._handle_close()
        self.app.data = self.original_data
        self.app._indices = {}
        self.app._selected_trigger_idx = 0
        self.app.trigger_panel.refresh_triggers()
        self.app.dirty_tracker.set_dirty(False)

    @property
    def rows(self):
        return self.app.data["keymaps"][0]["triggers"]

    def test_duplicate_row_is_gray_in_both_lists_and_stop_reason_wins(self):
        full = self.app.full_view.trigger_box.trigger_list
        compact = self.app.compact_view.trigger_box.trigger_list
        for listing in (full, compact):
            self.assertIn("上のトリガーと重複", listing.get(1))
            self.assertEqual(listing.itemcget(1, "foreground"), "#888888")
            self.assertIn("停止キーと重複", listing.get(3))
            self.assertNotIn("上のトリガーと重複", listing.get(3))

    def test_same_key_label_edit_skips_duplicate_check(self):
        with patch.object(self.app.trigger_service, "key_exists", wraps=self.app.trigger_service.key_exists) as key_exists, \
             patch.object(panel_module, "TriggerDialog", return_value=_DialogResult({
                 "key": "f1", "label": "Renamed shadow",
             })):
            self.app.trigger_panel.rename_trigger()

        key_exists.assert_not_called()
        self.assertEqual(self.rows[1]["label"], "Renamed shadow")

    def test_shadowed_key_change_keeps_effective_state_and_call_target(self):
        caller = self.rows[2]
        with patch.object(self.app.sequence_runner, "cancel_pending_wait") as cancel_wait, \
             patch.object(self.app.state, "rekey_trigger") as rekey, \
             patch.object(panel_module, "TriggerDialog", return_value=_DialogResult({
                 "key": "f2", "label": "Moved shadow",
             })):
            self.app.trigger_panel.rename_trigger()

        self.assertEqual((self.app._indices.get("f1"), self.app._indices.get("f2")), (2, 0))
        self.assertEqual(caller["actions"][0]["target"], "f1")
        cancel_wait.assert_not_called()
        rekey.assert_not_called()

    def test_effective_key_change_keeps_existing_state_transfer_and_call_rewrite(self):
        self.rows[1]["key"] = "f3"
        self.app._selected_trigger_idx = 0
        self.app.trigger_panel.refresh_triggers()
        with patch.object(panel_module, "TriggerDialog", return_value=_DialogResult({
            "key": "f2", "label": "Renamed first",
        })):
            self.app.trigger_panel.rename_trigger()

        self.assertEqual(self.app._indices.get("f2"), 2)
        self.assertNotIn("f1", self.app._indices)
        self.assertEqual(self.rows[2]["actions"][0]["target"], "f2")

    def test_call_candidates_exclude_duplicate_but_keep_overlap_rows(self):
        candidates, _check = self.app.trigger_panel._action_edit._call_dialog_options("caller")
        self.assertEqual(candidates, [("f1", "First"), ("f12", "Stop overlap")])

    def test_keyboard_uses_first_duplicate_row_number(self):
        self.app.layout.open_keyboard_window()
        window = self.app.layout.keyboard_window
        window.update_from_config(self.app.data, custom_enabled=True)
        self.assertEqual(window._display_map["f1"], "1")
        self.assertEqual(window._kind_map["f1"], "trigger")


if __name__ == "__main__":
    unittest.main()
