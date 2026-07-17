from __future__ import annotations


def validate_hotkey_syntax(hotkey: str) -> tuple[str, str, list[str]]:
    """hotkey の文法を検証し (エラーメッセージ, 正規化hotkey, 要素リスト) を返す。

    エラーなしならエラーメッセージは ""。キー名の実在は検証しない（infrastructure の関心）。
    """
    s = (hotkey or "").strip()
    if not s:
        return "hotkey が空です。", "", []

    # split結果を保持して空要素を検出する（ctrl++c / +ctrl+c / ctrl+c+ を弾く）
    raw = s.split("+")
    parts = [p.strip().lower() for p in raw]

    if any(p == "" for p in parts):
        return "hotkey の '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。", "", []

    # ここで正規化（余分な空白・大文字を吸収）
    normalized = "+".join(parts)

    # 同一キーの重複を弾く（例: ctrl+ctrl+c）
    if len(set(parts)) != len(parts):
        return "hotkey に同じキーが重複しています（例: 'ctrl+ctrl+c'）。", "", []

    return "", normalized, parts
