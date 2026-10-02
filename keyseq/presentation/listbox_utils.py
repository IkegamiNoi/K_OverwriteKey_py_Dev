from __future__ import annotations

import tkinter as tk


_CLICK_SYNC_STATE_ATTR = "_listbox_click_selection_sync_state"


def bind_listbox_click_selection_sync(listbox: tk.Listbox, callback) -> None:
    """押下/解放を追跡し、クラスバインド後に選択同期を呼び出す。"""
    state = {"pressed": False, "after_id": None}
    setattr(listbox, _CLICK_SYNC_STATE_ATTR, state)

    def on_press(_event=None):
        state["pressed"] = True
        after_id = state["after_id"]
        if after_id is not None:
            try:
                listbox.after_cancel(after_id)
            except tk.TclError:
                pass
            state["after_id"] = None

    def on_release(_event=None):
        state["pressed"] = False

        def commit_selection():
            state["after_id"] = None
            try:
                if listbox.winfo_exists():
                    callback(listbox)
            except tk.TclError:
                return

        state["after_id"] = listbox.after_idle(commit_selection)

    listbox.bind("<ButtonPress-1>", on_press, add="+")
    listbox.bind("<ButtonRelease-1>", on_release, add="+")


def listbox_mouse_button_is_down(listbox: tk.Listbox) -> bool:
    """この一覧で左ボタンを押している間かを返す。"""
    state = getattr(listbox, _CLICK_SYNC_STATE_ATTR, None)
    return bool(state and state["pressed"])


def set_listbox_mouse_button_down(listbox: tk.Listbox, pressed: bool) -> None:
    """一覧の選択部品から、既存の押下中の印を更新する。"""
    state = getattr(listbox, _CLICK_SYNC_STATE_ATTR, None)
    if state is None:
        state = {"pressed": False, "after_id": None}
        setattr(listbox, _CLICK_SYNC_STATE_ATTR, state)
    state["pressed"] = pressed


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


def sync_listbox_selection_to_focus(
    root: tk.Misc,
    listbox: tk.Listbox,
    item_count: int,
    *,
    prefer_selection: bool = False,
) -> int | None:
    index = None
    if prefer_selection and item_count > 0:
        try:
            selection = listbox.curselection()
            if selection:
                selected_index = int(selection[0])
                if 0 <= selected_index < item_count:
                    index = selected_index
        except Exception:
            return None
    if index is None:
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
