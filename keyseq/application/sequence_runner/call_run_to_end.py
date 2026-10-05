from __future__ import annotations

from typing import Any

from keyseq.application.call_context import (
    CallContext,
    CallStep,
    call_step,
    chain_text,
    finish_call_action,
    top_interval,
    start_linked_call,
)
from keyseq.application.sequence_history import StepSnapshot
from keyseq.application.sequence_steps import (
    LoopFrame, StepOutcome, after_normal_action, settle_after_normal,
    apply_deferred_counters,
)
from keyseq.application.sequence_runner.file_line_wait import (
    FILE_LINE_POLL_INTERVAL_MS,
    FILE_LINE_UNAVAILABLE_MESSAGE,
)
from keyseq.domain.call_graph import call_target
from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS, coerce_nonnegative_int
from keyseq.domain.sequence_control import ACTION_TYPE_FILE_LINE, OP_CALL, is_step_call, system_op


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
        outcome: StepOutcome, snapshot: StepSnapshot,
    ) -> None:
        ancestors, depth = self._linked_ancestors(key)
        ctx = start_linked_call(
            self._get_trigger_set_id(), key, call_target(actions[index]), self._find_trigger,
            self.state, step=is_step_call(actions[index]),
            ancestors=ancestors, ancestor_depth=depth,
        )
        ctx.before[key] = snapshot
        ctx.press_processed = outcome.processed
        ctx.record_deltas(key, outcome.counter_deltas)
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
        self._publish_call_view()

    def _run_to_end_call_is_current(self, generation: int, key: str, token: int) -> bool:
        return (
            self._run_to_end_call_matches(generation, key, token)
            and not self.state.run_to_end_paused
        )

    def _run_to_end_call_matches(
        self, generation: int, key: str, token: int,
        ctx: CallContext | None = None,
    ) -> bool:
        return (
            generation == self._run_to_end_generation
            and key == self.state.run_to_end_key
            and token == self._run_to_end_call_token
            and (self._run_to_end_call is ctx if ctx is not None
                 else isinstance(self._run_to_end_call, CallContext))
        )

    def _run_to_end_call_failure_matches(
        self, generation: int, key: str, token: int, ctx: CallContext,
    ) -> bool:
        """Allow a pause token change only while confirming a reported failure."""
        return (
            generation == self._run_to_end_generation
            and key == self.state.run_to_end_key
            and token in (self._run_to_end_call_token,
                          self._run_to_end_call_token - 1)
            and self._run_to_end_call is ctx
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
        if ctx.root_continuation is not None:
            self._complete_run_to_end_call(generation, key, token, ctx)
            return
        sent_before_step = self._run_to_end_sent
        step = self._call_step_discarding_paused(lambda: call_step(
            ctx, self.state.counters, run_to_end=True,
            sent=lambda: self._run_to_end_sent,
            on_call_success=self._mark_run_to_end_sent,
        ))
        if step.kind == "ignored":
            if ctx.sent_action:
                # Keep progress through actions already sent in this call context.
                self._commit_run_to_end_call(ctx)
                self.state.run_to_end_paused = True
            else:
                self._rollback_linked_press(ctx)
                self._discard_run_to_end_call()
                self._run_to_end_resume = None
                self._run_to_end_snapshot = None
                self._run_to_end_wait_position = None
                if sent_before_step:
                    self.state.run_to_end_paused = True
                else:
                    self.state.run_to_end_key = None
                    self.state.run_to_end_paused = False
                    self.state.run_to_end_after_id = None
                    self._run_to_end_sent = False
                    self._run_to_end_generation += 1
            self._update_status()
            return
        self._publish_run_to_end_call_progress()
        if step.kind == "action":
            self._perform_run_to_end_call_action(generation, key, token, ctx, step)
        elif step.kind == "wait":
            self._schedule_run_to_end_call(generation, key, token, step.wait_ms or 0)
        elif step.kind == "next":
            self._handle_finished_run_to_end_call(generation, key, token, ctx, step)
        elif step.kind == "error":
            self._report_run_to_end_call_error(generation, key, token, ctx, step)
        elif step.kind == "done":
            self._complete_run_to_end_call(generation, key, token, ctx)
        elif step.kind == "stopped":
            self._handle_stopped_run_to_end_call(generation, key, token, ctx, step)

    def _publish_run_to_end_call_progress(self) -> None:
        if self._run_to_end_call is not None:
            self._write_linked_progress(self._run_to_end_call)
        self._publish_call_view()

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
        ctx.performing = True
        try:
            succeeded = self._perform_action(action)
        finally:
            ctx.performing = False
        if succeeded is False:
            if not self._run_to_end_call_failure_matches(generation, key, token, ctx):
                return
            if not self._run_to_end_call_parent_is_current(ctx):
                self._abandon_invalid_run_to_end_call()
                return
            self._fail_run_to_end_call()
            return
        if (self.state.run_to_end_paused
                and self._run_to_end_call_failure_matches(generation, key, token, ctx)):
            ctx.sent_action = True
            self._finish_paused_run_to_end_action(ctx)
            return
        if not self._run_to_end_call_is_current(generation, key, token):
            return
        if not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
            return
        ctx.sent_action = True
        self._run_to_end_sent = True
        following = finish_call_action(ctx, self.state.counters, run_to_end=True,
                                       sent=lambda: self._run_to_end_sent)
        self._publish_run_to_end_call_progress()
        self._handle_finished_run_to_end_call(generation, key, token, ctx, following)

    def _begin_run_to_end_call_file_line(
        self, generation: int, key: str, token: int,
        ctx: CallContext, step: CallStep,
    ) -> None:
        if self._file_line_unavailable():
            self._report_call_error_message(
                generation, key, token, ctx,
                FILE_LINE_UNAVAILABLE_MESSAGE, step,
            )
            return
        handle = self._begin_file_line(step.action or {})
        if handle is None:
            if not self._run_to_end_call_failure_matches(generation, key, token, ctx):
                return
            if not self._run_to_end_call_parent_is_current(ctx):
                self._abandon_invalid_run_to_end_call()
                return
            self._fail_run_to_end_call()
            return
        if not self._run_to_end_call_is_current(generation, key, token):
            return
        if not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
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
        ctx.performing = True
        try:
            result = self._poll_file_line(handle)
        finally:
            ctx.performing = False
        if result is False:
            same_file_line = self._run_to_end_call_file_line is handle or (
                self._run_to_end_call_file_line is None
            )
            if (not self._run_to_end_call_failure_matches(generation, key, token, ctx)
                    or not same_file_line
                    or not isinstance(self._run_to_end_call, CallContext)):
                return
            ctx = self._run_to_end_call
            if not self._run_to_end_call_parent_is_current(ctx):
                self._abandon_invalid_run_to_end_call()
                return
            self._run_to_end_call_file_line = None
            self._fail_run_to_end_call()
            return
        if (self.state.run_to_end_paused
                and self._run_to_end_call_failure_matches(generation, key, token, ctx)):
            if not self._run_to_end_call_parent_is_current(ctx):
                self._abandon_invalid_run_to_end_call()
            elif result is None:
                self._commit_run_to_end_call(ctx)
            else:
                ctx.sent_action = True
                self._finish_paused_run_to_end_action(ctx)
            return
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
        ctx.sent_action = True
        self._run_to_end_sent = True
        following = finish_call_action(ctx, self.state.counters, run_to_end=True,
                                       sent=lambda: self._run_to_end_sent)
        self._publish_run_to_end_call_progress()
        self._handle_finished_run_to_end_call(generation, key, token, ctx, following)

    def _handle_finished_run_to_end_call(
        self, generation: int, key: str, token: int,
        ctx: CallContext, step: CallStep,
    ) -> None:
        if step.kind == "next":
            self._commit_run_to_end_call(ctx)
            self._schedule_run_to_end_call(
                generation, key, token, step.interval_ms or 0,
            )
        elif step.kind == "done":
            self._complete_run_to_end_call(generation, key, token, ctx)
        elif step.kind == "error":
            self._report_run_to_end_call_error(generation, key, token, ctx, step)
        elif step.kind == "stopped":
            self._handle_stopped_run_to_end_call(generation, key, token, ctx, step)

    def _handle_stopped_run_to_end_call(
        self, generation: int, key: str, token: int,
        ctx: CallContext, step: CallStep,
    ) -> None:
        if step.call_done:
            self._complete_run_to_end_call(generation, key, token, ctx, stopped_call=True)
        else:
            self._commit_run_to_end_call(ctx)
            self.pause_run_to_end()
            self._update_status()

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
        ctx.failed = True
        self._write_linked_progress(ctx, failed=True)
        self._report_error(action, message + suffix)
        if not self._run_to_end_call_failure_matches(generation, key, token, ctx):
            return
        if not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
            return
        self._fail_run_to_end_call()

    def _commit_run_to_end_call(self, ctx: CallContext, *, failed: bool = False) -> None:
        self._commit_linked_context(ctx, failed=failed)
        ctx.press_processed = 0

    def _fail_run_to_end_call(self) -> None:
        ctx = self._run_to_end_call
        if ctx is not None:
            ctx.failed = True
            self._commit_run_to_end_call(ctx, failed=True)
        self._discard_run_to_end_call()
        self._run_to_end_wait_position = None
        self._run_to_end_resume = None
        self._run_to_end_snapshot = None
        self.stop_run_to_end()

    def _complete_run_to_end_call(
        self, generation: int, key: str, token: int, ctx: CallContext,
        *, stopped_call: bool = False,
    ) -> None:
        if not self._run_to_end_call_is_current(generation, key, token):
            return
        if not self._run_to_end_call_parent_is_current(ctx):
            self._abandon_invalid_run_to_end_call()
            return
        trigger = self._find_trigger(key)
        actions = trigger.get("actions", [])
        self._run_to_end_sent = True
        self._write_linked_progress(ctx)
        if ctx.root_continuation is None:
            index = self._run_to_end_wait_position
            position, frames = after_normal_action(actions, index, self._get_frames(key))
        else:
            position, frames = ctx.root_continuation, self._get_frames(key)
        position, stopped, waiting = self._settle_run_to_end_call_root(
            ctx, actions, position, frames, stopped_call,
        )
        if waiting is not None:
            self._schedule_run_to_end_call(generation, key, token, waiting)
            return
        self._commit_run_to_end_call(ctx)
        self._discard_run_to_end_call()
        self._run_to_end_resume = None
        self._run_to_end_snapshot = None
        self._run_to_end_wait_position = None
        self._select_trigger(key)
        if position == 0 or stopped or stopped_call:
            self.stop_run_to_end()
        else:
            delay = coerce_nonnegative_int(
                trigger.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
                DEFAULT_RUN_TO_END_DELAY_MS,
            )
            self._schedule_run_to_end_step(key, delay)

    def _settle_run_to_end_call_root(
        self, ctx: CallContext, actions: list[dict[str, Any]], position: int,
        frames: list[LoopFrame], stopped_call: bool,
    ) -> tuple[int, bool, int | None]:
        deferred = self.state.deferred_counters_for(ctx.trigger_set_id).get(ctx.root_key, ())
        stopped, waiting = False, None
        if position != 0:
            settled = settle_after_normal(
                actions, position, frames, self.state.counters, allow_wrap=False,
                stop_ends_run=not stopped_call, deferred_counters=deferred,
                wait_mode="skip" if stopped_call else "wait",
            )
            position, frames, deferred = settled.position, settled.frames, settled.deferred_counters
            ctx.record_deltas(ctx.root_key, settled.counter_deltas)
            stopped, waiting = settled.stopped, settled.wait_ms
            if stopped:
                ctx.record_deltas(ctx.root_key, apply_deferred_counters(deferred, self.state.counters))
                deltas, position = self._settle_after_stopped_sequence(
                    ctx.root_key, actions, position, frames, settled.processed, (),
                )
                ctx.record_deltas(ctx.root_key, deltas)
                frames = self._get_frames(ctx.root_key)
                deferred = self.state.deferred_counters_for(ctx.trigger_set_id).get(ctx.root_key, ())
        if position == 0:
            ctx.record_deltas(ctx.root_key, apply_deferred_counters(deferred, self.state.counters))
            deferred = ()
            ctx.completed.append(ctx.root_key)
        ctx.root_continuation = position + 1 if waiting is not None else position
        self._save_progress(ctx.root_key, position, frames, deferred)
        return position, stopped, waiting

    def _finish_paused_run_to_end_action(self, ctx: CallContext) -> None:
        ctx.sent_action = True
        self._run_to_end_sent = True
        step = finish_call_action(ctx, self.state.counters, run_to_end=True, sent=True)
        if step.kind == "error":
            self._fail_run_to_end_call()
            return
        if step.kind == "done" or (step.kind == "stopped" and step.call_done):
            trigger = self._find_trigger(ctx.root_key)
            actions = trigger.get("actions", []) if trigger else []
            position, frames = after_normal_action(
                actions, self._run_to_end_wait_position, self._get_frames(ctx.root_key),
            )
            position, _, _ = self._settle_run_to_end_call_root(ctx, actions, position, frames, True)
            self._commit_run_to_end_call(ctx)
            self._discard_run_to_end_call()
            self._run_to_end_resume = None
            self._run_to_end_snapshot = None
            self._run_to_end_wait_position = None
            if position == 0 or step.kind == "stopped":
                self.stop_run_to_end()
        else:
            self._commit_run_to_end_call(ctx)

    def _mark_run_to_end_sent(self) -> None:
        self._run_to_end_sent = True

    def _rebuild_paused_run_to_end_call(self) -> bool:
        ctx = self._run_to_end_call
        if ctx is None:
            return False
        key = ctx.root_key
        delay = top_interval(ctx)
        trigger = self._find_trigger(key)
        actions = trigger.get("actions", []) if trigger else []
        index = self._get_index(key)
        is_call = 0 <= index < len(actions) and system_op(actions[index]) == OP_CALL
        self._discard_run_to_end_call()
        self._run_to_end_resume = None
        self._run_to_end_snapshot = None
        self._run_to_end_wait_position = None
        if not is_call:
            return False
        ancestors, depth = self._linked_ancestors(key)
        self._run_to_end_call = start_linked_call(
            self._get_trigger_set_id(), key, call_target(actions[index]), self._find_trigger,
            self.state, step=is_step_call(actions[index]), ancestors=ancestors, ancestor_depth=depth,
        )
        self._run_to_end_wait_position = index
        self.state.run_to_end_paused = False
        self._schedule_run_to_end_call(self._run_to_end_generation, key,
                                       self._run_to_end_call_token, delay)
        return True
