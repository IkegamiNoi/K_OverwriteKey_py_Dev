from dataclasses import dataclass
from typing import Sequence


PANE_WIDTHS_KEY = "full_view_pane_widths"
MIN_LIST_CHARS = 10
DEFAULT_LIST_CHARS = 26


@dataclass(frozen=True)
class PaneWidths:
    """両端の枠の希望幅または表示幅を保持する（暫定仕様16 §3-5）。"""

    keymap: int
    sequence: int


@dataclass(frozen=True)
class MinWidths:
    """3 枠の最小幅を保持する（暫定仕様16 §3-4）。"""

    keymap: int
    trigger: int
    sequence: int


@dataclass(frozen=True)
class LayoutPlan:
    """表示幅とウィンドウ幅の最終値を保持する（暫定仕様16 §3-7）。"""

    keymap: int
    sequence: int
    window_min_width: int
    window_width: int


def parse_saved_pane_widths(raw: object) -> PaneWidths | None:
    """保存値を検証し、正の整数の希望幅だけを採用する（暫定仕様16 §3-6）。"""
    if not isinstance(raw, dict):
        return None
    keymap = raw.get("keymap")
    sequence = raw.get("sequence")
    for width in (keymap, sequence):
        if isinstance(width, bool) or not isinstance(width, int) or width < 1:
            return None
    return PaneWidths(keymap=keymap, sequence=sequence)


def list_row_width(
    char_width: int, chars: int, list_chrome: int, scrollbar_width: int
) -> int:
    """一覧の文字・枠線・スクロールバーの幅を合計する（暫定仕様16 §3-4）。"""
    return char_width * chars + list_chrome + scrollbar_width


def stacked_min_width(
    list_row: int, other_widths: Sequence[int], frame_chrome: int, title_width: int
) -> int:
    """縦並びの最も広い子と見出しから最小幅を求める（暫定仕様16 §3-4）。"""
    return max(max((list_row, *other_widths)) + frame_chrome, title_width)


def side_by_side_min_width(
    list_row: int,
    buttons_width: int,
    gap: int,
    frame_chrome: int,
    title_width: int,
) -> int:
    """横並びの合計幅と見出しから最小幅を求める（暫定仕様16 §3-4）。"""
    return max(list_row + buttons_width + gap + frame_chrome, title_width)


def default_pane_widths(
    main_width: int,
    keymap_req: int,
    trigger_req: int,
    sash_total: int,
    mins: MinWidths,
) -> PaneWidths:
    """現状の要求幅と残り幅から両端の既定幅を求める（暫定仕様16 §3-6）。"""
    return PaneWidths(
        keymap=max(keymap_req, mins.keymap),
        sequence=max(main_width - keymap_req - trigger_req - sash_total, mins.sequence),
    )


def drag_limits(
    total_width: int,
    own_min: int,
    other_side_width: int,
    trigger_min: int,
    sash_total: int,
) -> tuple[int, int]:
    """反対側の表示幅とトリガー最小幅を残す可動範囲を返す（暫定仕様16 §3-2）。"""
    return own_min, max(
        own_min, total_width - other_side_width - trigger_min - sash_total
    )


def clamp(value: int, lo: int, hi: int) -> int:
    """値を可動範囲へ収め、上限が下限未満なら下限を返す（暫定仕様16 §3-2）。"""
    return max(lo, min(value, hi))


def update_desired_after_drag(
    desired: PaneWidths, side: str, width_before: int, width_after: int
) -> PaneWidths:
    """表示幅が変化した側だけ希望幅を更新する（暫定仕様16 §3-5）。"""
    if side not in ("keymap", "sequence"):
        raise ValueError(f"Invalid pane side: {side!r}")
    if width_before == width_after:
        return desired
    if side == "keymap":
        return PaneWidths(keymap=width_after, sequence=desired.sequence)
    return PaneWidths(keymap=desired.keymap, sequence=width_after)


def resolve_layout(
    desired: PaneWidths,
    mins: MinWidths,
    sash_total: int,
    window_extra: int,
    current_window_width: int,
    screen_width: int,
) -> LayoutPlan:
    """画面超過時の縮小を反映した最終レイアウトを返す（暫定仕様16 §3-7）。"""
    keymap = max(desired.keymap, mins.keymap)
    sequence = max(desired.sequence, mins.sequence)
    required = keymap + sequence + mins.trigger + sash_total + window_extra
    if required > screen_width:
        sequence_reduction = min(required - screen_width, sequence - mins.sequence)
        sequence -= sequence_reduction
        required -= sequence_reduction
        keymap_reduction = min(required - screen_width, keymap - mins.keymap)
        keymap -= keymap_reduction
        required = keymap + sequence + mins.trigger + sash_total + window_extra
    return LayoutPlan(
        keymap=keymap,
        sequence=sequence,
        window_min_width=required,
        window_width=max(current_window_width, required),
    )
