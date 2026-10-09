"""Lifecycle checks for runtime call marks under v0.6 linked-call semantics."""

import unittest
from types import SimpleNamespace

from keyseq.application.app_state import AppState
from keyseq.application.sequence_runner import SequenceRunner
from keyseq.presentation.controllers.hook_controller import HookController


def system(op, **values):
    return {"type": "system", "op": op, **values}


def call(target, *, all=False):
    return system("call", target=target, **({"all": True} if all else {}))


def text(value):
    return {"type": "text", "value": value}


class Scheduler:
    def __init__(self):
        self.queue = []
        self.next_id = 0

    def after(self, _delay, callback):
        self.next_id += 1
        self.queue.append((self.next_id, callback))
        return self.next_id

    def after_cancel(self, handle):
        self.queue = [(item, callback) for item, callback in self.queue if item != handle]

    def run_one(self):
        _handle, callback = self.queue.pop(0)
        callback()

    def run_all(self):
        while self.queue:
            self.run_one()


class CallLinkLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState()
        self.active_set = ["set-a"]
        self.triggers = {"set-a": [], "set-b": []}
        self.scheduler = Scheduler()
        self.errors = []
        self.performed = []
        self.file_line_polls = []
        self.file_line_handle = object()
        self.runner = SequenceRunner(
            state=self.state,
            find_trigger=self.find_trigger,
            perform_action=self.perform_action,
            select_trigger=lambda _key: None,
            refresh_actions=lambda: None,
            update_status=lambda: None,
            after=self.scheduler.after,
            after_cancel=self.scheduler.after_cancel,
            get_trigger_set_id=lambda: self.active_set[0],
            notify_error=lambda action, message: self.errors.append((action, message)),
            begin_file_line=lambda _action: self.file_line_handle,
            poll_file_line=self.poll_file_line,
        )

    def perform_action(self, action):
        self.performed.append(action)
        return True

    def poll_file_line(self, handle):
        self.file_line_polls.append(handle)
        return None

    def find_trigger(self, key):
        return next((item for item in self.triggers[self.active_set[0]]
                     if item["key"] == key), None)

    def add_trigger(self, key, actions, *, trigger_set_id=None):
        trigger = {"key": key, "actions": actions}
        self.triggers[trigger_set_id or self.active_set[0]].append(trigger)
        return trigger

    def start_call(self):
        self.add_trigger("f1", [call("f5"), text("caller next")])
        self.add_trigger("f5", [text("callee one"), text("callee two")])
        self.runner.handle_key("f1")
        self.scheduler.run_all()

    def stop_hook(self):
        app = SimpleNamespace(
            sequence_runner=self.runner,
            held_inputs=SimpleNamespace(release_all=lambda: []),
            hook_coordinator=SimpleNamespace(stop=lambda: None),
            key_state_manager=SimpleNamespace(clear=lambda: None),
            layout=SimpleNamespace(refresh_keyboard_window=lambda: None),
            trigger_panel=SimpleNamespace(update_status=lambda: None),
        )
        controller = HookController(app)
        controller.hook_active = True
        controller.stop_hook()

    def test_editing_caller_clears_its_mark(self):
        # §4.5.1: editing T clears T's own reference mark.
        self.start_call()
        self.assertIn("f1", self.state.call_refs_for("set-a"))

        self.runner.reset_loop_frames("f1")

        self.assertNotIn("f1", self.state.call_refs_for("set-a"))
        self.assertEqual(self.state.indices_for("set-a").get("f5"), 1)

    def test_removing_caller_clears_its_mark(self):
        # §4.5.1: deleting T removes its own mark from runtime state.
        self.start_call()
        self.state.forget_trigger("set-a", "f1")

        self.assertNotIn("f1", self.state.call_refs_for("set-a"))

    def test_callee_edit_keeps_caller_mark_then_missing_target_error_clears_it(self):
        # §4.5.7: U's own edit state follows existing rules while T stays marked.
        self.start_call()
        self.runner.reset_loop_frames("f5")
        self.assertIn("f1", self.state.call_refs_for("set-a"))

        # §4.5.7: deleting U leaves T marked until its next press reports no target.
        self.triggers["set-a"] = [item for item in self.triggers["set-a"]
                                   if item["key"] != "f5"]
        self.runner.handle_key("f1")
        self.scheduler.run_all()

        self.assertNotIn("f1", self.state.call_refs_for("set-a"))
        self.assertTrue(any("呼び出し先のトリガーがありません" in message
                            for _action, message in self.errors))
        self.assertEqual(self.state.indices_for("set-a")["f1"], 0)

    def test_renaming_callee_keeps_caller_mark(self):
        # §4.5.7: U's key change applies U's state rules without clearing T's mark.
        self.start_call()
        self.state.rekey_trigger("set-a", "f5", "f6")

        self.assertIn("f1", self.state.call_refs_for("set-a"))

    def test_keymap_switch_round_trip_keeps_marks_in_each_trigger_set(self):
        # §4.5.1: call marks belong to each trigger list and survive switching away and back.
        self.start_call()
        self.add_trigger("f1", [text("other map")], trigger_set_id="set-b")
        self.active_set[0] = "set-b"
        self.runner.handle_key("f1")
        self.active_set[0] = "set-a"

        self.assertIn("f1", self.state.call_refs_for("set-a"))
        self.assertEqual(self.state.call_refs_for("set-b"), set())

    def test_renaming_caller_moves_its_mark_to_the_new_key(self):
        # §4.5.1: changing T's key migrates its runtime mark.
        self.start_call()
        self.state.rekey_trigger("set-a", "f1", "f9")

        self.assertNotIn("f1", self.state.call_refs_for("set-a"))
        self.assertIn("f9", self.state.call_refs_for("set-a"))

    def test_effective_row_replacement_forgets_the_previous_callers_mark(self):
        # §4.5.1: effective-row changes use the same forget-trigger cleanup entrance.
        self.start_call()
        self.state.forget_trigger("set-a", "f1")

        self.assertNotIn("f1", self.state.call_refs_for("set-a"))

    def test_pause_and_resume_keeps_mark_and_continues_from_live_callee_position(self):
        # §4.5.1 / §4.5.7: pausing keeps T marked and resumes U from its current position.
        self.add_trigger("f1", [call("f5", all=True)])
        self.add_trigger("f5", [text("callee one"), text("callee two")])
        self.triggers["set-a"][0]["run_to_end"] = True
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.runner.pause_run_to_end()

        self.assertIn("f1", self.state.call_refs_for("set-a"))
        self.assertEqual(self.state.indices_for("set-a").get("f5"), 1)

        self.runner.resume_run_to_end()
        self.scheduler.run_all()

        self.assertEqual(self.state.indices_for("set-a").get("f1"), 0)
        self.assertNotIn("f1", self.state.call_refs_for("set-a"))
        self.assertEqual(self.state.indices_for("set-a").get("f5"), 0)
        self.assertEqual([action["value"] for action in self.performed],
                         ["callee one", "callee two"])

    def test_hook_stop_cancels_reserved_call_and_continues_from_saved_position(self):
        # §4.5.7 / §10-16: hook stop preserves live positions and marks for continuation.
        self.add_trigger("f1", [call("f5"), text("caller next")])
        self.add_trigger("f5", [text("callee one"), text("callee two")])
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.runner.handle_key("f1")
        self.assertIn(("set-a", "f1"), self.state.pending_steps)
        stale_step = self.scheduler.queue[0][1]
        self.stop_hook()
        stale_step()

        self.assertNotIn(("set-a", "f1"), self.state.pending_steps)
        self.assertIn("f1", self.state.call_refs_for("set-a"))
        self.assertEqual(self.state.indices_for("set-a").get("f5"), 1)

        self.runner.handle_key("f1")
        self.scheduler.run_all()
        self.assertEqual([action["value"] for action in self.performed],
                         ["callee one", "callee two"])

    def test_hook_stop_cancels_remaining_call_wait_but_keeps_mark(self):
        # §4.5.1: stop cancels a pending wait remainder while preserving the call mark.
        self.add_trigger("f1", [call("f5")])
        self.add_trigger("f5", [system("wait", ms=500), text("after wait")])
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        self.assertIn("f1", self.state.call_refs_for("set-a"))
        self.stop_hook()

        self.assertNotIn(("set-a", "f1"), self.state.pending_steps)
        self.assertIn("f1", self.state.call_refs_for("set-a"))
        self.assertEqual(self.file_line_polls, [])

    def test_hook_stop_cancels_unstarted_continuous_call_without_clearing_saved_mark(self):
        self.start_call()
        self.find_trigger("f1")["run_to_end"] = True
        self.runner.handle_key("f1")
        self.assertFalse(self.runner._run_to_end_call.started)
        self.stop_hook()
        self.assertIn("f1", self.state.call_refs_for("set-a"))
        self.assertEqual(self.state.indices_for("set-a")["f5"], 1)
        self.runner.handle_key("f1")
        self.scheduler.run_all()
        self.assertEqual([action["value"] for action in self.performed],
                         ["callee one", "callee two", "caller next"])

    def test_hook_stop_discards_file_line_poll_and_keeps_mark(self):
        # §4.5.1: stopping during file-line loading cancels polling but retains the mark.
        self.add_trigger("f1", [call("f5")])
        self.add_trigger("f5", [{"type": "file_line", "path": "rows.txt"}, text("after")])
        self.runner.handle_key("f1")
        self.scheduler.run_one()
        pending = self.state.pending_steps[("set-a", "f1")]
        stale_poll = next(callback for _handle, callback in self.scheduler.queue)
        self.assertIs(pending.call_file_line, self.file_line_handle)
        self.stop_hook()
        stale_poll()

        self.assertNotIn(("set-a", "f1"), self.state.pending_steps)
        self.assertIn("f1", self.state.call_refs_for("set-a"))
        self.assertEqual(self.file_line_polls, [])

    def test_rewind_clears_only_target_mark_and_keeps_callee_position(self):
        # §4.5.5: rewind resets T's position and mark while leaving its callee alone.
        self.start_call()
        self.add_trigger("f2", [system("rewind")])
        self.runner.handle_key("f2")

        self.assertNotIn("f1", self.state.call_refs_for("set-a"))
        self.assertEqual(self.state.indices_for("set-a").get("f1"), 0)
        self.assertEqual(self.state.indices_for("set-a").get("f5"), 1)


if __name__ == "__main__":
    unittest.main()
