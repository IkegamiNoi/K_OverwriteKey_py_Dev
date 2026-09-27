from __future__ import annotations

from typing import Any

from keyseq.application.app_state import PendingStep
from keyseq.application.sequence_history import StepSnapshot, commit_step
from keyseq.application.sequence_steps import StepOutcome, resume_for_pending
from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS, coerce_nonnegative_int

FILE_LINE_POLL_INTERVAL_MS = 50


class FileLineWaitMixin:
    # Uses runner attributes: state, _begin_file_line, _poll_file_line,
    # _run_to_end_resume, _run_to_end_snapshot, _run_to_end_wait_position,
    # _run_to_end_generation, _run_to_end_file_line,
    # _run_to_end_file_line_trigger_set_id, _run_to_end_file_line_token,
    # _get_trigger_set_id, _find_trigger, _get_index, _after, _save_progress,
    # _finish_single_normal_action, _finish_run_to_end_normal_action,
    # _schedule_run_to_end_step, _select_trigger, _report_error,
    # stop_run_to_end.
    def _queue_single_file_line(
        self, key: str, outcome: StepOutcome, snapshot: StepSnapshot,
        handle: object, initial_position: int,
    ) -> None:
        trigger_set_id = self._get_trigger_set_id()
        identity = (trigger_set_id, key)
        resume = resume_for_pending(outcome, initial_position)
        with self.state.lock:
            self.state.pending_step_generation += 1
            generation = self.state.pending_step_generation
            pending = PendingStep(
                generation, None, outcome.normal_index, resume, snapshot, file_line=handle,
            )
            self.state.pending_steps[identity] = pending
        pending.after_id = self._after(
            FILE_LINE_POLL_INTERVAL_MS,
            lambda: self._poll_single_file_line(trigger_set_id, key, generation),
        )

    def _poll_single_file_line(
        self, trigger_set_id: str, key: str, generation: int,
    ) -> None:
        identity = (trigger_set_id, key)
        with self.state.lock:
            pending = self.state.pending_steps.get(identity)
            if pending is None or pending.generation != generation or pending.file_line is None:
                return
        trigger = self._find_trigger(key) if self._get_trigger_set_id() == trigger_set_id else None
        if trigger is None:
            with self.state.lock:
                if self.state.pending_steps.get(identity) is pending:
                    self.state.pending_steps.pop(identity)
            return
        result = self._poll_file_line(pending.file_line)
        if result is None:
            pending.after_id = self._after(
                FILE_LINE_POLL_INTERVAL_MS,
                lambda: self._poll_single_file_line(trigger_set_id, key, generation),
            )
            return
        with self.state.lock:
            current = self.state.pending_steps.get(identity)
            if current is not pending or current.generation != generation:
                return
            self.state.pending_steps.pop(identity)
        if result:
            actions = trigger.get("actions", [])
            deltas = self._finish_single_normal_action(
                key, actions, pending.position, pending.resume,
            )
            commit_step(self.state, pending.snapshot, deltas)
        else:
            commit_step(self.state, pending.snapshot, pending.resume.counter_deltas)
        self._select_trigger(key)

    def _discard_run_to_end_file_line(self) -> None:
        self._run_to_end_file_line = None
        self._run_to_end_file_line_trigger_set_id = None
        self._run_to_end_file_line_token += 1

    def _begin_run_to_end_file_line(
        self, key: str, action: dict[str, Any], index: int,
        outcome: StepOutcome, snapshot: StepSnapshot, initial_position: int,
    ) -> bool:
        if self._begin_file_line is None or self._poll_file_line is None:
            self._report_error(action, "file_line の読込の仕組みが未設定です")
            return False
        handle = self._begin_file_line(action)
        if handle is None:
            return False
        self._run_to_end_resume = resume_for_pending(outcome, initial_position)
        self._run_to_end_snapshot = snapshot
        self._run_to_end_wait_position = index
        self._save_progress(key, index, outcome.frames)
        self._run_to_end_file_line = handle
        self._run_to_end_file_line_trigger_set_id = self._get_trigger_set_id()
        self._run_to_end_file_line_token += 1
        token = self._run_to_end_file_line_token
        generation = self._run_to_end_generation
        self.state.run_to_end_after_id = self._after(
            FILE_LINE_POLL_INTERVAL_MS,
            lambda: self._poll_run_to_end_file_line(generation, key, token),
        )
        return True

    def _poll_run_to_end_file_line(self, generation: int, key: str, token: int) -> None:
        handle = self._run_to_end_file_line
        if (generation != self._run_to_end_generation
                or key != self.state.run_to_end_key
                or token != self._run_to_end_file_line_token
                or self.state.run_to_end_paused
                or handle is None):
            return
        self.state.run_to_end_after_id = None
        trigger = self._find_trigger(key)
        if (trigger is None
                or self._get_trigger_set_id() != self._run_to_end_file_line_trigger_set_id):
            self._discard_run_to_end_file_line()
            self._run_to_end_resume = None
            self._run_to_end_snapshot = None
            self._run_to_end_wait_position = None
            self.stop_run_to_end()
            return
        result = self._poll_file_line(handle)
        if result is None:
            self.state.run_to_end_after_id = self._after(
                FILE_LINE_POLL_INTERVAL_MS,
                lambda: self._poll_run_to_end_file_line(generation, key, token),
            )
            return

        if (generation != self._run_to_end_generation
                or key != self.state.run_to_end_key
                or token != self._run_to_end_file_line_token
                or self.state.run_to_end_paused
                or self._run_to_end_file_line is not handle):
            return

        self._discard_run_to_end_file_line()
        resume = self._run_to_end_resume
        snapshot = self._run_to_end_snapshot
        self._run_to_end_resume = None
        self._run_to_end_wait_position = None
        if resume is None or snapshot is None:
            self._run_to_end_snapshot = None
            self.stop_run_to_end()
            return
        delay = coerce_nonnegative_int(
            (self._find_trigger(key) or {}).get(
                "run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS,
            ),
            DEFAULT_RUN_TO_END_DELAY_MS,
        )
        stop = not result
        if result:
            trigger = self._find_trigger(key)
            actions = trigger.get("actions", []) if trigger is not None else []
            index = self._get_index(key)
            deltas, position = self._finish_run_to_end_normal_action(
                key, actions, index, resume,
            )
            stop = position == 0
        else:
            deltas = resume.counter_deltas
        commit_step(self.state, snapshot, deltas)
        self._run_to_end_snapshot = None
        self._select_trigger(key)
        if stop:
            self.stop_run_to_end()
        else:
            self._schedule_run_to_end_step(key, delay)
