from __future__ import annotations

from typing import Any, Callable

from keyseq.application.app_state import PendingStep
from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS, coerce_nonnegative_int, normalize_key_name
from keyseq.application.sequence_steps import LoopFrame, StepOutcome, StepResume, advance, after_normal_action, reset_frames


class SequenceRunner:
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
        self._run_to_end_resume: StepResume | None = None

    def _get_index(self, key: str) -> int:
        return int(self.state.indices_for(self._get_trigger_set_id()).get(key, 0) or 0)

    def _set_index(self, key: str, value: int) -> None:
        self.state.indices_for(self._get_trigger_set_id())[key] = int(value)

    def _get_frames(self, key: str) -> list[LoopFrame]:
        return self.state.loop_frames_for(self._get_trigger_set_id()).get(key, [])

    def _save_progress(self, key: str, position: int, frames: list[LoopFrame]) -> None:
        with self.state.lock:
            self._set_index(key, position)
            self.state.loop_frames_for(self._get_trigger_set_id())[key] = list(frames)

    def reset_loop_frames(self, key: str) -> None:
        key = normalize_key_name(key)
        self.cancel_pending_wait(key)
        trigger = self._find_trigger(key)
        actions = trigger.get("actions", []) if trigger else []
        with self.state.lock:
            frames = reset_frames(actions, self._get_index(key))
            self.state.loop_frames_for(self._get_trigger_set_id())[key] = frames

    def cancel_pending_wait(self, key: str) -> None:
        identity = (self._get_trigger_set_id(), normalize_key_name(key))
        with self.state.lock:
            pending = self.state.pending_steps.pop(identity, None)
        if pending is not None and pending.after_id is not None:
            try:
                self._after_cancel(pending.after_id)
            except Exception:
                pass

    def cancel_pending_waits(self) -> None:
        with self.state.lock:
            pending_steps = tuple(self.state.pending_steps.values())
            self.state.pending_steps.clear()
        for pending in pending_steps:
            if pending.after_id is not None:
                try:
                    self._after_cancel(pending.after_id)
                except Exception:
                    pass

    def _queue_single_wait(self, key: str, outcome: StepOutcome) -> None:
        trigger_set_id = self._get_trigger_set_id()
        identity = (trigger_set_id, key)
        with self.state.lock:
            self.state.pending_step_generation += 1
            generation = self.state.pending_step_generation
            pending = PendingStep(generation, None, outcome.resume_position, outcome.resume)
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
                                position=pending.position, resume=pending.resume)

    def _report_error(self, action: dict[str, Any], message: str) -> None:
        if self._notify_error is not None:
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
                           position: int | None = None, resume: StepResume | None = None) -> None:
        with self.state.lock:
            if key in self.state.reentry_guard:
                return
            self.state.reentry_guard.add(key)

        try:
            outcome = advance(actions, self._get_index(key) if position is None else position,
                              self._get_frames(key), self.state.counters,
                              wrap_once=True, resume=resume)
            self._save_progress(key, outcome.position, outcome.frames)
            if outcome.wait_ms is not None:
                self._queue_single_wait(key, outcome)
                return
            if outcome.error:
                index, message = outcome.error
                self._report_error(actions[index], message)
                return
            if outcome.normal_index is None:
                return
            index = outcome.normal_index
            if self._perform_action(actions[index]) is False:
                return
            position, frames = after_normal_action(actions, index, outcome.frames)
            self._save_progress(key, position, frames)
        finally:
            with self.state.lock:
                self.state.reentry_guard.discard(key)
            self._select_trigger(key)

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
        self._run_to_end_resume = None
        self.state.run_to_end_key = key
        self.state.run_to_end_paused = False
        self._select_trigger(key)
        self._run_to_end_step()

    def pause_run_to_end(self) -> None:
        self.state.run_to_end_paused = True
        if self.state.run_to_end_after_id is not None:
            try:
                self._after_cancel(self.state.run_to_end_after_id)
            except Exception:
                pass
            self.state.run_to_end_after_id = None

    def resume_run_to_end(self) -> None:
        self.state.run_to_end_paused = False
        self._run_to_end_step(schedule_only=True)

    def stop_run_to_end(self) -> None:
        if self.state.run_to_end_after_id is not None:
            try:
                self._after_cancel(self.state.run_to_end_after_id)
            except Exception:
                pass
        self.state.run_to_end_after_id = None
        self.state.run_to_end_key = None
        self.state.run_to_end_paused = False
        self._run_to_end_resume = None
        self._update_status()

    def _run_to_end_step(self, schedule_only: bool = False) -> None:
        key = self.state.run_to_end_key
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
            self.state.run_to_end_after_id = self._after(delay, self._run_to_end_step)
            return
        self._perform_run_to_end_step(key, actions, delay)

    def _perform_run_to_end_step(self, key: str, actions: list[dict[str, Any]], delay: int) -> None:
        outcome = advance(actions, self._get_index(key), self._get_frames(key),
                          self.state.counters, wrap_once=False,
                          resume=self._run_to_end_resume)
        self._save_progress(key, outcome.resume_position if outcome.wait_ms is not None
                            else outcome.position, outcome.frames)
        if outcome.wait_ms is not None:
            self._run_to_end_resume = outcome.resume
            self.state.run_to_end_after_id = self._after(outcome.wait_ms, self._run_to_end_step)
        elif outcome.error:
            index, message = outcome.error
            self._report_error(actions[index], message)
            self.stop_run_to_end()
        elif outcome.normal_index is None:
            self.stop_run_to_end()
        else:
            self._run_to_end_resume = None
            index = outcome.normal_index
            if self._perform_action(actions[index]) is False:
                self.stop_run_to_end()
            else:
                position, frames = after_normal_action(actions, index, outcome.frames)
                self._save_progress(key, position, frames)
                if position == 0:
                    self.stop_run_to_end()
                else:
                    self.state.run_to_end_after_id = self._after(delay, self._run_to_end_step)
        self._select_trigger(key)
