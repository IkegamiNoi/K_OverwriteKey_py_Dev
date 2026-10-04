from __future__ import annotations

from dataclasses import replace
from typing import Any

from keyseq.application.app_state import PendingStep
from keyseq.application.call_context import (
    CallContext, CallStep, call_step, chain_text, finish_call_action, start_call,
)
from keyseq.application.sequence_history import StepSnapshot, commit_step
from keyseq.application.sequence_steps import StepOutcome, resume_for_pending
from keyseq.application.sequence_runner.file_line_wait import (
    FILE_LINE_POLL_INTERVAL_MS,
    FILE_LINE_UNAVAILABLE_MESSAGE,
)
from keyseq.domain.call_graph import call_target
from keyseq.domain.sequence_control import ACTION_TYPE_FILE_LINE, is_step_call


class CallWaitMixin:
    # Uses runner attributes: state, _after, _find_trigger, _get_trigger_set_id,
    # _begin_file_line, _poll_file_line, _perform_action, _report_error,
    # _finish_single_normal_action, _select_trigger.
    def _start_single_call(
        self, key: str, actions: list[dict[str, Any]], outcome: StepOutcome,
        snapshot: StepSnapshot, initial_position: int,
    ) -> None:
        trigger_set_id = self._get_trigger_set_id()
        ctx = start_call(
            trigger_set_id, key, call_target(actions[outcome.normal_index]), self._find_trigger,
            step=is_step_call(actions[outcome.normal_index]),
        )
        identity = (trigger_set_id, key)
        with self.state.lock:
            self.state.pending_step_generation += 1
            generation = self.state.pending_step_generation
            pending = PendingStep(
                generation, None, outcome.normal_index,
                resume_for_pending(outcome, initial_position), snapshot, call=ctx,
            )
            self.state.pending_steps[identity] = pending
        pending.after_id = self._after(
            0, lambda: self._advance_single_call(trigger_set_id, key, generation),
        )

    def _single_call_pending(
        self, trigger_set_id: str, key: str, generation: int,
    ) -> PendingStep | None:
        identity = (trigger_set_id, key)
        with self.state.lock:
            pending = self.state.pending_steps.get(identity)
            if (pending is None or pending.generation != generation
                    or pending.call is None or pending.call_paused):
                return None
            return pending

    def _call_pending_is_current(
        self, trigger_set_id: str, key: str, generation: int, pending: PendingStep,
    ) -> bool:
        return (
            self._get_trigger_set_id() == trigger_set_id
            and self._single_call_pending(trigger_set_id, key, generation) is pending
        )

    def _call_parent_is_current(
        self, trigger_set_id: str, key: str, generation: int, pending: PendingStep,
    ) -> bool:
        return (
            self._call_pending_is_current(trigger_set_id, key, generation, pending)
            and self._find_trigger(key) is not None
        )

    def _drop_single_call(
        self, trigger_set_id: str, key: str, generation: int, pending: PendingStep,
    ) -> bool:
        identity = (trigger_set_id, key)
        with self.state.lock:
            if (self.state.pending_steps.get(identity) is not pending
                    or pending.generation != generation):
                return False
            self.state.pending_steps.pop(identity)
            return True

    def _discard_if_parent_invalid(
        self, trigger_set_id: str, key: str, generation: int, pending: PendingStep,
    ) -> None:
        if (self._single_call_pending(trigger_set_id, key, generation) is pending
                and (self._get_trigger_set_id() != trigger_set_id
                     or self._find_trigger(key) is None)):
            self._drop_single_call(trigger_set_id, key, generation, pending)

    def _schedule_single_call(
        self, trigger_set_id: str, key: str, generation: int,
        pending: PendingStep, delay_ms: int,
    ) -> None:
        pending.after_id = self._after(
            delay_ms,
            lambda: self._advance_single_call(trigger_set_id, key, generation),
        )

    def _add_call_deltas(self, pending: PendingStep, deltas: tuple[tuple[str, int], ...]) -> None:
        pending.resume = replace(
            pending.resume, counter_deltas=pending.resume.counter_deltas + deltas,
        )

    def _advance_single_call(self, trigger_set_id: str, key: str, generation: int) -> None:
        pending = self._single_call_pending(trigger_set_id, key, generation)
        if pending is None:
            return
        ctx = pending.call
        if not isinstance(ctx, CallContext):
            return
        if (self._get_trigger_set_id() != ctx.trigger_set_id
                or self._find_trigger(key) is None):
            self._drop_single_call(trigger_set_id, key, generation, pending)
            return
        step = call_step(ctx, self.state.counters)
        self._add_call_deltas(pending, step.counter_deltas)
        if step.kind == "action":
            self._perform_single_call_action(
                trigger_set_id, key, generation, pending, step,
            )
        elif step.kind == "wait":
            self._schedule_single_call(
                trigger_set_id, key, generation, pending, step.wait_ms or 0,
            )
        elif step.kind == "error":
            self._report_single_call_error(
                trigger_set_id, key, generation, pending, step,
            )
        elif step.kind == "done":
            self._complete_single_call(trigger_set_id, key, generation, pending)

    def _perform_single_call_action(
        self, trigger_set_id: str, key: str, generation: int,
        pending: PendingStep, step: CallStep,
    ) -> None:
        action = step.action or {}
        raw_type = action.get("type")
        action_type = raw_type.strip().lower() if isinstance(raw_type, str) else ""
        if action_type == ACTION_TYPE_FILE_LINE:
            self._begin_single_call_file_line(
                trigger_set_id, key, generation, pending, step,
            )
            return
        succeeded = self._perform_action(action)
        if (pending.call_paused
                and self.state.pending_steps.get((trigger_set_id, key)) is pending
                and pending.generation != generation):
            if succeeded is False:
                self._fail_single_call(trigger_set_id, key, pending.generation, pending)
                return
            ctx = pending.call
            if isinstance(ctx, CallContext):
                following = finish_call_action(ctx, self.state.counters)
                self._add_call_deltas(pending, following.counter_deltas)
                if following.kind == "error":
                    message = following.message or "呼び出しを実行できません"
                    self._report_error(self._call_action(key, pending),
                                       message + self._call_chain_suffix(following))
                    self._fail_single_call(trigger_set_id, key, pending.generation, pending)
            return
        if not self._call_parent_is_current(trigger_set_id, key, generation, pending):
            self._discard_if_parent_invalid(trigger_set_id, key, generation, pending)
            return
        if succeeded is False:
            self._fail_single_call(trigger_set_id, key, generation, pending)
            return
        ctx = pending.call
        if not isinstance(ctx, CallContext):
            return
        following = finish_call_action(ctx, self.state.counters)
        self._add_call_deltas(pending, following.counter_deltas)
        self._handle_finished_call_step(
            trigger_set_id, key, generation, pending, following,
        )

    def _begin_single_call_file_line(
        self, trigger_set_id: str, key: str, generation: int,
        pending: PendingStep, step: CallStep,
    ) -> None:
        if self._file_line_unavailable():
            self._report_error(
                self._call_action(key, pending),
                FILE_LINE_UNAVAILABLE_MESSAGE + self._call_chain_suffix(step),
            )
            if self._call_parent_is_current(trigger_set_id, key, generation, pending):
                self._fail_single_call(trigger_set_id, key, generation, pending)
            else:
                self._discard_if_parent_invalid(trigger_set_id, key, generation, pending)
            return
        handle = self._begin_file_line(step.action or {})
        if not self._call_parent_is_current(trigger_set_id, key, generation, pending):
            self._discard_if_parent_invalid(trigger_set_id, key, generation, pending)
            return
        if handle is None:
            self._fail_single_call(trigger_set_id, key, generation, pending)
            return
        pending.call_file_line = handle
        self._schedule_single_call_file_line(
            trigger_set_id, key, generation, pending,
        )

    def _schedule_single_call_file_line(
        self, trigger_set_id: str, key: str, generation: int, pending: PendingStep,
    ) -> None:
        pending.after_id = self._after(
            FILE_LINE_POLL_INTERVAL_MS,
            lambda: self._poll_single_call_file_line(trigger_set_id, key, generation),
        )

    def _poll_single_call_file_line(
        self, trigger_set_id: str, key: str, generation: int,
    ) -> None:
        pending = self._single_call_pending(trigger_set_id, key, generation)
        if pending is None or pending.call_file_line is None:
            return
        if not self._call_parent_is_current(trigger_set_id, key, generation, pending):
            self._discard_if_parent_invalid(trigger_set_id, key, generation, pending)
            return
        result = self._poll_file_line(pending.call_file_line)
        if not self._call_parent_is_current(trigger_set_id, key, generation, pending):
            self._discard_if_parent_invalid(trigger_set_id, key, generation, pending)
            return
        if result is None:
            self._schedule_single_call_file_line(
                trigger_set_id, key, generation, pending,
            )
            return
        if result is False:
            self._fail_single_call(trigger_set_id, key, generation, pending)
            return
        ctx = pending.call
        if not isinstance(ctx, CallContext):
            return
        following = finish_call_action(ctx, self.state.counters)
        pending.call_file_line = None
        self._add_call_deltas(pending, following.counter_deltas)
        self._handle_finished_call_step(
            trigger_set_id, key, generation, pending, following,
        )

    def _handle_finished_call_step(
        self, trigger_set_id: str, key: str, generation: int,
        pending: PendingStep, step: CallStep,
    ) -> None:
        if step.kind == "next":
            if isinstance(pending.call, CallContext) and pending.call.top_is_step():
                self._pause_single_call(key)
            else:
                self._schedule_single_call(
                    trigger_set_id, key, generation, pending, step.interval_ms or 0,
                )
        elif step.kind == "done":
            self._complete_single_call(trigger_set_id, key, generation, pending)
        elif step.kind == "error":
            self._report_single_call_error(
                trigger_set_id, key, generation, pending, step,
            )

    def _report_single_call_error(
        self, trigger_set_id: str, key: str, generation: int,
        pending: PendingStep, step: CallStep,
    ) -> None:
        message = step.message or "呼び出しを実行できません"
        suffix = f" / {chain_text(step.chain)}" if step.chain else ""
        self._report_error(self._call_action(key, pending), message + suffix)
        if self._call_parent_is_current(trigger_set_id, key, generation, pending):
            self._fail_single_call(trigger_set_id, key, generation, pending)
        elif (pending.call_paused
              and self.state.pending_steps.get((trigger_set_id, key)) is pending
              and self._get_trigger_set_id() == trigger_set_id
              and self._find_trigger(key) is not None):
            self._fail_single_call(trigger_set_id, key, pending.generation, pending)
        else:
            self._discard_if_parent_invalid(trigger_set_id, key, generation, pending)

    def _call_action(self, key: str, pending: PendingStep) -> dict[str, Any]:
        trigger = self._find_trigger(key)
        actions = trigger.get("actions", []) if trigger else []
        if 0 <= pending.position < len(actions):
            return actions[pending.position]
        return {"type": "system", "op": "call"}

    @staticmethod
    def _call_chain_suffix(step: CallStep) -> str:
        return f" / {chain_text(step.chain)}" if step.chain else ""

    def _fail_single_call(
        self, trigger_set_id: str, key: str, generation: int, pending: PendingStep,
    ) -> None:
        if not self._drop_single_call(trigger_set_id, key, generation, pending):
            return
        commit_step(self.state, pending.snapshot, pending.resume.counter_deltas)
        self._select_trigger(key)

    def _complete_single_call(
        self, trigger_set_id: str, key: str, generation: int, pending: PendingStep,
    ) -> None:
        if not self._drop_single_call(trigger_set_id, key, generation, pending):
            return
        trigger = self._find_trigger(key)
        if trigger is None:
            return
        deltas = self._finish_single_normal_action(
            key, trigger.get("actions", []), pending.position, pending.resume,
            pending.snapshot,
        )
        if deltas is not None:
            commit_step(self.state, pending.snapshot, deltas)
        self._select_trigger(key)
