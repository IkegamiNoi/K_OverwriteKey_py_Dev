"""Query the selected trigger's live chain and notify of possible changes."""

from __future__ import annotations

from keyseq.application.call_context import CallContext
from keyseq.application.call_chain import chain_from
from keyseq.application.call_view import CallViewSummary, build_call_view_summary
from keyseq.application.sequence_steps import LoopFrame
from keyseq.domain.config import normalize_key_name


class CallViewMixin:
    def call_view_summary_for(self, key: str) -> CallViewSummary | None:
        """Prefer in-flight frame values until linked progress is written back."""
        key = normalize_key_name(key)
        trigger_set_id = self._get_trigger_set_id()
        with self.state.lock:
            positions = dict(self.state.indices_for(trigger_set_id))
            refs = set(self.state.call_refs_for(trigger_set_id))
            frames_by_key: dict[str, list[LoopFrame]] = {}
            for ctx in self._live_call_view_contexts(trigger_set_id):
                for frame in ctx.changed_frames.values():
                    positions[frame.key] = frame.position
                    frames_by_key[frame.key] = frame.frames
                    refs.discard(frame.key)
                refs.discard(ctx.root_key)
                if ctx.stack and not ctx.failed:
                    refs.add(ctx.root_key)
                    refs.update(frame.key for frame in ctx.stack[:-1])
        path = chain_from(self.state, trigger_set_id, key, self._find_trigger,
                          positions=positions, call_refs=refs)
        if len(path) < 2:
            return None
        top = path[-1]
        trigger = self._find_trigger(top)
        if trigger is None:
            return None
        with self.state.lock:
            frames = frames_by_key.get(top, self.state.loop_frames_for(trigger_set_id).get(top, []))
            return build_call_view_summary(path, trigger.get("actions", []),
                                           positions.get(top, 0), frames, self.state.counters)

    def _live_call_view_contexts(self, trigger_set_id: str) -> list[CallContext]:
        # Paused contexts can lag behind another press on the shared callee.
        contexts = [pending.call for identity, pending in self.state.pending_steps.items()
                    if identity[0] == trigger_set_id and not pending.call_paused]
        if not self.state.run_to_end_paused:
            contexts.append(self._run_to_end_call)
        return [ctx for ctx in contexts if isinstance(ctx, CallContext)
                and ctx.trigger_set_id == trigger_set_id and ctx.started]

    def publish_call_view(self) -> None:
        """Notify after external state cleanup."""
        self._publish_call_view()

    def _publish_call_view(self) -> None:
        if self._notify_call_view is not None:
            self._notify_call_view()
