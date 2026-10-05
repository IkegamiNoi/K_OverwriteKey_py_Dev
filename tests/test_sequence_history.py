import unittest
from types import SimpleNamespace

from keyseq.application.app_state import AppState
from keyseq.application.sequence_history import (
    HistoryEntry,
    MAX_HISTORY_ENTRIES,
    NO_TARGET_MESSAGE,
    PENDING_TARGET_MESSAGE,
    StepSnapshot,
    apply_control,
    clear_history,
    commit_press,
    commit_step,
    pop_history,
    push_history,
    snapshot_for,
    undo_counter_deltas,
)


class SequenceHistoryTest(unittest.TestCase):
    def test_unchanged_step_is_not_pushed(self):
        history = []
        snapshot = StepSnapshot("set-a", "a", 2, [(0, 1)])

        pushed = push_history(history, snapshot, 2, [(0, 1)], [])

        self.assertFalse(pushed)
        self.assertEqual(history, [])

    def test_position_loop_or_counter_change_pushes_start_state(self):
        cases = (
            (3, [(0, 1)], []),
            (2, [(0, 2)], []),
            (2, [(0, 1)], [("n", 1)]),
        )
        for position, frames, deltas in cases:
            with self.subTest(position=position, frames=frames, deltas=deltas):
                history = []
                snapshot = StepSnapshot("set-a", "a", 2, [(0, 1)])

                self.assertTrue(push_history(history, snapshot, position, frames, deltas))
                self.assertEqual(
                    history,
                    [HistoryEntry(2, [(0, 1)], list(deltas))],
                )

    def test_history_keeps_only_the_newest_100_entries(self):
        history = []
        for position in range(MAX_HISTORY_ENTRIES + 7):
            snapshot = StepSnapshot("set-a", "a", position, [])
            self.assertTrue(push_history(history, snapshot, position + 1, [], []))

        self.assertEqual(len(history), MAX_HISTORY_ENTRIES)
        self.assertEqual(history[0].position, 7)
        self.assertEqual(history[-1].position, MAX_HISTORY_ENTRIES + 6)

    def test_pop_and_clear_history(self):
        older = HistoryEntry(1, [], [])
        newer = HistoryEntry(2, [], [])
        history = [older, newer]

        self.assertIs(pop_history(history), newer)
        self.assertEqual(history, [older])
        clear_history(history)
        self.assertEqual(history, [])
        self.assertIsNone(pop_history(history))

    def test_undo_reverses_deltas_and_preserves_unrelated_counter_changes(self):
        counters = {"n": 2}

        undo_counter_deltas(counters, [("n", 1), ("n", -5)])

        self.assertEqual(counters["n"], 6)

    def test_undo_counter_increment(self):
        counters = {"n": 1}

        undo_counter_deltas(counters, [("n", 1)])

        self.assertEqual(counters["n"], 0)

    def test_undo_keeps_another_triggers_increment(self):
        # A: 0 -> 1, then B: 1 -> 2. Undoing A removes only A's +1.
        counters = {"n": 2}

        undo_counter_deltas(counters, [("n", 1)])

        self.assertEqual(counters["n"], 1)

    def test_undo_counter_reset_after_another_trigger_increment(self):
        # A: 5 -> 0, then B: 0 -> 1. Undoing A adds the five A removed.
        counters = {"n": 1}

        undo_counter_deltas(counters, [("n", -5)])

        self.assertEqual(counters["n"], 6)

    def test_undo_keeps_negative_values(self):
        counters = {"n": 0}

        undo_counter_deltas(counters, [("n", 1)])

        self.assertEqual(counters["n"], -1)


class SequenceHistoryControlTest(unittest.TestCase):
    def setUp(self):
        self.state = AppState()
        self.state.last_trigger = ("set-a", "target")
        self.state.indices_for("set-a")["target"] = 4
        self.state.loop_frames_for("set-a")["target"] = [(1, 2)]
        self.state.history_for("set-a")["target"] = []
        self.active_keys = {"target"}

    def find_trigger(self, key):
        return {"key": key} if key in self.active_keys else None

    def test_back_restores_one_entry_and_undoes_its_counter_operations(self):
        self.state.history_for("set-a")["target"].append(
            HistoryEntry(2, [(0, 1)], [("n", 1), ("reset", -5)])
        )
        self.state.counters.update(n=2, reset=0)

        selected, message = apply_control(
            self.state, ("set-a", "undo-key"), "back", self.find_trigger
        )

        self.assertEqual((selected, message), ("target", None))
        self.assertEqual(self.state.indices_for("set-a")["target"], 2)
        self.assertEqual(self.state.loop_frames_for("set-a")["target"], [(0, 1)])
        self.assertEqual(self.state.counters, {"n": 1, "reset": 5})
        self.assertEqual(self.state.history_for("set-a")["target"], [])

    def test_back_with_empty_history_does_nothing(self):
        before = self.state.indices_for("set-a")["target"]

        result = apply_control(
            self.state, ("set-a", "undo-key"), "back", self.find_trigger
        )

        self.assertEqual(result, (None, None))
        self.assertEqual(self.state.indices_for("set-a")["target"], before)

    def test_rewind_resets_position_and_frames_without_changing_counters(self):
        self.state.history_for("set-a")["target"].append(HistoryEntry(1, [], []))
        self.state.counters["n"] = 9

        selected, message = apply_control(
            self.state, ("set-a", "undo-key"), "rewind", self.find_trigger
        )

        self.assertEqual((selected, message), ("target", None))
        self.assertEqual(self.state.indices_for("set-a")["target"], 0)
        self.assertEqual(self.state.loop_frames_for("set-a")["target"], [])
        self.assertEqual(self.state.history_for("set-a")["target"], [])
        self.assertEqual(self.state.counters["n"], 9)

    def test_explicit_target_controls_back_and_rewind_without_changing_last_trigger(self):
        self.active_keys.update({"other", "undo"})
        self.state.last_trigger = ("set-a", "other")
        self.state.indices_for("set-a")["other"] = 6
        self.state.history_for("set-a")["target"].append(
            HistoryEntry(2, [(0, 1)], [("n", 1)])
        )
        self.state.indices_for("set-a")["target"] = 5
        self.state.counters["n"] = 1

        result = apply_control(
            self.state, ("set-a", "undo"), "back", self.find_trigger,
            target_key="target",
        )

        self.assertEqual(result, ("target", None))
        self.assertEqual(self.state.indices_for("set-a")["target"], 2)
        self.assertEqual(self.state.loop_frames_for("set-a")["target"], [(0, 1)])
        self.assertEqual(self.state.history_for("set-a")["target"], [])
        self.assertEqual(self.state.indices_for("set-a")["other"], 6)
        self.assertEqual(self.state.last_trigger, ("set-a", "other"))
        self.assertEqual(self.state.counters["n"], 0)

        self.state.history_for("set-a")["target"].append(HistoryEntry(1, [], []))
        result = apply_control(
            self.state, ("set-a", "undo"), "rewind", self.find_trigger,
            target_key="target",
        )
        self.assertEqual(result, ("target", None))
        self.assertEqual(self.state.indices_for("set-a")["target"], 0)
        self.assertEqual(self.state.loop_frames_for("set-a")["target"], [])
        self.assertEqual(self.state.history_for("set-a")["target"], [])
        self.assertEqual(self.state.last_trigger, ("set-a", "other"))

    def test_explicit_target_works_without_last_trigger(self):
        self.state.last_trigger = None
        self.state.history_for("set-a")["target"].append(HistoryEntry(2, [], []))

        result = apply_control(
            self.state, ("set-a", "undo-key"), "back", self.find_trigger,
            target_key="target",
        )

        self.assertEqual(result, ("target", None))
        self.assertEqual(self.state.indices_for("set-a")["target"], 2)
        self.assertIsNone(self.state.last_trigger)

    def test_empty_self_or_missing_explicit_target_returns_message_without_mutation(self):
        self.active_keys.add("undo-key")
        self.state.last_trigger = ("set-a", "target")
        before = (
            dict(self.state.indices_for("set-a")),
            dict(self.state.loop_frames_for("set-a")),
            {key: list(history) for key, history in self.state.history_for("set-a").items()},
            set(self.state.call_refs_for("set-a")),
            self.state.last_trigger,
        )
        for target_key in ("", "undo-key", "missing"):
            with self.subTest(target_key=target_key):
                result = apply_control(
                    self.state, ("set-a", "undo-key"), "rewind", self.find_trigger,
                    target_key=target_key,
                )
                self.assertEqual(result, (None, NO_TARGET_MESSAGE))
                self.assertEqual((
                    dict(self.state.indices_for("set-a")),
                    dict(self.state.loop_frames_for("set-a")),
                    {key: list(history) for key, history in self.state.history_for("set-a").items()},
                    set(self.state.call_refs_for("set-a")),
                    self.state.last_trigger,
                ), before)

    def test_explicit_marked_target_uses_chain_top_as_back_origin(self):
        histories = self.state.history_for("set-a")
        histories["target"] = [HistoryEntry(3, [], [], press_id=90)]
        histories["callee"] = [HistoryEntry(1, [], [], press_id=91)]
        self.state.call_refs_for("set-a").add("target")
        self.state.last_trigger = ("set-a", "other")
        self.state.indices_for("set-a").update(target=0, callee=4)
        self.active_keys.update({"callee", "other", "undo"})

        selected, message = apply_control(
            self.state, ("set-a", "undo"), "back",
            lambda key: {"actions": [{"type": "system", "op": "call", "target": "callee"}]}
            if key == "target" else {"actions": []} if key == "callee" else None,
            target_key="target",
        )

        self.assertEqual((selected, message), ("callee", None))
        self.assertEqual(self.state.indices_for("set-a")["target"], 0)
        self.assertEqual(self.state.indices_for("set-a")["callee"], 1)
        self.assertEqual(self.state.last_trigger, ("set-a", "other"))

    def test_explicit_pending_target_returns_pending_message(self):
        self.state.pending_steps[("set-a", "target")] = object()

        result = apply_control(
            self.state, ("set-a", "undo-key"), "rewind", self.find_trigger,
            target_key="target",
        )

        self.assertEqual(result, (None, PENDING_TARGET_MESSAGE))

    def test_missing_self_or_inactive_target_returns_no_target_message(self):
        cases = (
            (None, ("set-a", "undo-key"), {"target"}),
            (("set-a", "undo-key"), ("set-a", "undo-key"), {"target"}),
            (("set-old", "target"), ("set-a", "undo-key"), {"target"}),
            (("set-a", "missing"), ("set-a", "undo-key"), {"target"}),
        )
        for last_trigger, source, active_keys in cases:
            with self.subTest(last_trigger=last_trigger):
                self.state.last_trigger = last_trigger
                self.active_keys = active_keys
                self.assertEqual(
                    apply_control(self.state, source, "back", self.find_trigger),
                    (None, NO_TARGET_MESSAGE),
                )

    def test_pending_target_returns_pending_message(self):
        self.state.pending_steps[("set-a", "target")] = object()

        result = apply_control(
            self.state, ("set-a", "undo-key"), "rewind", self.find_trigger
        )

        self.assertEqual(result, (None, PENDING_TARGET_MESSAGE))

    def test_commit_step_updates_last_trigger_only_for_a_change(self):
        snapshot = StepSnapshot("set-a", "target", 4, [(1, 2)])
        self.state.last_trigger = None

        self.assertFalse(commit_step(self.state, snapshot, []))
        self.assertIsNone(self.state.last_trigger)

        self.state.indices_for("set-a")["target"] = 3
        self.assertTrue(commit_step(self.state, snapshot, []))
        self.assertEqual(self.state.last_trigger, ("set-a", "target"))
        self.assertEqual(self.state.history_for("set-a")["target"], [
            HistoryEntry(4, [(1, 2)], []),
        ])

    def test_snapshot_for_copies_position_and_frames(self):
        frames = [(1, 2)]
        self.state.loop_frames_for("set-a")["target"] = frames

        snapshot = snapshot_for(self.state, "set-a", "target")
        frames.append((3, 1))

        self.assertEqual(snapshot, StepSnapshot("set-a", "target", 4, [(1, 2)]))

    def test_snapshot_for_copies_call_ref_mark(self):
        self.state.call_refs_for("set-a").add("target")

        snapshot = snapshot_for(self.state, "set-a", "target")

        self.assertTrue(snapshot.call_ref)

    def test_call_ref_change_alone_is_recorded(self):
        snapshot = StepSnapshot("set-a", "target", 4, [(1, 2)])
        history = []

        self.assertTrue(push_history(
            history, snapshot, 4, [(1, 2)], [], press_id=27, call_ref=True
        ))
        self.assertEqual(history[0].call_ref, False)
        self.assertEqual(history[0].press_id, 27)

    def test_commit_press_records_only_changed_triggers_with_one_press_id(self):
        first = StepSnapshot("set-a", "first", 0, [])
        second = StepSnapshot("set-a", "second", 2, [])
        unchanged = StepSnapshot("set-a", "unchanged", 3, [])
        self.state.indices_for("set-a")["first"] = 1
        self.state.indices_for("set-a")["second"] = 3
        self.state.indices_for("set-a")["unchanged"] = 3

        self.assertTrue(commit_press(
            self.state, [first, second, unchanged], {}, pressed_key="pressed"
        ))

        first_entry = self.state.history_for("set-a")["first"][0]
        second_entry = self.state.history_for("set-a")["second"][0]
        self.assertGreater(first_entry.press_id, 0)
        self.assertEqual(second_entry.press_id, first_entry.press_id)
        self.assertNotIn("unchanged", self.state.history_for("set-a"))
        self.assertEqual(self.state.last_trigger, ("set-a", "pressed"))

    def test_back_restores_top_entries_sharing_press_id_and_undoes_all_deltas(self):
        histories = self.state.history_for("set-a")
        histories["caller"] = [HistoryEntry(0, [], [], press_id=71)]
        histories["callee"] = [HistoryEntry(2, [], [("n", 1)], [], 71, True)]
        histories["inner"] = [HistoryEntry(1, [], [("n", 2)], [], 71)]
        self.state.call_refs_for("set-a").update({"caller", "callee"})
        self.state.indices_for("set-a").update(caller=0, callee=0, inner=1)
        self.state.counters["n"] = 3
        self.state.last_trigger = ("set-a", "caller")
        triggers = {
            "caller": {"actions": [{"type": "system", "op": "call", "target": "callee"}]},
            "callee": {"actions": [{"type": "system", "op": "call", "target": "inner"}]},
            "inner": {"actions": []},
        }

        selected, message = apply_control(
            self.state, ("set-a", "undo"), "back", triggers.get
        )

        self.assertEqual((selected, message), ("inner", None))
        indices = self.state.indices_for("set-a")
        self.assertEqual(
            {key: indices[key] for key in ("caller", "callee", "inner")},
            {"caller": 0, "callee": 2, "inner": 1},
        )
        self.assertEqual(self.state.counters["n"], 0)
        self.assertEqual(self.state.call_refs_for("set-a"), {"callee"})
        self.assertTrue(all(not entries for entries in histories.values()))

    def test_back_does_not_restore_another_trigger_with_a_newer_top_entry(self):
        histories = self.state.history_for("set-a")
        histories["target"] = [HistoryEntry(1, [], [], press_id=81)]
        histories["other"] = [HistoryEntry(0, [], [], press_id=80)]
        self.state.last_trigger = ("set-a", "target")
        self.state.indices_for("set-a").update(target=2, other=3)

        apply_control(self.state, ("set-a", "undo"), "back", self.find_trigger)

        self.assertEqual(self.state.indices_for("set-a"), {"target": 1, "other": 3})
        self.assertEqual(len(histories["other"]), 1)

    def test_unmarked_legacy_history_without_press_ids_restores_only_target(self):
        histories = self.state.history_for("set-a")
        histories["target"] = [HistoryEntry(1, [], [])]
        histories["other"] = [HistoryEntry(0, [], [])]
        self.state.last_trigger = ("set-a", "target")
        self.state.indices_for("set-a").update(target=2, other=3)

        apply_control(self.state, ("set-a", "undo"), "back", self.find_trigger)

        self.assertEqual(self.state.indices_for("set-a"), {"target": 1, "other": 3})

    def test_back_from_marked_target_uses_chain_top_as_origin(self):
        histories = self.state.history_for("set-a")
        histories["target"] = [HistoryEntry(3, [], [], press_id=90)]
        histories["callee"] = [HistoryEntry(1, [], [], press_id=91)]
        self.state.call_refs_for("set-a").add("target")
        self.state.last_trigger = ("set-a", "target")
        self.state.indices_for("set-a")["target"] = 0
        self.active_keys.add("callee")

        selected, message = apply_control(
            self.state, ("set-a", "undo"), "back",
            lambda key: {"actions": [{"type": "system", "op": "call", "target": "callee"}]}
            if key == "target" else {"actions": []} if key == "callee" else None,
        )

        self.assertEqual((selected, message), ("callee", None))
        self.assertEqual(self.state.indices_for("set-a")["target"], 0)
        self.assertEqual(self.state.indices_for("set-a")["callee"], 1)

    def test_back_refuses_when_any_grouped_trigger_is_waiting_without_mutation(self):
        histories = self.state.history_for("set-a")
        histories["target"] = [HistoryEntry(2, [], [], press_id=92)]
        histories["callee"] = [HistoryEntry(1, [], [("n", 1)], press_id=92)]
        self.state.indices_for("set-a").update(target=4, callee=3)
        self.state.counters["n"] = 1
        self.state.pending_steps[("set-a", "callee")] = SimpleNamespace(
            call=None, file_line=None, call_paused=False
        )
        prepared = []

        result = apply_control(
            self.state, ("set-a", "undo-key"), "back", self.find_trigger,
            prepare_targets=lambda identities: prepared.append(identities) or True,
        )

        self.assertEqual(result, (None, PENDING_TARGET_MESSAGE))
        self.assertEqual(prepared, [])
        self.assertEqual(histories["target"], [HistoryEntry(2, [], [], press_id=92)])
        self.assertEqual(histories["callee"], [HistoryEntry(1, [], [("n", 1)], press_id=92)])
        self.assertEqual(self.state.indices_for("set-a"), {"target": 4, "callee": 3})
        self.assertEqual(self.state.counters["n"], 1)

        # Loading or executing a call is refused before preparation as well.
        pending = self.state.pending_steps[("set-a", "callee")]
        for kind in ("file_line", "call"):
            with self.subTest(kind=kind):
                pending.file_line = object() if kind == "file_line" else None
                pending.call = object() if kind == "call" else None
                self.assertEqual(apply_control(
                    self.state, ("set-a", "undo-key"), "back", self.find_trigger,
                    prepare_targets=lambda identities: prepared.append(identities) or True,
                ), (None, PENDING_TARGET_MESSAGE))
                self.assertEqual(prepared, [])
                self.assertEqual(len(histories["target"]), 1)
                self.assertEqual(len(histories["callee"]), 1)
                self.assertEqual(self.state.counters["n"], 1)

    def test_back_prepares_all_grouped_paused_triggers_as_one_batch(self):
        histories = self.state.history_for("set-a")
        histories["target"] = [HistoryEntry(1, [], [], press_id=93)]
        histories["callee"] = [HistoryEntry(2, [], [], press_id=93)]
        histories["other"] = [HistoryEntry(0, [], [], press_id=94)]
        self.state.indices_for("set-a").update(target=4, callee=5, other=3)
        self.state.pending_steps[("set-a", "callee")] = SimpleNamespace(
            call=object(), call_paused=True
        )
        batches = []

        result = apply_control(
            self.state, ("set-a", "undo-key"), "back", self.find_trigger,
            prepare_targets=lambda identities: batches.append(identities) or False,
        )

        self.assertEqual(result, (None, None))
        self.assertEqual(batches, [(('set-a', 'target'), ('set-a', 'callee'))])
        self.assertEqual(self.state.indices_for("set-a"), {"target": 4, "callee": 5, "other": 3})
        self.assertEqual(len(histories["target"]), 1)
        self.assertEqual(len(histories["callee"]), 1)
        self.assertEqual(len(histories["other"]), 1)

    def test_marked_target_falls_back_to_own_history_when_chain_top_is_empty(self):
        histories = self.state.history_for("set-a")
        histories["target"] = [HistoryEntry(3, [], [], press_id=95)]
        histories["callee"] = []
        self.state.call_refs_for("set-a").add("target")
        self.state.last_trigger = ("set-a", "target")
        self.state.indices_for("set-a")["target"] = 0
        self.active_keys.add("callee")
        batches = []

        selected, message = apply_control(
            self.state, ("set-a", "undo-key"), "back",
            lambda key: {"actions": [{"type": "system", "op": "call", "target": "callee"}]}
            if key == "target" else {"actions": []} if key == "callee" else None,
            prepare_targets=lambda identities: batches.append(identities) or True,
        )

        self.assertEqual((selected, message), ("target", None))
        self.assertEqual(batches, [(('set-a', 'target'),)])
        self.assertEqual(self.state.indices_for("set-a")["target"], 3)
        self.assertEqual(histories["target"], [])

    def test_rewind_clears_target_call_ref_only(self):
        self.state.call_refs_for("set-a").update({"target", "other"})

        apply_control(self.state, ("set-a", "undo"), "rewind", self.find_trigger)

        self.assertEqual(self.state.call_refs_for("set-a"), {"other"})


if __name__ == "__main__":
    unittest.main()
