import unittest

from keyseq.application.input_router import GridKeyAction
from keyseq.application.screen_grid_session import MonitorInfo, ScreenGridSession
from keyseq.domain.screen_grid import monitor_identifier, nudge_step


def monitor(rect, primary=False):
    return MonitorInfo(monitor_identifier(*rect), rect, primary)


class ScreenGridSessionTest(unittest.TestCase):
    def setUp(self):
        self.left = monitor((0, 0, 1200, 900), True)
        self.above = monitor((-800, -600, 0, 0))
        self.monitors = [self.left, self.above]
        self.cursor = (-200, -200)
        self.moves = []
        self.clicks = []
        self.changed = 0
        self.session = ScreenGridSession(
            list_monitors=lambda: list(self.monitors),
            cursor_position=lambda: self.cursor,
            move_cursor=lambda x, y: self.moves.append((x, y)),
            click=lambda x, y, button: self.clicks.append((x, y, button)),
            on_view_changed=self._changed,
        )
        self.grid = {"enabled": True}
        self.session.sync(keymap_id="one", grid=self.grid, active=True)

    def _changed(self):
        self.changed += 1

    def action(self, key, **kwargs):
        self.session.handle(GridKeyAction(key, self.session.view().generation,
                                          kwargs.get("shift", False), kwargs.get("repeat", False)))

    def test_sync_visibility_generation_and_equal_content(self):
        generation = self.session.view().generation
        self.session.sync(keymap_id="one", grid={"enabled": True}, active=True)
        self.assertEqual(self.session.view().generation, generation)
        self.session.sync(keymap_id="two", grid={"enabled": True}, active=True)
        self.assertEqual(self.session.view().generation, generation + 1)
        self.session.sync(keymap_id="two", grid={"enabled": True, "sub": {"rows": 2}}, active=True)
        self.assertEqual(self.session.view().generation, generation + 2)
        self.session.sync(keymap_id="two", grid={"enabled": False}, active=True)
        self.assertFalse(self.session.view().visible)
        self.assertEqual(self.session.view().generation, generation + 3)
        self.session.sync(keymap_id="two", grid=self.grid, active=True)
        self.assertTrue(self.session.view().visible)
        hidden_generation = self.session.view().generation
        self.session.sync(keymap_id="two", grid=self.grid, active=False)
        self.assertFalse(self.session.view().visible)
        self.assertEqual(self.session.view().generation, hidden_generation + 1)

    def test_view_label_position_defaults_to_center_and_reads_top_left(self):
        self.assertEqual(self.session.view().label_position, "center")
        self.session.sync(keymap_id="top-left", grid={"enabled": True, "label_position": "top_left"}, active=True)
        self.assertEqual(self.session.view().label_position, "top_left")

    def test_starts_on_cursor_monitor_including_negative_coordinates(self):
        self.assertEqual(self.session.view().monitor, self.above)
        self.assertEqual(self.session.view().region, self.above.rect)
        self.cursor = (20, 20)
        self.session.sync(keymap_id="changed", grid=self.grid, active=True)
        self.assertEqual(self.session.view().monitor, self.left)

    def test_select_subdivide_back_and_too_small(self):
        key = self.session.view().cells[0][1]
        self.action(key)
        self.assertEqual(self.session.view().selected, 0)
        self.assertEqual(self.moves[-1], (self.session.view().cells[0][0][0] +
                         (self.session.view().cells[0][0][2] - self.session.view().cells[0][0][0]) // 2,
                         self.session.view().cells[0][0][1] +
                         (self.session.view().cells[0][0][3] - self.session.view().cells[0][0][1]) // 2))
        self.action("space")
        self.assertEqual(self.session.view().level, 1)
        self.assertIsNone(self.session.view().selected)
        self.action("esc")
        self.assertEqual(self.session.view().level, 0)
        self.assertIsNotNone(self.session.view().selected)
        self.action("space")
        self.action("backspace")
        self.assertEqual(self.session.view().level, 0)
        tiny_monitor = monitor((-4, -4, 0, 0))
        self.monitors = [tiny_monitor]
        self.cursor = (-2, -2)
        tiny = {"enabled": True, "monitors": {tiny_monitor.id: {"rows": [
            {"h": 1, "cells": [{"w": 1, "key": "q"}]}
        ]}}, "sub": {"rows": 3, "cols": 3, "keys": list("qweasdzxc")}}
        self.session.sync(keymap_id="tiny", grid=tiny, active=True)
        self.action("q")
        tiny_point = self.session.view().click_point
        self.action("space")
        self.assertEqual(self.session.view().level, 0)
        self.assertEqual(self.session.view().click_point, tiny_point)

    def test_enter_left_right_repeat_and_center_without_selection(self):
        self.action("enter")
        self.assertEqual(self.clicks, [])
        self.action(self.session.view().cells[0][1])
        self.action("enter", repeat=True)
        self.assertEqual(self.clicks, [])
        self.action("enter", shift=True)
        self.assertEqual(self.clicks[-1][2], "right")
        self.assertEqual(self.session.view().level, 0)
        self.action(self.session.view().cells[0][1])
        self.action("num enter", shift=True)
        self.assertEqual(self.clicks[-1][2], "right")
        self.action(self.session.view().cells[0][1])
        self.action("space")
        region = self.session.view().region
        self.action("enter")
        self.assertEqual(self.clicks[-1][:2], ((region[0] + region[2]) // 2,
                                               (region[1] + region[3]) // 2))

    def test_click_missing_monitor_resets_without_clicking(self):
        self.action(self.session.view().cells[0][1])
        self.monitors = [self.left]
        self.action("enter")
        self.assertEqual(self.clicks, [])
        self.assertEqual(self.session.view().monitor, self.left)
        self.assertEqual(self.session.view().level, 0)

    def test_tab_cycles_and_single_monitor_does_nothing(self):
        self.action("tab")
        self.assertEqual(self.session.view().monitor, self.left)
        self.action("tab")
        self.assertEqual(self.session.view().monitor, self.above)
        self.monitors = [self.above]
        self.action("tab")
        self.assertEqual(self.session.view().monitor, self.above)

    def test_stale_action_suppression_set_updates_with_session_state(self):
        generation = self.session.view().generation
        custom_grid = {"enabled": True, "monitors": {self.above.id: {"rows": [
            {"h": 1, "cells": [{"w": 1, "key": "p"}]}
        ]}}}
        self.session.sync(keymap_id="two", grid=custom_grid, active=True)
        key = self.session.view().cells[0][1]
        self.session.handle(GridKeyAction(key, generation, False, False))
        self.assertIsNone(self.session.view().selected)
        snap = self.session.snapshot()
        self.assertTrue(set("qweasdzxc").issubset(snap.suppress_keys))
        self.assertTrue({"enter", "num enter", "space", "backspace", "tab"}.issubset(snap.suppress_keys))
        self.assertNotIn("esc", snap.suppress_keys)
        self.assertFalse({"up", "down", "left", "right"} & snap.suppress_keys)
        self.assertEqual(snap.suppress_keys,
                         set("qwerasdfzxcv") | {"p"} | set("qweasdzxc") |
                         {"enter", "num enter", "space", "backspace", "tab"})
        before = snap.suppress_keys
        self.action(self.session.view().cells[0][1])
        self.action("space")
        self.assertEqual(self.session.snapshot().suppress_keys, before | {"esc"})
        self.assertIn("esc", self.session.snapshot().suppress_keys)

    def test_escape_and_backspace_do_nothing_at_level_zero(self):
        self.moves.clear()
        self.action(self.session.view().cells[0][1])
        selected_point = self.session.view().click_point
        self.moves.clear()
        for key in ("esc", "backspace"):
            with self.subTest(key=key):
                self.action(key)
                self.assertEqual(self.session.view().level, 0)
                self.assertEqual(self.session.view().click_point, selected_point)
                self.assertEqual(self.moves, [])

    def test_repeated_grid_actions_are_ignored(self):
        self.action(self.session.view().cells[0][1])
        self.action("space")
        self.assertEqual(self.session.view().level, 1)
        self.moves.clear()
        view = self.session.view()
        for key in (view.cells[0][1], "space", "esc", "tab"):
            with self.subTest(key=key):
                before = self.session.view()
                self.action(key, repeat=True)
                self.assertEqual(self.session.view(), before)
                self.assertEqual(self.moves, [])

    def test_effective_suppression_tracks_depth_selection_and_frame_key_conflicts(self):
        self.assertNotIn("esc", self.session.snapshot().suppress_keys)
        self.assertFalse({"up", "down", "left", "right"} & self.session.snapshot().suppress_keys)
        self.action(self.session.view().cells[0][1])
        self.assertTrue({"up", "down", "left", "right"}.issubset(self.session.snapshot().suppress_keys))
        self.action("space")
        self.assertIn("esc", self.session.snapshot().suppress_keys)
        self.assertFalse({"up", "down", "left", "right"} & self.session.snapshot().suppress_keys)
        self.action("esc")
        self.assertEqual(self.session.view().level, 0)
        self.assertNotIn("esc", self.session.snapshot().suppress_keys)

        custom = {"enabled": True, "ops": {"deepen": "h", "up": "up"},
                  "sub": {"rows": 3, "cols": 3, "keys": ["esc", "up", "x", "a", "s", "d", "z", "c", "v"]}}
        self.session.sync(keymap_id="conflicts", grid=custom, active=True)
        self.assertNotIn("esc", self.session.snapshot().suppress_keys)
        self.assertNotIn("up", self.session.snapshot().suppress_keys)
        self.action(self.session.view().cells[0][1])
        self.action("h")
        self.assertEqual(self.session.view().level, 1)
        self.assertIn("esc", self.session.snapshot().suppress_keys)
        self.assertIn("up", self.session.snapshot().suppress_keys)
        self.action("esc")
        self.assertEqual(self.session.view().selected, 0)
        self.action("up")
        self.assertEqual(self.session.view().selected, 1)

    def test_custom_ops_replace_default_keys(self):
        custom = {"enabled": True, "ops": {"deepen": "h", "click": "k"}}
        self.session.sync(keymap_id="custom-ops", grid=custom, active=True)
        self.assertIn("h", self.session.snapshot().suppress_keys)
        self.assertIn("k", self.session.snapshot().suppress_keys)
        self.assertNotIn("space", self.session.snapshot().suppress_keys)
        self.assertNotIn("enter", self.session.snapshot().suppress_keys)
        self.action("space")
        self.action("enter")
        self.assertEqual(self.session.view().level, 0)
        self.assertEqual(self.clicks, [])
        self.action(self.session.view().cells[0][1])
        self.action("h")
        self.assertEqual(self.session.view().level, 1)
        self.action("k")
        self.assertEqual(len(self.clicks), 1)

    def test_click_point_nudge_shift_edges_and_click_uses_point(self):
        self.assertIsNone(self.session.view().click_point)
        key = self.session.view().cells[0][1]
        rect = self.session.view().cells[0][0]
        self.action(key)
        center = ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)
        self.assertEqual(self.session.view().click_point, center)
        self.action("right")
        step = max(1, min(16, (rect[2] - rect[0]) // 8))
        self.assertEqual(self.session.view().click_point, (center[0] + step, center[1]))
        for _ in range(rect[2] - rect[0] + 1):
            self.action("right")
        self.assertEqual(self.session.view().click_point, (rect[2] - 1, center[1]))
        move_count = len(self.moves)
        self.action("right")
        self.assertEqual(len(self.moves), move_count)
        self.action("left")
        self.action("down", shift=True)
        expected_point = (rect[2] - 1 - step, center[1] + 1)
        self.assertEqual(self.session.view().click_point, expected_point)
        self.action("enter", shift=True)
        self.assertEqual(self.clicks[-1], (*self.moves[-1], "right"))
        self.assertEqual(self.clicks[-1][:2], expected_point)
        self.assertIsNone(self.session.view().click_point)

    def test_click_point_resets_on_select_back_and_monitor_change(self):
        first_key = self.session.view().cells[0][1]
        self.action(first_key)
        self.action("right")
        second_key = self.session.view().cells[1][1]
        self.action(second_key)
        second_rect = self.session.view().cells[1][0]
        self.assertEqual(self.session.view().click_point,
                         ((second_rect[0] + second_rect[2]) // 2,
                          (second_rect[1] + second_rect[3]) // 2))
        self.action("space")
        self.assertIsNone(self.session.view().click_point)
        self.action("esc")
        self.assertEqual(self.session.view().click_point,
                         ((second_rect[0] + second_rect[2]) // 2,
                          (second_rect[1] + second_rect[3]) // 2))
        self.action("tab")
        self.assertIsNone(self.session.view().click_point)

    def test_nudge_step_and_noop_paths_preserve_click_point(self):
        self.assertEqual(nudge_step(1000, False), 16)
        self.assertEqual(nudge_step(7, False), 1)
        self.assertEqual(nudge_step(80, False), 10)
        self.assertEqual(nudge_step(80, True), 1)
        self.monitors = [self.left]
        self.session.sync(keymap_id="one-monitor", grid=self.grid, active=True)
        self.assertIsNone(self.session.view().click_point)
        self.action("right")
        self.assertIsNone(self.session.view().click_point)
        self.action(self.session.view().cells[0][1])
        self.action("right")
        point = self.session.view().click_point
        self.action("tab")
        self.assertEqual(self.session.view().click_point, point)

    def test_arrow_repeat_moves_selected_click_point(self):
        key = self.session.view().cells[0][1]
        rect = self.session.view().cells[0][0]
        self.action(key)
        start = self.session.view().click_point
        step = max(1, min(16, (rect[2] - rect[0]) // 8))
        self.action("right", repeat=True)
        self.assertEqual(self.session.view().click_point, (start[0] + step, start[1]))

    def test_zero_pixel_frame_nudge_stays_at_its_only_point(self):
        zero_width = monitor((5, 5, 5, 20), True)
        self.monitors = [zero_width]
        self.session.sync(keymap_id="zero-width", grid=self.grid, active=True)
        cell_key = self.session.view().cells[0][1]
        self.action(cell_key)
        point = self.session.view().click_point
        self.action("right")
        self.action("left")
        self.assertEqual(self.session.view().click_point, point)

    def test_monitor_refresh_rebuilds_suppression_and_empty_monitor_sync(self):
        custom_grid = {"enabled": True, "monitors": {self.above.id: {"rows": [
            {"h": 1, "cells": [{"w": 1, "key": "p"}]}
        ]}}}
        self.session.sync(keymap_id="custom", grid=custom_grid, active=True)
        self.assertIn("p", self.session.snapshot().suppress_keys)

        self.monitors = [self.left]
        self.action("tab")
        self.assertNotIn("p", self.session.snapshot().suppress_keys)

        self.monitors = []
        self.session.sync(keymap_id="empty", grid=self.grid, active=True)
        self.assertFalse(self.session.view().visible)
        self.assertFalse(self.session.snapshot().visible)
        self.assertIsNone(self.session.view().monitor)
        self.assertEqual(self.session.view().cells, ())
        self.assertEqual(self.session.snapshot().suppress_keys, frozenset())

        self.monitors = [self.left, self.above]
        self.session.sync(keymap_id="empty", grid=self.grid, active=True)
        self.assertTrue(self.session.view().visible)
        self.assertEqual(self.session.view().monitor, self.above)

    def test_tab_with_empty_monitor_refresh_raises_without_changing_state(self):
        before_view = self.session.view()
        before_snapshot = self.session.snapshot()
        self.monitors = []

        with self.assertRaisesRegex(RuntimeError, "画面（モニタ）を取得できませんでした"):
            self.action("tab")

        self.assertEqual(self.session.view(), before_view)
        self.assertEqual(self.session.snapshot(), before_snapshot)

    def test_enter_with_empty_monitor_refresh_raises_without_clicking(self):
        self.action(self.session.view().cells[0][1])
        before_view = self.session.view()
        before_snapshot = self.session.snapshot()
        self.monitors = []

        with self.assertRaisesRegex(RuntimeError, "画面（モニタ）を取得できませんでした"):
            self.action("enter")

        self.assertEqual(self.clicks, [])
        self.assertEqual(self.session.view(), before_view)
        self.assertEqual(self.session.snapshot(), before_snapshot)

    def test_abort_advances_generation_discards_state_and_publishes_hidden_snapshot(self):
        previous_generation = self.session.view().generation
        previous_changed = self.changed

        self.session.abort()

        self.assertEqual(self.session.view().generation, previous_generation + 1)
        self.assertFalse(self.session.snapshot().visible)
        self.assertFalse(self.session.snapshot().suppress_keys)
        self.assertFalse(self.session.view().visible)
        self.assertEqual(self.changed, previous_changed + 1)


if __name__ == "__main__":
    unittest.main()
