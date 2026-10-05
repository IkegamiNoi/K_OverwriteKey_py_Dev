"""Focused runner integration coverage for task 11b decisions."""

import unittest
from types import SimpleNamespace

import test_sequence_runner_call as runner_call_tests
from keyseq.application.app_state import PendingStep
from keyseq.application.sequence_history import HistoryEntry, snapshot_for
from keyseq.application.sequence_steps import StepResume


def system(op, **values):
    return {"type": "system", "op": op, **values}


def call(target, *, all=False):
    return system("call", target=target, **({"all": True} if all else {}))


def text(value):
    return {"type": "text", "value": value}


class CallChainRunToEndIntegrationTests(unittest.TestCase):
    def setUp(self):
        # Reuse the established deterministic runner/scheduler fixture without
        # inheriting its large test class and duplicating its entire suite.
        self.fx = runner_call_tests.SequenceRunnerCallTests()
        self.fx.setUp()

    def test_running_chain_query_excludes_caller_and_paused_chain(self):
        self.fx.trigger("f1", [call("f5"), text("after")], run_to_end=True)
        self.fx.trigger("f5", [text("callee"), text("callee tail")])
        self.fx.trigger("f6", [text("unrelated")])

        # Starting f1 enters its call to f5; the chain is live while run-to-end
        # has not been paused. The caller itself and unrelated keys are excluded.
        self.fx.runner.handle_key("f1")
        self.assertTrue(self.fx.runner.is_running_chain_callee("f5"))
        self.assertFalse(self.fx.runner.is_running_chain_callee("f1"))
        self.assertFalse(self.fx.runner.is_running_chain_callee("f6"))

        # Pausing changes the classification immediately, even though f5 remains
        # in the retained call context and will be resumed later.
        self.fx.runner.pause_run_to_end()
        self.assertFalse(self.fx.runner.is_running_chain_callee("f5"))

    def test_running_chain_query_drops_completed_callee_while_caller_waits(self):
        self.fx.trigger(
            "f1", [call("f5"), system("wait", ms=100), text("after")], run_to_end=True,
        )
        self.fx.trigger("f5", [text("callee")])

        # While f1 is inside f5, f5 is protected. Once f5 reaches its end and
        # f1 is waiting on its own next row, f5 is no longer an active callee.
        self.fx.runner.handle_key("f1")
        self.assertTrue(self.fx.runner.is_running_chain_callee("f5"))
        self.fx.scheduler.run_one()
        self.assertEqual(self.fx.index("f1"), 1)
        self.assertFalse(self.fx.runner.is_running_chain_callee("f5"))

    def test_paused_run_to_end_callee_finishing_from_another_call_ends_its_run(self):
        self.fx.trigger("f1", [text("a"), text("b")], run_to_end=True)
        self.fx.trigger("f2", [call("f1", all=True)])

        # U=f1 sends its first action, then pauses with its run retained.
        self.fx.runner.handle_key("f1")
        self.fx.runner.pause_run_to_end()
        self.assertTrue(self.fx.state.run_to_end_paused)
        self.assertEqual(self.fx.state.run_to_end_key, "f1")

        # X=f2 invokes U through to its end. Completion must stop U's paused run;
        # otherwise a later resume would replay the already completed sequence.
        self.fx.runner.handle_key("f2")
        self.fx.run_all()
        self.assertEqual([item["value"] for item in self.fx.performed], ["a", "b"])
        self.assertIsNone(self.fx.state.run_to_end_key)
        self.assertFalse(self.fx.state.run_to_end_paused)
        self.assertIsNone(self.fx.runner._run_to_end_call)

    def test_linked_completion_stops_before_paused_caller_wait_then_resume_waits(self):
        self.fx.trigger(
            "f1", [call("f5"), system("wait", ms=500), text("B")], run_to_end=True,
        )
        self.fx.trigger("f5", [text("A"), text("callee tail")])
        self.fx.trigger("f2", [call("f5", all=True)])

        # f1 enters f5; one scheduler step sends A. Pausing retains the run at
        # the call while another trigger can finish f5.
        self.fx.runner.handle_key("f1")
        self.fx.scheduler.run_one()
        self.fx.runner.pause_run_to_end()
        self.assertTrue(self.fx.state.run_to_end_paused)

        # Completing f5 propagates f1 forward, but must leave the wait row itself
        # as the next position instead of consuming its wait during propagation.
        self.fx.runner.handle_key("f2")
        self.fx.run_all()
        self.assertEqual(self.fx.index("f1"), 1)
        self.assertTrue(self.fx.state.run_to_end_paused)
        self.assertEqual([item["value"] for item in self.fx.performed], ["A", "callee tail"])

        # On resume the normal run-to-end path handles the wait first, then B.
        self.fx.runner.resume_run_to_end()
        self.fx.scheduler.run_one()
        self.assertIn(500, self.fx.scheduler.delays)
        self.assertNotIn("B", [item["value"] for item in self.fx.performed])
        self.fx.run_all()
        self.assertEqual(self.fx.performed[-1]["value"], "B")
        self.assertIsNone(self.fx.state.run_to_end_key)

    def test_linked_completion_stops_on_paused_caller_stop_row(self):
        self.fx.trigger(
            "f1", [call("f5"), system("stop"), text("must not run")], run_to_end=True,
        )
        self.fx.trigger("f5", [text("A"), text("callee tail")])
        self.fx.trigger("f2", [call("f5", all=True)])

        # As above, pause f1 while its call to f5 is active, then complete f5
        # with an independent batch call.
        self.fx.runner.handle_key("f1")
        self.fx.scheduler.run_one()
        self.fx.runner.pause_run_to_end()
        self.fx.runner.handle_key("f2")
        self.fx.run_all()

        # The stop action is still the next row. Resuming applies its usual
        # run-to-end stop behavior and never sends the following text action.
        self.assertEqual(self.fx.index("f1"), 1)
        self.assertTrue(self.fx.state.run_to_end_paused)
        self.fx.runner.resume_run_to_end()
        self.fx.run_all()
        self.assertIsNone(self.fx.state.run_to_end_key)
        self.assertEqual([item["value"] for item in self.fx.performed], ["A", "callee tail"])

    def test_run_to_end_start_cancels_single_wait_even_when_first_row_is_call(self):
        self.fx.trigger("f1", [call("f5"), text("after")], run_to_end=True)
        self.fx.trigger("f5", [text("callee")])
        self.fx.trigger("f7", [text("before"), system("wait", ms=1000), text("after wait")])

        # f7 creates an ordinary pending single wait. Starting f1 begins at a
        # call row, but §4.2.10 still requires this unrelated wait to be settled.
        self.fx.runner.handle_key("f7")
        self.assertIn(("set", "f7"), self.fx.state.pending_steps)
        self.fx.runner.handle_key("f1")

        self.assertNotIn(("set", "f7"), self.fx.state.pending_steps)
        self.assertEqual(self.fx.state.run_to_end_key, "f1")
        self.assertFalse(self.fx.state.run_to_end_paused)
        self.assertIsNotNone(self.fx.runner._run_to_end_call)

    def test_paused_callee_position_edit_and_loop_reset_apply_on_resume(self):
        self.fx.trigger("f1", [call("f5"), text("caller tail")], run_to_end=True)
        self.fx.trigger("f5", [text("A"), text("B"), text("C")])

        # f1 runs one callee step, then pauses with f5 as its active callee.
        self.fx.runner.handle_key("f1")
        self.fx.scheduler.run_one()
        self.fx.runner.pause_run_to_end()
        self.assertEqual(self.fx.index("f5"), 1)

        # A paused chain permits the position edit; reset_loop_frames keeps the
        # edited row as the next row when the run resumes.
        self.fx.state.indices_for("set")["f5"] = 2
        self.fx.runner.reset_loop_frames("f5")
        self.fx.runner.resume_run_to_end()
        self.fx.run_all()

        self.assertEqual([item["value"] for item in self.fx.performed], ["A", "C", "caller tail"])
        self.assertIsNone(self.fx.state.run_to_end_key)

    def test_run_to_end_back_and_rewind_preserve_unrelated_paused_single_call(self):
        # This control follows the regression setup: f1 and f5 are paused, while
        # f2 is a run-to-end trigger containing only back/rewind.
        for op in ("back", "rewind"):
            with self.subTest(op=op):
                self.fx.setUp()
                self.fx._prepare_run_to_end_discard_case(op)
                self.assertEqual(set(self.fx.runner.paused_keys()), {"f1", "f5"})

                # First press asks to discard only the targeted paused f1. The
                # second press discards f1 and executes control; f5 is retained.
                self.fx.runner.handle_key("f2")
                self.fx.runner.handle_key("f2")
                self.assertEqual(self.fx.runner.paused_keys(), ("f5",))
                self.assertIn(("set", "f5"), self.fx.state.pending_steps)
                self.assertNotIn(("set", "f1"), self.fx.state.pending_steps)

    def test_back_two_press_covers_grouped_paused_members_and_keeps_unrelated_paused_call(self):
        for key in ("f1", "f2", "f3"):
            self.fx.trigger(key, [text(f"{key} action")])
            self.fx.state.indices_for("set")[key] = 1
        self.fx.trigger("f4", [system("back")], run_to_end=True)

        histories = self.fx.state.history_for("set")
        histories["f1"] = [HistoryEntry(0, [], [], press_id=93)]
        histories["f2"] = [HistoryEntry(0, [], [], press_id=93)]
        histories["f3"] = [HistoryEntry(0, [], [], press_id=94)]
        self.fx.state.last_trigger = ("set", "f1")

        # f1 is the direct target; f2 shares its top press history, while f3 is
        # an independent paused call that must survive both presses.
        for key in ("f1", "f2", "f3"):
            self.fx.state.pending_step_generation += 1
            generation = self.fx.state.pending_step_generation
            self.fx.state.pending_steps[("set", key)] = PendingStep(
                generation=generation,
                after_id=None,
                position=1,
                resume=StepResume(initial_position=0, wrapped=False, processed=0),
                snapshot=snapshot_for(self.fx.state, "set", key),
                call=SimpleNamespace(),
                call_paused=True,
            )

        # First press resolves the whole restoration group and asks to discard
        # both paused members together. The second press discards those two;
        # f3 remains paused because its history belongs to another press.
        self.fx.runner.handle_key("f4")
        self.assertIn("一時停止中の f1, f2 を破棄します", self.fx.messages[-1])
        self.assertEqual(set(self.fx.runner.paused_keys()), {"f1", "f2", "f3"})
        self.fx.runner.handle_key("f4")

        self.assertEqual(self.fx.runner.paused_keys(), ("f3",))
        self.assertNotIn(("set", "f1"), self.fx.state.pending_steps)
        self.assertNotIn(("set", "f2"), self.fx.state.pending_steps)
        self.assertIn(("set", "f3"), self.fx.state.pending_steps)
        self.assertTrue(any("一時停止中の実行を破棄しました（f1, f2）" in message
                            for message in self.fx.messages))


if __name__ == "__main__":
    unittest.main()
