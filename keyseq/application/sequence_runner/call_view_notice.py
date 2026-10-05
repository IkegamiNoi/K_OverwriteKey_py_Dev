"""Remember stopped calls in stop order and publish their display snapshots."""

from __future__ import annotations

from keyseq.application.call_context import CallContext
from keyseq.application.call_chain import chain_from
from keyseq.application.call_view import build_call_view_summary


RUN_TO_END_CALL_VIEW = "run_to_end"
CallViewIdentity = tuple[str, str] | str


class CallViewMixin:
    def _call_view_stopped(self, identity: CallViewIdentity, ctx: CallContext) -> None:
        if not ctx.stack:
            return
        self._call_view_contexts.pop(identity, None)
        self._call_view_contexts[identity] = ctx
        self._publish_call_view()

    def _call_view_disappeared(self, identity: CallViewIdentity) -> None:
        self._call_view_contexts.pop(identity, None)
        self._publish_call_view()

    def publish_call_view(self) -> None:
        """Republish the current call view after external state cleanup."""
        self._publish_call_view()

    def _publish_call_view(self) -> None:
        # Only calls that have stopped can open the view. Resuming keeps their order.
        for identity, ctx in tuple(self._call_view_contexts.items()):
            if identity == RUN_TO_END_CALL_VIEW:
                current = self._run_to_end_call
                if current is not None and current is not ctx:
                    # Keep the stopped view until the rebuilt live frames are ready.
                    if not current.started:
                        continue
                    self._call_view_contexts[identity] = current
                    ctx = current
            else:
                pending = self.state.pending_steps.get(identity)
                current = pending.call if pending is not None else None
                if pending is None:
                    # This temporary display bridge is replaced in task_11 (表示の切替).
                    chain = chain_from(self.state, identity[0], identity[1], self._find_trigger)
                    if len(chain) > 1:
                        # Display compatibility only: this object never resumes execution.
                        ctx.stack = [ctx.changed_frames[key] for key in chain[1:]
                                     if key in ctx.changed_frames]
                        for frame in ctx.stack:
                            frame.position = self.state.indices_for(identity[0]).get(frame.key, 0)
                            frame.frames = list(self.state.loop_frames_for(identity[0]).get(frame.key, []))
                            ctx.entry_for(frame.key)
                        current = ctx
            if current is not ctx or not ctx.stack:
                self._call_view_contexts.pop(identity)
        opened = bool(self._call_view_contexts)
        if not opened and not self._call_view_open:
            return
        self._call_view_open = opened
        if self._notify_call_view is not None:
            summary = None
            if opened:
                ctx = next(reversed(self._call_view_contexts.values()))
                summary = build_call_view_summary(ctx, self.state.counters)
            self._notify_call_view(summary)
