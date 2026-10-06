"""UI coverage for the compact sequence pane."""

import re
import tkinter as tk
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.app import App


def _trigger(key, values, *, label=None):
    return {
        "key": key,
        "label": label or key,
        "actions": [{"type": "text", "value": value} for value in values],
    }


class CompactSequenceViewTest(unittest.TestCase):
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
            side_effect=AssertionError("unexpected keymap history save"),
        ))
        try:
            cls.app = App()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display is unavailable: {error}")
        cls.addClassCleanup(cls.app.destroy)
        cls.app.update_idletasks()
        cls.initially_open = cls.app.compact_sequence.is_open

    def setUp(self):
        self.app = type(self).app
        if self.app._compact_mode:
            self.app.show_full_view()
        self.app.data = self.app.config_service.normalize_runtime_data({
            "triggers": [],
            "keymaps": [{
                "id": "km1", "label": "Main", "mappings": {"a": "b"},
                "triggers": [
                    _trigger("f1", ["one", "two", "three", "four", "five", "six"]),
                    _trigger("f1", ["duplicate"]),
                    _trigger("f2", ["other one", "other two", "other three"]),
                ],
            }],
            "active_keymap_id": "km1",
        })
        self.app._selected_trigger_idx = 0
        self.app.state.reset_indices()
        self.app._indices["f1"] = 1
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()
        self.app.call_view._open_by_trigger.clear()
        self.app.call_view._manually_operated.clear()
        self.app.call_view.on_selection_changed()
        if self.app.compact_sequence.is_open:
            self.app.compact_sequence.on_heading_click()
        self.app.show_compact_view()
        self.app.update()
        self.box = self.app.compact_view.trigger_box
        self.panes = self.box.trigger_panes
        self.sequence = self.app.compact_sequence
        self.frame = self.sequence.frame

    def _open(self):
        if not self.sequence.is_open:
            self.frame.heading.event_generate("<Button-1>")
            self.app.update()

    def _row_event(self, sequence, row):
        self.frame.action_list.see(row)
        self.app.update_idletasks()
        bounds = self.frame.action_list.bbox(row)
        self.assertIsNotNone(bounds, f"row {row} must be visible for {sequence}")
        _x, y, _width, height = bounds
        self.frame.action_list.event_generate(sequence, x=5, y=y + height // 2)
        self.app.update()

    def _key(self, keysym, *, state=0):
        self.frame.action_list.focus_force()
        self.app.update()
        self.frame.action_list.event_generate(f"<KeyPress-{keysym}>", state=state)
        self.app.update()

    def _invoke_registered_binding(self, sequence):
        script = self.frame.action_list.bind(sequence)
        match = re.search(r"\[([^\s\]]+)\s+([^\]]*)\]", script)
        self.assertIsNotNone(match, f"missing Tcl callback for {sequence}")
        command, substitutions = match.groups()
        args = [self.frame.action_list._w if token == "%W" else "0"
                for token in substitutions.split()]
        return self.frame.action_list.tk.call(command, *args)

    def test_default_closed_heading_moves_between_trigger_and_sequence_panes(self):
        self.assertFalse(type(self).initially_open)
        self.assertFalse(self.sequence.is_open)
        self.assertEqual(self.frame.heading.cget("text"), "▸ シーケンス")
        self.assertEqual(len(self.panes.panes()), 1)
        self.assertIn(self.frame.heading, self.box.trigger_frame.pack_slaves())
        self.assertNotIn(str(self.frame.body), list(map(str, self.panes.panes())))

        self._open()
        self.assertEqual(self.frame.heading.cget("text"), "▾ シーケンス")
        self.assertEqual(list(map(str, self.panes.panes()))[1], str(self.frame.body))
        self.assertIn(self.frame.heading, self.frame.body.pack_slaves())

        self.frame.heading.event_generate("<Button-1>")
        self.app.update()
        self.assertFalse(self.sequence.is_open)
        self.assertEqual(self.frame.heading.cget("text"), "▸ シーケンス")
        self.assertIn(self.frame.heading, self.box.trigger_frame.pack_slaves())

    def test_sequence_pane_stays_before_an_open_call_pane(self):
        self.app.call_view.on_heading_click()
        self._open()
        panes = list(map(str, self.panes.panes()))
        self.assertEqual(panes[1], str(self.frame.body))
        self.assertEqual(panes[2], str(self.box.call_view_frame.body))

    def test_rows_match_full_view_and_follow_compact_trigger_selection(self):
        full_rows = tuple(self.app.full_view.action_list.get(0, tk.END))
        self._open()
        self.assertEqual(tuple(self.frame.action_list.get(0, tk.END)), full_rows)
        self.assertTrue(full_rows[1].startswith("▶ "))
        self.assertEqual(self.frame.action_list.curselection(), (1,))

        self.app.trigger_panel.refresh_actions(select=(0, 2))
        self.assertEqual(self.app.full_view.action_list.curselection(), (0, 1, 2))
        self.assertEqual(self.frame.action_list.curselection(), (1,))

        self.app.trigger_panel.set_selected_trigger_index(2)
        compact_rows = tuple(self.frame.action_list.get(0, tk.END))
        self.assertEqual(self.frame.action_list.curselection(), (0,))
        self.assertTrue(compact_rows[0].startswith("▶ "))
        self.app.show_full_view()
        self.app.update()
        self.assertEqual(tuple(self.app.full_view.action_list.get(0, tk.END)), compact_rows)

    def test_click_commit_and_press_cancellation_guards(self):
        self._open()
        self._row_event("<Button-1>", 2)
        self.assertEqual(self.frame.action_list.curselection(), (1,))
        self._row_event("<ButtonRelease-1>", 2)
        self.assertEqual(self.app._indices["f1"], 2)

        self._row_event("<Button-1>", 0)
        self._row_event("<ButtonRelease-1>", 1)
        self.assertEqual(self.app._indices["f1"], 2)

        self._row_event("<Button-1>", 2)
        self.app.trigger_panel.set_selected_trigger_index(2)
        self._row_event("<ButtonRelease-1>", 2)
        self.assertEqual(self.app._indices["f2"], 0)
        self.app.trigger_panel.set_selected_trigger_index(0)

        self._row_event("<Button-1>", 4)
        self.app.trigger_panel.refresh_actions()
        self._row_event("<ButtonRelease-1>", 4)
        self.assertEqual(self.app._indices["f1"], 2)

        self._row_event("<Button-1>", 3)
        with patch.object(self.app, "_active_trigger_set_id", return_value="other-set"):
            self._row_event("<ButtonRelease-1>", 3)
        self.assertEqual(self.app._indices["f1"], 2)

        self._row_event("<Button-1>", 3)
        self.frame.heading.event_generate("<Button-1>")
        self.app.update()
        self.frame.heading.event_generate("<Button-1>")
        self.app.update()
        self._row_event("<ButtonRelease-1>", 3)
        self.assertEqual(self.app._indices["f1"], 2)

    def test_navigation_rejects_ineffective_trigger_and_running_callee(self):
        self._open()
        self._key("Down")
        self.assertEqual(self.app._indices["f1"], 2)
        self._key("Up")
        self.assertEqual(self.app._indices["f1"], 1)
        self._key("Home")
        self.assertEqual(self.app._indices["f1"], 0)
        self._key("End")
        self.assertEqual(self.app._indices["f1"], 5)
        self._key("Home", state=1)
        self.assertEqual(self.app._indices["f1"], 5)

        self.app.trigger_panel.set_selected_trigger_index(1)
        before = self.app._indices["f1"]
        self._key("Down")
        self.assertEqual(self.app._indices["f1"], before)

        self.app.trigger_panel.set_selected_trigger_index(0)
        self._key("Home")
        with patch.object(self.app.sequence_runner, "is_running_chain_callee", return_value=True):
            self._key("Down")
            self.assertEqual(self.app._indices["f1"], 0)
            self._row_event("<Button-1>", 2)
            self._row_event("<ButtonRelease-1>", 2)
        self.assertEqual(self.app._indices["f1"], 0)

    def test_prior_next_use_visible_rows_and_noop_bindings_do_not_edit(self):
        self._open()
        count = self.sequence._visible_rows()
        self._key("Home")
        self._key("Next")
        self.assertEqual(self.app._indices["f1"], min(5, count))
        self._key("End")
        self._key("Prior")
        self.assertEqual(self.app._indices["f1"], max(0, 5 - count))

        actions_before = list(self.app.trigger_panel.selected_trigger()["actions"])
        index_before = self.app._indices["f1"]
        for sequence in ("<Double-Button-1>", "<Control-c>", "<Control-C>"):
            self.assertTrue(self.frame.action_list.bind(sequence))
        self.assertEqual(self.sequence.ignore(SimpleNamespace()), "break")
        with patch.object(self.app.trigger_panel, "edit_action") as edit_action:
            self.assertEqual(self._invoke_registered_binding("<Double-Button-1>"), "break")
            edit_action.assert_not_called()
        copy = patch.object(self.app.list_clipboard, "copy")
        with copy as copy_actions:
            self.frame.action_list.focus_force()
            self.app.update()
            self.frame.action_list.event_generate("<Control-c>")
            self.frame.action_list.event_generate("<Control-C>")
            self.app.update()
            copy_actions.assert_not_called()
        self.assertEqual(self.app.trigger_panel.selected_trigger()["actions"], actions_before)
        self.assertEqual(self.app._indices["f1"], index_before)

    def test_view_switch_and_hook_state_change_refresh_compact_rows(self):
        self.app.show_full_view()
        self.app.trigger_panel.set_selected_trigger_index(2)
        expected = tuple(self.app.full_view.action_list.get(0, tk.END))
        with patch.object(self.app.trigger_panel, "refresh_actions", wraps=self.app.trigger_panel.refresh_actions) as refresh:
            self.app.show_compact_view()
            self.app.update()
            refresh.assert_called()
        self._open()
        self.assertEqual(tuple(self.frame.action_list.get(0, tk.END)), expected)

        self.app.hook.hook_active = True
        self.app.hook.custom_input_enabled = True
        self.addCleanup(setattr, self.app.hook, "hook_active", False)
        self.addCleanup(setattr, self.app.hook, "custom_input_enabled", True)
        with patch.object(self.app.trigger_panel, "refresh_actions", wraps=self.app.trigger_panel.refresh_actions) as refresh:
            self.app.hook.toggle_custom_input_enabled()
            self.app.update()
            refresh.assert_called_once_with()
        self.assertEqual(tuple(self.frame.action_list.get(0, tk.END)), expected)
        self.app.hook.hook_active = False
        self.app.hook.custom_input_enabled = True
