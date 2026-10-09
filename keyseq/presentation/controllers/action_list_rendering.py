"""アクション一覧の表示文字列と背景色を組み立てる。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Callable

from keyseq.domain.config import format_action_list_item
from keyseq.domain.sequence_control import analyze_loops, loop_depth_style


_LOOP_DEPTH_COLORS: dict[tuple[str, str], str] = {
    ("blue", "light"): "#DCEBFF",
    ("green", "light"): "#DDF3DD",
    ("orange", "light"): "#FFEBD2",
    ("blue", "medium"): "#C2DBFF",
    ("green", "medium"): "#C4E8C4",
    ("orange", "medium"): "#FFDDB3",
    ("blue", "dark"): "#A8CBFF",
    ("green", "dark"): "#ABDDAB",
    ("orange", "dark"): "#FFCF94",
}


def build_action_rows(
    actions: Sequence[dict[str, Any]],
    *,
    loop_iterations: Mapping[int, int],
    counters: Mapping[str, int],
    resolve_call: Callable[[Any], tuple[str, str | None]] | None = None,
) -> list[tuple[str, str | None]]:
    """表示文字列と行ごとのループ背景色を返す。"""
    structure = analyze_loops(actions)
    rows = []
    for index, action in enumerate(actions):
        style = loop_depth_style(structure.depth[index])
        background = _LOOP_DEPTH_COLORS.get(style) if style is not None else None
        item_text = format_action_list_item(
            index,
            action,
            loop_iteration=loop_iterations.get(index),
            counters=counters,
            resolve_call=resolve_call,
        )
        rows.append((item_text, background))
    return rows


def format_next_action_summary(
    index: int,
    action: dict[str, Any],
    *,
    loop_iterations: Mapping[int, int],
    counters: Mapping[str, int],
    resolve_call: Callable[[Any], tuple[str, str | None]] | None = None,
) -> str:
    """省略表示の要約を作る。制御アクションは一覧と同じ値表示にする。"""
    action_kind = (action.get("type") or "").strip().lower()
    if action_kind in ("system", "file_line", "key_hold"):
        return format_action_list_item(
            index,
            action,
            loop_iteration=loop_iterations.get(index),
            counters=counters,
            resolve_call=resolve_call,
        )

    if action_kind == "mouse_click":
        x = action.get("x", "")
        y = action.get("y", "")
        button = action.get("button", "left")
        clicks = action.get("clicks", 1)
        return f"{index + 1:02d}. [mouse_click] ({x}, {y}) {button} x{clicks}"

    value = action.get("value", "")
    return f"{index + 1:02d}. [{action_kind}] {value}"
