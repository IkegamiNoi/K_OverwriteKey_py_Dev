"""Text のタグで開閉・絞り込みを表示するヘルプの一タブ。"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

from keyseq.presentation.help.help_content import HelpCategory, HelpItem, item_plain_text
from keyseq.presentation.help.help_filter import highlight_ranges, item_matches

HIGHLIGHT_COLOR = "#fff19c"
BODY_INDENT = 36
BULLET = "・"


class HelpTabView(ttk.Frame):
    def __init__(self, master: tk.Misc, categories: tuple[HelpCategory, ...]) -> None:
        super().__init__(master)
        self.categories = categories
        self._open: set[str] = set()
        self._matches: set[str] = set()
        self._headings: dict[str, tuple[str, str]] = {}
        self._body_indices: dict[str, list[str]] = {}
        self._spans: dict[str, list[tuple[str, int, int]]] = {}
        self._selected: str | None = None
        self.no_matches = False
        self._heading_font = tkfont.Font(root=self, font="TkDefaultFont")
        self.text = tk.Text(self, wrap="char", font="TkDefaultFont", cursor="arrow",
                            exportselection=False, takefocus=True, padx=8, pady=8)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True)
        self._build_text()
        self._bind_actions()
        self.apply_filter(())

    def _build_text(self) -> None:
        self.text.tag_configure("highlight", background=HIGHLIGHT_COLOR)
        self.text.tag_configure("selected", underline=True)
        self._sync_fonts()
        for category in self.categories:
            self._insert_heading(category.id, category.title, 0)
            for item in category.items:
                self._insert_heading(item.id, item.title, 18)
                self._insert_body(item)
        # Body tags are created per item; raise the shared bullet margin above them.
        self.text.tag_raise("bullet")
        self.text.insert("end", "一致する項目はありません。\n", "no_matches")
        self.text.configure(state="disabled")

    def _insert_heading(self, identifier: str, title: str, indent: int) -> None:
        start = self.text.index("end-1c")
        tag = f"heading:{identifier}"
        self.text.insert("end", f"▶ {title}\n", tag)
        self.text.tag_configure(tag, lmargin1=indent, lmargin2=indent)
        if indent == 0:
            self.text.tag_configure(tag, font=self._heading_font, spacing1=6)
        self._headings[identifier] = (start, self.text.index("end-1c"))

    def _insert_body(self, item: HelpItem) -> None:
        tag = f"body:{item.id}"
        self.text.tag_configure(tag, lmargin1=BODY_INDENT, lmargin2=BODY_INDENT, spacing3=3)
        indices: list[str] = []
        parts = [(line, block.kind == "list")
                 for block in item.body
                 for line in ((block.text,) if block.kind == "p" else block.items)]
        for number, (part, bullet) in enumerate(parts):
            if number:
                indices.append(self.text.index("end-1c"))
                self.text.insert("end", "\n", tag)
            tags = (tag, "bullet") if bullet else (tag,)
            if bullet:
                self.text.insert("end", BULLET, tags)
            start = self.text.index("end-1c")
            self.text.insert("end", part, tags)
            indices.extend(self.text.index(f"{start}+{offset}c")
                           for offset in range(len(part)))
        indices.append(self.text.index("end-1c"))
        self.text.insert("end", "\n", tag)
        self._body_indices[item.id] = indices

    def _bind_actions(self) -> None:
        self.text.bind("<Button-1>", self._click)
        for key, step in (("Up", -1), ("Down", 1)):
            self.text.bind(f"<{key}>", lambda event, d=step: self._move(d))
        for key in ("Return", "space", "KP_Enter"):
            self.text.bind(f"<{key}>", self._toggle_selected)
        self.text.bind("<Control-c>", self._copy)
        self.text.bind("<Control-C>", self._copy)
        self.copy_menu = tk.Menu(self, tearoff=False)
        self.copy_menu.add_command(label="コピー", command=self._copy)
        self.text.bind("<Button-3>", self._context_menu)

    def apply_filter(self, terms: tuple[str, ...]) -> int:
        self._open.clear()
        self._matches.clear()
        self._spans.clear()
        self.text.tag_remove("highlight", "1.0", "end")
        for category in self.categories:
            for item in category.items:
                if item_matches((category.title, item.title, item_plain_text(item)), terms):
                    self._matches.add(item.id)
                    if terms:
                        self._open.update((category.id, item.id))
                        self._highlight(item, terms)
        self.no_matches = not self._matches
        self.text.tag_configure("no_matches", elide=not self.no_matches)
        self._refresh()
        return len(self._matches)

    def on_font_changed(self) -> None:
        # TkDefaultFont is a named font; rebind it without rebuilding tags or text state.
        self.text.configure(font="TkDefaultFont")
        self._sync_fonts()

    def _sync_fonts(self) -> None:
        base = tkfont.nametofont("TkDefaultFont", root=self)
        self._heading_font.configure(**base.actual())
        self._heading_font.configure(weight="bold")
        # Hanging indent: wrapped lines of a bullet start under the text, not the bullet.
        self.text.tag_configure("bullet", lmargin2=BODY_INDENT + base.measure(BULLET))

    def reveal(self, target_id: str) -> bool:
        for category in self.categories:
            identifiers = {category.id, *(item.id for item in category.items)}
            if target_id in identifiers:
                self._open.update((category.id, target_id))
                self._selected = target_id
                self._refresh()
                self.text.yview(self._headings[target_id][0])
                return True
        return False

    def _highlight(self, item: HelpItem, terms: tuple[str, ...]) -> None:
        spans: list[tuple[str, int, int]] = []
        for field, value in (("title", item.title), ("body", item_plain_text(item))):
            for start, end in highlight_ranges(value, terms):
                spans.append((field, start, end))
                if field == "title":
                    origin = self._headings[item.id][0]
                    first, last = f"{origin}+{start + 2}c", f"{origin}+{end + 2}c"
                else:
                    indices = self._body_indices[item.id]
                    first = indices[start]
                    last = self.text.index(f"{indices[end - 1]}+1c")
                self.text.tag_add("highlight", first, last)
        self._spans[item.id] = spans

    def _refresh(self) -> None:
        self.text.configure(state="normal")
        for category in self.categories:
            visible = self._category_visible(category)
            self._show_heading(category.id, visible)
            for item in category.items:
                shown = self.is_item_visible(item.id) and self.is_category_open(category.id)
                self._show_heading(item.id, shown)
                self.text.tag_configure(f"body:{item.id}",
                                        elide=not (shown and self.is_item_open(item.id)))
        self.text.configure(state="disabled")
        visible_ids = self._visible_headings()
        if self._selected not in visible_ids:
            self._selected = visible_ids[0] if visible_ids else None
        self._mark_selected()

    def _show_heading(self, identifier: str, visible: bool) -> None:
        start, _end = self._headings[identifier]
        tag = f"heading:{identifier}"
        self.text.delete(start, f"{start}+1c")
        self.text.insert(start, "▼" if identifier in self._open else "▶", tag)
        self.text.tag_configure(tag, elide=not visible)

    def is_category_open(self, identifier: str) -> bool:
        return identifier in self._open

    def is_item_open(self, identifier: str) -> bool:
        return identifier in self._open

    def is_item_visible(self, identifier: str) -> bool:
        """分類の開閉とは独立した、絞り込みによる表示対象かを返す。"""
        return identifier in self._matches

    def highlight_spans(self, item_id: str) -> list[tuple[str, int, int]]:
        """title / body（item_plain_text）の元文字列上の半開区間。"""
        return list(self._spans.get(item_id, ()))

    def toggle(self, identifier: str) -> None:
        if identifier not in self._headings:
            raise KeyError(identifier)
        if identifier in self._open:
            self._open.remove(identifier)
        else:
            self._open.add(identifier)
        self._selected = identifier
        self._refresh()

    def _visible_headings(self) -> list[str]:
        result: list[str] = []
        for category in self.categories:
            if self._category_visible(category):
                result.append(category.id)
                if self.is_category_open(category.id):
                    result.extend(item.id for item in category.items if self.is_item_visible(item.id))
        return result

    def _category_visible(self, category: HelpCategory) -> bool:
        return (any(item.id in self._matches for item in category.items)
                or (not category.items and category.id in self._open))

    def _mark_selected(self) -> None:
        self.text.tag_remove("selected", "1.0", "end")
        if self._selected is not None:
            start, end = self._headings[self._selected]
            self.text.tag_add("selected", start, f"{end}-1c")

    def _move(self, step: int) -> str:
        headings = self._visible_headings()
        if headings:
            position = headings.index(self._selected) if self._selected in headings else 0
            self._selected = headings[max(0, min(position + step, len(headings) - 1))]
            self._mark_selected()
            self.text.see(self._headings[self._selected][0])
        return "break"

    def _toggle_selected(self, _event: tk.Event) -> str:
        if self._selected is not None:
            self.toggle(self._selected)
        return "break"

    def _click(self, event: tk.Event) -> None:
        self.text.focus_set()
        index = self.text.index(f"@{event.x},{event.y}")
        for identifier in self._visible_headings():
            start, end = self._headings[identifier]
            if self.text.compare(start, "<=", index) and self.text.compare(index, "<", end):
                self.toggle(identifier)
                break

    def _copy(self, _event: tk.Event | None = None) -> str:
        selection = self.text.tag_ranges("sel")
        if selection:
            value = self.text.get(selection[0], selection[1])
            self.text.clipboard_clear()
            self.text.clipboard_append(value)
        return "break"

    def _context_menu(self, event: tk.Event) -> str:
        self.text.focus_set()
        try:
            self.copy_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.copy_menu.grab_release()
        return "break"
