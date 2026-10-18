import threading
import unittest

from keyseq.application.delayed_calls import DelayedCallWorker


class DelayedCallWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.worker = DelayedCallWorker()
        self.addCleanup(self.stop_worker)

    def stop_worker(self) -> None:
        self.worker.stop()
        if self.worker._thread is not None:
            self.worker._thread.join(timeout=1.0)
            self.assertFalse(self.worker._thread.is_alive())

    def test_callbacks_run_in_deadline_order(self) -> None:
        called = []
        done = threading.Event()
        # Keep the worker occupied while adding deadlines, including one
        # earlier than the deadline it will initially be waiting for.
        ready = threading.Event()
        release = threading.Event()
        self.addCleanup(release.set)

        def block() -> None:
            ready.set()
            release.wait(timeout=1.0)

        self.worker.schedule(0, block)
        self.assertTrue(ready.wait(timeout=1.0))
        self.worker.schedule(0.10, lambda: (called.append("last"), done.set()))
        self.worker.schedule(0.03, lambda: called.append("first"))
        self.worker.schedule(0.06, lambda: called.append("second"))
        release.set()
        self.assertTrue(done.wait(timeout=2.0))
        self.assertEqual(called, ["first", "second", "last"])

    def test_schedule_never_calls_back_on_caller_with_lock_held(self) -> None:
        lock = threading.Lock()
        done = threading.Event()
        caller_done = threading.Event()
        callback_threads = []

        def callback() -> None:
            with lock:
                callback_threads.append(threading.get_ident())
                done.set()

        def caller() -> None:
            with lock:
                self.worker.schedule(0, callback)
            caller_done.set()

        thread = threading.Thread(target=caller, daemon=True)
        thread.start()
        self.assertTrue(caller_done.wait(timeout=1.0))
        self.assertTrue(done.wait(timeout=1.0))
        thread.join(timeout=1.0)
        self.assertNotEqual(callback_threads, [thread.ident])

    def test_callback_exception_is_logged_and_worker_continues(self) -> None:
        done = threading.Event()

        def fail() -> None:
            raise ValueError("callback failure")

        with self.assertLogs("keyseq.application.delayed_calls", level="ERROR") as logs:
            self.worker.schedule(0, fail)
            self.worker.schedule(0, done.set)
            self.assertTrue(done.wait(timeout=1.0))
        self.assertIn("callback failure", "\n".join(logs.output))

    def test_stop_discards_pending_calls_and_terminates_worker(self) -> None:
        called = threading.Event()
        self.worker.schedule(60, called.set)
        self.stop_worker()
        self.worker.schedule(0, called.set)
        self.worker.stop()  # repeated shutdown is harmless
        self.assertFalse(called.is_set())

    def test_stop_before_first_schedule_does_not_start_worker(self) -> None:
        self.worker.stop()
        self.worker.schedule(0, lambda: self.fail("stopped worker called back"))
        self.assertIsNone(self.worker._thread)


if __name__ == "__main__":
    unittest.main()
