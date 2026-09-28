import unittest

from keyseq.application.app_state import AppState


class AppStateKeymapSwitchTests(unittest.TestCase):
    def test_switch_is_allowed_during_paused_continuous_run(self):
        state = AppState()
        state.run_to_end_key = "f1"
        state.run_to_end_paused = True

        self.assertTrue(state.can_switch_keymap("set-b", "set-a"))

    def test_switch_is_rejected_during_active_continuous_run(self):
        state = AppState()
        state.run_to_end_key = "f1"
        state.run_to_end_paused = False

        self.assertFalse(state.can_switch_keymap("set-b", "set-a"))

