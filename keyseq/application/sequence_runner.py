from __future__ import annotations

from typing import Any, Callable

from keyseq.domain.config import DEFAULT_RUN_TO_END_DELAY_MS, coerce_nonnegative_int, normalize_key_name


class SequenceRunner:
    def __init__(
        self,
        *,
        state,
        find_trigger: Callable[[str], dict[str, Any] | None],
        perform_action: Callable[[dict[str, Any]], bool | None],
        select_trigger: Callable[[str], None],
        refresh_actions: Callable[[], None],
        update_status: Callable[[], None],
        after: Callable[[int, Callable[..., None]], Any],
        after_cancel: Callable[[Any], None],
        get_trigger_set_id: Callable[[], str] | None = None,
    ):
        self.state = state
        self._find_trigger = find_trigger
        self._perform_action = perform_action
        self._select_trigger = select_trigger
        self._refresh_actions = refresh_actions
        self._update_status = update_status
        self._after = after
        self._after_cancel = after_cancel
        self._get_trigger_set_id = get_trigger_set_id or (lambda: "")

    def _get_index(self, key: str) -> int:
        return int(self.state.indices_for(self._get_trigger_set_id()).get(key, 0) or 0)

    def _set_index(self, key: str, value: int) -> None:
        self.state.indices_for(self._get_trigger_set_id())[key] = int(value)

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
            i = self._get_index(key) % len(actions)
            if self._perform_action(actions[i]) is False:
                return
            with self.state.lock:
                self._set_index(key, (i + 1) % len(actions))
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

        delay = coerce_nonnegative_int(
            trig.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
            DEFAULT_RUN_TO_END_DELAY_MS,
        )

        i = self._get_index(key)
        if i < 0:
            i = 0

        if schedule_only:
            self.state.run_to_end_after_id = self._after(delay, self._run_to_end_step)
            return

        if i >= len(actions):
            self._set_index(key, 0)
            self.stop_run_to_end()
            self._select_trigger(key)
            return

        if self._perform_action(actions[i]) is False:
            self.stop_run_to_end()
            self._select_trigger(key)
            return
        self._set_index(key, i + 1)
        self._select_trigger(key)

        if self._get_index(key) >= len(actions):
            self._set_index(key, 0)
            self.stop_run_to_end()
            self._select_trigger(key)
            return

        self.state.run_to_end_after_id = self._after(delay, self._run_to_end_step)
