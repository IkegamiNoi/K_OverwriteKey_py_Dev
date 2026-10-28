"""絞り込み欄と二つのタブを持つ非モーダルのヘルプ窓。"""

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from keyseq.presentation.help.help_content import HelpLoadResult
from keyseq.presentation.help.help_filter import parse_query
from keyseq.presentation.help.help_tab_view import HelpTabView


class HelpWindow(tk.Toplevel):
    def __init__(
        self, master: tk.Misc, result: HelpLoadResult, *,
        suspend_hook: Callable[[], None], resume_hook: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._suspend_hook = suspend_hook
        self._resume_hook = resume_hook
        self._filter_hook_suspended = False
        self.title("ヘルプ")
        self.minsize(420, 300)
        width = min(720, self.winfo_screenwidth())
        height = min(560, self.winfo_screenheight())
        self.geometry(f"{width}x{height}")
        self.tabs: dict[str, HelpTabView] = {}
        self.notebook: ttk.Notebook | None = None
        self._build_filter()
        self._build_content(result)
        self.filter_entry.bind("<FocusIn>", self._on_filter_focus_in, add="+")
        self.filter_entry.bind("<FocusOut>", self._on_filter_focus_out, add="+")
        self.filter_entry.bind("<Destroy>", self._on_filter_destroy, add="+")
        self.bind("<Destroy>", self._on_window_destroy, add="+")
        self.filter_var.trace_add("write", self._filter_changed)
        self.bind("<Escape>", self._escape)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._focus_after_id: str | None = self.after_idle(self._initial_focus)
        self.bind("<Destroy>", self._cancel_initial_focus, add="+")

    def _build_filter(self) -> None:
        bar = ttk.Frame(self, padding=8)
        bar.pack(fill="x")
        ttk.Label(bar, text="絞り込み:").pack(side="left")
        self.filter_var = tk.StringVar(self)
        self.filter_entry = ttk.Entry(bar, textvariable=self.filter_var)
        self.filter_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.clear_button = ttk.Button(bar, text="×", width=3,
                                       command=lambda: self.filter_var.set(""))
        self.clear_button.pack(side="left")

    def _build_content(self, result: HelpLoadResult) -> None:
        if result.content is None:
            self.error_label = ttk.Label(
                self, text=f"ヘルプを読み込めませんでした。（{result.error}）",
                wraplength=400, padding=8,
            )
            self.error_label.pack(fill="both", expand=True)
            return
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        for name, label in (("guide", "主要機能"), ("faq", "QA")):
            view = HelpTabView(self.notebook, getattr(result.content, name))
            self.tabs[name] = view
            self.notebook.add(view, text=label)

    @property
    def filter_text(self) -> str:
        return self.filter_var.get()

    def select_tab(self, tab: str) -> None:
        if self.notebook is not None:
            self.notebook.select(self.tabs[tab])

    def clear_filter(self) -> None:
        self.filter_var.set("")

    def reveal(self, tab: str, target_id: str) -> bool:
        view = self.tabs.get(tab)
        return view.reveal(target_id) if view is not None else False

    def _on_filter_focus_in(self, _event: tk.Event) -> None:
        if not self._filter_hook_suspended:
            self._suspend_hook()
            self._filter_hook_suspended = True

    def _on_filter_focus_out(self, _event: tk.Event) -> None:
        self._resume_filter_hook()

    def _on_filter_destroy(self, event: tk.Event) -> None:
        if event.widget is self.filter_entry:
            self._resume_filter_hook()

    def _on_window_destroy(self, event: tk.Event) -> None:
        if event.widget is self:
            self._resume_filter_hook()

    def _resume_filter_hook(self) -> None:
        if self._filter_hook_suspended:
            self._filter_hook_suspended = False
            self._resume_hook()

    def on_font_changed(self) -> None:
        for view in self.tabs.values():
            view.on_font_changed()

    def apply_topmost(self, enabled: bool) -> None:
        self.attributes("-topmost", bool(enabled))

    def _filter_changed(self, *_args: str) -> None:
        terms = parse_query(self.filter_text)
        for name, label in (("guide", "主要機能"), ("faq", "QA")):
            if name in self.tabs and self.notebook is not None:
                count = self.tabs[name].apply_filter(terms)
                text = f"{label} ({count})" if terms else label
                self.notebook.tab(self.tabs[name], text=text)

    def _initial_focus(self) -> None:
        self._focus_after_id = None
        if self.winfo_exists():
            target = self.notebook if self.notebook is not None else self
            target.focus_set()

    def _cancel_initial_focus(self, event: tk.Event) -> None:
        if event.widget is self and self._focus_after_id is not None:
            self.after_cancel(self._focus_after_id)
            self._focus_after_id = None

    def _escape(self, _event: tk.Event) -> str:
        if self.focus_get() is self.filter_entry and self.filter_text:
            self.filter_var.set("")
        else:
            self.destroy()
        return "break"
