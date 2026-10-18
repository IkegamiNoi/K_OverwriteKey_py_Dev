"""単一のワーカーで、期限順に遅延コールバックを呼ぶ。"""

from __future__ import annotations

import heapq
import itertools
import logging
import threading
import time
from collections.abc import Callable


logger = logging.getLogger(__name__)


class DelayedCallWorker:
    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._pending: list[tuple[float, int, Callable[[], None]]] = []
        self._order = itertools.count()
        self._thread: threading.Thread | None = None
        self._stopped = False

    def schedule(self, delay_s: float, callback: Callable[[], None]) -> None:
        with self._condition:
            if self._stopped:
                return
            heapq.heappush(
                self._pending,
                (time.perf_counter() + max(0.0, delay_s), next(self._order), callback),
            )
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, daemon=True)
                self._thread.start()
            self._condition.notify()

    def stop(self) -> None:
        """待機中の予約を捨てる。実行中の callback の終了は待たない。"""
        with self._condition:
            self._stopped = True
            self._pending.clear()
            self._condition.notify_all()

    def _run(self) -> None:
        while True:
            with self._condition:
                while not self._stopped:
                    if not self._pending:
                        self._condition.wait()
                        continue
                    remaining = self._pending[0][0] - time.perf_counter()
                    if remaining > 0:
                        self._condition.wait(remaining)
                        continue
                    _, _, callback = heapq.heappop(self._pending)
                    break
                else:
                    return
            try:
                callback()
            except Exception:
                logger.exception("Delayed callback failed")
