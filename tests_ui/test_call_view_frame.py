"""UI coverage for the full-view call context pane."""

import os
import tkinter as tk
import unittest
from unittest.mock import patch

from keyseq.application.call_view import CallViewSummary
from keyseq.application.sequence_steps import LoopFrame
from keyseq.presentation import app as app_module
from keyseq.presentation.app import App
from keyseq.presentation.call_view_heights import (
    CALL_VIEW_HEIGHTS_KEY,
    default_call_view_height,
    parse_call_view_heights,
)
from keyseq.presentation.controllers.call_view_controller import CallViewController
from keyseq.presentation.controllers.config_io.startup_io import StartupIo


SAVED_HEIGHTS = {"full": 180, "compact": 120}


class CallViewFrameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._patchers = []
        for target, name, value in (
            (app_module, "load_startup_settings", {CALL_VIEW_HEIGHTS_KEY: dict(SAVED_HEIGHTS)}),
            (StartupIo, "load_startup_and_config", None),
        ):
            patcher = patch.object(target, name, return_value=value)
            patcher.start()
            cls._patchers.append(patcher)
        try:
            cls.app = App()
        except tk.TclError as error:
            for patcher in reversed(cls._patchers):
                patcher.stop()
            raise unittest.SkipTest(f"Tk display is unavailable: {error}")
        cls.addClassCleanup(cls._destroy_app)
        for patcher in reversed(cls._patchers):
            cls.addClassCleanup(patcher.stop)
        cls.app.update()

    @classmethod
    def _destroy_app(cls):
        try:
            cls.app.pane_layout.cancel_window_width_save()
            cls.app.call_view.on_changed()
            cls.app.update_idletasks()
        finally:
            cls.app.destroy()

    def setUp(self):
        self.app = type(self).app
        self.controller = self.app.call_view
        self.box = self.app.full_view.sequence_box
        self.panes = self.box.action_panes
        self.saved = {
            "geometry": self.app.geometry(),
            "minsize": self.app.wm_minsize(),
            "desired": dict(self.controller.desired),
            "startup": dict(self.app._startup_settings),
        }
        self.selected_key = "f1"
        self.summaries = {}
        query_patch = patch.object(self.app.sequence_runner, "call_view_summary_for",
                                   side_effect=lambda key: self.summaries.get(key))
        query_patch.start()
        self.addCleanup(query_patch.stop)
        self._selected_key_patch = patch.object(
            self.app.trigger_panel, "selected_trigger_key",
            side_effect=lambda: self.selected_key,
        )
        self._selected_key_patch.start()
        self.addCleanup(self._selected_key_patch.stop)
        self.addCleanup(self._restore)
        self.controller._open_by_trigger.clear()
        self.controller._manually_operated.clear()
        self.notify(None)
        self.controller.on_selection_changed()
        self.app.update()

    def _restore(self):
        self.notify(None)
        self.controller._open_by_trigger.clear()
        self.controller._manually_operated.clear()
        self.controller.desired = self.saved["desired"]
        self.app._startup_settings = self.saved["startup"]
        self.app.minsize(*self.saved["minsize"])
        self.app.geometry(self.saved["geometry"])
        self.app.update()

    @staticmethod
    def summary(position=2):
        actions = (
            {"type": "system", "op": "loop_start", "count": 3},
            {"type": "text", "value": "hello", "label": "Greeting"},
            {"type": "system", "op": "counter_inc", "counter": "score"},
            {"type": "system", "op": "loop_end"},
        )
        return CallViewSummary(
            path=("f1", "f5"),
            actions=actions,
            position=position,
            loop_frames=(LoopFrame(start=0, iteration=2),),
            counters={"score": 4},
        )

    def notify(self, summary):
        if summary is None:
            self.summaries.clear()
        else:
            self.summaries[summary.path[0]] = summary
        self.controller.on_changed()

    def test_selection_switches_between_two_chains_and_unmarked_trigger(self):
        self.notify(self.summary())
        self.notify(CallViewSummary(path=("f2", "f6"), actions=({"type": "text", "value": "other"},),
                                    position=0, loop_frames=(), counters={}))
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▾ 呼び出し先　f1 › f5")
        self.selected_key = "f2"
        self.controller.on_selection_changed()
        self.assertTrue(self.controller.is_open)
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▾ 呼び出し先　f2 › f6")
        self.assertIn("other", self.box.call_view_frame.action_list.get(0))
        self.selected_key = "f1"
        self.controller.on_selection_changed()
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▾ 呼び出し先　f1 › f5")
        self.selected_key = "f3"
        self.controller.on_heading_click()
        self.assertEqual(self.box.call_view_frame.action_list.get(0), "呼び出し中ではありません")

    def _outer_pane_sizes(self):
        panes = self.app.full_view.panes
        boxes = (self.app.full_view.keymap_box, self.app.full_view.trigger_box, self.box)
        return tuple(
            (panes.panecget(box, "width"), panes.panecget(box, "minsize"), box.winfo_width())
            for box in boxes
        )

    def test_startup_is_collapsed_and_summary_opens_and_renders_content(self):
        frame = self.box.call_view_frame
        self.assertFalse(self.controller.is_open)
        self.assertEqual(frame.heading.cget("text"), "▸ 呼び出し先")
        self.assertEqual(tuple(map(str, self.panes.panes())), (str(self.box.action_frame),))
        # 閉じている間は呼び出し先の一覧が外れるため、出力シーケンスの一覧と比べる
        sequence_list = self.box.action_list
        self.assertGreater(sequence_list.winfo_height(), 0)
        self.assertGreaterEqual(
            frame.heading.winfo_rooty(),
            sequence_list.winfo_rooty() + sequence_list.winfo_height(),
        )
        self.assertEqual(self.controller.desired, SAVED_HEIGHTS)

        self.notify(self.summary())
        self.app.update()

        frame = self.box.call_view_frame
        self.assertTrue(self.controller.is_open)
        self.assertEqual(frame.heading.cget("text"), "▾ 呼び出し先　f1 › f5")
        self.assertLess(frame.heading.winfo_rooty(), frame.content.winfo_rooty())
        self.assertEqual(
            tuple(frame.action_list.get(0, tk.END)),
            (
                "　 01. [loop] 2/3",
                "　 02. [text] hello: Greeting",
                "▶ 03. [count+1] score (=4)",
                "　 04. [loop_end]",
            ),
        )
        self.assertTrue(all(
            frame.action_list.itemcget(index, "background") == "#DCEBFF"
            for index in range(4)
        ))
        self.assertEqual(frame.action_list.yview()[0], 0.0)

    def test_selected_trigger_in_path_but_not_first_does_not_auto_open(self):
        self.selected_key = "f5"
        self.notify(self.summary())
        self.app.update()

        self.assertFalse(self.controller.is_open)
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▸ 呼び出し先")

    def test_refresh_actions_notifies_call_view_of_selection(self):
        with patch.object(self.controller, "on_selection_changed", wraps=self.controller.on_selection_changed) as changed:
            self.app.trigger_panel.refresh_actions()

        changed.assert_called_once_with()

    def test_none_does_not_close_and_open_empty_state_is_read_only_message(self):
        self.notify(None)
        self.assertFalse(self.controller.is_open)

        self.notify(self.summary())
        self.app.update()
        self.assertTrue(self.controller.is_open)
        self.notify(None)
        self.app.update()

        self.assertTrue(self.controller.is_open)
        self.assertEqual(self.box.call_view_frame.action_list.get(0), "呼び出し中ではありません")
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▾ 呼び出し先")

    def test_manual_close_suppresses_automatic_reopen_for_that_trigger(self):
        self.notify(self.summary())
        self.controller.on_heading_click()
        self.assertFalse(self.controller.is_open)
        self.notify(self.summary())
        self.app.update()
        self.assertFalse(self.controller.is_open)
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▸ 呼び出し先")

    def test_open_state_is_per_trigger_and_nonmatching_summary_shows_empty_state_when_opened(self):
        self.notify(self.summary())
        self.assertTrue(self.controller.is_open)

        self.selected_key = "f2"
        self.controller.on_selection_changed()
        self.app.update()
        self.assertFalse(self.controller.is_open)
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▸ 呼び出し先")
        self.controller.on_heading_click()
        self.assertTrue(self.controller.is_open)
        self.assertEqual(self.box.call_view_frame.action_list.get(0), "呼び出し中ではありません")

        self.selected_key = "f1"
        self.controller.on_selection_changed()
        self.app.update()
        self.assertTrue(self.controller.is_open)
        self.assertTrue(self.box.call_view_frame.action_list.get(0).startswith("　 "))

    def test_heading_click_toggles_open_and_closed(self):
        heading = self.box.call_view_frame.heading
        heading.event_generate("<Button-1>")
        self.app.update()
        self.assertTrue(self.controller.is_open)
        heading.event_generate("<Button-1>")
        self.app.update()
        self.assertFalse(self.controller.is_open)

    def test_call_view_is_read_only_for_mouse_and_keyboard_events(self):
        self.notify(self.summary())
        self.app.update()
        listing = self.box.call_view_frame.action_list
        before_history = dict(self.app.state.keymap_history)
        before_indices = {key: dict(value) for key, value in self.app.state.keymap_indices.items()}
        before_pending = dict(self.app.state.pending_steps)
        before_last_trigger = self.app.state.last_trigger
        before_action_selection = tuple(self.app.full_view.action_list.curselection())
        self.app.list_clipboard.copy("actions", [{"type": "text", "value": "clipboard"}])
        before_clipboard = self.app.list_clipboard.paste("actions")
        self.assertFalse(listing.cget("exportselection"))
        self.assertEqual(listing.cget("selectbackground"), listing.cget("background"))
        self.assertEqual(listing.cget("selectforeground"), listing.cget("foreground"))
        self.assertTrue(listing.bind("<Double-Button-1>"))

        listing.focus_force()
        self.app.update_idletasks()
        self.assertTrue(listing.winfo_ismapped())
        # 自動スクロールで見える現在位置をクリックする（先頭行の可視性には依存しない）。
        bounds = listing.bbox(self.summary().position)
        self.assertIsNotNone(bounds)
        x, y, width, height = bounds
        for _click in range(2):
            listing.event_generate("<Button-1>", x=x + width // 2, y=y + height // 2)
            listing.event_generate("<ButtonRelease-1>", x=x + width // 2, y=y + height // 2)
        listing.event_generate("<Control-c>")
        listing.event_generate("<Control-v>")
        self.app.update()

        self.assertEqual(tuple(listing.curselection()), ())
        self.assertEqual(tuple(self.app.full_view.action_list.curselection()), before_action_selection)
        self.assertEqual(self.app.state.keymap_history, before_history)
        self.assertEqual(self.app.state.keymap_indices, before_indices)
        self.assertEqual(self.app.state.pending_steps, before_pending)
        self.assertEqual(self.app.state.last_trigger, before_last_trigger)
        self.assertEqual(self.app.list_clipboard.paste("actions"), before_clipboard)

    def test_sash_release_writes_both_heights_and_reopening_uses_saved_full_height(self):
        self.notify(self.summary())
        self.app.update()
        self.app.update_idletasks()
        self.assertTrue(self.controller.is_open)
        self.assertTrue(self.box.call_view_frame.body.winfo_ismapped())
        start_height = (
            self.box.call_view_frame.heading.winfo_height()
            + self.box.call_view_frame.content.winfo_height()
        )
        _sash_x, sash_y = self.panes.sash_coord(0)
        with patch.object(self.app.config_service, "save_startup", return_value=None) as save:
            self.panes.event_generate(
                "<Button-1>", x=self.panes.winfo_width() // 2,
                y=sash_y + int(self.panes.cget("sashwidth")) // 2,
            )
            self.assertEqual(self.controller.hosts["full"].drag_height, start_height)
            # 押下を Tk の境界線の処理（MarkSash）まで通してから動かす（実機ではイベントループが順に処理する）
            self.app.update()
            self.panes.event_generate(
                "<B1-Motion>", x=self.panes.winfo_width() // 2, y=sash_y - 35, state=0x100,
            )
            self.app.update()
            self.app.update_idletasks()
            self.panes.event_generate(
                "<ButtonRelease-1>", x=self.panes.winfo_width() // 2, y=sash_y - 35,
            )
            self.app.update()
        changed_height = (
            self.box.call_view_frame.heading.winfo_height()
            + self.box.call_view_frame.content.winfo_height()
        )
        self.assertNotEqual(changed_height, start_height)

        save.assert_called_once()
        saved_settings = save.call_args.args[1]
        self.assertEqual(
            saved_settings[CALL_VIEW_HEIGHTS_KEY],
            {"full": changed_height, "compact": SAVED_HEIGHTS["compact"]},
        )
        self.assertEqual(
            save.call_args.args[0], os.path.join(self.app.config_root, "config.json"),
        )
        self.assertEqual(self.controller.desired["full"], changed_height)
        loaded = CallViewController(self.app)
        self.assertEqual(
            loaded.desired,
            {"full": changed_height, "compact": SAVED_HEIGHTS["compact"]},
        )

        self.notify(None)
        self.app.update()
        self.notify(self.summary())
        self.app.update()
        self.assertAlmostEqual(
            self.box.call_view_frame.heading.winfo_height()
            + self.box.call_view_frame.content.winfo_height(),
            changed_height, delta=2,
        )

        self.controller.on_heading_click()
        self.assertFalse(self.controller.is_open)
        with patch.object(self.app.config_service, "save_startup", return_value=None) as save:
            self.controller.on_heading_click()
            self.app.update()
        self.assertTrue(self.controller.is_open)
        save.assert_not_called()
        self.assertEqual(self.controller.desired["full"], changed_height)

    def test_press_and_release_without_sash_motion_does_not_save(self):
        self.notify(self.summary())
        self.app.update()
        _sash_x, sash_y = self.panes.sash_coord(0)
        x = self.panes.winfo_width() // 2
        y = sash_y + int(self.panes.cget("sashwidth")) // 2

        with patch.object(self.app.config_service, "save_startup", return_value=None) as save:
            self.panes.event_generate("<Button-1>", x=x, y=y)
            self.panes.event_generate("<ButtonRelease-1>", x=x, y=y)
            self.app.update()

        save.assert_not_called()

    def test_sash_uses_a_flat_three_or_four_pixel_divider(self):
        self.assertEqual(self.panes.cget("sashrelief"), "flat")
        self.assertIn(int(self.panes.cget("sashwidth")), (3, 4))

    def test_invalid_saved_values_use_default_heights(self):
        invalid = parse_call_view_heights({"full": True, "compact": 0})
        self.assertEqual(invalid, {})
        self.controller.desired = invalid

        self.notify(self.summary())
        self.app.update()

        self.assertEqual(
            self.controller.desired["full"],
            default_call_view_height(self.panes.winfo_height()),
        )
        self.assertEqual(
            self.controller.desired.get("compact"), None,
        )

    def test_open_close_preserves_full_view_minimum_and_three_outer_pane_widths(self):
        self.app.update_idletasks()
        before_minimum = self.app.wm_minsize()
        before_widths = self._outer_pane_sizes()
        self.assertEqual(
            self.box.action_column.winfo_reqheight(),
            self.box.action_frame.winfo_reqheight(),
        )

        self.notify(self.summary())
        self.app.update()
        self.assertEqual(self.app.wm_minsize(), before_minimum)
        self.assertEqual(self._outer_pane_sizes(), before_widths)

        self.controller.on_heading_click()
        self.app.update()
        self.assertFalse(self.controller.is_open)
        self.assertEqual(self.app.wm_minsize(), before_minimum)
        self.assertEqual(self._outer_pane_sizes(), before_widths)
        self.assertEqual(
            self.box.action_column.winfo_reqheight(),
            self.box.action_frame.winfo_reqheight(),
        )

    def test_low_saved_height_stays_desired_while_display_meets_minimum(self):
        self.controller.desired["full"] = 1

        self.notify(self.summary())
        self.app.update()

        self.assertEqual(self.controller.desired["full"], 1)
        self.assertGreaterEqual(
            self.box.call_view_frame.body.winfo_height(),
            self.box.call_view_frame.heading.winfo_reqheight()
            + self.box.call_view_frame.minimum_body_height(),
        )

    def test_long_summary_scrolls_to_the_current_position(self):
        actions = tuple({"type": "text", "value": f"row {index}"} for index in range(30))
        summary = CallViewSummary(
            path=("f1", "f5"), actions=actions, position=24,
            loop_frames=(), counters={},
        )

        self.notify(summary)
        self.app.update()

        listing = self.box.call_view_frame.action_list
        self.assertTrue(listing.yview()[0] > 0)
        self.assertTrue(listing.get(24).startswith("▶ "))


if __name__ == "__main__":
    unittest.main()
