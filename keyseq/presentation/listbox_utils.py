from __future__ import annotations

import tkinter as tk


def focused_listbox_index(root: tk.Misc, listbox: tk.Listbox, item_count: int) -> int | None:
    """Listbox にフォーカスがある場合は active 行を、なければ選択行を返す。"""
    if item_count <= 0:
        return None
    try:
        if root.focus_get() is listbox:
            index = int(listbox.index(tk.ACTIVE))
            if 0 <= index < item_count:
                return index
        selection = listbox.curselection()
        if selection:
            index = int(selection[0])
            if 0 <= index < item_count:
                return index
    except Exception:
        return None
    return None


def sync_listbox_selection_to_focus(root: tk.Misc, listbox: tk.Listbox, item_count: int) -> int | None:
    index = focused_listbox_index(root, listbox, item_count)
    if index is None:
        return None
    try:
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(index)
        listbox.activate(index)
        listbox.see(index)
    except Exception:
        return None
    return index
