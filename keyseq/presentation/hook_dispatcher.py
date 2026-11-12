from __future__ import annotations

import logging
import queue
import threading
import time
from collections.abc import Callable
from typing import Protocol


Callback = Callable[[], None]
After = Callable[[int, Callback], object]


class HookDispatcher(Protocol):
    def dispatch(
        self, run: Callback, *, on_discard: Callback | None = None, priority: bool = False,
    ) -> bool: ...

    def invalidate(self) -> None: ...

    def close(self) -> None: ...


class ImmediateHookDispatcher:
    """Preserve the Windows callback handoff through after(0)."""

    def __init__(self, after: After) -> None:
        self._after = after

    def dispatch(
        self, run: Callback, *, on_discard: Callback | None = None, priority: bool = False,
    ) -> bool:
        self._after(0, run)
        return True

    def invalidate(self) -> None:
        pass

    def close(self) -> None:
        pass


class QueuedHookDispatcher:
    """Accept hook work without Tk calls; start and drain on the UI thread."""

    def __init__(
        self, after: After, clock: Callable[[], float] = time.monotonic, *,
        limit: int = 64, ttl_s: float = 1.0, interval_ms: int = 10,
    ) -> None:
        self._after = after
        self._clock = clock
        self._limit = limit
        self._ttl_s = ttl_s
        self._interval_ms = interval_ms
        self._normal: queue.SimpleQueue[tuple[Callback, Callback | None, float, int]] = queue.SimpleQueue()
        self._priority: queue.SimpleQueue[Callback] = queue.SimpleQueue()
        self._lock = threading.Lock()
        self._count = 0
        self._generation = 0
        self._closed = False
        self._started = False
        self._logger = logging.getLogger(__name__)

    def dispatch(
        self, run: Callback, *, on_discard: Callback | None = None, priority: bool = False,
    ) -> bool:
        with self._lock:
            if priority:
                self._priority.put(run)
                return True
            if self._count >= self._limit:
                return False
            self._normal.put((run, on_discard, self._clock(), self._generation))
            self._count += 1
            return True

    def invalidate(self) -> None:
        with self._lock:
            self._generation += 1

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def start(self) -> None:
        with self._lock:
            if self._started or self._closed:
                return
            self._started = True
        self._schedule()

    def _schedule(self) -> None:
        with self._lock:
            if self._closed:
                return
        try:
            self._after(self._interval_ms, self._drain)
        except Exception:
            self._logger.exception("Could not schedule hook dispatch drain")

    def _call(self, callback: Callback) -> None:
        try:
            callback()
        except Exception:
            self._logger.exception("Hook dispatch callback failed")

    def _drain(self) -> None:
        with self._lock:
            if self._closed:
                return
            # Work added during this drain waits for the next UI tick.
            count = self._count
        while not self._closed:
            try:
                run = self._priority.get_nowait()
            except queue.Empty:
                break
            self._call(run)
        for _ in range(count):
            with self._lock:
                if self._closed:
                    return
                run, on_discard, queued_at, generation = self._normal.get_nowait()
                self._count -= 1
                current_generation = self._generation
            if generation != current_generation:
                continue
            if self._clock() - queued_at > self._ttl_s:
                if on_discard is not None:
                    self._call(on_discard)
            else:
                self._call(run)
        self._schedule()


def create_hook_dispatcher(after: After, *, queued: bool) -> HookDispatcher:
    if queued:
        dispatcher = QueuedHookDispatcher(after)
        dispatcher.start()
        return dispatcher
    return ImmediateHookDispatcher(after)
