from __future__ import annotations

import unittest

from keyseq.presentation.hook_dispatcher import (
    ImmediateHookDispatcher,
    QueuedHookDispatcher,
)


class FakeAfter:
    def __init__(self) -> None:
        self.calls: list[tuple[int, object]] = []

    def __call__(self, delay: int, callback):
        self.calls.append((delay, callback))
        return len(self.calls)

    def run_next(self) -> None:
        _delay, callback = self.calls.pop(0)
        callback()


class HookDispatcherTests(unittest.TestCase):
    def test_immediate_dispatch_calls_after_zero_and_ignores_discard(self):
        calls = []
        discarded = []
        after = FakeAfter()
        dispatcher = ImmediateHookDispatcher(after)
        self.assertTrue(dispatcher.dispatch(
            lambda: calls.append("run"), on_discard=lambda: discarded.append(1), priority=True,
        ))
        self.assertEqual(after.calls[0][0], 0)
        self.assertEqual(calls, [])
        after.run_next()
        self.assertEqual(calls, ["run"])
        self.assertEqual(discarded, [])
        dispatcher.invalidate()
        dispatcher.close()
        self.assertTrue(dispatcher.dispatch(lambda: calls.append("after-close")))
        after.run_next()
        self.assertEqual(calls, ["run", "after-close"])

    def test_queue_limit_rejects_regular_items_but_not_priority(self):
        after = FakeAfter()
        dispatcher = QueuedHookDispatcher(after, limit=2)
        self.assertTrue(dispatcher.dispatch(lambda: None))
        self.assertTrue(dispatcher.dispatch(lambda: None))
        rejected_calls = []
        self.assertFalse(dispatcher.dispatch(
            lambda: rejected_calls.append("run"),
            on_discard=lambda: rejected_calls.append("discard"),
        ))
        self.assertTrue(dispatcher.dispatch(lambda: None, priority=True))
        self.assertEqual(after.calls, [])
        dispatcher.start()
        after.run_next()
        self.assertEqual(rejected_calls, [])
        self.assertTrue(dispatcher.dispatch(lambda: None))

    def test_default_limit_is_64_and_priority_ignores_invalidation_and_expiry(self):
        now = [0.0]
        after = FakeAfter()
        dispatcher = QueuedHookDispatcher(after, clock=lambda: now[0])
        for _ in range(64):
            self.assertTrue(dispatcher.dispatch(lambda: None))
        self.assertFalse(dispatcher.dispatch(lambda: None))
        seen = []
        dispatcher.dispatch(lambda: seen.append("priority"), on_discard=lambda: seen.append("discard"), priority=True)
        dispatcher.invalidate()
        now[0] = 100
        dispatcher.start()
        after.run_next()
        self.assertEqual(seen, ["priority"])

    def test_priority_runs_before_regular_and_regular_batch_is_bounded(self):
        after = FakeAfter()
        dispatcher = QueuedHookDispatcher(after, interval_ms=10)
        seen = []
        dispatcher.start()
        dispatcher.dispatch(lambda: seen.append("regular-1"))
        dispatcher.dispatch(lambda: seen.append("regular-2"))
        dispatcher.dispatch(lambda: seen.append("priority"), priority=True)
        after.run_next()
        self.assertEqual(seen, ["priority", "regular-1", "regular-2"])
        self.assertEqual(after.calls[0][0], 10)

    def test_regular_item_enqueued_during_drain_waits_for_next_tick(self):
        after = FakeAfter()
        dispatcher = QueuedHookDispatcher(after)
        seen = []
        dispatcher.start()
        dispatcher.dispatch(
            lambda: (seen.append("priority-added"), dispatcher.dispatch(lambda: seen.append("later"))),
            priority=True,
        )
        dispatcher.dispatch(lambda: seen.append("first"))
        after.run_next()
        self.assertEqual(seen, ["priority-added", "first"])
        after.run_next()
        self.assertEqual(seen, ["priority-added", "first", "later"])

    def test_expired_item_calls_discard_and_stale_generation_does_not(self):
        now = [0.0]
        after = FakeAfter()
        dispatcher = QueuedHookDispatcher(after, clock=lambda: now[0], ttl_s=1.0)
        seen = []
        dispatcher.start()
        dispatcher.dispatch(lambda: seen.append("expired"), on_discard=lambda: seen.append("discard"))
        dispatcher.dispatch(lambda: seen.append("stale"), on_discard=lambda: seen.append("wrong-discard"))
        dispatcher.invalidate()
        dispatcher.dispatch(lambda: seen.append("expired"), on_discard=lambda: seen.append("discard"))
        now[0] = 2.0
        after.run_next()
        self.assertEqual(seen, ["discard"])

    def test_run_exception_is_logged_and_queue_continues(self):
        after = FakeAfter()
        dispatcher = QueuedHookDispatcher(after)
        seen = []
        dispatcher.start()
        dispatcher.dispatch(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        dispatcher.dispatch(lambda: seen.append("continued"))
        with self.assertLogs("keyseq.presentation.hook_dispatcher", level="ERROR"):
            after.run_next()
        self.assertEqual(seen, ["continued"])

    def test_discard_exception_is_logged_and_queue_continues(self):
        now = [0.0]
        after = FakeAfter()
        dispatcher = QueuedHookDispatcher(after, clock=lambda: now[0], ttl_s=1.0)
        seen = []
        dispatcher.start()
        dispatcher.dispatch(lambda: seen.append("expired"), on_discard=lambda: (_ for _ in ()).throw(RuntimeError("discard")))
        dispatcher.dispatch(lambda: seen.append("expired-next"), on_discard=lambda: seen.append("next"))
        now[0] = 2.0
        with self.assertLogs("keyseq.presentation.hook_dispatcher", level="ERROR"):
            after.run_next()
        self.assertEqual(seen, ["next"])

    def test_after_exception_is_logged_and_factory_starts_only_queued_dispatcher(self):
        from keyseq.presentation.hook_dispatcher import create_hook_dispatcher

        def bad_after(delay, callback):
            raise RuntimeError("tk closing")
        with self.assertLogs("keyseq.presentation.hook_dispatcher", level="ERROR"):
            queued = create_hook_dispatcher(bad_after, queued=True)
        self.assertIsInstance(queued, QueuedHookDispatcher)
        immediate_after = FakeAfter()
        immediate = create_hook_dispatcher(immediate_after, queued=False)
        self.assertIsInstance(immediate, ImmediateHookDispatcher)
        self.assertEqual(immediate_after.calls, [])

    def test_close_prevents_scheduled_drain_and_dispatch_never_calls_after(self):
        after = FakeAfter()
        dispatcher = QueuedHookDispatcher(after)
        dispatcher.start()
        self.assertEqual(len(after.calls), 1)
        seen = []
        dispatcher.dispatch(lambda: seen.append("drained"))
        self.assertEqual(len(after.calls), 1)
        dispatcher.close()
        after.run_next()
        self.assertEqual(len(after.calls), 0)
        self.assertEqual(seen, [])


if __name__ == "__main__":
    unittest.main()
