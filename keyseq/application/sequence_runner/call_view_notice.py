"""Remember stopped calls in stop order and publish their display snapshots."""

from __future__ import annotations

from keyseq.application.call_context import CallContext
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

    def _publish_call_view(self) -> None:
        # Only calls that have stopped can open the view. Resuming keeps their order.
        for identity, ctx in tuple(self._call_view_contexts.items()):
            if identity == RUN_TO_END_CALL_VIEW:
                current = self._run_to_end_call
            else:
                pending = self.state.pending_steps.get(identity)
                current = pending.call if pending is not None else None
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
