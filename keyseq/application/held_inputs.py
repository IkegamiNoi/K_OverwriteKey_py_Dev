from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Iterator

from keyseq.domain.key_hold import held_display_name


_logger = logging.getLogger(__name__)
InputIdentity = tuple[str, int, bool] | tuple[str, str]


@dataclass(frozen=True)
class HeldInput:
    name: str
    owner: str
    order: int


class HeldInputs:
    """UI スレッドから操作する押下中の集合。送信は gateway に委ねる。"""

    def __init__(
        self, input_gateway, *,
        enter_send_guard: Callable[[], None] | None = None,
        exit_send_guard: Callable[[], None] | None = None,
        on_change: Callable[[tuple[str, ...]], None] | None = None,
    ) -> None:
        self.input_gateway = input_gateway
        self._records: dict[InputIdentity, HeldInput] = {}
        self._next_order = 0
        self.current_owner: str | None = None
        self._on_change = on_change
        self.set_send_guard(enter_send_guard, exit_send_guard)

    @contextmanager
    def owner_scope(self, owner: str) -> Iterator[None]:
        previous = self.current_owner
        self.current_owner = owner
        try:
            yield
        finally:
            self.current_owner = previous

    def set_send_guard(
        self, enter: Callable[[], None] | None, exit: Callable[[], None] | None,
    ) -> None:
        self._enter_send_guard = enter
        self._exit_send_guard = exit

    @property
    def display_names(self) -> tuple[str, ...]:
        return tuple(
            held_display_name(identity[0], record.name)
            for identity, record in self._ordered_records()
        )

    def _ordered_records(self) -> list[tuple[InputIdentity, HeldInput]]:
        return sorted(self._records.items(), key=lambda item: item[1].order)

    def _notify(self) -> None:
        if self._on_change is not None:
            self._on_change(self.display_names)

    @contextmanager
    def _guard(self) -> Iterator[None]:
        if self._enter_send_guard is not None:
            self._enter_send_guard()
        try:
            yield
        finally:
            if self._exit_send_guard is not None:
                self._exit_send_guard()

    def _key_identity(self, key: str) -> InputIdentity:
        scan, extended = self.input_gateway.key_identity(key)
        return ("key", scan, extended)

    def _record(self, identity: InputIdentity, owner: str, name: str) -> None:
        previous = self._records.get(identity)
        order = previous.order if previous is not None else self._next_order
        if previous is None:
            self._next_order += 1
        record = HeldInput(name, owner, order)
        self._records[identity] = record
        if record != previous:
            self._notify()

    def _remove(self, identity: InputIdentity) -> None:
        if identity in self._records:
            del self._records[identity]
            self._notify()

    def _press(
        self, identity: InputIdentity, owner: str, name: str,
        send: Callable[[], None], release: Callable[[], None],
    ) -> None:
        self._record(identity, owner, name)
        try:
            send()
        except Exception:
            try:
                release()
            except Exception:
                _logger.exception("Failed to compensate held input press: %s", name)
            else:
                self._remove(identity)
            raise

    def press_key(self, owner: str, key: str) -> None:
        identity = self._key_identity(key)
        with self._guard():
            self._press(identity, owner, key,
                        lambda: self.input_gateway.press_key(key),
                        lambda: self.input_gateway.release_key(key))

    def press_mouse(
        self, owner: str, button: str, position: tuple[int, int] | None = None,
    ) -> None:
        x, y = position if position is not None else (None, None)
        self._press(("mouse", button), owner, button,
                    lambda: self.input_gateway.mouse_down(button, x, y),
                    lambda: self.input_gateway.mouse_up(button))

    def release_key(self, key: str) -> None:
        identity = self._key_identity(key)
        with self._guard():
            self.input_gateway.release_key(key)
        self._remove(identity)

    def release_mouse(
        self, button: str, position: tuple[int, int] | None = None,
    ) -> None:
        x, y = position if position is not None else (None, None)
        self.input_gateway.mouse_up(button, x, y)
        self._remove(("mouse", button))

    def _release_records(
        self, owner: str | None, *, keyboard_only: bool = False,
    ) -> list[Exception]:
        errors: list[Exception] = []
        for identity, record in self._ordered_records():
            if owner is not None and record.owner != owner:
                continue
            if keyboard_only and identity[0] != "key":
                continue
            try:
                if identity[0] == "key":
                    with self._guard():
                        self.input_gateway.release_key(record.name)
                else:
                    self.input_gateway.mouse_up(record.name)
            except Exception as exc:
                errors.append(exc)
            else:
                self._remove(identity)
        return errors

    def release_owner(self, owner: str) -> list[Exception]:
        return self._release_records(owner)

    def release_all(self) -> list[Exception]:
        return self._release_records(None)

    def release_keyboard(self) -> list[Exception]:
        """持ち主によらずキーボードの分だけ離す（text の送信失敗の後始末・暫定 35 §4.4）。"""
        return self._release_records(None, keyboard_only=True)

    def suspend_keyboard(self) -> None:
        errors: list[Exception] = []
        with self._guard():
            for identity, record in self._ordered_records():
                if identity[0] == "key":
                    try:
                        self.input_gateway.release_key(record.name)
                    except Exception as exc:
                        errors.append(exc)
        if errors:
            raise errors[0]

    def resume_keyboard(self) -> None:
        errors: list[Exception] = []
        for identity, record in self._ordered_records():
            if identity[0] == "key":
                # 押し直しの失敗も通常の押下と同じ補償を行う。
                try:
                    self.press_key(record.owner, record.name)
                except Exception as exc:
                    errors.append(exc)
        if errors:
            raise errors[0]
