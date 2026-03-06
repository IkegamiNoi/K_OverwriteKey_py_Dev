from __future__ import annotations

from typing import Callable, Sequence

from keyseq.domain.config import normalize_key_name


class HookCoordinator:
    def __init__(self, input_gateway):
        self.input_gateway = input_gateway
        self._hook_handles: dict[str, object] = {}
        self._stop_hook_handle: object | None = None

    @property
    def hook_handles(self) -> dict[str, object]:
        return self._hook_handles

    @property
    def stop_hook_handle(self) -> object | None:
        return self._stop_hook_handle

    def start(
        self,
        triggers: Sequence[dict],
        on_key_event: Callable[[str], None],
        stop_key: str,
        on_stop: Callable[[], None],
        on_error: Callable[[str, str], None],
    ) -> bool:
        usable: list[tuple[str, bool]] = []
        for t in triggers:
            k = normalize_key_name(t.get("key", ""))
            acts = t.get("actions", [])
            if k and isinstance(acts, list) and len(acts) > 0:
                usable.append((k, bool(t.get("suppress", True))))

        if not triggers:
            on_error("開始できません", "トリガーが1件も登録されていません。")
            return False
        if not usable:
            on_error("開始できません", "アクションが入っているトリガーがありません。")
            return False

        self.stop()

        try:
            self.install_stop_hook(stop_key, on_stop, on_error)
            self._hook_handles = {}
            for k, suppress in usable:
                self._hook_handles[k] = self.input_gateway.register_key_hook(
                    k,
                    lambda _e, kk=k: on_key_event(kk),
                    suppress=suppress,
                )
            return True
        except Exception as e:
            on_error("開始失敗", f"フックの開始に失敗しました。\n{e}")
            self.stop()
            return False

    def install_stop_hook(self, key: str, on_stop: Callable[[], None], on_error: Callable[[str, str], None]) -> None:
        self._uninstall_stop_hook()
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

    def stop(self) -> None:
        for _k, h in list(self._hook_handles.items()):
            try:
                self.input_gateway.unregister_hook(h)
            except Exception:
                pass
        self._hook_handles = {}
        self.uninstall_stop_hook()

    def uninstall_stop_hook(self) -> None:
        if self._stop_hook_handle is None:
            return
        try:
            self.input_gateway.unregister_hook(self._stop_hook_handle)
        except Exception:
            pass
        self._stop_hook_handle = None
