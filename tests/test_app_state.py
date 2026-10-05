import unittest

from keyseq.application.app_state import AppState


class AppStateCallRefTest(unittest.TestCase):
    def test_reset_indices_clears_call_refs_for_all_trigger_sets(self):
        state = AppState()
        state.call_refs_for().add("plain")
        state.call_refs_for("set-a").add("mapped")

        state.reset_indices()

        self.assertEqual(state.call_refs, set())
        self.assertEqual(state.keymap_call_refs, {})

    def test_forget_trigger_removes_its_call_ref(self):
        state = AppState()
        state.call_refs_for("set-a").update({"keep", "forget"})

        state.forget_trigger("set-a", "forget")

        self.assertEqual(state.call_refs_for("set-a"), {"keep"})

    def test_rekey_trigger_moves_its_call_ref(self):
        state = AppState()
        state.call_refs_for("set-a").add("old")

        state.rekey_trigger("set-a", "old", "new")

        self.assertEqual(state.call_refs_for("set-a"), {"new"})

    def test_forget_trigger_set_removes_its_call_ref_set(self):
        state = AppState()
        state.call_refs_for("set-a").add("a")
        state.call_refs_for("set-b").add("b")

        state.forget_trigger_set("set-a")

        self.assertNotIn("set-a", state.keymap_call_refs)
        self.assertEqual(state.call_refs_for("set-b"), {"b"})

    def test_rekey_trigger_set_moves_its_call_ref_set(self):
        state = AppState()
        state.call_refs_for("old-set").add("a")

        state.rekey_trigger_set("old-set", "new-set")

        self.assertNotIn("old-set", state.keymap_call_refs)
        self.assertEqual(state.call_refs_for("new-set"), {"a"})

    def test_next_press_id_increments(self):
        state = AppState()

        with state.lock:
            first = state.next_press_id()
            second = state.next_press_id()

        self.assertEqual((first, second), (1, 2))


if __name__ == "__main__":
    unittest.main()
