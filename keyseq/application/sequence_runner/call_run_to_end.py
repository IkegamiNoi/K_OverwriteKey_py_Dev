from __future__ import annotations

from dataclasses import replace
from typing import Any

from keyseq.application.call_context import (
    CallContext,
    CallStep,
    call_step,
    chain_text,
    finish_call_action,
    start_call,
)
from keyseq.application.sequence_history import StepSnapshot, commit_step
from keyseq.application.sequence_steps import StepOutcome, resume_for_pending
from keyseq.application.sequence_runner.file_line_wait import FILE_LINE_POLL_INTERVAL_MS
from keyseq.domain.call_graph import call_target
from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS, coerce_nonnegative_int
from keyseq.domain.sequence_control import ACTION_TYPE_FILE_LINE


class CallRunToEndMixin:
    # Uses runner attributes: state, _after, _after_cancel, _begin_file_line,
    # _find_trigger, _finish_run_to_end_normal_action, _get_trigger_set_id,
    # _notify_error, _perform_action, _poll_file_line, _report_error,
    # _run_to_end_generation, _run_to_end_resume, _run_to_end_sent,
    # _run_to_end_snapshot, _run_to_end_wait_position, _save_progress,
    # _schedule_run_to_end_step, _select_trigger, _set_index, _update_status,
    # stop_run_to_end.
    def _begin_run_to_end_call(
        self, key: str, actions: list[dict[str, Any]], index: int,
        outcome: StepOutcome, snapshot: StepSnapshot, initial_position: int,
    ) -> None:
        ctx = start_call(
            self._get_trigger_set_id(), key, call_target(actions[index]), self._find_trigger,
        )
        self._run_to_end_resume = resume_for_pending(outcome, initial_position)
        self._run_to_end_snapshot = snapshot
        self._run_to_end_wait_position = index
        self._run_to_end_call = ctx
        self._run_to_end_call_token += 1
        self._run_to_end_call_file_line = None
        self._save_progress(key, index, outcome.frames)
        generation = self._run_to_end_generation
        token = self._run_to_end_call_token
        self.state.run_to_end_after_id = self._after(
            0, lambda: self._advance_run_to_end_call(generation, key, token),
        )

    def _discard_run_to_end_call(self) -> None:
        self._run_to_end_call = None
        self._run_to_end_call_file_line = None
        self._run_to_end_call_token += 1

    def _run_to_end_call_is_current(self, generation: int, key: str, token: int) -> bool:
        return (
            generation == self._run_to_end_generation
            and key == self.state.run_to_end_key
            and token == self._run_to_end_call_token
            and not self.state.run_to_end_paused
            and isinstance(self._run_to_end_call, CallContext)
        )

    def _run_to_end_call_parent_is_current(self, ctx: CallContext) -> bool:
        return (
            self._get_trigger_set_id() == ctx.trigger_set_id
            and self._find_trigger(ctx.root_key) is not None
        )

    def _abandon_invalid_run_to_end_call(self) -> None:
        self._discard_run_to_end_call()
        self._run_to_end_resume = None
        self._run_to_end_snapshot = None
        self._run_to_end_wait_position = None
        self.stop_run_to_end()

    def _advance_run_to_end_call(self, generation: int, key: str, token: int) -> None:
        if not self._run_to_end_call_is_current(generation, key, token):
            return
        self.state.run_to_end_after_id = None
        ctx = self._run_to_end_call
        if not isinstance(ctx, CallContext) or not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
            return
        step = call_step(ctx, self.state.counters)
        self._append_run_to_end_call_deltas(step.counter_deltas)
        if step.kind == "action":
            self._perform_run_to_end_call_action(generation, key, token, ctx, step)
        elif step.kind == "wait":
            self._schedule_run_to_end_call(generation, key, token, step.wait_ms or 0)
        elif step.kind == "error":
            self._report_run_to_end_call_error(generation, key, token, ctx, step)
        elif step.kind == "done":
            self._complete_run_to_end_call(generation, key, token, ctx)

    def _append_run_to_end_call_deltas(
        self, deltas: tuple[tuple[str, int], ...],
    ) -> None:
        resume = self._run_to_end_resume
        if resume is not None and deltas:
            self._run_to_end_resume = replace(
                resume, counter_deltas=resume.counter_deltas + deltas,
            )

    def _schedule_run_to_end_call(
        self, generation: int, key: str, token: int, delay: int,
    ) -> None:
        self.state.run_to_end_after_id = self._after(
            delay, lambda: self._advance_run_to_end_call(generation, key, token),
        )

    def _perform_run_to_end_call_action(
        self, generation: int, key: str, token: int,
        ctx: CallContext, step: CallStep,
    ) -> None:
        action = step.action or {}
        raw_type = action.get("type")
        action_type = raw_type.strip().lower() if isinstance(raw_type, str) else ""
        if action_type == ACTION_TYPE_FILE_LINE:
            self._begin_run_to_end_call_file_line(generation, key, token, ctx, step)
            return
        succeeded = self._perform_action(action)
        if not self._run_to_end_call_is_current(generation, key, token):
            return
        if not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
            return
        if succeeded is False:
            self._fail_run_to_end_call()
            return
        following = finish_call_action(ctx, self.state.counters)
        self._append_run_to_end_call_deltas(following.counter_deltas)
        self._handle_finished_run_to_end_call(generation, key, token, ctx, following)

    def _begin_run_to_end_call_file_line(
        self, generation: int, key: str, token: int,
        ctx: CallContext, step: CallStep,
    ) -> None:
        if self._begin_file_line is None or self._poll_file_line is None:
            self._report_call_error_message(
                generation, key, token, ctx,
                "file_line の読込の仕組みが未設定です", step,
            )
            return
        handle = self._begin_file_line(step.action or {})
        if not self._run_to_end_call_is_current(generation, key, token):
            return
        if not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
            return
        if handle is None:
            self._fail_run_to_end_call()
            return
        self._run_to_end_call_file_line = handle
        self.state.run_to_end_after_id = self._after(
            FILE_LINE_POLL_INTERVAL_MS,
            lambda: self._poll_run_to_end_call_file_line(generation, key, token, handle),
        )

    def _poll_run_to_end_call_file_line(
        self, generation: int, key: str, token: int, handle: object,
    ) -> None:
        if (not self._run_to_end_call_is_current(generation, key, token)
                or self._run_to_end_call_file_line is not handle):
            return
        self.state.run_to_end_after_id = None
        ctx = self._run_to_end_call
        if not isinstance(ctx, CallContext) or not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
            return
        result = self._poll_file_line(handle)
        if not self._run_to_end_call_is_current(generation, key, token):
            return
        if (self._run_to_end_call_file_line is not handle
                or not isinstance(self._run_to_end_call, CallContext)):
            return
        ctx = self._run_to_end_call
        if not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
            return
        if result is None:
            self.state.run_to_end_after_id = self._after(
                FILE_LINE_POLL_INTERVAL_MS,
                lambda: self._poll_run_to_end_call_file_line(generation, key, token, handle),
            )
            return
        self._run_to_end_call_file_line = None
        if result is False:
            self._fail_run_to_end_call()
            return
        following = finish_call_action(ctx, self.state.counters)
        self._append_run_to_end_call_deltas(following.counter_deltas)
        self._handle_finished_run_to_end_call(generation, key, token, ctx, following)

    def _handle_finished_run_to_end_call(
        self, generation: int, key: str, token: int,
        ctx: CallContext, step: CallStep,
    ) -> None:
        if step.kind == "next":
            self._schedule_run_to_end_call(
                generation, key, token, step.interval_ms or 0,
            )
        elif step.kind == "done":
            self._complete_run_to_end_call(generation, key, token, ctx)
        elif step.kind == "error":
            self._report_run_to_end_call_error(generation, key, token, ctx, step)

    def _report_run_to_end_call_error(
        self, generation: int, key: str, token: int,
        ctx: CallContext, step: CallStep,
    ) -> None:
        self._report_call_error_message(
            generation, key, token, ctx,
            step.message or "呼び出しを実行できません", step,
        )

    def _report_call_error_message(
        self, generation: int, key: str, token: int, ctx: CallContext,
        message: str, step: CallStep,
    ) -> None:
        trigger = self._find_trigger(key)
        actions = trigger.get("actions", []) if trigger else []
        index = self._run_to_end_wait_position
        action = actions[index] if index is not None and index < len(actions) else {}
        suffix = f" / {chain_text(step.chain)}" if step.chain else ""
        self._report_error(action, message + suffix)
        if not self._run_to_end_call_is_current(generation, key, token):
            return
        if not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
            return
        self._fail_run_to_end_call()

    def _fail_run_to_end_call(self) -> None:
        snapshot = self._run_to_end_snapshot
        resume = self._run_to_end_resume
        self._discard_run_to_end_call()
        self._run_to_end_wait_position = None
        self._run_to_end_resume = None
        if snapshot is not None and resume is not None:
            commit_step(self.state, snapshot, resume.counter_deltas)
        self.stop_run_to_end()

    def _complete_run_to_end_call(
        self, generation: int, key: str, token: int, ctx: CallContext,
    ) -> None:
        if not self._run_to_end_call_is_current(generation, key, token):
            return
        if not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
            return
        snapshot = self._run_to_end_snapshot
        resume = self._run_to_end_resume
        index = self._run_to_end_wait_position
        trigger = self._find_trigger(key)
        if snapshot is None or resume is None or index is None or trigger is None:
            self._abandon_invalid_run_to_end_call()
            return
        actions = trigger.get("actions", [])
        self._discard_run_to_end_call()
        self._run_to_end_sent = True
        self._run_to_end_resume = None
        self._run_to_end_wait_position = None
        deltas, position, stopped = self._finish_run_to_end_normal_action(
            key, actions, index, resume,
        )
        commit_step(self.state, snapshot, deltas)
        self._run_to_end_snapshot = None
        self._select_trigger(key)
        if position == 0 or stopped:
            self.stop_run_to_end()
        else:
            delay = coerce_nonnegative_int(
                trigger.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
                DEFAULT_RUN_TO_END_DELAY_MS,
            )
            self._schedule_run_to_end_step(key, delay)
