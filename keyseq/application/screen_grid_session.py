from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable

from keyseq.application.input_router import GridKeyAction
from keyseq.domain.screen_grid.geometry import Rect
from keyseq.domain.screen_grid import (
    FIXED_BACK_KEY, FIXED_CLICK_KEY, GRID_OPS, arrow_keys, can_subdivide, clamp_point,
    label_position_of, nudge_step, ops_of, rect_center, sub_cell_rects,
    sub_layout_of, top_cell_rects, top_layout_for,
)


@dataclass(frozen=True)
class MonitorInfo:
    id: str
    rect: Rect
    primary: bool


@dataclass(frozen=True)
class GridRouteSnapshot:
    visible: bool
    generation: int
    suppress_keys: frozenset[str]


@dataclass(frozen=True)
class GridView:
    visible: bool
    monitor: MonitorInfo | None
    level: int
    region: Rect | None
    cells: tuple[tuple[Rect, str], ...]
    selected: int | None
    generation: int
    label_position: str = "center"
    click_point: tuple[int, int] | None = None


class ScreenGridSession:
    def __init__(
        self, *, list_monitors: Callable[[], list[MonitorInfo]],
        cursor_position: Callable[[], tuple[int, int]],
        move_cursor: Callable[[int, int], None],
        click: Callable[[int, int, str], None],
        on_view_changed: Callable[[], None] | None = None,
    ) -> None:
        self._list_monitors = list_monitors
        self._cursor_position = cursor_position
        self._move_cursor = move_cursor
        self._click = click
        self._on_view_changed = on_view_changed
        self._visible = False
        self._generation = 0
        self._keymap_id = ""
        self._grid: dict | None = None
        self._monitors: list[MonitorInfo] = []
        self._monitor: MonitorInfo | None = None
        self._regions: list[Rect] = []
        self._selected: int | None = None
        self._click_point: tuple[int, int] | None = None
        self._suppress_keys: frozenset[str] = frozenset()
        self._snapshot = GridRouteSnapshot(False, 0, frozenset())

    def snapshot(self) -> GridRouteSnapshot:
        return self._snapshot

    def view(self) -> GridView:
        cells = self._current_cells() if self._visible else ()
        region = self._regions[-1] if self._regions else None
        return GridView(
            self._visible, self._monitor, max(0, len(self._regions) - 1),
            region, cells, self._selected, self._generation,
            label_position_of(self._grid), self._click_point,
        )

    def sync(self, *, keymap_id: str, grid: dict | None, active: bool) -> None:
        enabled = bool(active and isinstance(grid, dict) and grid.get("enabled") is True)
        same = enabled and self._visible and keymap_id == self._keymap_id and grid == self._grid
        if same:
            return
        if not enabled:
            if self._visible:
                self._generation += 1
                self._clear_state()
                self._publish_snapshot()
                self._changed()
            return
        monitors = self._list_monitors()
        if not monitors:
            if self._visible:
                self._generation += 1
                self._clear_state()
                self._publish_snapshot()
                self._changed()
            return
        selected_monitor = self._cursor_monitor(monitors)
        self._generation += 1
        self._visible = True
        self._keymap_id = keymap_id
        self._grid = deepcopy(grid)
        self._monitors = monitors
        self._set_monitor(selected_monitor)
        self._rebuild_suppression()
        self._publish_snapshot()
        self._changed()

    def abort(self) -> None:
        """Discard the current display state after a presentation failure."""
        self._generation += 1
        self._clear_state()
        self._publish_snapshot()
        self._changed()

    def handle(self, action: GridKeyAction) -> None:
        if not self._visible or action.generation != self._generation:
            return
        key = action.key
        for index, (rect, cell_key) in enumerate(self._current_cells()):
            if key == cell_key:
                if action.repeat:
                    return
                point = rect_center(rect)
                self._move_cursor(*point)
                self._click_point = point
                self._selected = index
                self._changed()
                return
        ops = ops_of(self._grid)
        operation = next((name for name in GRID_OPS if ops[name] == key), None)
        if operation is None:
            if key == FIXED_BACK_KEY:
                operation = "back"
            elif key == FIXED_CLICK_KEY:
                operation = "click"
        if operation is None:
            return
        if operation in ("deepen", "back", "next_screen"):
            if action.repeat:
                return
            if operation == "deepen":
                self._subdivide()
            elif operation == "back":
                if key == FIXED_BACK_KEY and len(self._regions) <= 1:
                    return
                self._back()
            else:
                self._next_monitor()
        elif operation == "click":
            if not action.repeat:
                self._click_action(action.shift)
        else:
            self._nudge(operation, action.shift)

    def _current_cells(self) -> tuple[tuple[Rect, str], ...]:
        if not self._monitor or not self._regions:
            return ()
        region = self._regions[-1]
        if len(self._regions) == 1:
            layout = top_layout_for(self._grid, self._monitor.id)
            return tuple(cell for row in top_cell_rects(region, layout) for cell in row)
        return tuple(sub_cell_rects(region, sub_layout_of(self._grid)))

    def _cursor_monitor(self, monitors: list[MonitorInfo]) -> MonitorInfo | None:
        if not monitors:
            return None
        x, y = self._cursor_position()
        return next((m for m in monitors if m.rect[0] <= x < m.rect[2]
                     and m.rect[1] <= y < m.rect[3]), None) or next(
                         (m for m in monitors if m.primary), monitors[0]
                     )

    def _set_monitor(self, monitor: MonitorInfo | None) -> None:
        self._monitor = monitor
        self._regions = [monitor.rect] if monitor else []
        self._selected = None
        self._click_point = None

    def _rebuild_suppression(self) -> None:
        keys = {key for monitor in self._monitors for row in top_cell_rects(
            monitor.rect, top_layout_for(self._grid, monitor.id)
        ) for _rect, key in row}
        keys.update(sub_layout_of(self._grid).keys)
        ops = ops_of(self._grid)
        keys.update(ops[name] for name in ("deepen", "back", "click", "next_screen"))
        keys.add(FIXED_CLICK_KEY)
        keys.difference_update({FIXED_BACK_KEY, *arrow_keys(ops)})
        self._suppress_keys = frozenset(keys)

    def _publish_snapshot(self) -> None:
        keys = set(self._suppress_keys) if self._visible else set()
        if self._visible:
            ops = ops_of(self._grid)
            arrows = arrow_keys(ops)
            if len(self._regions) > 1:
                keys.add(FIXED_BACK_KEY)
            if self._selected is not None:
                keys.update(arrows)
            frame_keys = {key for _rect, key in self._current_cells()}
            keys.update(frame_keys & ({FIXED_BACK_KEY} | arrows))
        self._snapshot = GridRouteSnapshot(
            self._visible, self._generation, frozenset(keys),
        )

    def _subdivide(self) -> None:
        if self._selected is None:
            return
        cells = self._current_cells()
        rect = cells[self._selected][0]
        sub = sub_layout_of(self._grid)
        if not can_subdivide(rect, sub):
            return
        self._regions.append(rect)
        self._selected = None
        self._click_point = None
        self._changed()

    def _back(self) -> None:
        if len(self._regions) <= 1:
            return
        child_region = self._regions[-1]
        parent_region = self._regions[-2]
        if len(self._regions) == 2:
            parent_cells = tuple(cell for row in top_cell_rects(
                parent_region, top_layout_for(self._grid, self._monitor.id)
            ) for cell in row)
        else:
            parent_cells = tuple(sub_cell_rects(parent_region, sub_layout_of(self._grid)))
        selected = next((i for i, (rect, _) in enumerate(parent_cells)
                         if rect == child_region), None)
        if selected is not None:
            point = rect_center(parent_cells[selected][0])
            self._move_cursor(*point)
            self._click_point = point
        else:
            self._click_point = None
        self._regions.pop()
        self._selected = selected
        self._changed()

    def _refresh_monitors(self) -> bool:
        monitors = self._list_monitors()
        if not monitors:
            raise RuntimeError("画面（モニタ）を取得できませんでした")
        if monitors != self._monitors:
            self._monitors = monitors
            self._rebuild_suppression()
            self._publish_snapshot()
        found = next((m for m in self._monitors if self._monitor and m.id == self._monitor.id), None)
        if found is not None:
            self._monitor = found
            return True
        selected_monitor = self._cursor_monitor(self._monitors)
        self._generation += 1
        self._set_monitor(selected_monitor)
        self._rebuild_suppression()
        self._publish_snapshot()
        self._changed()
        return False

    def _click_action(self, right: bool) -> None:
        if self._selected is None and len(self._regions) == 1:
            return
        if not self._refresh_monitors():
            return
        x, y = self._click_point or rect_center(self._regions[-1])
        self._move_cursor(x, y)
        self._click(x, y, "right" if right else "left")
        self._regions = [self._monitor.rect] if self._monitor else []
        self._selected = None
        self._click_point = None
        self._changed()

    def _next_monitor(self) -> None:
        if not self._refresh_monitors() or len(self._monitors) < 2:
            return
        index = next(i for i, m in enumerate(self._monitors) if m.id == self._monitor.id)
        self._monitor = self._monitors[(index + 1) % len(self._monitors)]
        self._regions = [self._monitor.rect]
        self._selected = None
        self._click_point = None
        self._changed()

    def _clear_state(self) -> None:
        self._visible = False
        self._keymap_id = ""
        self._grid = None
        self._monitors = []
        self._monitor = None
        self._regions = []
        self._selected = None
        self._click_point = None
        self._suppress_keys = frozenset()

    def _nudge(self, operation: str, fine: bool) -> None:
        if self._selected is None or self._click_point is None:
            return
        rect = self._current_cells()[self._selected][0]
        left, top, right, bottom = rect
        dx = nudge_step(right - left, fine) if operation in ("left", "right") else 0
        dy = nudge_step(bottom - top, fine) if operation in ("up", "down") else 0
        direction = -1 if operation in ("left", "up") else 1
        x, y = self._click_point
        point = clamp_point(rect, x + direction * dx, y + direction * dy)
        if point == self._click_point:
            return
        self._move_cursor(*point)
        self._click_point = point
        self._changed()

    def _changed(self) -> None:
        self._publish_snapshot()
        if self._on_view_changed:
            self._on_view_changed()
