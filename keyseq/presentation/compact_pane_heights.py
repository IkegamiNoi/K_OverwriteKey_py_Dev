"""省略表示の各ペインに割り当てる高さ（tkinter 非依存）。"""

COMPACT_SEQUENCE_VIEW_KEY = "compact_sequence_view"


def parse_compact_sequence_view(raw: object) -> tuple[bool, int | None]:
    """保存値の open と height を独立して検証する。"""
    if not isinstance(raw, dict):
        return True, None

    opened = raw.get("open")
    if not isinstance(opened, bool):
        opened = True

    height = raw.get("height")
    if isinstance(height, bool) or not isinstance(height, int) or height < 1:
        height = None
    return opened, height


def _shrink(
    height: int, floor: int, amount: int,
) -> tuple[int, int]:
    reduction = min(max(0, height - floor), amount)
    return height - reduction, amount - reduction


def plan_compact_heights(
    available_height: int,
    trigger_minimum: int,
    trigger_floor: int,
    sequence: tuple[int, int, int] | None,
    call: tuple[int, int, int] | None,
) -> tuple[int | None, int | None]:
    """希望高さを保ちつつ、規則順に表示高さを収める。

    sequence/call は (希望の高さ, 最小の高さ, 見出しの高さ)。
    """
    panes = [
        [max(desired, minimum), minimum, heading]
        for item in (sequence, call)
        if item is not None
        for desired, minimum, heading in (item,)
    ]
    available = max(0, available_height)
    trigger = available - sum(pane[0] for pane in panes)

    # 呼び出し先の枠、シーケンス欄の順に各最小まで縮める。
    deficit = max(0, trigger_minimum - trigger)
    for pane_index in (1, 0):
        if pane_index < len(panes):
            panes[pane_index][0], deficit = _shrink(
                panes[pane_index][0], panes[pane_index][1], deficit,
            )
    # 一覧を下限まで縮めても足りない分を、見出しを残して下段から詰める。
    excess = max(0, trigger_floor + sum(pane[0] for pane in panes) - available)
    for pane_index in (1, 0):
        if pane_index < len(panes):
            floor = min(panes[pane_index][1], panes[pane_index][2])
            panes[pane_index][0], excess = _shrink(
                panes[pane_index][0], floor, excess,
            )

    sequence_height = panes[0][0] if sequence is not None else None
    call_index = 1 if sequence is not None else 0
    call_height = panes[call_index][0] if call is not None else None
    return sequence_height, call_height
