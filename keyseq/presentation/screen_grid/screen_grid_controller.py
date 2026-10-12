from __future__ import annotations

import logging

from keyseq.application.input_router import GridKeyAction
from keyseq.application.screen_grid_session import (
    GridRouteSnapshot, MonitorInfo, ScreenGridSession,
)
from keyseq.domain.screen_grid import monitor_identifier
from keyseq.infrastructure import win32_window
from .grid_overlay_window import GridOverlayWindow


_logger = logging.getLogger(__name__)


class ScreenGridController:
    """セッションと入力ゲートウェイ、UI スレッド上の窓をつなぐ。"""

    def __init__(self, app) -> None:
        self._app = app
        self._overlay = GridOverlayWindow(app)
        self.session = ScreenGridSession(
            list_monitors=self.list_monitors,
            cursor_position=app.input_gateway.cursor_position,
            move_cursor=app.input_gateway.move_cursor,
            click=app.input_gateway.click_at,
            on_view_changed=self._show_view,
        )
        self._failed_until_inactive = False
        self._failed_keymap_id = ""
        self._sync_keymap_id = ""

    @staticmethod
    def list_monitors() -> list[MonitorInfo]:
        return [MonitorInfo(monitor_identifier(*rect), rect, primary)
                for rect, primary in win32_window.list_monitor_rects()]

    def _show_view(self) -> None:
        self._overlay.show(self.session.view())

    def on_font_changed(self) -> None:
        """左上の文字の下地は描いた時点の寸法なので、フォントの変更で描き直す。"""
        try:
            self._show_view()
        except Exception as exc:
            # 描き直せず窓が無いまま suppress が続かないよう、他の失敗と同じく畳む（task_07）。
            self._abort_after_failure(exc)

    def snapshot(self) -> GridRouteSnapshot:
        return self.session.snapshot()

    def sync(self) -> None:
        hook = self._app.hook
        keymap = self._app.keymap_service.get_active_keymap(self._app.data) or {}
        keymap_id = keymap.get("id", "")
        grid_enabled = (
            isinstance(keymap.get("grid"), dict)
            and keymap["grid"].get("enabled") is True
        )
        active = bool(hook.hook_active and hook.custom_input_enabled
                      and hook.hook_suspend_count == 0 and grid_enabled)
        if not active or (self._failed_until_inactive and keymap_id != self._failed_keymap_id):
            self._failed_until_inactive = False
            self._failed_keymap_id = ""
        self._sync_keymap_id = keymap_id
        try:
            self.session.sync(
                keymap_id=keymap_id, grid=keymap.get("grid"),
                active=active and not self._failed_until_inactive,
            )
            self._show_view()
        except Exception as exc:
            self._abort_after_failure(exc)

    def handle(self, action: GridKeyAction) -> None:
        try:
            self.session.handle(action)
        except Exception as exc:
            self._abort_after_failure(exc)

    def _abort_after_failure(self, exc: Exception) -> None:
        self._failed_until_inactive = True
        self._failed_keymap_id = self._sync_keymap_id
        try:
            self.session.abort()
        except Exception:
            _logger.exception("枠の失敗後に状態を閉じられませんでした")
        self._report_error(exc)

    def _report_error(self, exc: Exception) -> None:
        _logger.exception("枠の操作に失敗しました")
        self._app._set_flash_message(f"枠の操作に失敗しました: {exc}")

    def shutdown(self) -> None:
        self._overlay.destroy()
