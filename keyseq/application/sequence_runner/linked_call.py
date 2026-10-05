"""Shared linked-call writeback, completion propagation, and press history."""

from __future__ import annotations

from keyseq.application.app_state import PendingStep
from keyseq.application.call_context import CallContext
from keyseq.application.call_chain import chain_from
from keyseq.application.sequence_history import StepSnapshot, commit_press, snapshot_for
from keyseq.application.sequence_steps import after_normal_action, settle_after_normal, apply_deferred_counters
from keyseq.domain.call_graph import call_target


class LinkedCallMixin:
    def _linked_ancestors(self, key: str) -> tuple[tuple[str, ...], int]:
        """Include marked callers above the pressed trigger in call validation."""
        refs = self.state.call_refs_for(self._get_trigger_set_id())
        paths = []
        for caller in self._ordered_callers():
            if caller not in refs or caller == key:
                continue
            chain = chain_from(self.state, self._get_trigger_set_id(), caller, self._find_trigger)
            if key in chain:
                paths.append(chain[:chain.index(key)])
        return tuple(dict.fromkeys(member for path in paths for member in path)), max(
            (len(path) for path in paths), default=0,
        )

    def _ordered_callers(self) -> tuple[str, ...]:
        if self._list_trigger_keys is not None:
            return tuple(self._list_trigger_keys())
        return tuple(sorted(self.state.call_refs_for(self._get_trigger_set_id())))

    def _write_linked_progress(self, ctx: CallContext, *, failed: bool = False) -> None:
        """Publish frame positions and marks as the triggers' own runtime state."""
        with self.state.lock:
            refs = self.state.call_refs_for(ctx.trigger_set_id)
            for frame in ctx.changed_frames.values():
                self.state.indices_for(ctx.trigger_set_id)[frame.key] = frame.position
                self.state.loop_frames_for(ctx.trigger_set_id)[frame.key] = list(frame.frames)
                deferred = frame.resume.deferred_counters if frame.resume is not None else frame.deferred
                self.state.deferred_counters_for(ctx.trigger_set_id)[frame.key] = list(deferred)
                refs.discard(frame.key)
            refs.discard(ctx.root_key)
            if not failed and ctx.stack:
                refs.add(ctx.root_key)
                refs.update(frame.key for frame in ctx.stack[:-1])

    def _propagate_linked_completion(
        self, completed: list[str], before: dict[str, StepSnapshot],
        deltas_by_key: dict[str, list[tuple[str, int]]], excluded: set[str],
    ) -> None:
        trigger_set_id = self._get_trigger_set_id()
        refs = self.state.call_refs_for(trigger_set_id)
        def finish_callers(target: str) -> None:
            for caller in self._ordered_callers():
                if caller in excluded or caller not in refs:
                    continue
                trigger = self._find_trigger(caller)
                actions = trigger.get("actions", []) if trigger else []
                index = self._get_index(caller)
                if not (0 <= index < len(actions)) or call_target(actions[index]) != target:
                    continue
                before.setdefault(caller, snapshot_for(self.state, trigger_set_id, caller))
                refs.discard(caller)
                position, frames = after_normal_action(actions, index, self._get_frames(caller))
                paused = caller == self.state.run_to_end_key and self.state.run_to_end_paused
                deferred = self.state.deferred_counters_for(trigger_set_id).get(caller, ())
                if index + 1 < len(actions):
                    settled = settle_after_normal(
                        actions, position, frames, self.state.counters, allow_wrap=False,
                        in_call=True, deferred_counters=deferred,
                        wait_mode="skip" if paused else "stop",
                    )
                    position, frames, deferred = settled.position, settled.frames, settled.deferred_counters
                    deltas_by_key.setdefault(caller, []).extend(settled.counter_deltas)
                if position == 0:
                    deltas_by_key.setdefault(caller, []).extend(
                        apply_deferred_counters(deferred, self.state.counters))
                    deferred = ()
                self._save_progress(caller, position, frames, deferred)
                if paused:
                    self._discard_run_to_end_call()
                    self._run_to_end_resume = None
                    self._run_to_end_snapshot = None
                    self._run_to_end_wait_position = None
                    if position == 0:
                        self.stop_run_to_end()
                if position == 0:
                    finish_callers(caller)
        for target in completed:
            finish_callers(target)

    def _commit_linked_call(self, pending: PendingStep, *, failed: bool = False) -> None:
        self._commit_linked_context(pending.call, failed=failed)

    def _commit_linked_context(self, ctx: CallContext, *, failed: bool = False) -> None:
        self._write_linked_progress(ctx, failed=failed or ctx.failed)
        self._propagate_linked_completion(
            ctx.completed, ctx.before, ctx.deltas_by_key,
            {ctx.root_key, *ctx.changed_frames},
        )
        commit_press(self.state, list(ctx.before.values()), ctx.deltas_by_key, pressed_key=ctx.root_key)
        self.state.last_trigger = (ctx.trigger_set_id, ctx.root_key)
        ctx.completed.clear()
        ctx.deltas_by_key.clear()
        ctx.before = {key: snapshot_for(self.state, ctx.trigger_set_id, key)
                      for key in ctx.before}
        self._refresh_actions()
        self._update_status()
