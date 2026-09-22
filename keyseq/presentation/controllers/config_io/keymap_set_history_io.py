from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Callable

from keyseq.application.config_service import contracts
from keyseq.domain import keymap_set_history as domain
from keyseq.presentation import keymap_set_history_text as text
from keyseq.presentation.dialogs import KeymapSetHistoryDialog
from .keymap_set_io import KEYMAP_SET_LOAD_OK

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

    def open_history_dialog(self) -> None:
        """履歴ダイアログを開く（メニューの入口）。"""
        dialog = KeymapSetHistoryDialog(self._app, controller=self)
        dialog.wait_window()

    def load_history(self) -> tuple[dict[str, Any], str]:
        """表示用の分類だけを名前順に整列する。"""
        try:
            history, status = self._app.config_service.load_keymap_set_history(
                config_root=self._app.config_root,
            )
            return {**history, "categories": domain.sorted_categories(history)}, status
        except Exception:
            return domain.normalize_history({}), contracts.HISTORY_READ_ONLY

    def is_read_only(self, status: str) -> bool:
        return status == contracts.HISTORY_READ_ONLY

    def entry_exists(self, stored_path: str) -> bool:
        try:
            path = self._app.config_service.resolve_config_path(
                stored_path, self._app.config_root,
            )
            return os.path.isfile(path)
        except Exception:
            return False

    def open_keymap_set(self, stored_path: str) -> bool:
        try:
            if not self._app.keymap_set_io.confirm_save_if_dirty(text.LOAD_ACTION):
                return False
            path = self._app.config_service.resolve_config_path(
                stored_path, self._app.config_root,
            )
            return self._app.keymap_set_io.load_keymap_set_path(path) == KEYMAP_SET_LOAD_OK
        except Exception as exc:
            self._app._set_flash_message(text.format_open_error(str(exc)), auto_clear=False)
            return False

    def _edit(
        self, transform: Callable[[dict[str, Any]], dict[str, Any] | None], reason: str,
    ) -> tuple[bool, str]:
        """永続化済みの履歴を変換し、保存できた場合だけ成功とする。"""
        try:
            history, status = self._app.config_service.load_keymap_set_history(
                config_root=self._app.config_root,
            )
            if status == contracts.HISTORY_READ_ONLY:
                return False, text.READ_ONLY_NOTICE
            updated = transform(history)
            if updated is None:
                return False, reason
            return self._app.config_service.save_keymap_set_history(
                updated, config_root=self._app.config_root,
            )
        except Exception as exc:
            return False, text.format_edit_error(str(exc))

    def add_category(self, name: str) -> tuple[bool, str]:
        return self._edit(lambda h: domain.add_category(h, name), text.INVALID_CATEGORY_NAME)

    def rename_category(self, old_name: str, new_name: str) -> tuple[bool, str]:
        return self._edit(
            lambda h: domain.rename_category(h, old_name, new_name), text.RENAME_REJECTED,
        )

    def remove_category(self, name: str) -> tuple[bool, str]:
        return self._edit(lambda h: domain.remove_category(h, name), text.CATEGORY_NOT_FOUND)

    def copy_to_category(self, name: str, stored_path: str) -> tuple[bool, str]:
        def key_of(path: str) -> str:
            return self._app.config_service.canonical_path(path, self._app.config_root)

        return self._edit(
            lambda h: domain.add_to_category(h, name, stored_path, key_of=key_of),
            text.COPY_REJECTED,
        )

    def remove_recent(self, index: int) -> tuple[bool, str]:
        return self._edit(lambda h: domain.remove_recent_at(h, index), text.ENTRY_NOT_FOUND)

    def remove_category_entry(self, name: str, index: int) -> tuple[bool, str]:
        return self._edit(
            lambda h: domain.remove_category_entry_at(h, name, index), text.ENTRY_NOT_FOUND,
        )
