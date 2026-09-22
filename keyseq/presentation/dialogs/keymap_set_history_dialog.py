from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont, messagebox, ttk
from typing import TYPE_CHECKING

from keyseq.presentation import keymap_set_history_text as text
from keyseq.presentation.modal import grab_modal

if TYPE_CHECKING:
    from keyseq.presentation.app import App
    from keyseq.presentation.controllers.config_io.keymap_set_history_io import KeymapSetHistoryIo

Node = tuple[str, str, int, str]


class KeymapSetHistoryDialog(tk.Toplevel):
    def __init__(self, parent: App, *, controller: KeymapSetHistoryIo):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.parent.hook.suspend_hook_for_dialog(self)
        self.title(text.TITLE)
        self._nodes: dict[str, Node] = {}
        self._read_only = False
        self._build_widgets()
        self._redraw()
        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        grab_modal(self, parent, focus=self.tree)

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        self.notice = ttk.Label(frame, text=text.READ_ONLY_NOTICE)
        self.notice.pack(anchor="w")
        listing = ttk.Frame(frame)
        listing.pack(fill="both", expand=True)
        default_font = tkfont.nametofont("TkDefaultFont")
        style = ttk.Style(self)
        style.configure("Treeview", font=default_font, rowheight=default_font.metrics("linespace") + 6)
        style.configure("Treeview.Heading", font=default_font)
        self.tree = ttk.Treeview(listing, columns=("path",), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text=text.NAME_HEADING)
        self.tree.heading("path", text=text.PATH_HEADING)
        # 枠の拡縮はパス列だけに配分する（名前列の幅は列境界のドラッグで変える）。
        self.tree.column("#0", width=240, minwidth=80, stretch=False)
        self.tree.column("path", width=400, minwidth=120, stretch=True)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(listing, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._update_buttons)
        self.tree.bind("<Double-1>", self._load)
        self._build_actions(frame)

    def _build_actions(self, frame: ttk.Frame) -> None:
        edits = ttk.Frame(frame)
        edits.pack(fill="x", pady=(8, 0))
        ttk.Label(edits, text=text.CATEGORY_LABEL).pack(side="left")
        self.category_name = tk.StringVar(self)
        self.category_entry = ttk.Entry(edits, textvariable=self.category_name)
        self.category_entry.pack(side="left", fill="x", expand=True)
        self.buttons: dict[str, ttk.Button] = {}
        for label, command in (
            (text.ADD_CATEGORY, self._add_category),
            (text.RENAME_CATEGORY, self._rename_category),
            (text.REMOVE_CATEGORY, self._remove_category),
        ):
            self.buttons[label] = ttk.Button(edits, text=label, command=command)
            self.buttons[label].pack(side="left", padx=3)
        actions = ttk.Frame(frame)
        actions.pack(anchor="e", pady=(12, 0))
        for label, command in (
            (text.LOAD, self._load), (text.REMOVE_ENTRY, self._remove_entry),
            (text.COPY_ENTRY, self._copy_entry), (text.CLOSE, self.destroy),
        ):
            self.buttons[label] = ttk.Button(actions, text=label, command=command)
            self.buttons[label].pack(side="left", padx=3)

    def _selected(self) -> Node | None:
        selection = self.tree.selection()
        return self._nodes.get(selection[0]) if selection else None

    def _redraw(self) -> None:
        selected = self._selected()
        expanded = {self._nodes[iid]: bool(self.tree.item(iid, "open"))
                    for iid in self.tree.get_children()}
        history, status = self.controller.load_history()
        self._read_only = self.controller.is_read_only(status)
        if self._read_only:
            self.notice.pack(before=self.tree.master, anchor="w")
        else:
            self.notice.pack_forget()
        self.tree.delete(*self.tree.get_children())
        self._nodes.clear()
        root = self._insert("", ("recent_root", "", -1, ""), text.RECENT_NODE_LABEL, opened=True)
        self._insert_entries(root, "recent_entry", "", history["recent"])
        for category in history["categories"]:
            name = category["name"]
            root = self._insert("", ("category", name, -1, ""), name)
            self._insert_entries(root, "category_entry", name, category["entries"])
        for iid, node in self._nodes.items():
            if node in expanded:
                self.tree.item(iid, open=expanded[node])
            if node == selected:
                self.tree.selection_set(iid)
                self.tree.focus(iid)
        self._update_buttons()

    def _insert(self, parent: str, node: Node, label: str, *, opened: bool = False) -> str:
        iid = self.tree.insert(parent, "end", text=label, values=(node[3],), open=opened)
        self._nodes[iid] = node
        return iid

    def _insert_entries(self, root: str, kind: str, name: str, entries: list[dict[str, str]]) -> None:
        for index, entry in enumerate(entries):
            path = entry["path"]
            label = text.format_entry_name(path, exists=self.controller.entry_exists(path))
            self._insert(root, (kind, name, index, path), label)

    def _update_buttons(self, _event=None) -> None:
        selected = self._selected()
        kind = selected[0] if selected else ""
        entry = kind in ("recent_entry", "category_entry")
        enabled = {
            text.LOAD: entry, text.CLOSE: True,
            text.ADD_CATEGORY: not self._read_only,
            text.RENAME_CATEGORY: kind == "category" and not self._read_only,
            text.REMOVE_CATEGORY: kind == "category" and not self._read_only,
            text.REMOVE_ENTRY: entry and not self._read_only,
            text.COPY_ENTRY: kind == "recent_entry" and not self._read_only,
        }
        for label, button in self.buttons.items():
            button.state(["!disabled" if enabled[label] else "disabled"])
        self.category_entry.state(["disabled" if self._read_only else "!disabled"])

    def _load(self, _event=None) -> None:
        selected = self._selected()
        if selected and selected[0] in ("recent_entry", "category_entry"):
            if self.controller.open_keymap_set(selected[3]):
                self.destroy()
            else:
                self._redraw()

    def _finish_edit(self, result: tuple[bool, str]) -> None:
        success, reason = result
        self._redraw()
        if not success:
            messagebox.showinfo(text.TITLE, reason, parent=self)

    def _add_category(self) -> None:
        if not self._read_only:
            self._finish_edit(self.controller.add_category(self.category_name.get()))

    def _rename_category(self) -> None:
        selected = self._selected()
        if not self._read_only and selected and selected[0] == "category":
            self._finish_edit(self.controller.rename_category(selected[1], self.category_name.get()))

    def _remove_category(self) -> None:
        selected = self._selected()
        if not self._read_only and selected and selected[0] == "category":
            if messagebox.askyesno(text.TITLE, text.confirm_remove_category(selected[1]), parent=self):
                self._finish_edit(self.controller.remove_category(selected[1]))

    def _remove_entry(self) -> None:
        selected = self._selected()
        if self._read_only or not selected or selected[0] not in ("recent_entry", "category_entry"):
            return
        kind, name, index, path = selected
        if messagebox.askyesno(text.TITLE, text.confirm_remove_entry(path), parent=self):
            result = (self.controller.remove_recent(index) if kind == "recent_entry"
                      else self.controller.remove_category_entry(name, index))
            self._finish_edit(result)

    def _copy_entry(self) -> None:
        selected = self._selected()
        if self._read_only or not selected or selected[0] != "recent_entry":
            return
        history, status = self.controller.load_history()
        if self.controller.is_read_only(status):
            self._redraw()
            return
        names = tuple(category["name"] for category in history["categories"])
        if not names:
            messagebox.showinfo(text.TITLE, text.NO_CATEGORIES, parent=self)
            return
        chooser = CategoryChooserDialog(self, names=names)
        chooser.wait_window()
        if chooser.result:
            self._finish_edit(self.controller.copy_to_category(chooser.result, selected[3]))


class CategoryChooserDialog(tk.Toplevel):
    def __init__(self, parent: KeymapSetHistoryDialog, *, names: tuple[str, ...]):
        super().__init__(parent)
        self.result: str = ""
        self.title(text.CHOOSER_TITLE)
        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(frame, exportselection=False)
        self.listbox.pack(fill="both", expand=True)
        for name in names:
            self.listbox.insert(tk.END, name)
        actions = ttk.Frame(frame)
        actions.pack(anchor="e", pady=(8, 0))
        ttk.Button(actions, text=text.OK, command=self._ok).pack(side="left")
        ttk.Button(actions, text=text.CANCEL, command=self.destroy).pack(side="left")
        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        grab_modal(self, parent, focus=self.listbox)

    def _ok(self) -> None:
        selected = self.listbox.curselection()
        if selected:
            self.result = self.listbox.get(selected[0])
            self.destroy()
