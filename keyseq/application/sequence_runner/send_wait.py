"""Schedule and settle waits after sending sequence actions."""

from __future__ import annotations

from typing import Any

from keyseq.application.app_state import PendingStep
from keyseq.application.sequence_history import StepSnapshot, commit_step
from keyseq.application.sequence_steps import (
    LoopFrame,
    SettleOutcome,
    StepOutcome,
    StepResume,
    after_normal_action,
    apply_deferred_counters,
    continue_resume,
    settle_after_normal,
)


class SendWaitMixin:
    def _queue_single_wait(self, key: str, settled: SettleOutcome,
                           resume: StepResume, snapshot: StepSnapshot) -> None:
        trigger_set_id = self._get_trigger_set_id()
        identity = (trigger_set_id, key)
        continuation = continue_resume(resume, settled)
        with self.state.lock:
            self.state.pending_step_generation += 1
            generation = self.state.pending_step_generation
            pending = PendingStep(generation, None, settled.position + 1, continuation, snapshot)
            self.state.pending_steps[identity] = pending
        pending.after_id = self._after(
            settled.wait_ms,
            lambda: self._resume_single_wait(trigger_set_id, key, generation),
        )

    def _resume_single_wait(self, trigger_set_id: str, key: str, generation: int) -> None:
        identity = (trigger_set_id, key)
        with self.state.lock:
            pending = self.state.pending_steps.get(identity)
            if pending is None or pending.generation != generation:
                return
        trigger = self._find_trigger(key) if self._get_trigger_set_id() == trigger_set_id else None
        if trigger is None:
            with self.state.lock:
                if self.state.pending_steps.get(identity) is pending:
                    self.state.pending_steps.pop(identity)
            return
        settled = settle_after_normal(
            trigger.get("actions", []), pending.position, self._get_frames(key),
            self.state.counters, allow_wrap=not pending.resume.wrapped,
            processed=pending.resume.processed, wrapped=pending.resume.wrapped,
            deferred_counters=pending.resume.deferred_counters, wait_mode="wait",
        )
        self._save_progress(key, settled.position, settled.frames,
                            settled.deferred_counters)
        with self.state.lock:
            if self.state.pending_steps.get(identity) is pending:
                self.state.pending_steps.pop(identity)
        if settled.wait_ms is not None:
            self._queue_single_wait(key, settled, pending.resume, pending.snapshot)
        else:
            commit_step(self.state, pending.snapshot,
                        pending.resume.counter_deltas + settled.counter_deltas)
        self._select_trigger(key)

    def _finish_single_normal_action(
        self, key: str, actions: list[dict[str, Any]], index: int,
        outcome: StepOutcome | StepResume, snapshot: StepSnapshot,
    ) -> tuple[tuple[str, int], ...] | None:
        position, frames = after_normal_action(actions, index, self._get_frames(key))
        deferred = ()
        if not (position == 0 and outcome.wrapped):
            settled = settle_after_normal(
                actions, position, frames, self.state.counters,
                allow_wrap=position != 0 and not outcome.wrapped,
                processed=outcome.processed, wait_mode="wait",
                wrapped=position == 0 or outcome.wrapped,
            )
            position, frames = settled.position, settled.frames
            deltas = outcome.counter_deltas + settled.counter_deltas
            deferred = settled.deferred_counters
            if settled.wait_ms is not None:
                self._save_progress(key, position, frames, deferred)
                self._queue_single_wait(
                    key, settled, StepResume(
                        index, outcome.wrapped, outcome.processed,
                        outcome.counter_deltas,
                    ), snapshot,
                )
                return None
        else:
            deltas = outcome.counter_deltas
        self._save_progress(key, position, frames, deferred)
        return deltas

    def _queue_run_to_end_wait(
        self, key: str, settled: SettleOutcome,
        outcome: StepOutcome | StepResume, snapshot: StepSnapshot,
    ) -> None:
        self._run_to_end_resume = StepResume(
            settled.position, settled.wrapped, settled.processed,
            outcome.counter_deltas + settled.counter_deltas, settled.deferred_counters,
        )
        self._run_to_end_snapshot = snapshot
        self._run_to_end_wait_position = settled.position
        self._save_progress(key, settled.position, settled.frames,
                            settled.deferred_counters)
        self._schedule_run_to_end_step(key, settled.wait_ms)

    def _continue_run_to_end_wait(self, key: str, actions: list[dict[str, Any]]) -> None:
        resume = self._run_to_end_resume
        snapshot = self._run_to_end_snapshot
        index = self._run_to_end_wait_position
        if resume is None or snapshot is None or index is None:
            return
        settled = settle_after_normal(
            actions, index + 1, self._get_frames(key), self.state.counters,
            allow_wrap=False, processed=resume.processed, stop_ends_run=True,
            deferred_counters=resume.deferred_counters, wait_mode="wait",
        )
        if settled.wait_ms is not None:
            self._queue_run_to_end_wait(key, settled, resume, snapshot)
            self._select_trigger(key)
            return
        deltas = resume.counter_deltas + settled.counter_deltas
        position, stopped = settled.position, settled.stopped
        deferred = settled.deferred_counters
        if (position == 0 or stopped) and deferred:
            deltas += apply_deferred_counters(deferred, self.state.counters)
            deferred = ()
        if stopped:
            deltas, position = self._settle_after_stopped_sequence(
                key, actions, position, settled.frames, settled.processed, deltas,
            )
        else:
            self._save_progress(key, position, settled.frames, deferred)
        self._run_to_end_resume = None
        self._run_to_end_wait_position = None
        self._run_to_end_snapshot = None
        commit_step(self.state, snapshot, deltas)
        self._select_trigger(key)
        if position == 0 or stopped:
            self.stop_run_to_end()
        else:
            self._schedule_run_to_end_step(key, 0)

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
            wait_mode="skip",
        )
        position, frames = settled.position, settled.frames
        deltas += settled.counter_deltas
        deferred = settled.deferred_counters
        if position == 0 and deferred:
            deltas += apply_deferred_counters(deferred, self.state.counters)
            deferred = ()
        self._save_progress(key, position, frames, deferred)
        return deltas, position
