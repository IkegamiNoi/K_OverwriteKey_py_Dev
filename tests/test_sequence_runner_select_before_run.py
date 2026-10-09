import unittest

from keyseq.application.app_state import AppState
from keyseq.application.sequence_runner import SequenceRunner


class FakeScheduler:
    def __init__(self):
        self.queue = []
        self.delays = []
        self._next_id = 1

    def after(self, delay_ms, callback):
        handle = self._next_id
        self._next_id += 1
        self.delays.append(delay_ms)
        self.queue.append((handle, callback))
        return handle

    def after_cancel(self, handle):
        self.queue = [(current, callback) for current, callback in self.queue
                      if current != handle]

    def run_one(self):
        if self.queue:
            _handle, callback = self.queue.pop(0)
            callback()


A1 = {"type": "text", "value": "one"}
A2 = {"type": "text", "value": "two"}


def make_runner(triggers, *, selected_key=None, enabled=False, inject=True,
                include_selected=True, include_enabled=True,
                include_control_selection=False):
    state = AppState()
    scheduler = FakeScheduler()
    performed = []
    selected = {"key": selected_key}
    selections = []
    messages = []

    def find_trigger(key):
        return next((trigger for trigger in triggers if trigger["key"] == key), None)

    def select_trigger(key):
        selections.append(key)
        selected["key"] = key

    kwargs = {}
    if inject:
        if include_selected:
            kwargs["get_selected_trigger_key"] = lambda: selected["key"]
        if include_enabled:
            kwargs["is_select_before_run_enabled"] = lambda: enabled
    if include_control_selection:
        kwargs["get_selected_trigger_key"] = lambda: selected["key"]

    runner = SequenceRunner(
        state=state,
        find_trigger=find_trigger,
        perform_action=performed.append,
        select_trigger=select_trigger,
        refresh_actions=lambda: None,
        update_status=lambda: None,
        after=scheduler.after,
        after_cancel=scheduler.after_cancel,
        notify_message=messages.append,
        **kwargs,
    )
    return runner, state, scheduler, performed, selected, selections, messages


class SelectBeforeRunTest(unittest.TestCase):
    def test_injection_omitted_or_incomplete_keeps_immediate_execution(self):
        trigger = {"key": "f1", "actions": [A1]}
        for options in ({"inject": False}, {"include_selected": False},
                        {"include_enabled": False}):
            with self.subTest(options=options):
                runner, _state, _scheduler, performed, _selected, selections, _messages = (
                    make_runner([trigger], selected_key=None, enabled=True, **options)
                )
                runner.handle_key("f1")
                self.assertEqual(performed, [A1])
                self.assertEqual(selections, ["f1"])

    def test_default_off_executes_on_first_press(self):
        trigger = {"key": "f1", "actions": [A1]}
        runner, _state, _scheduler, performed, _selected, _selections, _messages = (
            make_runner([trigger], selected_key="other")
        )
        runner.handle_key("f1")
        self.assertEqual(performed, [A1])

    def test_global_enabled_selects_then_executes_without_changing_run_state(self):
        first = {"key": "f1", "actions": [A1]}
        second = {"key": "f2", "actions": [A2]}
        runner, state, _scheduler, performed, selected, selections, messages = make_runner(
            [first, second], selected_key="f1", enabled=True,
        )
        runner.handle_key("f1")
        before = (
            state.indices_for("").copy(),
            {key: list(frames) for key, frames in state.loop_frames_for("").items()},
            {key: list(entries) for key, entries in state.history_for("").items()},
            state.last_trigger,
        )
        performed.clear()
        selections.clear()
        messages.clear()

        runner.handle_key("f2")
        self.assertEqual(performed, [])
        self.assertEqual(selections, ["f2"])
        self.assertEqual(messages, ["f2 を選びました（もう一度押すと実行します）"])
        self.assertEqual(selected["key"], "f2")
        self.assertEqual((
            state.indices_for("").copy(),
            {key: list(frames) for key, frames in state.loop_frames_for("").items()},
            {key: list(entries) for key, entries in state.history_for("").items()},
            state.last_trigger,
        ), before)

        runner.handle_key("f2")
        self.assertEqual(performed, [A2])

    def test_trigger_setting_enables_selection_when_global_setting_is_off(self):
        trigger = {"key": "f1", "select_before_run": True, "actions": [A1]}
        runner, _state, _scheduler, performed, selected, selections, _messages = make_runner(
            [trigger], selected_key="f2", enabled=False,
        )
        runner.handle_key("f1")
        self.assertEqual(performed, [])
        self.assertEqual(selected["key"], "f1")
        self.assertEqual(selections, ["f1"])
        runner.handle_key("f1")
        self.assertEqual(performed, [A1])

    def test_standalone_back_and_rewind_are_not_selection_only(self):
        for op in ("back", "rewind"):
            with self.subTest(op=op):
                trigger = {"key": "f1", "actions": [{"type": "system", "op": op}]}
                runner, _state, _scheduler, performed, _selected, selections, messages = (
                    make_runner([trigger], selected_key="other", enabled=True)
                )
                runner.handle_key("f1")
                self.assertEqual(performed, [])
                self.assertEqual(selections, [])
                self.assertEqual(messages, ["戻す対象のトリガーがありません"])

    def test_back_and_rewind_use_selected_trigger_when_target_is_omitted(self):
        for op in ("back", "rewind"):
            with self.subTest(op=op):
                target = {"key": "x", "actions": [A1, A2]}
                control = {"key": "b", "actions": [{"type": "system", "op": op}]}
                runner, state, _scheduler, performed, selected, _selections, _messages = (
                    make_runner([target, control], selected_key="x",
                                include_control_selection=True)
                )
                runner.handle_key("x")
                selected["key"] = "x"
                runner.handle_key("b")

                self.assertEqual(state.indices_for("").get("x", 0), 0)
                self.assertEqual(state.history_for("").get("x", []), [])
                self.assertEqual(state.last_trigger, ("", "x"))
                self.assertEqual(performed, [A1])

    def test_selected_self_or_standalone_control_falls_back_to_last_trigger(self):
        target = {"key": "x", "actions": [A1, A2]}
        control = {"key": "b", "actions": [{"type": "system", "op": "back"}]}
        standalone = {"key": "c", "actions": [{"type": "system", "op": "rewind"}]}
        for selected_key in ("b", "c"):
            with self.subTest(selected_key=selected_key):
                runner, state, _scheduler, _performed, selected, _selections, _messages = (
                    make_runner([target, control, standalone], selected_key=selected_key,
                                include_control_selection=True)
                )
                runner.handle_key("x")
                selected["key"] = selected_key
                runner.handle_key("b")
                self.assertEqual(state.indices_for("").get("x", 0), 0)
                self.assertEqual(state.history_for("").get("x", []), [])

    def test_control_target_is_resolved_again_on_each_confirmation_press(self):
        first = {"key": "x", "actions": [A1, A2]}
        second = {"key": "y", "actions": [A2, A1]}
        control = {"key": "b", "actions": [{"type": "system", "op": "back"}]}
        runner, _state, _scheduler, _performed, selected, _selections, _messages = (
            make_runner([first, second, control], selected_key="x",
                        include_control_selection=True)
        )
        resolved = []
        runner._prepare_control_targets = lambda identities: resolved.append(identities) or False

        self.assertIsNone(runner._control("b", "back"))
        selected["key"] = "y"
        self.assertIsNone(runner._control("b", "back"))

        self.assertEqual(resolved, [(('', 'x'),), (('', 'y'),)])

    def test_paused_selected_target_stays_selected_through_two_press_back(self):
        paused = {"key": "x", "run_to_end": True, "run_to_end_delay_ms": 0,
                  "actions": [A1, {"type": "system", "op": "wait", "ms": 25}, A2]}
        other = {"key": "y", "actions": [A2, A1]}
        control = {"key": "b", "actions": [{"type": "system", "op": "back"}]}
        runner, state, _scheduler, _performed, selected, selections, messages = make_runner(
            [paused, other, control], selected_key="y", include_control_selection=True,
        )
        runner.handle_key("y")
        selected["key"] = "x"
        runner.handle_key("x")
        runner.handle_key("x")
        self.assertTrue(state.run_to_end_paused)
        # 選んでいる X と直前のトリガー Y が異なる状態（暫定 34 §10 の 9c）
        state.last_trigger = ("", "y")
        selections.clear()

        runner.handle_key("b")
        self.assertEqual(selected["key"], "x")
        self.assertEqual(selections, [])
        self.assertIn("一時停止中の x を破棄します。もう一度押すと実行します", messages)
        runner.handle_key("b")

        self.assertFalse(state.run_to_end_paused)
        self.assertEqual(state.indices_for("").get("x", 0), 0)
        self.assertEqual(state.indices_for("").get("y", 0), 1)
        self.assertEqual(selected["key"], "x")
        self.assertEqual(selections, ["x"])

    def test_pause_resume_and_own_pending_wait_keep_existing_handling(self):
        continuous = {"key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
                      "actions": [A1, A2]}
        runner, state, scheduler, performed, selected, selections, _messages = make_runner(
            [continuous], selected_key="f1", enabled=True,
        )
        runner.handle_key("f1")
        selected["key"] = None
        runner.handle_key("f1")
        self.assertTrue(state.run_to_end_paused)
        selections.clear()
        runner.handle_key("f1")
        self.assertFalse(state.run_to_end_paused)
        self.assertEqual(selections, [])
        scheduler.run_one()
        self.assertEqual(performed, [A1, A2])

        waiting = {"key": "f2", "actions": [A1, {"type": "system", "op": "wait", "ms": 5}, A2]}
        runner, state, scheduler, performed, selected, selections, _messages = make_runner(
            [waiting], selected_key="f2", enabled=True,
        )
        runner.handle_key("f2")
        selected["key"] = None
        selections.clear()
        runner.handle_key("f2")
        self.assertIn(("", "f2"), state.pending_steps)
        self.assertEqual(selections, [])
        self.assertEqual(performed, [A1])

    def test_select_only_continuous_press_preserves_paused_run_and_other_wait(self):
        paused = {"key": "f1", "run_to_end": True, "run_to_end_delay_ms": 0,
                  "actions": [A1, A1]}
        waiting = {"key": "f2", "actions": [A2, {"type": "system", "op": "wait", "ms": 8}, A1]}
        continuous = {"key": "f3", "run_to_end": True, "run_to_end_delay_ms": 0,
                      "actions": [A2, A2]}
        runner, state, _scheduler, _performed, selected, selections, _messages = make_runner(
            [paused, waiting, continuous], selected_key="f1", enabled=True,
        )
        runner.handle_key("f1")
        runner.handle_key("f1")
        runner.handle_key("f2")
        runner.handle_key("f2")
        self.assertTrue(state.run_to_end_paused)
        self.assertIn(("", "f2"), state.pending_steps)
        selected["key"] = None
        selections.clear()

        runner.handle_key("f3")
        self.assertEqual(selections, ["f3"])
        self.assertEqual(selected["key"], "f3")
        self.assertEqual(state.run_to_end_key, "f1")
        self.assertTrue(state.run_to_end_paused)
        self.assertIn(("", "f2"), state.pending_steps)

    def test_none_selected_key_treats_duplicate_row_as_not_selected(self):
        trigger = {"key": "f1", "actions": [A1]}
        runner, _state, _scheduler, performed, selected, selections, _messages = make_runner(
            [trigger], selected_key=None, enabled=True,
        )
        runner.handle_key("f1")
        self.assertEqual(performed, [])
        self.assertEqual(selected["key"], "f1")
        self.assertEqual(selections, ["f1"])

    def test_repeat_of_select_only_key_is_ignored_until_other_down_or_release(self):
        first = {"key": "f1", "actions": [A1]}
        second = {"key": "f2", "actions": [A2]}
        runner, _state, _scheduler, performed, _selected, selections, messages = make_runner(
            [first, second], selected_key="f2", enabled=True,
        )
        runner.handle_key("f1")
        pending_control = ("", "f1")
        runner._pending_control_discard = pending_control
        runner.handle_key("f1", repeat=True)
        self.assertEqual(performed, [])
        self.assertEqual(selections, ["f1"])
        self.assertEqual(len(messages), 1)
        self.assertIs(runner._pending_control_discard, pending_control)
        runner.handle_key("f1", repeat=False)
        self.assertEqual(performed, [A1])

        runner, _state, _scheduler, performed, _selected, selections, messages = make_runner(
            [first, second], selected_key="f2", enabled=True,
        )
        runner.handle_key("f1")
        runner.handle_key("f2")
        runner.handle_key("f1", repeat=True)
        self.assertEqual(performed, [])
        self.assertEqual(selections, ["f1", "f2", "f1"])
        self.assertEqual(len(messages), 3)

        runner, _state, _scheduler, performed, _selected, _selections, _messages = make_runner(
            [first], selected_key=None, enabled=True,
        )
        runner.handle_key("f1")
        runner.handle_key("f9")
        runner.handle_key("f1", repeat=True)
        self.assertEqual(performed, [A1])

        runner, _state, _scheduler, performed, _selected, _selections, _messages = make_runner(
            [first], selected_key="f1", enabled=True,
        )
        runner.handle_key("f1", repeat=True)
        self.assertEqual(performed, [A1])

    def test_single_wait_reselects_only_when_selection_is_still_its_key(self):
        trigger = {"key": "f1", "actions": [A1, {"type": "system", "op": "wait", "ms": 5}]}
        runner, _state, scheduler, _performed, selected, selections, _messages = make_runner(
            [trigger], selected_key="f1", enabled=True,
        )
        runner.handle_key("f1")
        selections.clear()
        selected["key"] = "f2"
        scheduler.run_one()
        self.assertEqual(selected["key"], "f2")
        self.assertEqual(selections, ["f2"])

        runner, _state, scheduler, _performed, _selected, selections, _messages = make_runner(
            [trigger], selected_key="f1", enabled=True,
        )
        runner.handle_key("f1")
        selections.clear()
        scheduler.run_one()
        self.assertEqual(selections, ["f1"])

        runner, _state, scheduler, _performed, _selected, selections, _messages = make_runner(
            [trigger], enabled=False, inject=False,
        )
        runner.handle_key("f1")
        selections.clear()
        scheduler.run_one()
        self.assertEqual(selections, ["f1"])

        runner, _state, scheduler, _performed, selected, selections, _messages = make_runner(
            [trigger], selected_key="f1", enabled=False,
        )
        runner.handle_key("f1")
        selections.clear()
        selected["key"] = "f2"
        scheduler.run_one()
        self.assertEqual(selected["key"], "f2")
        self.assertEqual(selections, ["f2"])

    def test_single_wait_does_not_reselect_when_no_trigger_is_selected(self):
        trigger = {"key": "f1", "actions": [A1, {"type": "system", "op": "wait", "ms": 5}]}
        runner, _state, scheduler, _performed, selected, selections, _messages = make_runner(
            [trigger], selected_key="f1", enabled=True,
        )
        runner.handle_key("f1")
        selections.clear()
        selected["key"] = None

        scheduler.run_one()

        self.assertIsNone(selected["key"])
        self.assertEqual(selections, [])

    def test_step_call_caller_can_be_pressed_again_without_select_only_interruption(self):
        caller = {"key": "f1", "actions": [
            {"type": "system", "op": "call", "target": "f2"}, A2,
        ]}
        callee = {"key": "f2", "actions": [A1, A2]}
        runner, _state, scheduler, performed, selected, selections, messages = make_runner(
            [caller, callee], selected_key="f1", enabled=True,
        )

        runner.handle_key("f1")
        scheduler.run_one()
        self.assertEqual(performed, [A1])
        self.assertEqual(selected["key"], "f1")
        selections.clear()
        messages.clear()

        runner.handle_key("f1")
        scheduler.run_one()

        self.assertEqual(performed, [A1, A2])
        # 実行後に runner が押したキーを選ぶ既存の動きだけで、選ぶだけの案内は出ない
        self.assertEqual(set(selections), {"f1"})
        self.assertEqual(messages, [])

    def test_call_chain_other_trigger_is_select_only_on_first_press(self):
        caller = {"key": "f1", "actions": [
            {"type": "system", "op": "call", "target": "f2"},
        ]}
        callee = {"key": "f2", "actions": [A1, A2]}
        runner, _state, scheduler, performed, selected, selections, messages = make_runner(
            [caller, callee], selected_key="f1", enabled=True,
        )

        runner.handle_key("f1")
        scheduler.run_one()
        self.assertEqual(performed, [A1])
        selections.clear()
        messages.clear()

        runner.handle_key("f2")

        self.assertEqual(performed, [A1])
        self.assertEqual(selected["key"], "f2")
        self.assertEqual(selections, ["f2"])
        self.assertEqual(messages, ["f2 を選びました（もう一度押すと実行します）"])

    def test_call_to_trigger_with_pending_wait_selects_then_keeps_existing_ignore(self):
        caller = {"key": "f1", "actions": [
            {"type": "system", "op": "call", "target": "f2"},
        ]}
        waiting = {"key": "f2", "actions": [A1, {"type": "system", "op": "wait", "ms": 5}, A2]}
        runner, state, _scheduler, performed, selected, selections, messages = make_runner(
            [caller, waiting], selected_key="f2", enabled=True,
        )
        runner.handle_key("f2")
        self.assertIn(("", "f2"), state.pending_steps)
        performed.clear()
        selections.clear()
        messages.clear()
        selected["key"] = None

        runner.handle_key("f1")
        self.assertEqual(performed, [])
        self.assertEqual(selected["key"], "f1")
        self.assertEqual(selections, ["f1"])
        self.assertEqual(messages, ["f1 を選びました（もう一度押すと実行します）"])

        runner.handle_key("f1")
        self.assertEqual(performed, [])
        self.assertIn(("", "f2"), state.pending_steps)
        # 2 回目は選ぶだけにならない（案内は 1 回目の分だけ）。選択は実行後の既存の選び直しで f1 のまま
        self.assertEqual(messages, ["f1 を選びました（もう一度押すと実行します）"])
        self.assertEqual(selected["key"], "f1")

    def test_call_to_paused_trigger_selects_then_keeps_existing_discard(self):
        paused = {"key": "f2", "actions": [
            {"type": "system", "op": "call", "target": "f3", "all": True},
        ]}
        callee = {"key": "f3", "actions": [A1, {"type": "system", "op": "wait", "ms": 5}, A2]}
        caller = {"key": "f1", "actions": [
            {"type": "system", "op": "call", "target": "f2"},
        ]}
        runner, state, scheduler, performed, selected, selections, messages = make_runner(
            [caller, paused, callee], selected_key="f2", enabled=True,
        )

        runner.handle_key("f2")
        scheduler.run_one()
        scheduler.run_one()
        runner.handle_key("f2")
        pending = state.pending_steps[("", "f2")]
        self.assertTrue(pending.call_paused)
        performed.clear()
        selections.clear()
        messages.clear()
        selected["key"] = None

        runner.handle_key("f1")
        self.assertEqual(selected["key"], "f1")
        self.assertTrue(state.pending_steps[("", "f2")].call_paused)
        self.assertEqual(performed, [])
        self.assertEqual(selections, ["f1"])

        runner.handle_key("f1")
        while scheduler.queue:
            scheduler.run_one()
        self.assertNotIn(("", "f2"), state.pending_steps)
        self.assertFalse(runner.paused_keys())
        self.assertEqual(performed, [A2])
        self.assertEqual(messages, [
            "f1 を選びました（もう一度押すと実行します）",
            "一時停止中の実行を破棄しました（f2）",
        ])

    def test_single_wait_keeps_selection_made_by_trigger_press(self):
        waiting = {"key": "f1", "actions": [
            A1, {"type": "system", "op": "wait", "ms": 5},
        ]}
        other = {"key": "f2", "actions": [A2]}
        runner, _state, scheduler, _performed, selected, selections, _messages = make_runner(
            [waiting, other], selected_key="f1", enabled=True,
        )
        runner.handle_key("f1")
        selections.clear()

        runner.handle_key("f2")
        self.assertEqual(selected["key"], "f2")
        self.assertEqual(selections, ["f2"])
        scheduler.run_one()

        self.assertEqual(selected["key"], "f2")
        self.assertEqual(selections, ["f2", "f2"])

    def test_repeated_waits_keep_selection_made_by_trigger_press(self):
        waiting = {"key": "f1", "actions": [
            A1, {"type": "system", "op": "wait", "ms": 5}, A2,
            {"type": "system", "op": "wait", "ms": 7}, A1,
        ]}
        other = {"key": "f2", "actions": [A2]}
        runner, _state, scheduler, _performed, selected, selections, _messages = make_runner(
            [waiting, other], selected_key="f1", enabled=True,
        )
        runner.handle_key("f1")
        selections.clear()

        runner.handle_key("f2")
        self.assertEqual(selected["key"], "f2")
        self.assertEqual(selections, ["f2"])

        scheduler.run_one()
        self.assertEqual(selected["key"], "f2")
        self.assertEqual(selections, ["f2", "f2"])
        scheduler.run_one()
        self.assertEqual(selected["key"], "f2")
        self.assertEqual(selections, ["f2", "f2"])  # 2 つ目の待機は次の押下まで始まらない

    def test_wait_refreshes_linked_caller_after_callee_completes(self):
        caller = {"key": "x", "actions": [
            {"type": "system", "op": "call", "target": "a"},
            {"type": "text", "value": "c"},
        ]}
        callee = {"key": "a", "actions": [
            A1, A2, {"type": "system", "op": "wait", "ms": 5},
        ]}
        runner, state, scheduler, _performed, selected, selections, _messages = make_runner(
            [caller, callee], selected_key="a", enabled=True,
        )
        # X has already called A to send a; A is about to send b and wait.
        state.indices_for("")["x"] = 0
        state.indices_for("")["a"] = 1
        state.call_refs_for("").add("x")

        runner.handle_key("a")
        self.assertIn(("", "a"), state.pending_steps)
        selected["key"] = "x"
        selections.clear()
        scheduler.run_one()

        self.assertEqual(selected["key"], "x")
        self.assertEqual(selections[-1], "x")
        self.assertEqual(state.indices_for("")["x"], 1)


if __name__ == "__main__":
    unittest.main()
