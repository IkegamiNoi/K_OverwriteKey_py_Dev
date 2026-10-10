from __future__ import annotations

from collections.abc import Iterable, Sequence
from contextlib import AbstractContextManager, nullcontext
from typing import Any, Callable

from keyseq.application.call_context import CallContext
from keyseq.application.held_inputs import HeldInputs
from keyseq.application.call_chain import chain_from
from keyseq.application.sequence_history import (
    StepSnapshot, apply_control, commit_step, commit_press, snapshot_for,
)
from keyseq.domain.config import normalize_key_name
from keyseq.domain.sequence_control import (
    ACTION_TYPE_FILE_LINE, ACTION_TYPE_SYSTEM, OP_CALL, system_op,
)
from keyseq.application.sequence_steps import (
    LoopFrame, StepOutcome, StepResume, advance, format_system_error_notification,
    apply_deferred_counters, reset_frames, resume_for_pending,
)
from keyseq.application.sequence_runner.file_line_wait import (
    FILE_LINE_POLL_INTERVAL_MS, FILE_LINE_UNAVAILABLE_MESSAGE, FileLineWaitMixin,
)
from keyseq.application.sequence_runner.linked_call import LinkedCallMixin
from keyseq.application.sequence_runner.call_wait import CallWaitMixin
from keyseq.application.sequence_runner.call_run_to_end import CallRunToEndMixin
from keyseq.application.sequence_runner.input_acceptance import InputAcceptanceMixin
from keyseq.application.sequence_runner.wait_stop import WaitStopMixin
from keyseq.application.sequence_runner.send_wait import SendWaitMixin
from keyseq.application.sequence_runner.call_view_notice import CallViewMixin
from keyseq.application.sequence_runner.run_to_end import RunToEndMixin


class SequenceRunner(CallViewMixin, InputAcceptanceMixin, WaitStopMixin, SendWaitMixin, FileLineWaitMixin,
                     RunToEndMixin, LinkedCallMixin, CallWaitMixin, CallRunToEndMixin):
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
        notify_call_view: Callable[[], None] | None = None,
        list_trigger_keys: Callable[[], Sequence[str]] | None = None,
        get_selected_trigger_key: Callable[[], str | None] | None = None,
        is_select_before_run_enabled: Callable[[], bool] | None = None,
        held_inputs: HeldInputs | None = None,
    ):
        self.state = state
        self.held_inputs = held_inputs
        self._find_trigger = find_trigger
        self._list_trigger_keys = list_trigger_keys
        self._single_finishing_steps: dict[tuple[str, str], tuple[StepSnapshot, bool]] = {}
        self._perform_action = perform_action
        self._select_trigger = select_trigger
        self._get_selected_trigger_key = get_selected_trigger_key
        self._is_select_before_run_enabled = is_select_before_run_enabled
        self._select_only_key: str | None = None
        self._refresh_actions = refresh_actions
        self._update_status = update_status
        self._after = after
        self._after_cancel = after_cancel
        self._get_trigger_set_id = get_trigger_set_id or (lambda: "")
        self._notify_error = notify_error
        self._notify_message = notify_message
        self._notify_call_view = notify_call_view
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

    def _owner_scope(self, key: str) -> AbstractContextManager[None]:
        return self.held_inputs.owner_scope(key) if self.held_inputs is not None else nullcontext()

    def _notify_release_errors(self, errors: list[Exception]) -> None:
        if errors and self._notify_error is not None:
            message = "押下中の入力の解放に失敗しました: " + "; ".join(str(exc) for exc in errors)
            notify = self._notify_error
            # モーダル通知による再入は、取消・停止等の状態遷移を終えた後にする。
            self._after(0, lambda: notify({}, message))

    def _release_owner(self, key: str | None) -> None:
        if key is not None:
            self._release_owners((key,))

    def _release_owners(self, keys: Iterable[str]) -> None:
        if self.held_inputs is None:
            return
        errors: list[Exception] = []
        for key in dict.fromkeys(keys):
            errors.extend(self.held_inputs.release_owner(key))
        self._notify_release_errors(errors)

    def release_all_held(self) -> None:
        """押下中のキー / ボタンをすべて離し、送信の失敗を知らせる（キーマップの切替 / アクティブの削除・暫定 35 §2-19）。"""
        if self.held_inputs is None:
            return
        self._notify_release_errors(self.held_inputs.release_all())

    def _send_action(self, action: dict[str, Any], key: str) -> bool | None:
        with self._owner_scope(key):
            result = self._perform_action(action)
        if result is False:
            self._release_owner(key)
        return result

    def _begin_owned_file_line(self, action: dict[str, Any], key: str) -> object | None:
        with self._owner_scope(key):
            handle = self._begin_file_line(action)
        if handle is None:
            self._release_owner(key)
        return handle

    def _poll_owned_file_line(self, handle: object, key: str) -> bool | None:
        with self._owner_scope(key):
            result = self._poll_file_line(handle)
        if result is False:
            self._release_owner(key)
        return result

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

    def is_running_chain_callee(self, key: str) -> bool:
        """Identify callees protected from list edits during a running chain."""
        key = normalize_key_name(key)
        root = self.state.run_to_end_key
        if not key or root is None or self.state.run_to_end_paused or key == root:
            return False
        ctx = self._run_to_end_call
        if ctx is not None and ctx.trigger_set_id == self._get_trigger_set_id():
            if any(normalize_key_name(frame.key) == key for frame in ctx.stack):
                return True
            if not ctx.started and normalize_key_name(ctx.first_target) == key:
                return True
        return key in chain_from(
            self.state, self._get_trigger_set_id(), root, self._find_trigger,
        )[1:]

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
        # Paused calls already published their live progress when they paused.
        cancelling = tuple((current, pending) for current, pending in self.state.pending_steps.items()
                           if identity is None or current == identity)
        self._release_owners(current[1] for current, _pending in cancelling)
        for current, pending in cancelling:
            ctx = pending.call
            if ((identity is not None and current != identity)
                    or not isinstance(ctx, CallContext)):
                continue
            self.state.pending_steps.pop(current, None)
            if pending.after_id is not None:
                try:
                    self._after_cancel(pending.after_id)
                except Exception:
                    pass
            if not pending.call_paused:
                self._commit_linked_call(pending)
            self._publish_call_view()
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
        self._release_owner(key)
        self._cancel_calls_for_reset(key)
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
        self._publish_call_view()

    def _cancel_calls_for_reset(self, key: str) -> None:
        trigger_set_id = self._get_trigger_set_id()
        # The caller has already selected the new position; writeback must not undo it.
        position = self._get_index(key)
        identities = tuple(
            identity for identity, pending in self.state.pending_steps.items()
            if identity[0] == trigger_set_id and not pending.call_paused
            and isinstance(pending.call, CallContext)
            and self._call_context_uses_key(pending.call, key)
        )
        for identity in identities:
            self._cancel_pending_steps(identity, settle_wait=False)
        self._cancel_pending_steps((trigger_set_id, key), settle_wait=False)
        self.state.indices_for(trigger_set_id)[key] = position

    def cancel_pending_wait(self, key: str) -> None:
        identity = (self._get_trigger_set_id(), normalize_key_name(key))
        if identity not in self.state.pending_steps:
            self._release_owner(identity[1])
        self._cancel_pending_steps(identity)

    def cancel_pending_waits(self) -> None:
        self._cancel_pending_steps()

    def _control(self, key: str, op: str, target_key: str | None = None) -> str | None:
        self._control_source = key
        selected_key = None
        if target_key is None and self._get_selected_trigger_key is not None:
            candidate = self._get_selected_trigger_key()
            selected = self._find_trigger(candidate) if candidate else None
            if (candidate != key and selected is not None
                    and not self._is_standalone_control(selected.get("actions", []))):
                selected_key = candidate
        target, message = apply_control(self.state, (self._get_trigger_set_id(), key),
                                        op, self._find_trigger,
                                        prepare_targets=self._prepare_control_targets,
                                        target_key=target_key, selected_key=selected_key)
        if op == "rewind" and target is not None:
            self._release_owner(target)
        self._publish_call_view()
        if message and self._notify_message is not None:
            self._notify_message(message)
        return target

    def _report_error(self, action: dict[str, Any], message: str,
                      owner: str | None = None) -> None:
        if self.held_inputs is not None:
            if owner is None:
                owner = self.held_inputs.current_owner
            if owner is not None:
                errors = self.held_inputs.release_owner(owner)
                if errors:
                    message += " / 解放エラー: " + "; ".join(str(exc) for exc in errors)
        if self._notify_error is not None:
            if action.get("type") == "system":
                action, message = format_system_error_notification(action, message)
            self._notify_error(action, message)

    def handle_key(self, key: str, repeat: bool = False) -> None:
        key = normalize_key_name(key)
        if repeat and key == self._select_only_key:
            return
        self._select_only_key = None
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
        def on_control(op: str, target_key: str | None) -> None:
            nonlocal target
            target = self._control(key, op, target_key) or target
        try:
            starting_position = self._get_index(key) if position is None else position
            outcome = advance(actions, self._get_index(key) if position is None else position,
                              self._get_frames(key), self.state.counters,
                              wrap_once=True, resume=resume,
                              deferred_counters=self.state.deferred_counters_for(
                                  self._get_trigger_set_id()).get(key, ()),
                              on_control=on_control)
            self._save_progress(key, outcome.position, outcome.frames)
            if outcome.reached_end or outcome.wrapped:
                self._release_owner(key)
            if outcome.error:
                index, message = outcome.error
                self._report_error(actions[index], message, key)
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
                    self._report_error(action, FILE_LINE_UNAVAILABLE_MESSAGE, key)
                    return
                handle = self._begin_owned_file_line(action, key)
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
            if self._send_action(action, key) is False:
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
            if not self._is_standalone_control(actions):
                self._select_trigger(key)
            if target is not None:
                self._select_trigger(target)
