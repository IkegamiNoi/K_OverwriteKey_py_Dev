from __future__ import annotations

import threading
import time
from typing import Any, Callable

from keyseq.domain.config import normalize_key_name


class SequenceRunner:
    def __init__(
        self,
        *,
        state,
        find_trigger: Callable[[str], dict[str, Any] | None],
        perform_action: Callable[[dict[str, Any]], None],
        select_trigger: Callable[[str], None],
        refresh_actions: Callable[[], None],
        update_status: Callable[[], None],
        after: Callable[[int, Callable[..., None]], Any],
        after_cancel: Callable[[Any], None],
    ):
        self.state = state
        self._find_trigger = find_trigger
        self._perform_action = perform_action
        self._select_trigger = select_trigger
        self._refresh_actions = refresh_actions
        self._update_status = update_status
        self._after = after
        self._after_cancel = after_cancel

    def handle_key(self, key: str) -> None:
        key = normalize_key_name(key)

        # 連続実行中は同一トリガーのみトグル
        if self.state.run_to_end_key is not None:
            if key != self.state.run_to_end_key:
                return
            if not self.state.run_to_end_paused:
                self.pause_run_to_end()
            else:
                self.resume_run_to_end()
            self._update_status()
            return

        trig = self._find_trigger(key)
        if not trig:
            return
        actions = trig.get("actions", [])
        if not actions:
            return

        if bool(trig.get("run_to_end", False)):
            self._start_run_to_end(key)
            return

        self._run_single_action(key, actions)

    def _run_single_action(self, key: str, actions: list[dict[str, Any]]) -> None:
        with self.state.lock:
            if key in self.state.reentry_guard:
                return
            self.state.reentry_guard.add(key)

        try:
            i = self.state.indices.get(key, 0) % len(actions)
            self._perform_action(actions[i])
            with self.state.lock:
                self.state.indices[key] = (i + 1) % len(actions)
        finally:
            with self.state.lock:
                self.state.reentry_guard.discard(key)
            self._select_trigger(key)

    # --- run_to_end ---
    def _start_run_to_end(self, key: str) -> None:
        key = normalize_key_name(key)
        trig = self._find_trigger(key)
        if not trig:
            return
        actions = trig.get("actions", [])
        if not actions:
            return

        self.state.run_to_end_key = key
        self.state.run_to_end_paused = False
        self._select_trigger(key)
        self._run_to_end_step()

    def pause_run_to_end(self) -> None:
        self.state.run_to_end_paused = True
        if self.state.run_to_end_after_id is not None:
            try:
                self._after_cancel(self.state.run_to_end_after_id)
            except Exception:
                pass
            self.state.run_to_end_after_id = None

    def resume_run_to_end(self) -> None:
        self.state.run_to_end_paused = False
        self._run_to_end_step(schedule_only=True)

    def stop_run_to_end(self) -> None:
        if self.state.run_to_end_after_id is not None:
            try:
                self._after_cancel(self.state.run_to_end_after_id)
            except Exception:
                pass
        self.state.run_to_end_after_id = None
        self.state.run_to_end_key = None
        self.state.run_to_end_paused = False
        self._update_status()

    def _run_to_end_step(self, schedule_only: bool = False) -> None:
        key = self.state.run_to_end_key
        if not key or self.state.run_to_end_paused:
            return

        trig = self._find_trigger(key)
        if not trig:
            self.stop_run_to_end()
            return

        actions = trig.get("actions", [])
        if not actions:
            self.stop_run_to_end()
            return

        delay = trig.get("run_to_end_delay_ms", 300)
        try:
            delay = int(delay)
        except Exception:
            delay = 300
        if delay < 0:
            delay = 0

        i = int(self.state.indices.get(key, 0) or 0)
        if i < 0:
            i = 0

        if schedule_only:
            self.state.run_to_end_after_id = self._after(delay, self._run_to_end_step)
            return

        if i >= len(actions):
            self.state.indices[key] = 0
            self.stop_run_to_end()
            self._select_trigger(key)
            return

        self._perform_action(actions[i])
        self.state.indices[key] = i + 1
        self._select_trigger(key)

        if self.state.indices[key] >= len(actions):
            self.state.indices[key] = 0
            self.stop_run_to_end()
            self._select_trigger(key)
            return

        self.state.run_to_end_after_id = self._after(delay, self._run_to_end_step)

    # --- chain run ---
    def chain_start_or_toggle(self, key: str) -> None:
        key = normalize_key_name(key)

        if self.state.chain_running and self.state.chain_key == key:
            if self.state.chain_paused:
                self.state.chain_paused = False
                self.state.chain_pause_event.clear()
                self._after(0, self._update_status)
            else:
                self.state.chain_paused = True
                self.state.chain_pause_event.set()
                self._after(0, self._update_status)
            return

        if self.state.chain_running and (not self.state.chain_paused):
            return

        self.stop_chain(force=True)
        self.state.chain_key = key
        self.state.chain_running = True
        self.state.chain_paused = False
        self.state.chain_stop_event.clear()
        self.state.chain_pause_event.clear()

        th = threading.Thread(target=self._chain_worker, args=(key,), daemon=True)
        self.state.chain_thread = th
        th.start()
        self._after(0, self._update_status)

    def stop_chain(self, force: bool = False) -> None:
        if not self.state.chain_running and not force:
            return
        self.state.chain_stop_event.set()
        self.state.chain_pause_event.clear()
        self.state.chain_running = False
        self.state.chain_paused = False
        self.state.chain_key = None

    def _chain_worker(self, key: str) -> None:
        key = normalize_key_name(key)

        while not self.state.chain_stop_event.is_set():
            if self.state.chain_pause_event.is_set():
                time.sleep(0.05)
                continue

            trig = self._find_trigger(key)
            if not trig:
                break
            actions = trig.get("actions", [])
            if not actions:
                break

            with self.state.lock:
                idx = int(self.state.indices.get(key, 0) or 0)

            if idx >= len(actions):
                idx = 0
                with self.state.lock:
                    self.state.indices[key] = 0

            action = actions[idx]
            self._perform_action(action)

            with self.state.lock:
                self.state.indices[key] = idx + 1
                done = (self.state.indices[key] >= len(actions))

            self._after(0, lambda k=key: self._select_trigger(k))

            if done:
                self.state.chain_stop_event.set()
                break

            time.sleep(0.01)

        self._after(
            0,
            self._finish_chain,
        )

    def _finish_chain(self) -> None:
        self.state.chain_running = False
        self.state.chain_paused = False
        self.state.chain_key = None
        self.state.chain_stop_event.clear()
        self.state.chain_pause_event.clear()
        self._update_status()
        self._refresh_actions()

    def is_chain_running(self) -> bool:
        return bool(self.state.chain_running)

    def refresh_status(self) -> None:
        self._update_status()

    def set_hooks(self, *, after: Callable[[int, Callable[..., None]], Any] | None = None) -> None:
        if after is not None:
            self._after = after
