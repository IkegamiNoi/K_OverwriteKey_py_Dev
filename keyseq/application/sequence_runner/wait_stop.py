"""Finish ordinary waits when their pending execution is stopped."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from keyseq.application.call_context import CallContext, settle_call_wait
from keyseq.application.sequence_history import cancel_pending_steps
from keyseq.application.sequence_steps import after_normal_action, settle_after_normal
from keyseq.domain.sequence_control import ACTION_TYPE_SYSTEM, OP_WAIT, action_type, system_op


class WaitStopMixin:
    def _settle_stopped_wait(self, key, pending) -> bool:
        trigger = self._find_trigger(key)
        if trigger is None:
            return False
        settled = settle_after_normal(
            trigger.get("actions", []), pending.position, self._get_frames(key),
            self.state.counters,
            allow_wrap=pending.position != 0 and not pending.resume.wrapped,
            processed=pending.resume.processed,
            wrapped=pending.resume.wrapped,
            deferred_counters=pending.resume.deferred_counters,
            wait_mode="skip",
        )
        self._save_progress(key, settled.position, settled.frames,
                            settled.deferred_counters)
        pending.resume = replace(
            pending.resume,
            counter_deltas=pending.resume.counter_deltas + settled.counter_deltas,
        )
        return settled.position == 0

    def _cancel_pending_steps(self, identity=None, *, settle_wait=True) -> None:
        settled_waits = []
        if settle_wait:
            for current, pending in tuple(self.state.pending_steps.items()):
                if (identity is not None and current != identity) or current[0] != self._get_trigger_set_id():
                    continue
                if pending.file_line is None and pending.call is None:
                    reached_end = self._settle_stopped_wait(current[1], pending)
                    self._record_single_completion(pending.snapshot, reached_end)
                    settled_waits.append((current, pending))
        for current, pending in settled_waits:
            self.state.pending_steps.pop(current, None)
            if pending.after_id is not None:
                try:
                    self._after_cancel(pending.after_id)
                except Exception:
                    pass
            self._commit_step_and_publish(pending.snapshot, pending.resume.counter_deltas)
        cancel_pending_steps(self.state, self._after_cancel, identity)
        self._publish_call_view()

    def _finish_run_to_end_wait(self) -> bool:
        if self._run_to_end_call is not None:
            return self._finish_linked_run_to_end_wait()
        key = self.state.run_to_end_key
        resume = self._run_to_end_resume
        snapshot = self._run_to_end_snapshot
        if (key is None or resume is None or snapshot is None
                or self._run_to_end_wait_position is None
                or self._run_to_end_file_line is not None):
            return False
        trigger = self._find_trigger(key)
        if trigger is None:
            return False
        actions = trigger.get("actions", [])
        index = self._run_to_end_wait_position
        if not (0 <= index < len(actions)):
            return False
        action = actions[index]
        if (not isinstance(action, Mapping)
                or action_type(action) != ACTION_TYPE_SYSTEM
                or system_op(action) != OP_WAIT):
            return False
        settled = settle_after_normal(
            actions, index + 1,
            self._get_frames(key),
            self.state.counters,
            allow_wrap=False,
            processed=resume.processed,
            stop_ends_run=self._run_to_end_sent,
            deferred_counters=resume.deferred_counters,
            wait_mode="skip",
        )
        deltas = resume.counter_deltas + settled.counter_deltas
        position = settled.position
        deferred = settled.deferred_counters
        if (position == 0 or settled.stopped) and deferred:
            deltas += self._apply_deferred_counters_and_publish(deferred)
            deferred = ()
        if settled.stopped:
            deltas, position = self._settle_after_stopped_sequence(
                key, actions, position, settled.frames, settled.processed, deltas,
            )
        else:
            self._save_progress(key, position, settled.frames, deferred)
        self._record_single_completion(snapshot, position == 0)
        self._commit_step_and_publish(snapshot, deltas)
        self._run_to_end_resume = None
        self._run_to_end_snapshot = None
        self._run_to_end_wait_position = None
        return settled.stopped or position == 0

    def _finish_linked_run_to_end_wait(self) -> bool:
        ctx = self._run_to_end_call
        if ctx.performing:
            return False
        step = settle_call_wait(ctx, self.state.counters)
        if step is None and ctx.root_continuation is None:
            return False
        finished = False
        if not ctx.stack:
            trigger = self._find_trigger(ctx.root_key)
            if trigger is None:
                return False
            actions = trigger.get("actions", [])
            if ctx.root_continuation is None:
                position, frames = self._call_root_after_wait(ctx, actions)
            else:
                position, frames = ctx.root_continuation, self._get_frames(ctx.root_key)
            position, stopped, _ = self._settle_run_to_end_call_root(
                ctx, actions, position, frames, True,
            )
            finished = position == 0 or stopped
        self._commit_run_to_end_call(ctx)
        return finished

    def _call_root_after_wait(self, ctx: CallContext, actions: list[dict]):
        return after_normal_action(actions, self._run_to_end_wait_position,
                                   self._get_frames(ctx.root_key))
