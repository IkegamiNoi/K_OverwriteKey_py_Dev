from __future__ import annotations

import logging
from typing import Callable


InputIdentity = tuple[str, int, bool] | tuple[str, str]
RepeatTarget = tuple[InputIdentity, str, dict]
_logger = logging.getLogger(__name__)


class KeyRepeater:
    """UI スレッドの予約で、一つのキーの押下を送り直す。"""

    def __init__(
        self, *, after: Callable[[int, Callable[[], None]], object] | None = None,
        after_cancel: Callable[[object], None] | None = None,
        get_timing: Callable[[], tuple[int, int]],
        send: Callable[[str], None] | None = None,
        on_failure: Callable[[InputIdentity, str, dict, Exception], None] | None = None,
    ) -> None:
        self._after = after
        self._after_cancel = after_cancel
        self._get_timing = get_timing
        self._send = send
        self._on_failure = on_failure
        self._target: RepeatTarget | None = None
        self._reservation: object | None = None
        self._generation = 0
        self._suppress_count = 0

    def set_callbacks(
        self, send: Callable[[str], None],
        on_failure: Callable[[InputIdentity, str, dict, Exception], None],
    ) -> None:
        """保持入力の集合から送信と後始末を受け取る。"""
        self._send = send
        self._on_failure = on_failure

    def start(self, identity: InputIdentity, key: str, action: dict) -> None:
        if self._suppress_count:
            return
        self.stop()
        if self._after is None or self._after_cancel is None or self._send is None:
            return
        delay, interval = self._get_timing()
        target = (identity, key, action)
        self._target = target
        self._schedule(delay, interval, self._generation, target)

    def stop(self) -> None:
        reservation = self._reservation
        self._reservation = None
        self._target = None
        self._generation += 1
        if reservation is not None and self._after_cancel is not None:
            try:
                self._after_cancel(reservation)
            except Exception:
                # 取り消せなくても、世代の照合で古い予約の送信を防ぐ。
                _logger.exception("リピート予約の取り消しに失敗しました")

    @property
    def has_target(self) -> bool:
        return self._target is not None

    def is_target(self, identity: InputIdentity) -> bool:
        return self._target is not None and self._target[0] == identity

    def _schedule(
        self, delay: int, interval: int, generation: int, target: RepeatTarget,
    ) -> None:
        self._reservation = self._after(
            delay, lambda: self._fire(generation, target, interval),
        )

    def _fire(self, generation: int, target: RepeatTarget, interval: int) -> None:
        if generation != self._generation or self._target is not target:
            return
        self._reservation = None
        if self._suppress_count:
            self.stop()
            return
        identity, key, action = target
        try:
            self._send(key)
        except Exception as exc:
            self.stop()
            if self._on_failure is not None:
                self._on_failure(identity, key, action, exc)
            else:
                _logger.exception("リピートの送信に失敗しました: %s", key)
            return
        if generation == self._generation and self._target is target:
            try:
                self._schedule(interval, interval, generation, target)
            except Exception:
                # 予約できなければ対象だけ残さず止める。
                _logger.exception("リピートの再予約に失敗しました: %s", key)
                self.stop()

    def pause_for_text(self) -> RepeatTarget | None:
        saved = self._target
        self.stop()
        return saved

    def resume_after_text(self, saved: RepeatTarget | None) -> None:
        if saved is not None and not self._suppress_count:
            self.start(*saved)

    def begin_suppress(self) -> None:
        self._suppress_count += 1
        self.stop()

    def end_suppress(self) -> None:
        if self._suppress_count:
            self._suppress_count -= 1
