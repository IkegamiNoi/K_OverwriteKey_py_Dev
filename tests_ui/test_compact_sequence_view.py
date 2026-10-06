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
from keyseq.presentation.compact_pane_heights import plan_compact_heights
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.views.full_view.call_view_frame import list_minimum_height


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
        stack.enter_context(patch.object(app_module, "load_startup_settings", return_value={}))
        stack.enter_context(patch.object(StartupIo, "load_startup_and_config"))
        stack.enter_context(patch.object(StartupIo, "write_startup", return_value=True))
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
        self.saved_layout = {
            "geometry": self.app.geometry(),
            "minsize": self.app.wm_minsize(),
            "sequence_height": self.app.compact_sequence.desired_height,
            "call_desired": dict(self.app.call_view.desired),
            "startup": dict(self.app._startup_settings),
        }
        self.addCleanup(self._restore_layout)
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

    def _restore_layout(self):
        if self.app.compact_sequence.is_open:
            self.app.compact_sequence.on_heading_click()
        self.app.call_view._open_by_trigger.clear()
        self.app.call_view._manually_operated.clear()
        self.app.call_view.on_selection_changed()
        self.app.compact_sequence.desired_height = self.saved_layout["sequence_height"]
        self.app.call_view.desired = self.saved_layout["call_desired"]
        self.app._startup_settings = self.saved_layout["startup"]
        self.app.minsize(*self.saved_layout["minsize"])
        self.app.geometry(self.saved_layout["geometry"])
        self.app.show_compact_view()
        self.app.update()

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

    def test_default_open_heading_moves_between_trigger_and_sequence_panes(self):
        self.assertTrue(type(self).initially_open)
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

    def test_saved_open_false_starts_closed(self):
        with patch.object(
            app_module, "load_startup_settings",
            return_value={"compact_sequence_view": {"open": False, "height": 123}},
        ), patch.object(StartupIo, "load_startup_and_config"), \
                patch.object(StartupIo, "write_startup", return_value=True):
            app = App()
        try:
            self.assertFalse(app.compact_sequence.is_open)
            self.assertEqual(app.compact_sequence.desired_height, 123)
        finally:
            app.destroy()

    def test_open_and_close_persist_compact_sequence_settings(self):
        with patch.object(self.app.startup_io, "write_startup", return_value=True) as write:
            self._open()
            write.assert_called_once()
            self.assertTrue(write.call_args.args[0]["compact_sequence_view"]["open"])
            write.reset_mock()
            self.frame.heading.event_generate("<Button-1>")
            self.app.update()
            write.assert_called_once()
            self.assertFalse(write.call_args.args[0]["compact_sequence_view"]["open"])
            self.assertEqual(
                write.call_args.args[0]["compact_sequence_view"],
                {"open": False, "height": self.sequence.desired_height},
            )
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
        with patch.object(
            self.app.call_view, "on_selection_changed",
            wraps=self.app.call_view.on_selection_changed,
        ) as selection_changed:
            self.app.trigger_panel.set_selected_trigger_index(0)
            selection_changed.assert_called_once_with()
        self.app.trigger_panel.set_selected_trigger_index(2)
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

    def test_clicking_blank_space_below_rows_does_not_change_next_action(self):
        self.app.geometry("270x900")
        self.app.update()
        self._open()
        # 6 行すべてと下の空白が見える高さにする（一覧の行数ではなく欄の高さで決まる）。
        self.sequence.desired_height = self.panes.winfo_height()
        self.app.compact_pane_layout.schedule_layout()
        self.app.update()
        listing = self.frame.action_list
        listing.yview_moveto(0)
        self.app.update()
        _x, top, _width, height = listing.bbox(5)
        blank_y = top + height + 2
        self.assertLess(blank_y, listing.winfo_height())
        self.sequence.on_press(SimpleNamespace(y=blank_y))
        self.sequence.on_release(SimpleNamespace(y=blank_y))
        self.assertEqual(self.app._indices["f1"], 1)
        self.assertEqual(listing.curselection(), (1,))

    def test_press_on_row_and_release_outside_does_not_change_next_action(self):
        self._open()
        listing = self.frame.action_list
        _x, y, _width, height = listing.bbox(2)
        self.sequence.on_press(SimpleNamespace(y=y + height // 2))
        self.sequence.on_release(SimpleNamespace(y=listing.winfo_height() + 1))
        self.assertEqual(self.app._indices["f1"], 1)
        self.assertEqual(listing.curselection(), (1,))

    def test_leaving_and_reentering_while_pressed_keeps_next_action_highlighted(self):
        self._open()
        listing = self.frame.action_list
        self._row_event("<Button-1>", 2)
        listing.event_generate("<B1-Leave>", x=-1, y=-1, state=0x100)
        listing.event_generate("<B1-Enter>", x=5, y=5, state=0x100)
        self.app.update()
        self.assertEqual(listing.curselection(), (1,))
        self.assertEqual(self.app._indices["f1"], 1)
        self.sequence.on_release(SimpleNamespace(y=listing.winfo_height() + 1))
        self.assertEqual(listing.curselection(), (1,))
        self.assertEqual(self.app._indices["f1"], 1)

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

    def test_opening_and_closing_preserves_window_size_and_resizes_trigger_list(self):
        self.app.update_idletasks()
        geometry = self.app.geometry()
        closed_height = self.box.trigger_list.winfo_height()
        self._open()
        open_height = self.box.trigger_list.winfo_height()
        self.assertEqual(self.app.geometry(), geometry)
        self.assertLess(open_height, closed_height)
        self.frame.heading.event_generate("<Button-1>")
        self.app.update()
        self.assertEqual(self.app.geometry(), geometry)
        self.assertGreater(self.box.trigger_list.winfo_height(), open_height)

    def test_saved_sequence_height_controls_open_pane_height(self):
        self._open()
        desired = max(100, self.panes.winfo_height() // 2)
        self.sequence.desired_height = desired
        self.app.compact_pane_layout.schedule_layout()
        self.app.update()
        self.assertAlmostEqual(self.frame.body.winfo_height(), desired, delta=8)

    def test_default_sequence_height_is_about_one_third_of_paned_window(self):
        self.app._startup_settings.pop("compact_sequence_view", None)
        self.sequence.desired_height = None
        self.assertNotIn("compact_sequence_view", self.app._startup_settings)
        initial_panes_height = self.panes.winfo_height()
        self._open()
        self.assertAlmostEqual(
            self.frame.body.winfo_height(), initial_panes_height / 3, delta=12,
        )

    def test_font_change_remeasures_sequence_pane_minimum(self):
        self._open()

        def pane_minimum():
            return int(self.panes.paneconfigure(str(self.frame.body))["minsize"][-1])

        before = pane_minimum()
        self.app._apply_font_delta(3)
        self.app.update()
        self.assertGreater(pane_minimum(), before)

    def test_low_window_keeps_sequence_and_call_headings_visible(self):
        self._open()
        self.app.call_view.on_heading_click()
        self.app.update()
        sequence = self.frame
        call = self.box.call_view_frame
        self.app.compact_sequence.desired_height = max(240, self.panes.winfo_height())
        self.app.call_view.desired["compact"] = max(240, self.panes.winfo_height())
        desired = (
            self.app.compact_sequence.desired_height,
            self.app.call_view.desired["compact"],
        )
        self.app.update_idletasks()
        overhead = self.app.winfo_height() - self.panes.winfo_height()
        self.app.minsize(1, 1)
        self.app.geometry(f"270x{max(1, overhead + sequence.heading.winfo_reqheight() + call.heading.winfo_reqheight() + 8)}")
        self.app.update()
        panes_height = self.panes.winfo_height()
        sash = int(self.panes.cget("sashwidth"))
        seq_min = sequence.heading.winfo_reqheight() + sequence.minimum_body_height()
        call_min = call.heading.winfo_reqheight() + call.minimum_body_height()
        expected = plan_compact_heights(
            panes_height - 2 * sash, list_minimum_height(self.box.trigger_list), 0,
            (desired[0], seq_min, sequence.heading.winfo_reqheight()),
            (desired[1], call_min, call.heading.winfo_reqheight()),
        )
        self.assertAlmostEqual(sequence.body.winfo_height(), expected[0], delta=2)
        self.assertAlmostEqual(call.body.winfo_height(), expected[1], delta=2)
        self.assertGreaterEqual(sequence.heading.winfo_height(), sequence.heading.winfo_reqheight())
        self.assertGreaterEqual(call.heading.winfo_height(), call.heading.winfo_reqheight())
        trigger_height = self.panes.sash_coord(0)[1]
        self.assertLess(trigger_height, list_minimum_height(self.box.trigger_list))
        self.assertEqual(self.app.compact_sequence.desired_height, desired[0])
        self.assertEqual(self.app.call_view.desired["compact"], desired[1])

    def test_sash_release_saves_only_changed_compact_pane_keys_once(self):
        self._open()
        self.app.call_view.on_heading_click()
        self.app.minsize(1, 1)
        self.app.geometry("270x820")
        self.app.update()
        desired = max(1, self.panes.winfo_height() // 3)
        self.app.compact_sequence.desired_height = desired
        self.app.call_view.desired["compact"] = desired
        self.app.compact_pane_layout.schedule_layout()
        self.app.update()
        before = {
            "sequence": self.frame.body.winfo_height(),
            "call": self.box.call_view_frame.body.winfo_height(),
        }
        sash_y = self.panes.sash_coord(1)[1]
        x = self.panes.winfo_width() // 2
        persisted = {}

        def capture_write(data):
            persisted["data"] = data
            persisted["heights"] = {
                "sequence": self.frame.body.winfo_height(),
                "call": self.box.call_view_frame.body.winfo_height(),
            }
            return True

        with patch.object(self.app.startup_io, "write_startup", side_effect=capture_write) as write:
            self.panes.event_generate("<Button-1>", x=x, y=sash_y + int(self.panes.cget("sashwidth")) // 2)
            self.app.update()
            self.panes.event_generate("<B1-Motion>", x=x, y=sash_y - 30, state=0x100)
            self.app.update()
            self.app.update_idletasks()
            self.panes.event_generate("<ButtonRelease-1>", x=x, y=sash_y - 30)
            self.app.update()
        after = {
            "sequence": self.frame.body.winfo_height(),
            "call": self.box.call_view_frame.body.winfo_height(),
        }
        changed = {name for name in before if before[name] != after[name]}
        self.assertTrue(changed)
        write.assert_called_once()
        changed_at_save = {
            name for name in before if before[name] != persisted["heights"][name]
        }
        self.assertTrue(changed_at_save)
        expected_keys = {
            "compact_sequence_view" if name == "sequence" else "call_view_heights"
            for name in changed_at_save
        }
        self.assertEqual(set(persisted["data"]), expected_keys)
        if "sequence" in changed_at_save:
            self.assertEqual(
                persisted["data"]["compact_sequence_view"]["height"],
                persisted["heights"]["sequence"],
            )
        if "call" in changed_at_save:
            self.assertEqual(
                persisted["data"]["call_view_heights"]["compact"],
                persisted["heights"]["call"],
            )

    def test_first_sash_release_saves_only_sequence_height(self):
        self._open()
        self.app.call_view.on_heading_click()
        self.app.update()
        before = {
            "sequence": self.frame.body.winfo_height(),
            "call": self.box.call_view_frame.body.winfo_height(),
        }
        sash_y = self.panes.sash_coord(0)[1]
        x = self.panes.winfo_width() // 2
        captured = {}

        def capture_write(data):
            captured["data"] = data
            captured["heights"] = {
                "sequence": self.frame.body.winfo_height(),
                "call": self.box.call_view_frame.body.winfo_height(),
            }
            return True

        with patch.object(self.app.startup_io, "write_startup", side_effect=capture_write) as write:
            self.panes.event_generate(
                "<Button-1>", x=x, y=sash_y + int(self.panes.cget("sashwidth")) // 2,
            )
            self.app.update()
            self.panes.event_generate("<B1-Motion>", x=x, y=sash_y - 25, state=0x100)
            self.app.update()
            self.panes.event_generate("<ButtonRelease-1>", x=x, y=sash_y - 25)
            self.app.update()
        changed = {name for name in before if before[name] != captured["heights"][name]}
        self.assertEqual(changed, {"sequence"})
        write.assert_called_once()
        self.assertEqual(set(captured["data"]), {"compact_sequence_view"})

    def test_sash_release_without_height_changes_does_not_save(self):
        self._open()
        self.app.call_view.on_heading_click()
        self.app.update()
        sash_y = self.panes.sash_coord(1)[1]
        x = self.panes.winfo_width() // 2
        with patch.object(self.app.startup_io, "write_startup", return_value=True) as write:
            self.panes.event_generate(
                "<Button-1>", x=x, y=sash_y + int(self.panes.cget("sashwidth")) // 2,
            )
            self.app.update()
            self.panes.event_generate("<ButtonRelease-1>", x=x, y=sash_y)
            self.app.update()
        write.assert_not_called()
