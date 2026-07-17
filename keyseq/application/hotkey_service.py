from __future__ import annotations

from typing import Callable

from keyseq.domain.hotkey import validate_hotkey_syntax


class HotkeyService:
    def __init__(self, *, validate_key_name: Callable[[str], None]) -> None:
        self._validate_key_name = validate_key_name

    def validate(self, hotkey: str) -> tuple[str, str]:
        """(エラーメッセージ, 正規化hotkey) を返す。App.validate_hotkey と同一契約。"""
        error_message, normalized, parts = validate_hotkey_syntax(hotkey)
        if error_message:
            return error_message, ""

        try:
            for p in parts:
                self._validate_key_name(p)
        except Exception as e:
            return f"不明なキー名があります: '{p}'（詳細: {e}）", ""

        return "", normalized
