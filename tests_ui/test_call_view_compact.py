"""UI coverage for the compact-view call context pane."""

import os
import tkinter as tk
import unittest
from unittest.mock import patch

from keyseq.application.call_view import CallViewSummary
from keyseq.application.config_service import ConfigService
from keyseq.application.sequence_steps import LoopFrame
from keyseq.presentation import app as app_module
from keyseq.presentation.app import App
from keyseq.presentation.call_view_heights import CALL_VIEW_HEIGHTS_KEY, default_call_view_height
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.views.full_view.call_view_frame import list_minimum_height


SAVED_HEIGHTS = {"full": 180, "compact": 120}
WRITE_STARTUP = StartupIo.write_startup


class CallViewCompactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._patchers = []
        for target, name, value in (
            (app_module, "load_startup_settings", {CALL_VIEW_HEIGHTS_KEY: dict(SAVED_HEIGHTS)}),
            (StartupIo, "load_startup_and_config", None),
            (StartupIo, "write_startup", True),
            (app_module.JsonRepository, "save_json", None),
            (ConfigService, "ensure_split_config_dirs", None),
            (ConfigService, "save_keymap_set_history", None),
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
        self.box = self.app.compact_view.trigger_box
        self.panes = self.box.trigger_panes
        self.saved = {
            "geometry": self.app.geometry(),
            "minsize": self.app.wm_minsize(),
            "desired": dict(self.controller.desired),
            "startup": dict(self.app._startup_settings),
            "compact_mode": self.app._compact_mode,
            "selected_index": self.app._selected_trigger_idx,
        }
        self.selected_key = "f1"
        self.summaries = {}
        query_patch = patch.object(
            self.app.sequence_runner, "call_view_summary_for",
            side_effect=lambda key: self.summaries.get(key),
        )
        query_patch.start()
        self.addCleanup(query_patch.stop)
        selected_patch = patch.object(
            self.app.trigger_panel, "selected_trigger_key",
            side_effect=lambda: self.selected_key,
        )
        selected_patch.start()
        self.addCleanup(selected_patch.stop)
        self.addCleanup(self._restore)
        if self.app.compact_sequence.is_open:
            self.app.compact_sequence.on_heading_click()
        self.controller._open_by_trigger.clear()
        self.controller._manually_operated.clear()
        self.notify(None)
        self.controller.on_selection_changed()
        self.app.show_compact_view()
        self.app.update()

    def _restore(self):
        self.notify(None)
        self.controller._open_by_trigger.clear()
        self.controller._manually_operated.clear()
        self.controller.desired = self.saved["desired"]
        self.app._startup_settings = self.saved["startup"]
        self.app._selected_trigger_idx = self.saved["selected_index"]
        self.app.minsize(*self.saved["minsize"])
        if self.saved["compact_mode"]:
            self.app.show_compact_view()
        else:
            self.app.show_full_view()
        self.app.geometry(self.saved["geometry"])
        self.app.update()

    @staticmethod
    def summary(key="f1", value="hello", position=2):
        actions = (
            {"type": "system", "op": "loop_start", "count": 3},
            {"type": "text", "value": value, "label": "Greeting"},
            {"type": "system", "op": "counter_inc", "counter": "score"},
            {"type": "system", "op": "loop_end"},
        )
        return CallViewSummary(
            path=(key, "f5"), actions=actions, position=position,
            loop_frames=(LoopFrame(start=0, iteration=2),), counters={"score": 4},
        )

    def notify(self, summary):
        if summary is None:
            self.summaries.clear()
        else:
            self.summaries[summary.path[0]] = summary
        self.controller.on_changed()

    def test_compact_switch_starts_with_closed_heading_and_no_sash(self):
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▸ 呼び出し先")
        self.assertEqual(len(self.panes.panes()), 1)

    def test_summary_opens_compact_pane_with_same_heading_and_rows_as_full_view(self):
        self.notify(self.summary())
        self.app.update()

        compact_frame = self.box.call_view_frame
        full_frame = self.app.full_view.sequence_box.call_view_frame
        self.assertTrue(self.controller.is_open)
        self.assertEqual(len(self.panes.panes()), 2)
        self.assertEqual(compact_frame.heading.cget("text"), full_frame.heading.cget("text"))
        self.assertIn("f5", compact_frame.heading.cget("text"))
        self.assertEqual(compact_frame.action_list.get(0, tk.END), full_frame.action_list.get(0, tk.END))
        self.assertTrue(compact_frame.action_list.get(2).startswith("▶ "))
        self.assertIn("hello", compact_frame.action_list.get(1))

    def test_open_state_is_shared_when_switching_between_views_both_ways(self):
        self.notify(self.summary())
        self.app.update()
        self.app.show_full_view()
        self.app.update()
        self.assertTrue(self.controller.is_open)

        self.app.show_compact_view()
        self.app.update()
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▾ 呼び出し先　f1 › f5")
        self.box.call_view_frame.heading.event_generate("<Button-1>")
        self.app.update()
        self.assertFalse(self.controller.is_open)
        self.app.show_full_view()
        self.app.update()
        self.assertEqual(
            self.app.full_view.sequence_box.call_view_frame.heading.cget("text"),
            "▸ 呼び出し先",
        )
        self.app.show_compact_view()
        self.app.update()
        self.box.call_view_frame.heading.event_generate("<Button-1>")
        self.app.update()
        self.assertTrue(self.controller.is_open)
        self.app.show_full_view()
        self.app.update()
        self.assertEqual(
            self.app.full_view.sequence_box.call_view_frame.heading.cget("text"),
            "▾ 呼び出し先　f1 › f5",
        )

    def test_compact_selection_change_through_trigger_panel_updates_shared_view(self):
        self.notify(self.summary("f1", "first"))
        self.notify(self.summary("f2", "second"))
        self.selected_key = "f2"
        self.app.trigger_panel.set_selected_trigger_index(1)
        self.app.update()

        self.assertTrue(self.controller.is_open)
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▾ 呼び出し先　f2 › f5")
        self.assertIn("second", self.box.call_view_frame.action_list.get(1))
        self.selected_key = "f1"
        self.app.trigger_panel.set_selected_trigger_index(0)
        self.app.update()
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▾ 呼び出し先　f1 › f5")
        self.assertIn("first", self.box.call_view_frame.action_list.get(1))
        self.selected_key = "f3"
        self.app.trigger_panel.set_selected_trigger_index(2)
        self.app.update()
        self.assertEqual(len(self.panes.panes()), 1)
        self.controller.on_heading_click()
        self.app.update()
        self.assertEqual(self.box.call_view_frame.action_list.get(0), "呼び出し中ではありません")

    def test_manual_close_in_full_view_survives_switch_and_summary_notification(self):
        self.notify(self.summary())
        self.app.show_full_view()
        self.app.update()
        self.app.full_view.sequence_box.call_view_frame.heading.event_generate("<Button-1>")
        self.app.update()
        self.app.show_compact_view()
        self.notify(self.summary(position=1))
        self.app.update()
        self.assertEqual(len(self.panes.panes()), 1)
        self.assertEqual(self.box.call_view_frame.heading.cget("text"), "▸ 呼び出し先")

    def test_opening_and_closing_compact_pane_preserves_window_size_and_resizes_list(self):
        self.app.update_idletasks()
        before_geometry = self.app.geometry()
        before_list_height = self.box.trigger_list.winfo_height()
        self.notify(self.summary())
        self.app.update()
        opened_list_height = self.box.trigger_list.winfo_height()
        self.assertEqual(self.app.geometry(), before_geometry)
        self.assertLess(opened_list_height, before_list_height)

        self.box.call_view_frame.heading.event_generate("<Button-1>")
        self.app.update()
        self.assertEqual(self.app.geometry(), before_geometry)
        self.assertGreater(self.box.trigger_list.winfo_height(), opened_list_height)

    def test_compact_sash_release_saves_only_compact_height(self):
        self.notify(self.summary())
        self.app.show_full_view()
        self.app.update()
        full_frame = self.app.full_view.sequence_box.call_view_frame
        full_height_before = full_frame.body.winfo_height()
        self.app.show_compact_view()
        self.app.update()
        self.app.update_idletasks()
        _sash_x, sash_y = self.panes.sash_coord(0)
        x = self.panes.winfo_width() // 2
        self.app.compact_window.cancel_save()  # 窓の大きさの遅延保存が書き込みの回数に混ざらないように
        with patch.object(
            self.app.startup_io, "write_startup",
            side_effect=lambda data: WRITE_STARTUP(self.app.startup_io, data),
        ), patch.object(self.app.config_service, "save_startup", return_value=None) as save:
            self.panes.event_generate(
                "<Button-1>", x=x, y=sash_y + int(self.panes.cget("sashwidth")) // 2,
            )
            self.app.update()
            self.panes.event_generate(
                "<B1-Motion>", x=x, y=sash_y - 30, state=0x100,
            )
            self.app.update()
            self.app.update_idletasks()
            self.panes.event_generate("<ButtonRelease-1>", x=x, y=sash_y - 30)
            self.app.update()

        compact_height = (
            self.box.call_view_frame.heading.winfo_height()
            + self.box.call_view_frame.content.winfo_height()
        )
        save.assert_called_once()
        self.assertEqual(
            save.call_args.args[1][CALL_VIEW_HEIGHTS_KEY],
            {"full": SAVED_HEIGHTS["full"], "compact": compact_height},
        )
        self.assertEqual(save.call_args.args[0], os.path.join(self.app.config_root, "config.json"))
        self.assertEqual(self.controller.desired["compact"], compact_height)
        self.assertEqual(self.controller.desired["full"], SAVED_HEIGHTS["full"])
        self.app.show_full_view()
        self.app.update()
        self.assertAlmostEqual(full_frame.body.winfo_height(), full_height_before, delta=2)

    def test_low_window_keeps_three_trigger_rows_and_call_pane_minimum(self):
        self.notify(self.summary())
        self.app.update()
        frame = self.box.call_view_frame
        minimum = frame.heading.winfo_reqheight() + frame.minimum_body_height()
        overhead = self.app.winfo_height() - self.panes.winfo_height()
        height = (
            overhead + minimum + list_minimum_height(self.box.trigger_list)
            + self.box.sequence_frame.heading.winfo_reqheight() + 4
        )
        self.app.geometry(f"270x{height}")
        self.app.update()
        self.assertGreaterEqual(
            frame.body.winfo_height(),
            frame.heading.winfo_reqheight() + frame.minimum_body_height(),
        )
        self.assertGreaterEqual(
            self.box.trigger_list.winfo_height(),
            list_minimum_height(self.box.trigger_list),
        )

    def test_compact_call_view_is_read_only(self):
        self.notify(self.summary())
        self.app.update()
        listing = self.box.call_view_frame.action_list
        before_rows = tuple(listing.get(0, tk.END))
        before_history = dict(self.app.state.keymap_history)
        self.assertFalse(listing.cget("exportselection"))
        self.assertTrue(listing.bind("<Double-Button-1>"))
        listing.focus_force()
        self.app.update_idletasks()

        bounds = listing.bbox(self.summary().position)
        self.assertIsNotNone(bounds)
        x, y, width, height = bounds
        for _click in range(2):
            listing.event_generate("<Button-1>", x=x + width // 2, y=y + height // 2)
            listing.event_generate("<ButtonRelease-1>", x=x + width // 2, y=y + height // 2)
        listing.event_generate("<KeyPress-space>")
        self.app.update()

        self.assertEqual(tuple(listing.get(0, tk.END)), before_rows)
        self.assertEqual(tuple(listing.curselection()), ())
        self.assertEqual(self.app.state.keymap_history, before_history)

    def test_compact_default_waits_for_visible_pane_total_height(self):
        self.app.show_full_view()
        self.app.update()
        self.controller.desired = {}
        self.notify(self.summary())
        self.app.update()
        self.assertNotIn("compact", self.controller.desired)
        apply_geometry = self.app._apply_compact_geometry

        def apply_geometry_before_mapping():
            self.assertFalse(self.panes.winfo_ismapped())
            apply_geometry()
            self.assertNotIn("compact", self.controller.desired)

        with patch.object(self.app, "_apply_compact_geometry",
                          side_effect=apply_geometry_before_mapping):
            self.app.show_compact_view()
        self.app.update()
        self.assertEqual(
            self.controller.desired["compact"], default_call_view_height(self.panes.winfo_height()),
        )

    def test_compact_render_and_configure_defer_default_until_idle_layout(self):
        self.controller.desired.pop("compact", None)
        self.notify(self.summary())
        self.assertNotIn("compact", self.controller.desired)
        event = tk.Event()
        event.height = self.panes.winfo_height()
        self.controller._on_configure(self.controller.hosts["compact"], event)
        self.assertNotIn("compact", self.controller.desired)
        self.app.update()
        self.assertEqual(
            self.controller.desired["compact"], default_call_view_height(self.panes.winfo_height()),
        )


if __name__ == "__main__":
    unittest.main()
