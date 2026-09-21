from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keyseq.presentation.app import App


class KeymapSetHistoryIo:
    def __init__(self, app: App) -> None:
        self._app = app

    def record(self, path: str) -> tuple[bool, str]:
        """構成セットを開いた状態になったことを履歴へ記録する。"""
        try:
            return self._app.config_service.record_keymap_set_history(
                path, config_root=self._app.config_root,
            )
        except Exception as exc:
            return False, f"構成セットの履歴を記録できませんでした: {exc}"
