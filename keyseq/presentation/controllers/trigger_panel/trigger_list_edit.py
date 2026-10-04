"""Range operations for the full-view trigger list."""

from tkinter import messagebox

from keyseq.domain.config import normalize_key_name
from keyseq.domain.keymap_triggers import get_active_triggers
from keyseq.domain.list_editing import move_block, numbered_labels
from keyseq.presentation.list_clipboard import CLIP_TRIGGERS
from keyseq.presentation.listbox_range_drag import range_or_index
from keyseq.presentation.controllers.trigger_panel.effective_row_transition import (
    apply_effective_row_transition,
)


class TriggerListEditFlow:
    def __init__(self, trigger_panel) -> None:
        self._panel = trigger_panel
        self._app = trigger_panel._app

    @property
    def listbox(self):
        view = getattr(self._app, "full_view", None)
        box = getattr(view, "trigger_box", None)
        return getattr(box, "trigger_list", None)

    def selection_bounds(self) -> tuple[int, int] | None:
        triggers = get_active_triggers(self._app.data)
        return range_or_index(
            self.listbox,
            len(triggers),
            self._panel.selected_trigger_index(),
            compact=getattr(self._app, "_compact_mode", False),
        )

    def move_trigger_range(self, start: int, end: int, target_start: int) -> bool:
        triggers = get_active_triggers(self._app.data)
        after = move_block(triggers, start, end, target_start)
        if all(old is new for old, new in zip(triggers, after)):
            return True
        if not self._apply(triggers, after):
            return False
        target = max(0, min(target_start, len(triggers) - (end - start + 1)))
        self._finish((target, target + end - start))
        return True

    def delete_trigger_range(self) -> None:
        bounds = self.selection_bounds()
        if bounds is None:
            return
        start, end = bounds
        triggers = get_active_triggers(self._app.data)
        count = end - start + 1
        key = normalize_key_name(triggers[start].get("key", ""))
        question = (f"トリガー {count} 件を削除しますか？" if count > 1
                    else f"トリガー {key} を削除しますか？")
        if not messagebox.askyesno("確認", question):
            return
        after = triggers[:start] + triggers[end + 1:]
        if self._apply(triggers, after):
            index = min(self._panel.selected_trigger_index() or 0, len(after) - 1)
            self._finish((index, index) if after else None)

    def copy_triggers(self, _event=None) -> str:
        bounds = self.selection_bounds()
        if bounds is not None:
            start, end = bounds
            triggers = get_active_triggers(self._app.data)
            self._app.list_clipboard.copy(CLIP_TRIGGERS, triggers[start:end + 1])
        return "break"

    def paste_triggers(self, _event=None) -> str:
        items = self._app.list_clipboard.paste(CLIP_TRIGGERS)
        if not items:
            return "break"
        triggers = get_active_triggers(self._app.data)
        items = [{key: value for key, value in row.items() if not key.startswith("_")}
                 for row in items]
        labels = numbered_labels(
            [row.get("label", "") for row in items],
            [row.get("label", "") for row in triggers],
        )
        for row, label in zip(items, labels):
            row["label"] = label
        start = len(triggers)
        if self._apply(triggers, triggers + items):
            self._finish((start, len(triggers) - 1))
            for row in items:
                self._app.mark_sequence_dirty(row)
        return "break"

    def _apply(self, triggers: list, after: list) -> bool:
        return apply_effective_row_transition(
            self._app, triggers, after, lambda: triggers.__setitem__(slice(None), after),
        )

    def _finish(self, select: tuple[int, int] | None) -> None:
        self._panel.refresh_triggers(select=select)
        self._panel.refresh_actions()
        self._app.dirty_tracker.mark_trigger_set_dirty()
        if self._app.hook.hook_active:
            self._app.hook.start_hook()
