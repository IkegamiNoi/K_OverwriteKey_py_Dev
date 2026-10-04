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
            cls.app.call_view.on_summary(None)
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
        self.addCleanup(self._restore)
        self.controller.on_summary(None)
        self.app.update()

    def _restore(self):
        self.controller.on_summary(None)
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

    def _outer_pane_sizes(self):
        panes = self.app.full_view.panes
        boxes = (self.app.full_view.keymap_box, self.app.full_view.trigger_box, self.box)
        return tuple(
            (panes.panecget(box, "width"), panes.panecget(box, "minsize"), box.winfo_width())
            for box in boxes
        )

    def test_summary_opens_and_renders_path_position_names_counters_and_loop_colors(self):
        self.assertEqual(self.controller.desired, SAVED_HEIGHTS)

        self.controller.on_summary(self.summary())
        self.app.update()

        frame = self.box.call_view_frame
        self.assertTrue(self.controller.is_open)
        self.assertEqual(frame.heading.cget("text"), "f1 › f5")
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

    def test_none_closes_the_pane_and_is_safe_while_already_closed(self):
        self.controller.on_summary(None)
        self.assertFalse(self.controller.is_open)

        self.controller.on_summary(self.summary())
        self.app.update()
        self.assertTrue(self.controller.is_open)
        self.controller.on_summary(None)
        self.app.update()

        self.assertFalse(self.controller.is_open)
        self.assertNotIn(str(self.box.call_view_frame), {str(pane) for pane in self.panes.panes()})

    def test_call_view_is_read_only_for_mouse_and_keyboard_events(self):
        self.controller.on_summary(self.summary())
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
        self.controller.on_summary(self.summary())
        self.app.update()
        self.app.update_idletasks()
        self.assertTrue(self.controller.is_open)
        self.assertTrue(self.box.call_view_frame.winfo_ismapped())
        start_height = self.box.call_view_frame.winfo_height()
        _sash_x, sash_y = self.panes.sash_coord(0)
        with patch.object(self.app.config_service, "save_startup", return_value=None) as save:
            self.panes.event_generate(
                "<Button-1>", x=self.panes.winfo_width() // 2,
                y=sash_y + int(self.panes.cget("sashwidth")) // 2,
            )
            self.assertEqual(self.controller._drag_height, start_height)
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
        changed_height = self.box.call_view_frame.winfo_height()
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

        self.controller.on_summary(None)
        self.app.update()
        self.controller.on_summary(self.summary())
        self.app.update()
        self.assertAlmostEqual(
            self.box.call_view_frame.winfo_height(), changed_height, delta=2,
        )

    def test_press_and_release_without_sash_motion_does_not_save(self):
        self.controller.on_summary(self.summary())
        self.app.update()
        _sash_x, sash_y = self.panes.sash_coord(0)
        x = self.panes.winfo_width() // 2
        y = sash_y + int(self.panes.cget("sashwidth")) // 2

        with patch.object(self.app.config_service, "save_startup", return_value=None) as save:
            self.panes.event_generate("<Button-1>", x=x, y=y)
            self.panes.event_generate("<ButtonRelease-1>", x=x, y=y)
            self.app.update()

        save.assert_not_called()

    def test_invalid_saved_values_use_default_heights(self):
        invalid = parse_call_view_heights({"full": True, "compact": 0})
        self.assertEqual(invalid, {})
        self.controller.desired = invalid

        self.controller.on_summary(self.summary())
        self.app.update()

        self.assertEqual(
            self.controller.desired["full"],
            default_call_view_height(self.panes.winfo_height()),
        )
        self.assertEqual(
            self.controller.desired["compact"],
            default_call_view_height(
                self.app.compact_view.trigger_box.trigger_list.winfo_reqheight(),
            ),
        )

    def test_open_close_preserves_full_view_minimum_and_three_outer_pane_widths(self):
        self.app.update_idletasks()
        before_minimum = self.app.wm_minsize()
        before_widths = self._outer_pane_sizes()

        self.controller.on_summary(self.summary())
        self.app.update()
        self.assertEqual(self.app.wm_minsize(), before_minimum)
        self.assertEqual(self._outer_pane_sizes(), before_widths)

        self.controller.on_summary(None)
        self.app.update()
        self.assertEqual(self.app.wm_minsize(), before_minimum)
        self.assertEqual(self._outer_pane_sizes(), before_widths)

    def test_low_saved_height_stays_desired_while_display_meets_minimum(self):
        self.controller.desired["full"] = 1

        self.controller.on_summary(self.summary())
        self.app.update()

        self.assertEqual(self.controller.desired["full"], 1)
        self.assertGreaterEqual(
            self.box.call_view_frame.winfo_height(),
            self.box.call_view_frame.minimum_height(),
        )

    def test_long_summary_scrolls_to_the_current_position(self):
        actions = tuple({"type": "text", "value": f"row {index}"} for index in range(30))
        summary = CallViewSummary(
            path=("f1", "f5"), actions=actions, position=24,
            loop_frames=(), counters={},
        )

        self.controller.on_summary(summary)
        self.app.update()

        listing = self.box.call_view_frame.action_list
        self.assertTrue(listing.yview()[0] > 0)
        self.assertTrue(listing.get(24).startswith("▶ "))


if __name__ == "__main__":
    unittest.main()
