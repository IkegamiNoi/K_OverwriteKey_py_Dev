from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class AppState:
    selected_trigger_idx: int = 0
    indices: dict[str, int] = field(default_factory=dict)

    run_to_end_key: str | None = None
    run_to_end_paused: bool = False
    run_to_end_after_id: Any = None

    chain_running: bool = False
    chain_paused: bool = False
    chain_key: str | None = None
    chain_thread: threading.Thread | None = None

    lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    reentry_guard: set[str] = field(default_factory=set, init=False)
    chain_stop_event: threading.Event = field(default_factory=threading.Event, init=False)
    chain_pause_event: threading.Event = field(default_factory=threading.Event, init=False)

    def reset_indices(self) -> None:
        self.indices = {}

    def update_selected_index(self, value: int) -> None:
        self.selected_trigger_idx = int(value)

    def get_selected_index(self) -> int:
        return int(self.selected_trigger_idx)

    def request_main_thread(self, callback: Callable[[], None], *args, **kwargs) -> None:
        """Adapter hook kept for compatibility in case caller injects scheduling."""
        callback(*args, **kwargs)
