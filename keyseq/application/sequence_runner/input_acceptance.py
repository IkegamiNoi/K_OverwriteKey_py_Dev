"""Trigger acceptance, paused calls, and discard notices."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from keyseq.application.call_context import CallContext, start_linked_call, top_interval
from keyseq.application.call_chain import chain_from, chain_top
from keyseq.application.sequence_history import snapshot_for
from keyseq.domain.call_graph import call_target
from keyseq.domain.sequence_control import (
    ACTION_TYPE_SYSTEM, OP_BACK, OP_REWIND, action_type, system_op,
    is_step_call,
)
from keyseq.domain.sequence_editing import standalone_violation


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

    def discard_paused(self, keys: tuple[str, ...] | None = None) -> tuple[str, ...]:
        """Stop selected paused executions and report the discarded keys."""
        paused = self.paused_keys()
        selected = paused if keys is None else tuple(key for key in paused if key in keys)
        if not selected:
            return ()
        for key in selected:
            if key == self.state.run_to_end_key and self.state.run_to_end_paused:
                self.stop_run_to_end()
            identity = (self._get_trigger_set_id(), key)
            pending = self.state.pending_steps.get(identity)
            if pending is not None and pending.call is not None and pending.call_paused:
                self.cancel_pending_wait(key)
        if self._notify_message is not None:
            self._notify_message(f"一時停止中の実行を破棄しました（{', '.join(selected)}）")
        return selected

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
        if isinstance(pending.call, CallContext):
            self._write_linked_progress(pending.call)
            if not pending.call.performing:
                self._commit_linked_call(pending)
            self._call_view_stopped((self._get_trigger_set_id(), key), pending.call)

    def _resume_single_call(self, key: str) -> None:
        trigger_set_id = self._get_trigger_set_id()
        with self.state.lock:
            pending = self.state.pending_steps[(trigger_set_id, key)]
            pending.call_paused = False
        ctx = pending.call
        delay = top_interval(ctx) if isinstance(ctx, CallContext) and not ctx.top_is_step() else 0
        if isinstance(ctx, CallContext):
            if ctx.root_continuation is None:
                trigger = self._find_trigger(key)
                actions = trigger.get("actions", []) if trigger else []
                index = self._get_index(key)
                if key not in self.state.call_refs_for(trigger_set_id):
                    self._drop_single_call(trigger_set_id, key, pending.generation, pending)
                    self._run_single_action(key, actions)
                    return
                ancestors, depth = self._linked_ancestors(key)
                ctx = start_linked_call(trigger_set_id, key, call_target(actions[index]),
                                        self._find_trigger, self.state, step=is_step_call(actions[index]),
                                        ancestors=ancestors, ancestor_depth=depth)
                for member in chain_from(self.state, trigger_set_id, key, self._find_trigger):
                    ctx.before[member] = snapshot_for(self.state, trigger_set_id, member)
                pending.call = ctx
                pending.position = index
                if (trigger_set_id, key) in self._call_view_contexts:
                    self._call_view_contexts[(trigger_set_id, key)] = ctx
        self._schedule_single_call(trigger_set_id, key, pending.generation, pending, delay)
        self._update_status()

    def _prepare_control_target(self, identity: tuple[str, str]) -> bool:
        trigger_set_id, key = identity
        if key == self.state.run_to_end_key and not self.state.run_to_end_paused:
            return False
        pending = self.state.pending_steps.get(identity)
        paused_call = pending is not None and pending.call is not None and pending.call_paused
        paused_run = key == self.state.run_to_end_key and self.state.run_to_end_paused
        if paused_call or paused_run:
            current = (self._control_source, identity, self._acceptance_snapshot(key))
            if self._pending_control_discard == current:
                self._pending_control_discard = None
                self.discard_paused((key,))
                return True
            self._pending_control_discard = current
            if self._notify_message is not None:
                self._notify_message(
                    f"一時停止中の {key} を破棄します。もう一度押すと実行します"
                )
            return False
        return True

    def _accept_key(self, key: str) -> None:
        active = self._active_key()
        if active is not None:
            pending = self.state.pending_steps.get((self._get_trigger_set_id(), active))
            ctx = self._run_to_end_call if active == self.state.run_to_end_key else (
                pending.call if pending is not None else None)
            same_chain = False
            if isinstance(ctx, CallContext):
                chain = chain_from(self.state, self._get_trigger_set_id(), key, self._find_trigger)
                members = {active, ctx.first_target, *(frame.key for frame in ctx.stack)}
                same_chain = key in members or chain[-1] in members
            if key == active or same_chain:
                if active == self.state.run_to_end_key:
                    self.pause_run_to_end()
                    self._update_status()
                else:
                    if pending is not None and pending.call is not None:
                        # ステップの文脈の 1 ステップの処理中（入れ子の一括の実行中を含む）は無視する
                        if not (isinstance(pending.call, CallContext)
                                and (pending.call.is_step_context()
                                     or pending.call.root_continuation is not None)):
                            self._pause_single_call(active)
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
        # Calling a trigger with its own pending wait/read must not consume a press.
        position = self._get_index(key)
        actions = trigger.get("actions", [])
        if 0 <= position < len(actions):
            target = call_target(actions[position])
            top = chain_top(self.state, self._get_trigger_set_id(), target, self._find_trigger) if target else key
            if (self._get_trigger_set_id(), top) in self.state.pending_steps:
                return
        if bool(trigger.get("run_to_end", False)):
            actions = trigger.get("actions", [])
            if self._is_standalone_control(actions):
                self._run_single_action(key, actions)
                return
            self.discard_paused()
            self._start_run_to_end(key)
            return
        self._run_single_action(key, trigger.get("actions", []))

    @staticmethod
    def _is_standalone_control(actions: Sequence[Any]) -> bool:
        if len(actions) != 1 or not isinstance(actions[0], Mapping):
            return False
        action = actions[0]
        is_control = (action_type(action) == ACTION_TYPE_SYSTEM
                      and system_op(action) in (OP_BACK, OP_REWIND))
        return is_control and not standalone_violation(
            actions, action, replace_index=0,
        )
