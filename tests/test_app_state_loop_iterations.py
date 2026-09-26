import unittest

from keyseq.application.app_state import AppState
from keyseq.application.sequence_steps import LoopFrame


class AppStateLoopIterationsTest(unittest.TestCase):
    def test_returns_iteration_by_loop_start_for_trigger(self):
        state = AppState()
        state.keymap_loop_frames["set-1"] = {
            "a": [LoopFrame(start=2, iteration=3), LoopFrame(start=7, iteration=1)]
        }

        self.assertEqual(state.loop_iterations_for("set-1", "a"), {2: 3, 7: 1})

    def test_unregistered_trigger_returns_empty_mapping(self):
        state = AppState()

        self.assertEqual(state.loop_iterations_for("missing", "a"), {})

    def test_default_trigger_set_uses_default_loop_stack(self):
        state = AppState()
        state.loop_frames["a"] = [LoopFrame(start=4, iteration=2)]

        self.assertEqual(state.loop_iterations_for("", "a"), {4: 2})


if __name__ == "__main__":
    unittest.main()
