"""Trigger acceptance, paused calls, and confirmed discard."""

from __future__ import annotations

from keyseq.application.call_context import CallContext, top_interval


class InputAcceptanceMixin:
    def _active_key(self) -> str | None:
        if self.state.run_to_end_key is not None and not self.state.run_to_end_paused:
            return self.state.run_to_end_key
        for (trigger_set_id, key), pending in tuple(self.state.pending_steps.items()):
            if (trigger_set_id == self._get_trigger_set_id()
                    and (pending.file_line is not None
                         or (pending.call is not None and not pending.call_paused))):
                return key
        return None

    def paused_keys(self) -> tuple[str, ...]:
        keys = []
        if self.state.run_to_end_key is not None and self.state.run_to_end_paused:
            keys.append(self.state.run_to_end_key)
        keys.extend(
            key for (trigger_set_id, key), pending in tuple(self.state.pending_steps.items())
            if trigger_set_id == self._get_trigger_set_id()
            and pending.call is not None and pending.call_paused
        )
        return tuple(dict.fromkeys(keys))

    def _acceptance_snapshot(self, target: str | None = None) -> tuple:
        pending = tuple(sorted(
            (identity, step.generation, step.call_paused)
            for identity, step in self.state.pending_steps.items()
        ))
        paused = tuple(sorted(
            (key, self._run_to_end_generation) for key in self.paused_keys()
            if key == self.state.run_to_end_key
        ))
        return (paused, self.state.run_to_end_key, self.state.run_to_end_paused,
                self._active_key(), pending, target, self.state.last_trigger,
                self._get_trigger_set_id())

    def confirm_and_discard(self, keys: tuple[str, ...] | None = None) -> bool:
        """Confirm and stop the selected paused executions; all when omitted."""
        if self.confirmation_active:
            return False
        paused = self.paused_keys()
        selected = paused if keys is None else tuple(key for key in paused if key in keys)
        if not selected:
            return True
        before = self._acceptance_snapshot(keys[0] if keys else None)
        self.confirmation_active = True
        try:
            accepted = self._confirm_discard(selected) if self._confirm_discard else True
        finally:
            self.confirmation_active = False
        if not accepted or before != self._acceptance_snapshot(keys[0] if keys else None):
            return False
        for key in selected:
            if key == self.state.run_to_end_key and self.state.run_to_end_paused:
                self.stop_run_to_end()
            identity = (self._get_trigger_set_id(), key)
            pending = self.state.pending_steps.get(identity)
            if pending is not None and pending.call is not None and pending.call_paused:
                self.cancel_pending_wait(key)
        return True

    def _pause_single_call(self, key: str) -> None:
        with self.state.lock:
            pending = self.state.pending_steps[(self._get_trigger_set_id(), key)]
            pending.call_paused = True
            self.state.pending_step_generation += 1
            pending.generation = self.state.pending_step_generation
            after_id = pending.after_id
            pending.after_id = None
            pending.call_file_line = None
        if after_id is not None:
            try:
                self._after_cancel(after_id)
            except Exception:
                pass
        self._update_status()

    def _resume_single_call(self, key: str) -> None:
        trigger_set_id = self._get_trigger_set_id()
        with self.state.lock:
            pending = self.state.pending_steps[(trigger_set_id, key)]
            pending.call_paused = False
        delay = top_interval(pending.call) if isinstance(pending.call, CallContext) else 0
        self._schedule_single_call(trigger_set_id, key, pending.generation, pending, delay)
        self._update_status()

    def _prepare_control_target(self, identity: tuple[str, str]) -> bool:
        trigger_set_id, key = identity
        if key == self.state.run_to_end_key and not self.state.run_to_end_paused:
            return False
        pending = self.state.pending_steps.get(identity)
        if pending is not None and pending.call is not None and pending.call_paused:
            return self.confirm_and_discard((key,))
        if key == self.state.run_to_end_key and self.state.run_to_end_paused:
            return self.confirm_and_discard((key,))
        return True

    def _accept_key(self, key: str) -> None:
        if self.confirmation_active:
            return
        active = self._active_key()
        if active is not None:
            if key == active:
                if key == self.state.run_to_end_key:
                    self.pause_run_to_end()
                    self._update_status()
                else:
                    pending = self.state.pending_steps.get((self._get_trigger_set_id(), key))
                    if pending is not None and pending.call is not None:
                        self._pause_single_call(key)
            return
        if key == self.state.run_to_end_key and self.state.run_to_end_paused:
            self.resume_run_to_end()
            self._update_status()
            return
        pending = self.state.pending_steps.get((self._get_trigger_set_id(), key))
        if pending is not None:
            if pending.call is not None and pending.call_paused:
                self._resume_single_call(key)
            return
        trigger = self._find_trigger(key)
        if not trigger or not trigger.get("actions", []):
            return
        if bool(trigger.get("run_to_end", False)):
            if self.confirm_and_discard():
                self._start_run_to_end(key)
            return
        self._run_single_action(key, trigger.get("actions", []))
