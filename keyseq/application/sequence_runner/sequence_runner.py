from __future__ import annotations

from typing import Any, Callable

from keyseq.application.app_state import PendingStep
from keyseq.application.sequence_history import (
    StepSnapshot, apply_control, cancel_pending_steps, commit_step, snapshot_for,
)
from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS, coerce_nonnegative_int, normalize_key_name
from keyseq.domain.sequence_control import ACTION_TYPE_FILE_LINE
from keyseq.application.sequence_steps import (
    LoopFrame, StepOutcome, StepResume, advance, after_normal_action,
    apply_deferred_counters, format_system_error_notification, reset_frames,
    resume_for_pending, settle_after_normal,
)
from keyseq.application.sequence_runner.file_line_wait import (
    FILE_LINE_POLL_INTERVAL_MS, FileLineWaitMixin,
)


class SequenceRunner(FileLineWaitMixin):
    def __init__(
        self,
        *,
        state,
        find_trigger: Callable[[str], dict[str, Any] | None],
        perform_action: Callable[[dict[str, Any]], bool | None],
        select_trigger: Callable[[str], None],
        refresh_actions: Callable[[], None],
        update_status: Callable[[], None],
        after: Callable[[int, Callable[..., None]], Any],
        after_cancel: Callable[[Any], None],
        get_trigger_set_id: Callable[[], str] | None = None,
        notify_error: Callable[[dict, str], None] | None = None,
        notify_message: Callable[[str], None] | None = None,
        begin_file_line: Callable[[dict[str, Any]], object | None] | None = None,
        poll_file_line: Callable[[object], bool | None] | None = None,
    ):
        self.state = state
        self._find_trigger = find_trigger
        self._perform_action = perform_action
        self._select_trigger = select_trigger
        self._refresh_actions = refresh_actions
        self._update_status = update_status
        self._after = after
        self._after_cancel = after_cancel
        self._get_trigger_set_id = get_trigger_set_id or (lambda: "")
        self._notify_error = notify_error
        self._notify_message = notify_message
        self._begin_file_line = begin_file_line
        self._poll_file_line = poll_file_line
        self._run_to_end_resume: StepResume | None = None
        self._run_to_end_snapshot: StepSnapshot | None = None
        self._run_to_end_wait_position: int | None = None
        self._run_to_end_sent = False
        self._run_to_end_generation = 0
        self._run_to_end_file_line: object | None = None
        self._run_to_end_file_line_trigger_set_id: str | None = None
        self._run_to_end_file_line_token = 0

    def _get_index(self, key: str) -> int:
        return int(self.state.indices_for(self._get_trigger_set_id()).get(key, 0) or 0)

    def _set_index(self, key: str, value: int) -> None:
        self.state.indices_for(self._get_trigger_set_id())[key] = int(value)

    def _get_frames(self, key: str) -> list[LoopFrame]:
        return self.state.loop_frames_for(self._get_trigger_set_id()).get(key, [])

    def _save_progress(self, key: str, position: int, frames: list[LoopFrame],
                       deferred: list[tuple[str, str]] | tuple[tuple[str, str], ...] = ()) -> None:
        with self.state.lock:
            self._set_index(key, position)
            self.state.loop_frames_for(self._get_trigger_set_id())[key] = list(frames)
            self.state.deferred_counters_for(self._get_trigger_set_id())[key] = list(deferred)

    def reset_loop_frames(self, key: str) -> None:
        key = normalize_key_name(key)
        self.cancel_pending_wait(key)
        reschedule_run_to_end = (
            self.state.run_to_end_key == key
            and self._run_to_end_file_line is not None
            and not self.state.run_to_end_paused
        )
        if self.state.run_to_end_key == key:
            if reschedule_run_to_end and self.state.run_to_end_after_id is not None:
                try:
                    self._after_cancel(self.state.run_to_end_after_id)
                except Exception:
                    pass
                self.state.run_to_end_after_id = None
            self._discard_run_to_end_file_line()
            self._run_to_end_resume = None
            self._run_to_end_snapshot = None
            self._run_to_end_wait_position = None
        self.state.forget_trigger(self._get_trigger_set_id(), key)
        trigger = self._find_trigger(key)
        actions = trigger.get("actions", []) if trigger else []
        with self.state.lock:
            frames = reset_frames(actions, self._get_index(key))
            self.state.loop_frames_for(self._get_trigger_set_id())[key] = frames
        if reschedule_run_to_end:
            self._run_to_end_step(schedule_only=True)

    def cancel_pending_wait(self, key: str) -> None:
        identity = (self._get_trigger_set_id(), normalize_key_name(key))
        cancel_pending_steps(self.state, self._after_cancel, identity)

    def cancel_pending_waits(self) -> None:
        cancel_pending_steps(self.state, self._after_cancel)

    def _queue_single_wait(self, key: str, outcome: StepOutcome, snapshot: StepSnapshot) -> None:
        trigger_set_id = self._get_trigger_set_id()
        identity = (trigger_set_id, key)
        with self.state.lock:
            self.state.pending_step_generation += 1
            generation = self.state.pending_step_generation
            pending = PendingStep(generation, None, outcome.resume_position, outcome.resume, snapshot)
            self.state.pending_steps[identity] = pending
        pending.after_id = self._after(
            outcome.wait_ms,
            lambda: self._resume_single_wait(trigger_set_id, key, generation),
        )

    def _resume_single_wait(self, trigger_set_id: str, key: str, generation: int) -> None:
        identity = (trigger_set_id, key)
        with self.state.lock:
            pending = self.state.pending_steps.get(identity)
            if pending is None or pending.generation != generation:
                return
            self.state.pending_steps.pop(identity)
        if self._get_trigger_set_id() != trigger_set_id:
            return
        trigger = self._find_trigger(key)
        if trigger is None:
            return
        self._run_single_action(key, trigger.get("actions", []),
                                position=pending.position, resume=pending.resume,
                                snapshot=pending.snapshot)

    def _finish_single_normal_action(
        self, key: str, actions: list[dict[str, Any]], index: int,
        outcome: StepOutcome | StepResume,
    ) -> tuple[tuple[str, int], ...]:
        position, frames = after_normal_action(actions, index, self._get_frames(key))
        deferred = ()
        if not (position == 0 and outcome.wrapped):
            settled = settle_after_normal(
                actions, position, frames, self.state.counters,
                allow_wrap=position != 0 and not outcome.wrapped,
                processed=outcome.processed,
            )
            position, frames = settled.position, settled.frames
            deltas = outcome.counter_deltas + settled.counter_deltas
            deferred = settled.deferred_counters
        else:
            deltas = outcome.counter_deltas
        self._save_progress(key, position, frames, deferred)
        return deltas

    def _control(self, key: str, op: str) -> str | None:
        target, message = apply_control(self.state, (self._get_trigger_set_id(), key),
                                        op, self._find_trigger)
        if message and self._notify_message is not None:
            self._notify_message(message)
        return target

    def _report_error(self, action: dict[str, Any], message: str) -> None:
        if self._notify_error is not None:
            if action.get("type") == "system":
                action, message = format_system_error_notification(action, message)
            self._notify_error(action, message)

    def handle_key(self, key: str) -> None:
        key = normalize_key_name(key)
        # 連続実行中は同一トリガーのみトグル
        if self.state.run_to_end_key is not None:
            if key != self.state.run_to_end_key:
                return
            if not self.state.run_to_end_paused:
                self.pause_run_to_end()
            else:
                self.resume_run_to_end()
            self._update_status()
            return
        if (self._get_trigger_set_id(), key) in self.state.pending_steps:
            return
        trig = self._find_trigger(key)
        if not trig:
            return
        actions = trig.get("actions", [])
        if not actions:
            return
        if bool(trig.get("run_to_end", False)):
            self._start_run_to_end(key)
            return
        self._run_single_action(key, actions)

    def _run_single_action(self, key: str, actions: list[dict[str, Any]], *,
                           position: int | None = None, resume: StepResume | None = None,
                           snapshot: StepSnapshot | None = None) -> None:
        with self.state.lock:
            if key in self.state.reentry_guard:
                return
            self.state.reentry_guard.add(key)
        snapshot = snapshot or snapshot_for(self.state, self._get_trigger_set_id(), key)
        outcome = None
        target = None
        waiting = False
        def on_control(op: str) -> None:
            nonlocal target
            target = self._control(key, op) or target
        try:
            starting_position = self._get_index(key) if position is None else position
            outcome = advance(actions, self._get_index(key) if position is None else position,
                              self._get_frames(key), self.state.counters,
                              wrap_once=True, resume=resume,
                              deferred_counters=self.state.deferred_counters_for(
                                  self._get_trigger_set_id()).get(key, ()),
                              on_control=on_control)
            self._save_progress(key, outcome.position, outcome.frames)
            if outcome.wait_ms is not None:
                self._queue_single_wait(key, outcome, snapshot)
                waiting = True
                return
            if outcome.error:
                index, message = outcome.error
                self._report_error(actions[index], message)
                return
            if outcome.normal_index is None:
                return
            index = outcome.normal_index
            action = actions[index]
            raw_type = action.get("type")
            action_type = raw_type.strip().lower() if isinstance(raw_type, str) else ""
            if action_type == ACTION_TYPE_FILE_LINE:
                if self._begin_file_line is None or self._poll_file_line is None:
                    self._report_error(action, "file_line の読込の仕組みが未設定です")
                    return
                handle = self._begin_file_line(action)
                if handle is None:
                    return
                self._queue_single_file_line(
                    key, outcome, snapshot, handle,
                    resume.initial_position if resume is not None else starting_position,
                )
                waiting = True
                return
            if self._perform_action(action) is False:
                return
            outcome.counter_deltas = self._finish_single_normal_action(
                key, actions, index, outcome,
            )
        finally:
            if not waiting and outcome is not None:
                commit_step(self.state, snapshot, outcome.counter_deltas)
            with self.state.lock:
                self.state.reentry_guard.discard(key)
            self._select_trigger(key)
            if target is not None:
                self._select_trigger(target)

    # --- run_to_end ---
    def _start_run_to_end(self, key: str) -> None:
        key = normalize_key_name(key)
        trig = self._find_trigger(key)
        if not trig:
            return
        actions = trig.get("actions", [])
        if not actions:
            return

        self.cancel_pending_waits()
        self._discard_run_to_end_file_line()
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
        self._discard_run_to_end_file_line()

    def resume_run_to_end(self) -> None:
        self.state.run_to_end_paused = False
        self._run_to_end_step(schedule_only=True)

    def stop_run_to_end(self) -> None:
        self._run_to_end_generation += 1
        if self.state.run_to_end_after_id is not None:
            try:
                self._after_cancel(self.state.run_to_end_after_id)
            except Exception:
                pass
        self.state.run_to_end_after_id = None
        self._discard_run_to_end_file_line()
        if self._run_to_end_wait_position is not None:
            key = self.state.run_to_end_key
            snapshot = self._run_to_end_snapshot
            resume = self._run_to_end_resume
            if key is not None and snapshot is not None:
                self._set_index(key, self._run_to_end_wait_position)
                commit_step(self.state, snapshot, resume.counter_deltas if resume else ())
        self.state.run_to_end_key = None
        self.state.run_to_end_paused = False
        self._run_to_end_resume = None
        self._run_to_end_snapshot = None
        self._run_to_end_wait_position = None
        self._update_status()

    def on_runtime_reset(self) -> None:
        if self.state.run_to_end_key is None:
            return
        self._discard_run_to_end_file_line()
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
            self.stop_run_to_end()
            return
        actions = trig.get("actions", [])
        if not actions:
            self.stop_run_to_end()
            return
        delay = coerce_nonnegative_int(
            trig.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
            DEFAULT_RUN_TO_END_DELAY_MS,
        )
        if schedule_only:
            self._schedule_run_to_end_step(key, delay)
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
        self._save_progress(key, outcome.resume_position if outcome.wait_ms is not None
                            else outcome.position, outcome.frames)
        if outcome.wait_ms is not None:
            self._run_to_end_resume = outcome.resume
            self._run_to_end_snapshot = snapshot
            self._run_to_end_wait_position = outcome.resume_position - 1
            self._schedule_run_to_end_step(key, outcome.wait_ms)
        else:
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
                elif self._perform_action(action) is False:
                    stop = True
                else:
                    self._run_to_end_sent = True
                    outcome.counter_deltas, position, stopped = self._finish_run_to_end_normal_action(
                        key, actions, index, outcome,
                    )
                    stop = position == 0 or stopped
            elif outcome.stopped:
                outcome.counter_deltas, _position = self._settle_after_stopped_sequence(
                    key, actions, outcome.position, outcome.frames,
                    outcome.processed, outcome.counter_deltas,
                )
            commit_step(self.state, snapshot, outcome.counter_deltas)
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
        outcome: StepOutcome | StepResume,
    ) -> tuple[tuple[tuple[str, int], ...], int, bool]:
        position, frames = after_normal_action(actions, index, self._get_frames(key))
        deferred = ()
        deltas = tuple(outcome.counter_deltas)
        stopped = False
        if position != 0:
            settled = settle_after_normal(
                actions, position, frames, self.state.counters,
                allow_wrap=False, processed=outcome.processed,
                stop_ends_run=True,
            )
            position, frames = settled.position, settled.frames
            deltas += settled.counter_deltas
            deferred = settled.deferred_counters
            stopped = settled.stopped
        if (position == 0 or stopped) and deferred:
            deltas += apply_deferred_counters(deferred, self.state.counters)
            deferred = ()
        if stopped:
            deltas, position = self._settle_after_stopped_sequence(
                key, actions, position, frames, outcome.processed, deltas,
            )
        else:
            self._save_progress(key, position, frames, deferred)
        return deltas, position, stopped

    def _settle_after_stopped_sequence(
        self, key: str, actions: list[dict[str, Any]], position: int,
        frames: list[LoopFrame], processed: int,
        deltas: tuple[tuple[str, int], ...],
    ) -> tuple[tuple[tuple[str, int], ...], int]:
        if position == 0:
            self._save_progress(key, 0, [], ())
            return deltas, 0
        settled = settle_after_normal(
            actions, position, frames, self.state.counters,
            allow_wrap=False, processed=processed, stop_ends_run=False,
        )
        position, frames = settled.position, settled.frames
        deltas += settled.counter_deltas
        deferred = settled.deferred_counters
        if position == 0 and deferred:
            deltas += apply_deferred_counters(deferred, self.state.counters)
            deferred = ()
        self._save_progress(key, position, frames, deferred)
        return deltas, position
