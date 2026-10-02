"""Range selection and reorder previews for a Tk Listbox."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from keyseq.domain.list_editing import move_block
from keyseq.presentation.listbox_utils import set_listbox_mouse_button_down


def selected_range(listbox: tk.Listbox) -> tuple[int, int] | None:
    """Return the inclusive bounds of the current selection, if any."""
    selected = tuple(int(index) for index in listbox.curselection())
    return (min(selected), max(selected)) if selected else None


def select_range(
    listbox: tk.Listbox, start: int, end: int, *, active: int | None = None
) -> None:
    """Select a contiguous range and set its anchor and active row."""
    count = listbox.size()
    if count == 0:
        return
    start, end = sorted((max(0, min(start, count - 1)), max(0, min(end, count - 1))))
    active = end if active is None else max(0, min(active, count - 1))
    listbox.selection_clear(0, tk.END)
    listbox.selection_set(start, end)
    listbox.selection_anchor(start)
    listbox.activate(active)
    listbox.see(active)


class ListboxRangeDrag:
    """Own the selection gestures and temporary reorder preview of a Listbox."""

    _AUTO_SCROLL_MS = 100

    def __init__(
        self,
        listbox: tk.Listbox,
        on_move: Callable[[int, int, int], bool],
        on_commit: Callable[[tk.Listbox], None] | None,
        can_start_drag: Callable[[], bool] | None,
    ) -> None:
        self.listbox = listbox
        self.on_move = on_move
        self.on_commit = on_commit
        self.can_start_drag = can_start_drag or (lambda: True)
        self._press_row: int | None = None
        self._button_pressed = False
        self._anchor = self._original_anchor = self._original_active = 0
        self._dragging = False
        self._shift_gesture = False
        self._cancelled = False
        self._items: list[str] = []
        self._styles: list[dict[str, str]] = []
        self._start = self._end = self._target = 0
        self._auto_id: str | None = None
        self._commit_id: str | None = None
        self._arrow_id: str | None = None
        self._pointer_y: int | None = None
        self._bind()

    def _bind(self) -> None:
        box = self.listbox
        box.bind("<ButtonPress-1>", lambda event: self._begin_press(event, shift=False))
        box.bind("<B1-Motion>", self._motion)
        box.bind("<ButtonRelease-1>", self._release)
        box.bind("<B1-Leave>", self._break_event)
        box.bind("<B1-Enter>", self._break_event)
        box.bind("<Escape>", self._escape)
        box.bind("<Destroy>", self._on_destroy, add="+")
        box.bind("<Shift-ButtonPress-1>", lambda event: self._begin_press(event, shift=True))
        box.bind("<Shift-ButtonRelease-1>", self._release)
        box.bind("<Shift-Up>", lambda _event: self._shift_step(-1))
        box.bind("<Shift-Down>", lambda _event: self._shift_step(1))
        box.bind("<Up>", self._plain_arrow, add="+")
        box.bind("<Down>", self._plain_arrow, add="+")
        for sequence in ("<Control-slash>", "<Control-backslash>", "<Shift-Control-Home>",
                         "<Shift-Control-End>", "<Shift-Home>", "<Shift-End>"):
            box.bind(sequence, self._break_event)

    def _row_at(self, y: int) -> int | None:
        count = self.listbox.size()
        if count == 0 or y < 0 or y >= self.listbox.winfo_height():
            return None
        row = int(self.listbox.nearest(y))
        bounds = self.listbox.bbox(row)
        return row if bounds and bounds[1] <= y < bounds[1] + bounds[3] else None

    def _begin_press(self, event, *, shift: bool):
        self._cancel_timers()
        self._button_pressed = True
        self._press_row = None
        self._cancelled = self._dragging = False
        set_listbox_mouse_button_down(self.listbox, True)
        self.listbox.focus_set()
        row = self._row_at(event.y)
        if row is None:
            self._shift_gesture = shift
            return "break"
        self._press_row = row
        self._shift_gesture = shift
        selection = selected_range(self.listbox)
        self._anchor = int(self.listbox.index("anchor"))
        if shift:
            self._set_range(self._anchor, row, active=row)
        elif selection is None or not selection[0] <= row <= selection[1]:
            select_range(self.listbox, row, row, active=row)
            self._anchor = row
        self._original_anchor = int(self.listbox.index("anchor"))
        self._original_active = int(self.listbox.index(tk.ACTIVE))
        self._start, self._end = selected_range(self.listbox)
        return "break"

    def _set_range(self, anchor: int, row: int, *, active: int) -> None:
        select_range(self.listbox, min(anchor, row), max(anchor, row), active=active)
        self.listbox.selection_anchor(anchor)

    def _motion(self, event):
        self._pointer_y = event.y
        if self._press_row is None or self._cancelled:
            return "break"
        if self._shift_gesture:
            row = self._row_at(event.y)
            if row is not None:
                self._set_range(self._anchor, row, active=row)
            return "break"
        row = self._row_at(event.y)
        if not self._dragging and row is not None and row != self._press_row:
            if not self.can_start_drag():
                return "break"
            self._start_drag()
        if self._dragging:
            if row is not None:
                self._preview(row)
            self._schedule_autoscroll()
        return "break"

    def _start_drag(self) -> None:
        self._items = [str(self.listbox.get(i)) for i in range(self.listbox.size())]
        keys = ("background", "foreground", "selectbackground", "selectforeground")
        self._styles = [
            {key: self.listbox.itemcget(i, key) for key in keys}
            for i in range(self.listbox.size())
        ]
        self._target = self._start
        self._dragging = True

    def _preview(self, row: int) -> None:
        # Keep the pressed row at the same offset within the dragged block.
        pressed_row = self._press_row
        if pressed_row is None:
            return
        length = self._end - self._start + 1
        target = self._start + (row - pressed_row)
        target = max(0, min(target, len(self._items) - length))
        if target == self._target:
            return
        self._target = target
        order = list(range(len(self._items)))
        self._render_order(move_block(order, self._start, self._end, target))
        box = self.listbox
        box.selection_clear(0, tk.END)
        length = self._end - self._start + 1
        box.selection_set(target, target + length - 1)
        box.activate(target)
        box.selection_anchor(target)

    def _schedule_autoscroll(self) -> None:
        if self._auto_id is not None:
            return
        y = self._pointer_y
        if y is None or 0 <= y < self.listbox.winfo_height():
            return
        self._auto_id = self.listbox.after(self._AUTO_SCROLL_MS, self._autoscroll)

    def _autoscroll(self) -> None:
        self._auto_id = None
        if not self._dragging or self._pointer_y is None:
            return
        if 0 <= self._pointer_y < self.listbox.winfo_height():
            return
        direction = -1 if self._pointer_y < 0 else 1
        self.listbox.yview_scroll(direction, "units")
        row = int(self.listbox.nearest(0 if direction < 0 else self.listbox.winfo_height() - 1))
        self._preview(row)
        self._schedule_autoscroll()

    def _release(self, _event=None):
        if not self._button_pressed:
            return "break"
        self._button_pressed = False
        self._cancel_timers()
        set_listbox_mouse_button_down(self.listbox, False)
        if self._dragging:
            self._render_order(list(range(len(self._items))))
            changed = self._target != self._start
            self._dragging = False
            if changed:
                accepted = self.on_move(self._start, self._end, self._target)
                if not accepted:
                    self._restore_selection()
            else:
                self._restore_selection()
        elif self._cancelled:
            pass
        elif self._press_row is not None:
            if not self._shift_gesture:
                select_range(self.listbox, self._press_row, self._press_row)
            self._commit_later()
        self._press_row = None
        self._shift_gesture = False
        return "break"

    def _render_order(self, order: list[int]) -> None:
        box = self.listbox
        top = box.yview()[0]
        box.delete(0, tk.END)
        for index in order:
            box.insert(tk.END, self._items[index])
            box.itemconfigure(tk.END, **self._styles[index])
        box.yview_moveto(top)

    def _escape(self, _event=None):
        if not self._dragging:
            return None
        self._cancel_timers()
        self._render_order(list(range(len(self._items))))
        self._restore_selection()
        self._dragging = False
        self._cancelled = True
        return "break"

    def _cancel_timers(self) -> None:
        for attribute in ("_auto_id", "_commit_id", "_arrow_id"):
            timer_id = getattr(self, attribute)
            if timer_id is not None:
                try:
                    self.listbox.after_cancel(timer_id)
                except tk.TclError:
                    pass
                setattr(self, attribute, None)

    def _restore_selection(self) -> None:
        select_range(self.listbox, self._start, self._end, active=self._original_active)
        self.listbox.selection_anchor(self._original_anchor)

    def _on_destroy(self, event) -> None:
        if event.widget is self.listbox:
            self._cancel_timers()
            set_listbox_mouse_button_down(self.listbox, False)

    def _shift_step(self, delta: int) -> str:
        count = self.listbox.size()
        if count:
            active = int(self.listbox.index(tk.ACTIVE))
            target = active + delta
            if 0 <= target < count:
                anchor = int(self.listbox.index("anchor"))
                self._set_range(anchor, target, active=target)
        self._commit_later()
        return "break"

    def _plain_arrow(self, _event=None):
        if self._arrow_id is None:
            self._arrow_id = self.listbox.after_idle(self._sync_plain_arrow)

    def _sync_plain_arrow(self) -> None:
        self._arrow_id = None
        if not self.listbox.winfo_exists():
            return
        active = int(self.listbox.index(tk.ACTIVE))
        self.listbox.selection_anchor(active)

    def _commit_later(self) -> None:
        if self.on_commit is not None:
            if self._commit_id is not None:
                try:
                    self.listbox.after_cancel(self._commit_id)
                except tk.TclError:
                    pass
            self._commit_id = self.listbox.after_idle(self._commit_selection)

    def _commit_selection(self) -> None:
        self._commit_id = None
        if self.on_commit is not None and self.listbox.winfo_exists():
            self.on_commit(self.listbox)

    @staticmethod
    def _break_event(_event=None):
        return "break"


def bind_listbox_range_drag(
    listbox: tk.Listbox,
    *,
    on_move: Callable[[int, int, int], bool],
    on_commit: Callable[[tk.Listbox], None] | None = None,
    can_start_drag: Callable[[], bool] | None = None,
) -> ListboxRangeDrag:
    """Bind range selection and block dragging to one Listbox."""
    return ListboxRangeDrag(listbox, on_move, on_commit, can_start_drag)
