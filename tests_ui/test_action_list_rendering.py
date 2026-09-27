import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from keyseq.application.app_state import AppState
from keyseq.application.sequence_steps import LoopFrame
from keyseq.presentation.controllers.action_list_rendering import (
    build_action_rows,
    format_next_action_summary,
)
from keyseq.presentation.controllers.trigger_panel import TriggerPanelController


class ActionListRenderingTest(unittest.TestCase):
    def test_build_action_rows_formats_runtime_loop_and_counter_values(self):
        actions = [
            {"type": "system", "op": "loop_start", "count": 3},
            {"type": "system", "op": "counter_inc", "counter": "score"},
            {"type": "file_line", "path": "C:/data/list.txt", "counter": "line"},
            {"type": "system", "op": "loop_end"},
        ]

        rows = build_action_rows(
            actions,
            loop_iterations={0: 2},
            counters={"score": 5, "line": 8},
        )

        self.assertEqual(rows[0][0], "01. [loop] 2/3")
        self.assertEqual(rows[1][0], "02. [count+1] score (=5)")
        self.assertEqual(rows[2][0], "03. [file_line] list.txt #line (=8)")
        self.assertEqual(rows[3][0], "04. [loop_end]")
        self.assertEqual(rows[0][1], "#DCEBFF")
        self.assertEqual(rows[1][1], "#DCEBFF")
        self.assertEqual(rows[2][1], "#DCEBFF")
        self.assertEqual(rows[3][1], "#DCEBFF")

    def test_loop_without_runtime_iteration_uses_total_count(self):
        rows = build_action_rows(
            [{"type": "system", "op": "loop_start", "count": 3}],
            loop_iterations={},
            counters={},
        )

        self.assertEqual(rows[0][0], "01. [loop] ×3")

    def test_loop_depth_colors_cover_one_through_nine(self):
        starts = [{"type": "system", "op": "loop_start", "count": 2} for _ in range(9)]
        ends = [{"type": "system", "op": "loop_end"} for _ in range(9)]
        rows = build_action_rows(starts + ends, loop_iterations={}, counters={})

        self.assertEqual(
            [rows[index][1] for index in range(9)],
            [
                "#DCEBFF",
                "#DDF3DD",
                "#FFEBD2",
                "#C2DBFF",
                "#C4E8C4",
                "#FFDDB3",
                "#A8CBFF",
                "#ABDDAB",
                "#FFCF94",
            ],
        )
        self.assertEqual([rows[index][1] for index in range(9, 18)], [
            "#FFCF94", "#ABDDAB", "#A8CBFF", "#FFDDB3", "#C4E8C4",
            "#C2DBFF", "#FFEBD2", "#DDF3DD", "#DCEBFF",
        ])

    def test_outside_and_malformed_loop_rows_have_no_color(self):
        actions = [
            {"type": "text", "value": "outside"},
            {"type": "system", "op": "loop_end"},
            {"type": "text", "value": "also outside"},
            {"type": "system", "op": "loop_start", "count": 2},
        ]

        rows = build_action_rows(actions, loop_iterations={}, counters={})

        self.assertEqual([row[1] for row in rows], [None, None, None, None])

    def test_existing_action_list_strings_are_unchanged(self):
        actions = [
            {"type": "text", "value": "hello", "label": "Greeting"},
            {"type": "mouse_click", "x": 10, "y": 20, "button": "right", "clicks": 2},
        ]

        rows = build_action_rows(actions, loop_iterations={}, counters={})

        self.assertEqual(
            [row[0] for row in rows],
            ["01. [text] hello: Greeting", "02. [mouse_click] (10, 20) right x2"],
        )

    def test_next_summary_formats_system_and_file_line(self):
        system = {"type": "system", "op": "loop_start", "count": 4}
        file_line = {"type": "file_line", "path": "list.txt", "counter": "line"}

        self.assertEqual(
            format_next_action_summary(
                1, system, loop_iterations={1: 2}, counters={}
            ),
            "02. [loop] 2/4",
        )
        self.assertEqual(
            format_next_action_summary(
                2, file_line, loop_iterations={}, counters={"line": 5}
            ),
            "03. [file_line] list.txt #line (=5)",
        )

    def test_existing_next_summary_format_is_unchanged(self):
        self.assertEqual(
            format_next_action_summary(
                0,
                {"type": "mouse_click", "x": 10, "y": 20, "drag": True, "label": "Move"},
                loop_iterations={},
                counters={},
            ),
            "01. [mouse_click] (10, 20) left x1",
        )
        self.assertEqual(
            format_next_action_summary(
                1, {"type": "text", "value": "hello"}, loop_iterations={}, counters={}
            ),
            "02. [text] hello",
        )

    def test_refresh_actions_applies_background_to_real_listbox(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Tk display is unavailable: {error}")
        self.addCleanup(root.destroy)
        root.withdraw()
        action_list = tk.Listbox(root)
        action_list.pack()
        trigger = {
            "key": "a",
            "actions": [
                {"type": "system", "op": "loop_start", "count": 3},
                {"type": "system", "op": "loop_end"},
            ],
        }
        state = AppState()
        state.keymap_loop_frames["set-1"] = {
            "a": [LoopFrame(start=0, iteration=2)]
        }
        state.counters["score"] = 5
        app = SimpleNamespace(
            data={"active_keymap_id": "set-1", "keymaps": [{"id": "set-1", "triggers": [trigger]}]},
            state=state,
            full_view=SimpleNamespace(action_list=action_list),
            _selected_trigger_idx=0,
            _active_trigger_set_id=lambda: "set-1",
            _indices={},
        )
        controller = TriggerPanelController(app)
        controller.select_next_action_row = Mock()
        controller.sync_suppress_checkbox = Mock()
        controller.sync_run_to_end_ui = Mock()
        controller.update_status = Mock()

        controller.refresh_actions()

        self.assertEqual(action_list.itemcget(0, "background"), "#DCEBFF")
        self.assertEqual(action_list.itemcget(1, "background"), "#DCEBFF")
        self.assertEqual(action_list.get(0), "01. [loop] 2/3")


if __name__ == "__main__":
    unittest.main()
