"""Finish ordinary waits when their pending execution is stopped."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from keyseq.application.sequence_history import cancel_pending_steps, commit_step
from keyseq.application.sequence_steps import apply_deferred_counters, settle_after_normal
from keyseq.domain.sequence_control import ACTION_TYPE_SYSTEM, OP_WAIT, action_type, system_op


class WaitStopMixin:
    def _settle_stopped_wait(self, key, pending) -> None:
        trigger = self._find_trigger(key)
        if trigger is None:
            return
        settled = settle_after_normal(
            trigger.get("actions", []), pending.position, self._get_frames(key),
            self.state.counters,
            allow_wrap=pending.position != 0 and not pending.resume.wrapped,
            processed=pending.resume.processed,
        )
        self._save_progress(key, settled.position, settled.frames,
                            settled.deferred_counters)
        pending.resume = replace(
            pending.resume,
            counter_deltas=pending.resume.counter_deltas + settled.counter_deltas,
        )

    def _cancel_pending_steps(self, identity=None, *, settle_wait=True) -> None:
        if settle_wait:
            for current, pending in tuple(self.state.pending_steps.items()):
                if (identity is not None and current != identity) or current[0] != self._get_trigger_set_id():
                    continue
                if pending.file_line is None and pending.call is None:
                    self._settle_stopped_wait(current[1], pending)
        cancel_pending_steps(self.state, self._after_cancel, identity)

    def _finish_run_to_end_wait(self) -> bool:
        key = self.state.run_to_end_key
        resume = self._run_to_end_resume
        snapshot = self._run_to_end_snapshot
        if (key is None or resume is None or snapshot is None
                or self._run_to_end_wait_position is None
                or self._run_to_end_call is not None
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
        )
        deltas = resume.counter_deltas + settled.counter_deltas
        position = settled.position
        deferred = settled.deferred_counters
        if (position == 0 or settled.stopped) and deferred:
            deltas += apply_deferred_counters(deferred, self.state.counters)
            deferred = ()
        if settled.stopped:
            deltas, position = self._settle_after_stopped_sequence(
                key, actions, position, settled.frames, resume.processed, deltas,
            )
        else:
            self._save_progress(key, position, settled.frames, deferred)
        commit_step(self.state, snapshot, deltas)
        self._run_to_end_resume = None
        self._run_to_end_snapshot = None
        self._run_to_end_wait_position = None
        return settled.stopped or position == 0
