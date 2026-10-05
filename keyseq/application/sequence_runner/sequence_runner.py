from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, Callable

from keyseq.application.call_context import CallContext, top_interval
from keyseq.application.call_view import CallViewSummary
from keyseq.application.sequence_history import (
    StepSnapshot, apply_control, commit_step, commit_press, snapshot_for,
)
from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS, coerce_nonnegative_int, normalize_key_name
from keyseq.domain.sequence_control import (
    ACTION_TYPE_FILE_LINE, ACTION_TYPE_SYSTEM, OP_CALL, OP_WAIT, system_op,
)
from keyseq.application.sequence_steps import (
    LoopFrame, StepOutcome, StepResume, advance, format_system_error_notification,
    after_normal_action, apply_deferred_counters, reset_frames, resume_for_pending,
    settle_after_normal,
)
from keyseq.application.sequence_runner.file_line_wait import (
    FILE_LINE_POLL_INTERVAL_MS, FILE_LINE_UNAVAILABLE_MESSAGE, FileLineWaitMixin,
)
from keyseq.application.sequence_runner.call_wait import CallWaitMixin
from keyseq.application.sequence_runner.call_run_to_end import CallRunToEndMixin
from keyseq.application.sequence_runner.input_acceptance import InputAcceptanceMixin
from keyseq.application.sequence_runner.wait_stop import WaitStopMixin
from keyseq.application.sequence_runner.send_wait import SendWaitMixin
from keyseq.application.sequence_runner.call_view_notice import CallViewMixin, RUN_TO_END_CALL_VIEW


class SequenceRunner(CallViewMixin, InputAcceptanceMixin, WaitStopMixin, SendWaitMixin, FileLineWaitMixin,
                     CallWaitMixin, CallRunToEndMixin):
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
        notify_call_view: Callable[[CallViewSummary | None], None] | None = None,
        list_trigger_keys: Callable[[], Sequence[str]] | None = None,
    ):
        self.state = state
        self._find_trigger = find_trigger
        self._list_trigger_keys = list_trigger_keys
        self._single_finishing_steps: dict[tuple[str, str], tuple[StepSnapshot, bool]] = {}
        self._perform_action = perform_action
        self._select_trigger = select_trigger
        self._refresh_actions = refresh_actions
        self._update_status = update_status
        self._after = after
        self._after_cancel = after_cancel
        self._get_trigger_set_id = get_trigger_set_id or (lambda: "")
        self._notify_error = notify_error
        self._notify_message = notify_message
        self._notify_call_view = notify_call_view
        self._call_view_contexts: dict[tuple[str, str] | str, CallContext] = {}
        self._call_view_open = False
        self._begin_file_line = begin_file_line
        self._poll_file_line = poll_file_line
        self._pending_control_discard: tuple | None = None
        self._control_source: str | None = None
        self._run_to_end_resume: StepResume | None = None
        self._run_to_end_snapshot: StepSnapshot | None = None
        self._run_to_end_wait_position: int | None = None
        self._run_to_end_sent = False
        self._run_to_end_generation = 0
        self._run_to_end_file_line: object | None = None
        self._run_to_end_file_line_trigger_set_id: str | None = None
        self._run_to_end_file_line_token = 0
        self._run_to_end_call: CallContext | None = None
        self._run_to_end_call_token = 0
        self._run_to_end_call_file_line: object | None = None

    def _get_index(self, key: str) -> int:
        return int(self.state.indices_for(self._get_trigger_set_id()).get(key, 0) or 0)

    def has_active_execution(self, key: str) -> bool:
        """Return whether the active trigger set is using this normalized key."""
        key = normalize_key_name(key)
        if not key:
            return False
        trigger_set_id = self._get_trigger_set_id()
        if normalize_key_name(self.state.run_to_end_key or "") == key:
            return True

        with self.state.lock:
            pending_steps = tuple(
                (identity, pending)
                for identity, pending in self.state.pending_steps.items()
                if identity[0] == trigger_set_id
            )
        if any(normalize_key_name(identity[1]) == key
               for identity, _pending in pending_steps):
            return True

        context = self._run_to_end_call
        if (context is not None and context.trigger_set_id == trigger_set_id
                and self._call_context_uses_key(context, key)):
            return True
        for _identity, pending in pending_steps:
            context = getattr(pending, "call", None)
            if context is not None and self._call_context_uses_key(context, key):
                return True
        return False

    def has_any_active_execution(self) -> bool:
        """Return whether any trigger set has work in progress or waiting."""
        with self.state.lock:
            has_pending_steps = bool(self.state.pending_steps)
            has_single_action = bool(self.state.reentry_guard)
        return bool(
            self.state.run_to_end_key is not None
            or has_single_action
            # Pending steps include paused calls, send waits, and file-line loads.
            or has_pending_steps
            or self._run_to_end_wait_position is not None
            or self._run_to_end_file_line is not None
            or self._run_to_end_call is not None
            or self._run_to_end_call_file_line is not None
        )

    @staticmethod
    def _call_context_uses_key(context: CallContext, key: str) -> bool:
        keys = (context.root_key, context.first_target,
                *(frame.key for frame in context.stack))
        return any(normalize_key_name(frame_key) == key for frame_key in keys)

    def _set_index(self, key: str, value: int) -> None:
        self.state.indices_for(self._get_trigger_set_id())[key] = int(value)

    def _get_frames(self, key: str) -> list[LoopFrame]:
        return self.state.loop_frames_for(self._get_trigger_set_id()).get(key, [])

    def _commit_step_and_publish(
        self, snapshot: StepSnapshot, deltas: Iterable[tuple[str, int]],
    ) -> bool:
        identity = (snapshot.trigger_set_id, snapshot.key)
        finishing = self._single_finishing_steps.get(identity)
        if finishing is not None and finishing[0] is snapshot and finishing[1]:
            before = {snapshot.key: snapshot}
            owned = {snapshot.key: list(deltas)}
            self._propagate_linked_completion([snapshot.key], before, owned, {snapshot.key})
            committed = commit_press(self.state, list(before.values()), owned,
                                     pressed_key=snapshot.key)
        else:
            committed = commit_step(self.state, snapshot, deltas)
        if finishing is not None and finishing[0] is snapshot:
            self._single_finishing_steps.pop(identity)
        self._publish_call_view()
        return committed

    def _finish_single_normal_action(
        self, key: str, actions: list[dict[str, Any]], index: int,
        outcome: StepOutcome | StepResume, snapshot: StepSnapshot,
    ) -> tuple[tuple[str, int], ...] | None:
        self._record_single_completion(snapshot, index + 1 >= len(actions) or outcome.wrapped)
        return super()._finish_single_normal_action(key, actions, index, outcome, snapshot)

    def _record_single_completion(self, snapshot: StepSnapshot, reached_end: bool) -> None:
        identity = (snapshot.trigger_set_id, snapshot.key)
        previous = self._single_finishing_steps.get(identity)
        reached_end = reached_end or (previous is not None and previous[0] is snapshot and previous[1])
        self._single_finishing_steps[identity] = (snapshot, reached_end)

    def _cancel_pending_steps(
        self, identity: tuple[str, str] | None = None, *, settle_wait: bool = True,
    ) -> None:
        # Keep the legacy cancellation helper untouched for snapshot-based runs.
        cancelling = tuple((current, pending) for current, pending in self.state.pending_steps.items()
                           if identity is None or current == identity)
        for current, pending in cancelling:
            ctx = pending.call
            if ((identity is not None and current != identity)
                    or not isinstance(ctx, CallContext) or ctx.state is None):
                continue
            self.state.pending_steps.pop(current, None)
            if pending.after_id is not None:
                try:
                    self._after_cancel(pending.after_id)
                except Exception:
                    pass
            self._commit_linked_call(pending)
            self._call_view_disappeared(current)
        super()._cancel_pending_steps(identity, settle_wait=settle_wait)
        for _current, pending in cancelling:
            finishing = self._single_finishing_steps.get(_current)
            if finishing is not None and finishing[0] is pending.snapshot:
                self._single_finishing_steps.pop(_current)

    def _apply_deferred_counters_and_publish(
        self, deferred: Sequence[tuple[str, str]],
    ) -> tuple[tuple[str, int], ...]:
        deltas = apply_deferred_counters(deferred, self.state.counters)
        self._publish_call_view()
        return deltas

    def _save_progress(self, key: str, position: int, frames: list[LoopFrame],
                       deferred: list[tuple[str, str]] | tuple[tuple[str, str], ...] = ()) -> None:
        with self.state.lock:
            self._set_index(key, position)
            self.state.loop_frames_for(self._get_trigger_set_id())[key] = list(frames)
            self.state.deferred_counters_for(self._get_trigger_set_id())[key] = list(deferred)
        self._publish_call_view()

    def reset_loop_frames(self, key: str) -> None:
        key = normalize_key_name(key)
        self._cancel_pending_steps((self._get_trigger_set_id(), key), settle_wait=False)
        reschedule_run_to_end = (
            self.state.run_to_end_key == key
            and (self._run_to_end_file_line is not None
                 or self._run_to_end_call is not None)
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
            self._discard_run_to_end_call()
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
        self._cancel_pending_steps(identity)

    def cancel_pending_waits(self) -> None:
        self._cancel_pending_steps()

    def _control(self, key: str, op: str) -> str | None:
        self._control_source = key
        target, message = apply_control(self.state, (self._get_trigger_set_id(), key),
                                        op, self._find_trigger,
                                        self._prepare_control_target)
        self._publish_call_view()
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
        if (self._pending_control_discard is not None
                and key != self._pending_control_discard[0]):
            self._pending_control_discard = None
        self._accept_key(key)

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
            if outcome.error:
                index, message = outcome.error
                self._report_error(actions[index], message)
                return
            if outcome.normal_index is None:
                if outcome.reached_end:
                    self._record_single_completion(snapshot, True)
                return
            index = outcome.normal_index
            action = actions[index]
            raw_type = action.get("type")
            action_type = raw_type.strip().lower() if isinstance(raw_type, str) else ""
            if action_type == ACTION_TYPE_FILE_LINE:
                if self._file_line_unavailable():
                    self._report_error(action, FILE_LINE_UNAVAILABLE_MESSAGE)
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
            if (action_type == ACTION_TYPE_SYSTEM
                    and system_op(action) == OP_CALL):
                initial_position = (
                    resume.initial_position if resume is not None else starting_position
                )
                self._start_single_call(key, actions, outcome, snapshot, initial_position)
                waiting = True
                return
            if self._perform_action(action) is False:
                return
            outcome.counter_deltas = self._finish_single_normal_action(
                key, actions, index, outcome, snapshot,
            )
            waiting = outcome.counter_deltas is None
        finally:
            if not waiting and outcome is not None:
                self._commit_step_and_publish(snapshot, outcome.counter_deltas)
            with self.state.lock:
                self.state.reentry_guard.discard(key)
            self._publish_call_view()
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
            self._run_to_end_call_file_line = None
            self._run_to_end_call_token += 1
            self._call_view_stopped(RUN_TO_END_CALL_VIEW, self._run_to_end_call)

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
        self._finish_run_to_end_wait()
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
        self._call_view_contexts.clear()
        self._publish_call_view()
        if self.state.run_to_end_key is None:
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
                initial_position = (
                    previous_resume.initial_position
                    if previous_resume is not None else advance_position
                )
                self._begin_run_to_end_call(
                    key, actions, index, outcome, snapshot, initial_position,
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
        return deltas, position, stopped, False
