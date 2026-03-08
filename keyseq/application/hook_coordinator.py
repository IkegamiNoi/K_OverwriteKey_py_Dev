from __future__ import annotations

from typing import Callable, Sequence

from keyseq.domain.config import normalize_key_name


class HookCoordinator:
    def __init__(self, input_gateway):
        self.input_gateway = input_gateway
        self._hook_handles: dict[str, object] = {}
        self._stop_hook_handle: object | None = None
        self._toggle_hook_handle: object | None = None

    @property
    def hook_handles(self) -> dict[str, object]:
        return self._hook_handles

    @property
    def stop_hook_handle(self) -> object | None:
        return self._stop_hook_handle

    @property
    def toggle_hook_handle(self) -> object | None:
        return self._toggle_hook_handle

    def start(
        self,
        triggers: Sequence[dict],
        on_key_event: Callable[[str], None],
        stop_key: str,
        on_stop: Callable[[], None],
        toggle_key: str,
        on_toggle: Callable[[], None],
        on_error: Callable[[str, str], None],
        *,
        enable_triggers: bool = True,
    ) -> bool:
        usable = self._collect_usable_triggers(triggers)
        if not self._validate_startable(triggers, usable, on_error):
            return False

        stop_key = normalize_key_name(stop_key)
        toggle_key = normalize_key_name(toggle_key)
        if not self._validate_control_key_conflicts(triggers, stop_key, toggle_key, on_error):
            return False

        self.stop()

        try:
            self.install_stop_hook(stop_key, on_stop, on_error)
            self.install_toggle_hook(toggle_key, on_toggle, on_error)
            if enable_triggers:
                self._register_trigger_hooks(usable, on_key_event)
            else:
                self._hook_handles = {}
            return True
        except Exception as e:
            on_error("開始失敗", f"フックの開始に失敗しました。\n{e}")
            self.stop()
            return False

    def enable_trigger_hooks(
        self,
        triggers: Sequence[dict],
        on_key_event: Callable[[str], None],
        on_error: Callable[[str, str], None],
    ) -> bool:
        usable = self._collect_usable_triggers(triggers)
        if not usable:
            on_error("有効化できません", "アクションが入っているトリガーがありません。")
            return False

        self.disable_trigger_hooks()
        try:
            self._register_trigger_hooks(usable, on_key_event)
            return True
        except Exception as e:
            self.disable_trigger_hooks()
            on_error("有効化失敗", f"通常トリガーの有効化に失敗しました。\n{e}")
            return False

    def disable_trigger_hooks(self) -> None:
        for _k, h in list(self._hook_handles.items()):
            try:
                self.input_gateway.unregister_hook(h)
            except Exception:
                pass
        self._hook_handles = {}

    def install_stop_hook(self, key: str, on_stop: Callable[[], None], on_error: Callable[[str, str], None]) -> None:
        self.uninstall_stop_hook()
        key = normalize_key_name(key)
        if not key:
            return

        try:
            self._stop_hook_handle = self.input_gateway.register_key_hook(
                key,
                lambda _e: on_stop(),
                suppress=True,
            )
        except Exception as e:
            self._stop_hook_handle = None
            on_error("フック設定失敗", f"停止トリガーの登録に失敗しました:\n{key}\n\n{type(e).__name__}: {e}")

    def install_toggle_hook(self, key: str, on_toggle: Callable[[], None], on_error: Callable[[str, str], None]) -> None:
        self.uninstall_toggle_hook()
        key = normalize_key_name(key)
        if not key:
            return

        try:
            self._toggle_hook_handle = self.input_gateway.register_key_hook(
                key,
                lambda _e: on_toggle(),
                suppress=True,
            )
        except Exception as e:
            self._toggle_hook_handle = None
            on_error("フック設定失敗", f"トグルキーの登録に失敗しました:\n{key}\n\n{type(e).__name__}: {e}")

    def stop(self) -> None:
        self.disable_trigger_hooks()
        self.uninstall_stop_hook()
        self.uninstall_toggle_hook()

    def uninstall_stop_hook(self) -> None:
        if self._stop_hook_handle is None:
            return
        try:
            self.input_gateway.unregister_hook(self._stop_hook_handle)
        except Exception:
            pass
        self._stop_hook_handle = None

    def uninstall_toggle_hook(self) -> None:
        if self._toggle_hook_handle is None:
            return
        try:
            self.input_gateway.unregister_hook(self._toggle_hook_handle)
        except Exception:
            pass
        self._toggle_hook_handle = None

    def _collect_usable_triggers(self, triggers: Sequence[dict]) -> list[tuple[str, bool]]:
        usable: list[tuple[str, bool]] = []
        for t in triggers:
            k = normalize_key_name(t.get("key", ""))
            acts = t.get("actions", [])
            if k and isinstance(acts, list) and len(acts) > 0:
                usable.append((k, bool(t.get("suppress", True))))
        return usable

    def _register_trigger_hooks(self, usable: Sequence[tuple[str, bool]], on_key_event: Callable[[str], None]) -> None:
        self._hook_handles = {}
        for k, suppress in usable:
            self._hook_handles[k] = self.input_gateway.register_key_hook(
                k,
                lambda _e, kk=k: on_key_event(kk),
                suppress=suppress,
            )

    def _validate_startable(
        self,
        triggers: Sequence[dict],
        usable: Sequence[tuple[str, bool]],
        on_error: Callable[[str, str], None],
    ) -> bool:
        if not triggers:
            on_error("開始できません", "トリガーが1件も登録されていません。")
            return False
        if not usable:
            on_error("開始できません", "アクションが入っているトリガーがありません。")
            return False
        return True

    def _validate_control_key_conflicts(
        self,
        triggers: Sequence[dict],
        stop_key: str,
        toggle_key: str,
        on_error: Callable[[str, str], None],
    ) -> bool:
        if stop_key and toggle_key and stop_key == toggle_key:
            on_error("開始できません", f"停止キーとトグルキーが重複しています:\n{stop_key}")
            return False

        trigger_keys = {
            normalize_key_name(t.get("key", ""))
            for t in triggers
            if normalize_key_name(t.get("key", ""))
        }
        if stop_key and stop_key in trigger_keys:
            on_error("開始できません", f"停止キーが通常トリガーと重複しています:\n{stop_key}")
            return False
        if toggle_key and toggle_key in trigger_keys:
            on_error("開始できません", f"トグルキーが通常トリガーと重複しています:\n{toggle_key}")
            return False
        return True

