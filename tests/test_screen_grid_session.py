import unittest

from keyseq.application.input_router import GridKeyAction
from keyseq.application.screen_grid_session import MonitorInfo, ScreenGridSession
from keyseq.domain.screen_grid import monitor_identifier


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
        self.action("space")
        self.assertEqual(self.session.view().level, 0)

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

    def test_stale_action_suppression_set_and_esc_flag(self):
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
        self.assertEqual(snap.suppress_keys,
                         set("qwerasdfzxcv") | {"p"} | set("qweasdzxc") |
                         {"enter", "num enter", "space", "backspace", "tab"})
        before = snap.suppress_keys
        self.action(self.session.view().cells[0][1])
        self.action("space")
        self.assertEqual(self.session.snapshot().suppress_keys, before)
        self.assertTrue(self.session.snapshot().esc_active)

    def test_escape_and_backspace_do_nothing_at_level_zero(self):
        self.moves.clear()
        for key in ("esc", "backspace"):
            with self.subTest(key=key):
                self.action(key)
                self.assertEqual(self.session.view().level, 0)
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

    def test_esc_active_tracks_back_navigation(self):
        self.action(self.session.view().cells[0][1])
        self.action("space")
        self.assertTrue(self.session.snapshot().esc_active)
        self.action("esc")
        self.assertEqual(self.session.view().level, 0)
        self.assertFalse(self.session.snapshot().esc_active)

        self.action(self.session.view().cells[0][1])
        self.action("space")
        self.action(self.session.view().cells[0][1])
        self.action("space")
        self.assertEqual(self.session.view().level, 2)
        self.action("backspace")
        self.assertEqual(self.session.view().level, 1)
        self.assertTrue(self.session.snapshot().esc_active)
        self.assertIsNotNone(self.session.view().selected)

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
        self.assertFalse(self.session.snapshot().esc_active)
        self.assertFalse(self.session.view().visible)
        self.assertEqual(self.changed, previous_changed + 1)


if __name__ == "__main__":
    unittest.main()
