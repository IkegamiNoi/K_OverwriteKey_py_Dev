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
                "mappings": {"a": "z", "f12": "q", "m": "x"},
                "triggers": [{"key": key, "label": key, "actions": []} for key in ("f12", "f11", "n", "a", "f2")],
            },
            {"id": "km2", "label": "Other", "mappings": {"b": "c"}, "triggers": [{"key": "f1", "actions": []}]},
            {"id": "km3", "label": "Third", "mappings": {}, "triggers": []},
            {"id": "km4", "label": "Fourth", "mappings": {}, "triggers": []},
        ],
        "active_keymap_id": "km1",
        "keymap_switch_keys": {"f12": "km2", "f11": "km3", "n": "km4"},
        "hook_stop_key": "f12",
        "hook_toggle_key": "f11",
    }


class Task05OverlapUiTest(unittest.TestCase):
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
        self.app._indices = {}
        self.app._selected_trigger_idx = 0
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

    def test_trigger_and_keymap_rows_show_reason_and_resolve_to_normal(self):
        trigger_list = self.app.full_view.trigger_box.trigger_list
        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        self.assertIn("停止キーと重複", trigger_list.get(0))
        self.assertEqual(trigger_list.itemcget(0, "foreground"), "#888888")
        self.assertIn("一時停止/再開キーと重複", trigger_list.get(1))
        self.assertIn("切替キーと重複", trigger_list.get(2))
        self.assertIn("置換と重複", trigger_list.get(3))
        self.assertIn("停止キーと重複", keymap_list.get(1))
        self.assertEqual(keymap_list.itemcget(1, "foreground"), "#888888")
        self.assertIn("一時停止/再開キーと重複", keymap_list.get(2))

        self.app.data["hook_stop_key"] = ""
        self.app.data["hook_toggle_key"] = ""
        self.app.data["keymap_switch_keys"].clear()
        self.app.data["keymaps"][0]["mappings"].pop("f12")
        self.app.trigger_panel.refresh_triggers()
        self.assertNotIn("重複", trigger_list.get(0))
        self.assertNotEqual(trigger_list.itemcget(0, "foreground"), "#888888")
        self.assertNotIn("重複", keymap_list.get(1))
        self.assertNotEqual(keymap_list.itemcget(1, "foreground"), "#888888")

    def test_shadowed_rows_remain_selectable_and_editable(self):
        trigger_list = self.app.full_view.trigger_box.trigger_list
        trigger_list.selection_set(0)
        trigger_list.activate(0)
        with patch(
            "keyseq.presentation.controllers.trigger_panel_controller.TriggerDialog",
            return_value=_DialogResult({"key": "f3", "label": "changed"}),
        ), patch(
            "keyseq.presentation.controllers.trigger_panel_controller.messagebox.showerror",
            side_effect=AssertionError("unexpected trigger edit error"),
        ):
            self.app.trigger_panel.rename_trigger()
        self.assertEqual(self.app.data["keymaps"][0]["triggers"][0]["key"], "f3")

        keymap_list = self.app.full_view.keymap_box.keymap_listbox
        keymap_list.selection_clear(0, "end")
        keymap_list.selection_set(1)
        keymap_list.activate(1)
        self.assertEqual(self.app.keymap_panel.selected_keymap_list_index(), 1)
        with patch(
            "keyseq.presentation.controllers.keymap_panel_controller.KeymapEditDialog",
            return_value=_DialogResult({"key": "f10", "label": "Other edited"}),
        ), patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror",
            side_effect=AssertionError("unexpected keymap edit error"),
        ):
            self.app.keymap_panel.edit_selected_keymap()
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km2"), "f10")

    def test_edit_refusals_use_active_or_all_keymap_sets_as_specified(self):
        with patch(
            "keyseq.presentation.controllers.trigger_panel_controller.TriggerDialog",
            return_value=_DialogResult({"key": "m", "label": ""}),
        ), patch(
            "keyseq.presentation.controllers.trigger_panel_controller.messagebox.showerror"
        ) as showerror:
            before = len(self.app.data["keymaps"][0]["triggers"])
            self.app.trigger_panel.add_trigger()
            showerror.assert_called_once()
            self.assertEqual(len(self.app.data["keymaps"][0]["triggers"]), before)

        errors = patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        )
        with errors as showerror:
            self.assertFalse(self.app.keymap_panel.validate_keymap_switch_assignment("f1", target_id="km4"))
            showerror.assert_called_once()
        with patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror"
        ) as showerror:
            self.assertFalse(self.app.keymap_panel.assign_keymap_from_keyboard_ui("f2", "b"))
            showerror.assert_called_once()

        with patch(
            "keyseq.presentation.controllers.trigger_panel_controller.TriggerDialog",
            return_value=_DialogResult({"key": "m", "label": ""}),
        ), patch(
            "keyseq.presentation.controllers.trigger_panel_controller.messagebox.showerror"
        ) as showerror:
            self.app._selected_trigger_idx = 4
            self.app.trigger_panel.rename_trigger()
            showerror.assert_called_once()
        self.assertEqual(self.app.data["keymaps"][0]["triggers"][4]["key"], "f2")

    def test_cross_keymap_trigger_and_replacement_source_is_allowed_and_control_capture_checks_all_maps(self):
        with patch(
            "keyseq.presentation.controllers.keymap_panel_controller.messagebox.showerror",
            side_effect=AssertionError("unexpected cross-keymap conflict"),
        ):
            self.assertTrue(self.app.keymap_panel.assign_keymap_from_keyboard_ui("f1", "b"))
        self.assertEqual(self.app.data["keymaps"][0]["mappings"]["f1"], "b")

        stop_checks = self.app.stop_key_capture._conflict_checks
        toggle_checks = self.app.toggle_key_capture._conflict_checks
        self.assertTrue(stop_checks[0][0](self.app, "f1"))
        self.assertTrue(toggle_checks[0][0](self.app, "f1"))
        self.assertTrue(stop_checks[3][0](self.app, "b"))
        self.assertTrue(toggle_checks[3][0](self.app, "b"))

    def test_keyboard_display_prefers_replacement_then_reserved_keys(self):
        self.app.layout.open_keyboard_window()
        window = self.app.layout.keyboard_window
        self.assertIsNotNone(window)
        window.update_from_config(self.app.data, custom_enabled=True)
        self.assertEqual(window._kind_map["a"], "keymap")
        self.assertEqual(window._kind_map["f12"], "stop")


class _DialogResult:
    def __init__(self, result):
        self.result = result

    def wait_window(self):
        return None


if __name__ == "__main__":
    unittest.main()
