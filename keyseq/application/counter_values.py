"""Explicit effective values and reset destinations for runtime counters."""

from collections.abc import Mapping


class CounterValues(dict[str, int]):
    def __init__(self) -> None:
        super().__init__()
        self.starts: dict[str, int] = {}

    def value(self, name: str) -> int:
        return self[name] if name in self else self.starts.get(name, 0)

    def set_starts(self, starts: Mapping[str, int]) -> None:
        self.starts = dict(starts)


def counter_value(counters: Mapping[str, int], name: str) -> int:
    if isinstance(counters, CounterValues):
        return counters.value(name)
    return counters.get(name, 0)


def counter_start(counters: Mapping[str, int], name: str) -> int:
    return counters.starts.get(name, 0) if isinstance(counters, CounterValues) else 0


def counter_display_values(counters: Mapping[str, int]) -> dict[str, int]:
    return {**counters.starts, **counters} if isinstance(counters, CounterValues) else dict(counters)


def counter_starts_of(counters: Mapping[str, int]) -> dict[str, int]:
    return dict(counters.starts) if isinstance(counters, CounterValues) else {}
