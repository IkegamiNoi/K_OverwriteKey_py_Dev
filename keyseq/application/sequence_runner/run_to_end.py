"""Control and advance continuous sequence execution."""

from __future__ import annotations

from typing import Any

from keyseq.application.call_context import CallContext, top_interval
from keyseq.application.sequence_history import StepSnapshot, snapshot_for
from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS, coerce_nonnegative_int, normalize_key_name
from keyseq.domain.sequence_control import ACTION_TYPE_FILE_LINE, ACTION_TYPE_SYSTEM, OP_CALL, OP_WAIT, system_op
from keyseq.application.sequence_steps import StepOutcome, StepResume, advance, after_normal_action, settle_after_normal


class RunToEndMixin:
    def _start_run_to_end(self, key: str) -> None:
        key = normalize_key_name(key)
        trig = self._find_trigger(key)
        if not trig:
            return
        actions = trig.get("actions", [])
        if not actions:
            return

        # Starting a run finishes ordinary single waits, never paused calls.
        for identity, pending in tuple(self.state.pending_steps.items()):
            if (identity[0] == self._get_trigger_set_id()
                    and pending.call is None and pending.file_line is None):
                self._cancel_pending_steps(identity)
        self._discard_run_to_end_file_line()
        self._discard_run_to_end_call()
        self._run_to_end_resume = None
        self._run_to_end_snapshot = None
        self._run_to_end_wait_position = None
        self._run_to_end_sent = False
        self._run_to_end_generation += 1
        self.state.run_to_end_key = key
        self.state.run_to_end_paused = False
        self._select_trigger(key)
        self._run_to_end_step(generation=self._run_to_end_generation, key=key)

    def pause_run_to_end(self) -> None:
        self.state.run_to_end_paused = True
        if self.state.run_to_end_after_id is not None:
            try:
                self._after_cancel(self.state.run_to_end_after_id)
            except Exception:
                pass
            self.state.run_to_end_after_id = None
        if self._finish_run_to_end_wait():
            self.stop_run_to_end()
            return
        self._discard_run_to_end_file_line()
        if self._run_to_end_call is not None:
            if not self._run_to_end_call.performing:
                self._commit_run_to_end_call(self._run_to_end_call)
            self._run_to_end_call_file_line = None
            self._run_to_end_call_token += 1
            self._publish_call_view()

    def resume_run_to_end(self) -> None:
        if self._rebuild_paused_run_to_end_call():
            return
        self.state.run_to_end_paused = False
        key = self.state.run_to_end_key
        trigger = self._find_trigger(key) if key is not None else None
        actions = trigger.get("actions", []) if trigger else []
        position = self._get_index(key) if key is not None else 0
        if (0 <= position < len(actions) and system_op(actions[position]) == OP_WAIT
                and self._run_to_end_wait_position is None):
            # Completion propagation left this row unprocessed while paused.
            settled = settle_after_normal(
                actions, position, self._get_frames(key), self.state.counters,
                allow_wrap=False, wait_mode="wait",
                deferred_counters=self.state.deferred_counters_for(
                    self._get_trigger_set_id()).get(key, ()),
            )
            if settled.wait_ms is not None:
                self._queue_run_to_end_wait(
                    key, settled, StepResume(position, False, 0),
                    snapshot_for(self.state, self._get_trigger_set_id(), key),
                )
                return
        self._run_to_end_step(schedule_only=True)

    def stop_run_to_end(self) -> None:
        self._run_to_end_generation += 1
        if self.state.run_to_end_after_id is not None:
            try:
                self._after_cancel(self.state.run_to_end_after_id)
            except Exception:
                pass
        self.state.run_to_end_after_id = None
        if not self.state.run_to_end_paused:
            self._finish_run_to_end_wait()
        if self._run_to_end_call is not None:
            if not self.state.run_to_end_paused:
                self._commit_run_to_end_call(self._run_to_end_call)
            self._run_to_end_resume = None
            self._run_to_end_snapshot = None
            self._run_to_end_wait_position = None
        self._discard_run_to_end_file_line()
        self._discard_run_to_end_call()
        if self._run_to_end_wait_position is not None:
            key = self.state.run_to_end_key
            snapshot = self._run_to_end_snapshot
            resume = self._run_to_end_resume
            if key is not None and snapshot is not None:
                self._set_index(key, self._run_to_end_wait_position)
                self._commit_step_and_publish(snapshot, resume.counter_deltas if resume else ())
        self.state.run_to_end_key = None
        self.state.run_to_end_paused = False
        self._run_to_end_resume = None
        self._run_to_end_snapshot = None
        self._run_to_end_wait_position = None
        self._update_status()

    def on_runtime_reset(self) -> None:
        self._single_finishing_steps.clear()
        if self.state.run_to_end_key is None:
            self._publish_call_view()
            return
        self._discard_run_to_end_file_line()
        self._discard_run_to_end_call()
        self._run_to_end_resume = None
        self._run_to_end_snapshot = None
        self._run_to_end_wait_position = None
        self.stop_run_to_end()

    def _run_to_end_step(self, schedule_only: bool = False, *,
                         generation: int | None = None, key: str | None = None) -> None:
        current_key = self.state.run_to_end_key
        if generation is not None and generation != self._run_to_end_generation:
            return
        if key is not None and key != current_key:
            return
        key = current_key
        if not key or self.state.run_to_end_paused:
            return
        trig = self._find_trigger(key)
        if not trig:
            if self._run_to_end_call is not None:
                self._abandon_invalid_run_to_end_call()
                return
            self.stop_run_to_end()
            return
        actions = trig.get("actions", [])
        if not actions:
            if self._run_to_end_call is not None:
                self._abandon_invalid_run_to_end_call()
                return
            self.stop_run_to_end()
            return
        delay = coerce_nonnegative_int(
            trig.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
            DEFAULT_RUN_TO_END_DELAY_MS,
        )
        if schedule_only:
            if self._run_to_end_call is not None:
                if (not isinstance(self._run_to_end_call, CallContext)
                        or not self._run_to_end_call_parent_is_current(
                            self._run_to_end_call,
                        )):
                    self._abandon_invalid_run_to_end_call()
                    return
                generation = self._run_to_end_generation
                token = self._run_to_end_call_token
                call = self._run_to_end_call
                delay = top_interval(call) if isinstance(call, CallContext) else 0
                self.state.run_to_end_after_id = self._after(
                    delay,
                    lambda: self._advance_run_to_end_call(generation, key, token),
                )
                return
            self._schedule_run_to_end_step(key, delay)
            return
        if self._run_to_end_wait_position is not None and self._run_to_end_resume is not None:
            index = self._run_to_end_wait_position
            if (0 <= index < len(actions) and isinstance(actions[index], dict)
                    and system_op(actions[index]) == OP_WAIT):
                self._continue_run_to_end_wait(key, actions)
                return
        self._perform_run_to_end_step(key, actions, delay)

    def _schedule_run_to_end_step(self, key: str, delay: int) -> None:
        generation = self._run_to_end_generation
        self.state.run_to_end_after_id = self._after(
            delay,
            lambda: self._run_to_end_step(generation=generation, key=key),
        )

    def _perform_run_to_end_step(self, key: str, actions: list[dict[str, Any]], delay: int) -> None:
        snapshot = self._run_to_end_snapshot or snapshot_for(self.state, self._get_trigger_set_id(), key)
        previous_resume = self._run_to_end_resume
        advance_position = self._get_index(key)
        target = None
        def on_control(op: str) -> None:
            nonlocal target
            target = self._control(key, op) or target
        outcome = advance(actions, self._get_index(key), self._get_frames(key),
                          self.state.counters, wrap_once=False,
                          resume=self._run_to_end_resume,
                          deferred_counters=self.state.deferred_counters_for(
                              self._get_trigger_set_id()).get(key, ()),
                          on_control=on_control,
                          stop_ends_run=self._run_to_end_sent)
        self._save_progress(key, outcome.position, outcome.frames)
        self._run_to_end_resume = None
        self._run_to_end_wait_position = None
        stop = outcome.error is not None or outcome.normal_index is None
        if outcome.error:
            index, message = outcome.error
            self._report_error(actions[index], message)
        elif outcome.normal_index is not None:
            index = outcome.normal_index
            action = actions[index]
            raw_type = action.get("type")
            action_type = raw_type.strip().lower() if isinstance(raw_type, str) else ""
            if action_type == ACTION_TYPE_FILE_LINE:
                initial_position = (
                    previous_resume.initial_position
                    if previous_resume is not None else advance_position
                )
                if self._begin_run_to_end_file_line(
                    key, action, index, outcome, snapshot, initial_position,
                ):
                    self._select_trigger(key)
                    if target is not None:
                        self._select_trigger(target)
                    return
                stop = True
            elif (action_type == ACTION_TYPE_SYSTEM
                  and system_op(action) == OP_CALL):
                self._begin_run_to_end_call(
                    key, actions, index, outcome, snapshot,
                )
                self._select_trigger(key)
                if target is not None:
                    self._select_trigger(target)
                return
            elif self._perform_action(action) is False:
                stop = True
            else:
                self._run_to_end_sent = True
                outcome.counter_deltas, position, stopped, waiting = self._finish_run_to_end_normal_action(
                    key, actions, index, outcome, snapshot,
                )
                if waiting:
                    self._select_trigger(key)
                    return
                stop = position == 0 or stopped
        elif outcome.stopped:
            outcome.counter_deltas, _position = self._settle_after_stopped_sequence(
                key, actions, outcome.position, outcome.frames,
                outcome.processed, outcome.counter_deltas,
            )
        if outcome.reached_end:
            self._record_single_completion(snapshot, True)
        self._commit_step_and_publish(snapshot, outcome.counter_deltas)
        if stop:
            self.stop_run_to_end()
        else:
            self._schedule_run_to_end_step(key, delay)
        self._run_to_end_snapshot = None
        self._select_trigger(key)
        if target is not None:
            self._select_trigger(target)

    def _finish_run_to_end_normal_action(
        self, key: str, actions: list[dict[str, Any]], index: int,
        outcome: StepOutcome | StepResume, snapshot: StepSnapshot,
    ) -> tuple[tuple[tuple[str, int], ...], int, bool, bool]:
        position, frames = after_normal_action(actions, index, self._get_frames(key))
        deferred = ()
        deltas = tuple(outcome.counter_deltas)
        stopped = False
        if position != 0:
            settled = settle_after_normal(
                actions, position, frames, self.state.counters,
                allow_wrap=False, processed=outcome.processed,
                stop_ends_run=True, wait_mode="wait",
            )
            position, frames = settled.position, settled.frames
            deltas += settled.counter_deltas
            deferred = settled.deferred_counters
            stopped = settled.stopped
            if settled.wait_ms is not None:
                self._queue_run_to_end_wait(key, settled, outcome, snapshot)
                return deltas, position, False, True
        if (position == 0 or stopped) and deferred:
            deltas += self._apply_deferred_counters_and_publish(deferred)
            deferred = ()
        if stopped:
            deltas, position = self._settle_after_stopped_sequence(
                key, actions, position, frames, settled.processed, deltas,
            )
        else:
            self._save_progress(key, position, frames, deferred)
        self._record_single_completion(snapshot, position == 0)
        return deltas, position, stopped, False
