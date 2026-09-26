import unittest
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.application.input_router import StopHookAction
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
        self.assertNotIn("重複", trigger_list.get(3))
        self.assertNotEqual(trigger_list.itemcget(3, "foreground"), "#888888")
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
        self.app.keymap_panel.on_keymap_list_select()
        self.assertEqual(self.app.keymap_panel.selected_keymap_list_index(), 1)
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.KeymapEditDialog",
            return_value=_DialogResult({"key": "f10", "label": "Other edited"}),
        ), patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.showerror",
            side_effect=AssertionError("unexpected keymap edit error"),
        ):
            self.app.keymap_panel.edit_selected_keymap()
        self.assertEqual(self.app.keymap_service.find_switch_key_for_keymap(self.app.data, "km2"), "f10")

    def test_shadowed_notice_uses_flash_and_keeps_stop_message_without_paused_notice(self):
        status_before = self.app.ui_vars.status_var.get()
        flash_var = self.app.ui_vars.flash_message_var
        previous_flash = flash_var.get()
        previous_before = self.app.hook._status_before_shadowed_notice
        previous_last = self.app.hook._last_shadowed_status
        previous_custom_enabled = self.app.hook.custom_input_enabled
        previous_pressed = self.app.key_state_manager.pressed_keys
        self.app.hook._status_before_shadowed_notice = None
        self.app.hook._last_shadowed_status = None
        flash_var.set("停止しました")

        def set_flash(message, *, auto_clear=True):
            flash_var.set(message)

        try:
            conflicts = self.app.hook._key_overlap_report().shadowed_for_key("f12")
            self.assertTrue(conflicts)
            with patch.object(self.app, "_set_flash_message", side_effect=set_flash) as set_flash_message:
                self.app.hook.show_shadowed_assignments(StopHookAction(), conflicts)
                first_message = flash_var.get()
                self.assertIn("停止しました", first_message)
                self.assertIn("f12 は停止キーと重複", first_message)
                self.assertEqual(self.app.ui_vars.status_var.get(), status_before)
                self.assertEqual(set_flash_message.call_args.args[0], first_message)

                self.app.hook.show_shadowed_assignments(StopHookAction(), conflicts)
                self.assertEqual(flash_var.get(), first_message)

                self.app.hook.custom_input_enabled = False
                route = self.app.input_router.handle(
                    SimpleNamespace(event_type="down", name="f12", scan_code=None)
                )
                self.assertFalse(route.shadowed)
                self.assertEqual(flash_var.get(), first_message)
                self.assertEqual(set_flash_message.call_count, 2)
        finally:
            flash_var.set(previous_flash)
            self.app.hook._status_before_shadowed_notice = previous_before
            self.app.hook._last_shadowed_status = previous_last
            self.app.hook.custom_input_enabled = previous_custom_enabled
            self.app.key_state_manager.clear()
            for key in previous_pressed:
                self.app.key_state_manager.key_down(key)

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
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.showerror"
        )
        with errors as showerror:
            self.assertFalse(self.app.keymap_panel.validate_keymap_switch_assignment("f1", target_id="km4"))
            showerror.assert_called_once()
        with patch(
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.showerror"
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
            "keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.showerror",
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

    def test_keyboard_display_prefers_trigger_then_reserved_keys(self):
        self.app.layout.open_keyboard_window()
        window = self.app.layout.keyboard_window
        self.assertIsNotNone(window)
        window.update_from_config(self.app.data, custom_enabled=True)
        self.assertEqual(window._kind_map["a"], "trigger")
        self.assertEqual(window._kind_map["f12"], "stop")

    def test_overlap_table_is_shared_by_rows_and_reused_on_input(self):
        from keyseq.application.key_overlap import analyze_key_overlaps

        with patch("keyseq.presentation.app.analyze_key_overlaps", wraps=analyze_key_overlaps) as analyze:
            with patch.object(
                self.app.keymap_panel,
                "refresh_keymap_list_ui",
                wraps=self.app.keymap_panel.refresh_keymap_list_ui,
            ) as refresh_keymaps:
                self.app.trigger_panel.refresh_triggers()
            first_report = self.app._key_overlap_report()
            self.assertIs(refresh_keymaps.call_args.kwargs["overlap"], first_report)
            self.app.input_router.handle(
                SimpleNamespace(event_type="down", name="f12", scan_code=None)
            )
            analyze.assert_called_once()

            self.app.data["keymaps"][0]["mappings"].pop("a")
            self.app.trigger_panel.refresh_triggers()
            self.assertIsNot(self.app._key_overlap_report(), first_report)
            self.assertEqual(analyze.call_count, 2)

    def test_keymap_list_redraw_rebuilds_overlap_table(self):
        previous_report = self.app._key_overlap_report()
        self.app.data["keymap_switch_keys"].pop("n")
        self.app.keymap_panel.refresh_keymap_list_ui()
        current_report = self.app._key_overlap_report()
        self.assertIsNot(current_report, previous_report)
        self.assertIsNone(current_report.trigger_conflict("n"))


class _DialogResult:
    def __init__(self, result):
        self.result = result

    def wait_window(self):
        return None


if __name__ == "__main__":
    unittest.main()
