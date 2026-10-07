"""「選んでから実行」の presentation 配線。実 config への保存は遮断する。"""
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.application.input_router import TriggerAction
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io.startup_io import StartupIo


class SelectBeforeRunUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stack = ExitStack()
        cls.addClassCleanup(stack.close)
        stack.enter_context(patch.object(app_module.JsonRepository, "save_json"))
        stack.enter_context(patch.object(ConfigService, "ensure_split_config_dirs"))
        stack.enter_context(patch.object(
            ConfigService, "load_keymap_set_history",
            return_value=({"recent": [], "categories": []}, contracts.HISTORY_OK),
        ))
        stack.enter_context(patch.object(
            ConfigService, "save_keymap_set_history",
            side_effect=AssertionError("unpatched history save"),
        ))
        stack.enter_context(patch.object(StartupIo, "load_startup_and_config"))
        cls.app = app_module.App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.update()
        cls.app.destroy()

    def setUp(self):
        app = self.app
        app.update()
        app.show_full_view()
        app.state.reset_indices()
        app.data = app.config_service.normalize_runtime_data({
            "select_before_run": False,
            "active_keymap_id": "main",
            "keymaps": [{
                "id": "main", "label": "Main", "mappings": {},
                "triggers": [
                    {"key": "f1", "select_before_run": False,
                     "actions": [{"type": "text", "text": "first"}]},
                    {"key": "f2", "select_before_run": True,
                     "actions": [{"type": "text", "text": "second"}]},
                    {"key": "F1", "select_before_run": True,
                     "actions": [{"type": "text", "text": "shadow"}]},
                ],
            }],
            "hook_stop_key": "", "hook_toggle_key": "", "keymap_switch_keys": {},
        })
        app._selected_trigger_idx = 0
        app._sync_control_vars_from_data()
        app.trigger_panel.refresh_triggers()
        app.trigger_panel.refresh_actions()
        app.dirty_tracker.clear_individual_dirty_flags()
        app.dirty_tracker.set_dirty(False)
        app._clear_flash_message()
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.execute = stack.enter_context(patch.object(
            app.action_executor, "execute", return_value=True,
        ))
        self.callback_error = stack.enter_context(patch.object(
            app, "report_callback_exception",
        ))
        self.addCleanup(self.callback_error.assert_not_called)
        self.addCleanup(app.show_full_view)

    @property
    def global_check(self):
        return self.app.full_view.hook_frame.select_before_run_check

    @property
    def sequence_check(self):
        return self.app.full_view.sequence_box.select_before_run_chk

    def select_row(self, index):
        self.app._selected_trigger_idx = index
        self.app.trigger_panel.sync_trigger_selection_to_views()
        self.app.trigger_panel.refresh_actions()

    def test_global_operation_updates_data_and_config_dirty(self):
        for expected in (True, False):
            self.app.dirty_tracker.set_dirty(False)
            self.global_check.invoke()
            self.assertIs(self.app.data["select_before_run"], expected)
            self.assertTrue(self.app.dirty_tracker.config_dirty)
            self.assertTrue(self.app.dirty_tracker.is_dirty)

    def test_compact_global_check_is_disabled_and_shares_value(self):
        compact = self.app.compact_view.hook_frame.select_before_run_check
        self.app.show_compact_view()
        self.assertTrue(compact.instate(["disabled"]))
        self.assertEqual(str(compact.cget("variable")),
                         str(self.app.ui_vars.select_before_run_var))
        for expected in (True, False):
            self.app.ui_vars.select_before_run_var.set(expected)
            self.app.toggle_select_before_run()
            self.assertEqual(compact.instate(["selected"]), expected)
            compact.invoke()
            self.assertIs(self.app.data["select_before_run"], expected)
        def checks(widget):
            result = []
            for child in widget.winfo_children():
                if child.winfo_class() == "TCheckbutton":
                    result.append(child)
                result.extend(checks(child))
            return result

        self.assertEqual(
            [check for check in checks(self.app.compact_view)
             if check.cget("text") == "選んでから実行"], [compact],
        )

    def test_data_replacement_syncs_global_value_without_dirty(self):
        for value, expected in ((True, True), (False, False), (None, False), (1, False)):
            with self.subTest(value=value):
                self.app.data = {**self.app.data, "select_before_run": value}
                self.app._sync_control_vars_from_data()
                self.assertEqual(self.global_check.instate(["selected"]), expected)
                self.assertFalse(self.app.dirty_tracker.is_dirty)
        self.app.data = {k: v for k, v in self.app.data.items() if k != "select_before_run"}
        self.app._sync_control_vars_from_data()
        self.assertFalse(self.app.ui_vars.select_before_run_var.get())

    def test_sequence_selection_sync_and_writeback_marks_only_sequence(self):
        first = self.app.trigger_panel.selected_trigger()
        self.assertFalse(self.sequence_check.instate(["selected"]))
        self.app.trigger_panel.select_trigger_by_key("f2")
        second = self.app.trigger_panel.selected_trigger()
        self.assertTrue(self.sequence_check.instate(["selected"]))
        self.sequence_check.invoke()
        self.assertIs(second["select_before_run"], False)
        self.assertTrue(second[ConfigService.INTERNAL_SEQUENCE_DIRTY])
        self.assertFalse(first["select_before_run"])
        self.assertFalse(self.app.dirty_tracker.config_dirty)
        self.select_row(0)
        self.sequence_check.invoke()
        self.assertIs(first["select_before_run"], True)
        self.assertTrue(first[ConfigService.INTERNAL_SEQUENCE_DIRTY])
        self.select_row(1)
        self.assertFalse(self.sequence_check.instate(["selected"]))

    def test_unchanged_sequence_value_does_not_mark_dirty(self):
        from keyseq.presentation.controllers.trigger_panel.select_before_run import (
            update_select_before_run,
        )
        with patch.object(self.app, "mark_sequence_dirty") as mark:
            update_select_before_run(self.app.trigger_panel)
        mark.assert_not_called()

    def test_no_selection_and_gray_row_follow_run_to_end_editing(self):
        self.select_row(2)
        shadow = self.app.trigger_panel.selected_trigger()
        self.assertFalse(self.app.trigger_panel.selected_trigger_is_effective())
        self.assertTrue(self.sequence_check.instate(["selected"]))
        self.assertEqual(self.sequence_check.instate(["disabled"]),
                         self.app.full_view.sequence_box.run_to_end_chk.instate(["disabled"]))
        self.sequence_check.invoke()
        self.assertIs(shadow["select_before_run"], False)
        self.assertTrue(shadow[ConfigService.INTERNAL_SEQUENCE_DIRTY])
        self.select_row(99)
        self.assertFalse(self.app.ui_vars.sequence_select_before_run_var.get())
        with patch.object(self.app, "mark_sequence_dirty") as mark:
            self.sequence_check.invoke()
        mark.assert_not_called()

    def test_checkbox_positions(self):
        full = self.app.full_view.hook_frame
        compact = self.app.compact_view.hook_frame
        # フル表示は個別指定と同じ行（右隣）・省略表示は次の行
        self.assertIs(full.select_before_run_check.master, full.hook_keys_individual_check.master)
        siblings = full.hook_keys_individual_check.master.pack_slaves()
        self.assertEqual(siblings.index(full.select_before_run_check),
                         siblings.index(full.hook_keys_individual_check) + 1)
        self.assertEqual(int(compact.select_before_run_check.grid_info()["row"]),
                         int(compact.hook_keys_individual_check.grid_info()["row"]) + 1)
        box = self.app.full_view.sequence_box
        children = box.run_to_end_chk.master.pack_slaves()
        self.assertIs(children[children.index(box.run_to_end_chk) + 1], self.sequence_check)
        self.assertLess(children.index(self.sequence_check),
                        children.index(box.run_to_end_delay_entry.master))

    def test_global_wiring_selects_then_executes_in_both_views(self):
        for compact in (False, True):
            with self.subTest(compact=compact):
                self.app.state.reset_indices()
                self.select_row(1)
                self.execute.reset_mock()
                self.app.data["select_before_run"] = True
                if compact:
                    self.app.show_compact_view()
                self.app.sequence_runner.handle_key("F1")
                self.assertEqual(self.app.trigger_panel.selected_trigger_key(), "f1")
                self.execute.assert_not_called()
                self.assertEqual(self.app._flash_message,
                                 "f1 を選びました（もう一度押すと実行します）")
                self.app.sequence_runner.handle_key("f1")
                self.execute.assert_called_once_with({"type": "text", "text": "first", "label": ""})

    def test_both_settings_off_preserves_immediate_execution(self):
        self.select_row(1)
        self.app.sequence_runner.handle_key("f1")
        self.execute.assert_called_once_with({"type": "text", "text": "first", "label": ""})

    def test_individual_wiring_works_with_global_off(self):
        self.app.sequence_runner.handle_key("f2")
        self.execute.assert_not_called()
        self.assertEqual(self.app.trigger_panel.selected_trigger_key(), "f2")
        self.app.sequence_runner.handle_key("f2")
        self.execute.assert_called_once_with({"type": "text", "text": "second", "label": ""})

    def test_repeat_reaches_runner_and_is_ignored_after_select_only(self):
        self.app.data["select_before_run"] = True
        self.select_row(1)
        self.app.sequence_runner.handle_key("f1")
        with patch.object(self.app.sequence_runner, "handle_key",
                          wraps=self.app.sequence_runner.handle_key) as handle:
            self.app.action_executor.execute_router_action(TriggerAction("f1", True))
        handle.assert_called_once_with("f1", True)
        self.execute.assert_not_called()
        self.app.action_executor.execute_router_action(TriggerAction("f1", False))
        self.execute.assert_called_once_with({"type": "text", "text": "first", "label": ""})

    def test_gray_duplicate_selection_only_moves_to_effective_row(self):
        self.app.data["select_before_run"] = True
        self.select_row(2)
        self.app.sequence_runner.handle_key("f1")
        self.execute.assert_not_called()
        self.assertEqual(self.app._selected_trigger_idx, 0)
        self.assertTrue(self.app.trigger_panel.selected_trigger_is_effective())
        self.assertEqual(self.app._flash_message,
                         "f1 を選びました（もう一度押すと実行します）")
        self.app.sequence_runner.handle_key("f1")
        self.execute.assert_called_once_with({"type": "text", "text": "first", "label": ""})
