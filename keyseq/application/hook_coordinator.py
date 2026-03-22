from __future__ import annotations

from typing import Callable, Sequence

from keyseq.domain.config import normalize_key_name


class HookCoordinator:
    def __init__(self, input_gateway):
        self.input_gateway = input_gateway
        self._input_event_hook_handle: object | None = None

    def start(
        self,
        triggers: Sequence[dict],
        on_input_event: Callable[[object], None] | None,
        on_error: Callable[[str, str], None],
        *,
        has_keymaps: bool = False,
    ) -> bool:
        if not self._can_process_input(triggers, on_error, has_keymaps=has_keymaps):
            return False

        self.stop()
        try:
            self.install_input_event_hook(on_input_event, on_error)
            return True
        except Exception as e:
            on_error("開始失敗", f"フックの開始に失敗しました。\n{e}")
            self.stop()
            return False

    def can_enable_custom_input(
        self,
        triggers: Sequence[dict],
        on_error: Callable[[str, str], None],
        *,
        has_keymaps: bool = False,
    ) -> bool:
        return self._can_process_input(triggers, on_error, has_keymaps=has_keymaps)

    def stop(self) -> None:
        self.uninstall_input_event_hook()

    def install_input_event_hook(
        self,
        on_input_event: Callable[[object], None] | None,
        on_error: Callable[[str, str], None],
    ) -> None:
        self.uninstall_input_event_hook()
        if on_input_event is None:
            return

        try:
            self._input_event_hook_handle = self.input_gateway.register_global_hook(
                on_input_event,
                suppress=True,
            )
        except Exception as e:
            self._input_event_hook_handle = None
            on_error("フック設定失敗", f"入力イベント監視の登録に失敗しました。\n\n{type(e).__name__}: {e}")

    def uninstall_input_event_hook(self) -> None:
        if self._input_event_hook_handle is None:
            return
        try:
            self.input_gateway.unregister_hook(self._input_event_hook_handle)
        except Exception:
            pass
        self._input_event_hook_handle = None

    def _can_process_input(
        self,
        triggers: Sequence[dict],
        on_error: Callable[[str, str], None],
        *,
        has_keymaps: bool,
    ) -> bool:
        if not triggers and not has_keymaps:
            on_error("開始できません", "トリガーが1件も登録されていません。")
            return False
        if self._has_usable_triggers(triggers) or has_keymaps:
            return True
        on_error("開始できません", "アクションが入っているトリガーがありません。")
        return False

    def _has_usable_triggers(self, triggers: Sequence[dict]) -> bool:
        for trigger in triggers:
            key = normalize_key_name(trigger.get("key", ""))
            actions = trigger.get("actions", [])
            if key and isinstance(actions, list) and len(actions) > 0:
                return True
        return False
