"""ヘルプ窓の単一インスタンスを管理する。"""

from collections.abc import Callable
import tkinter as tk

from keyseq.presentation.help.help_content import HelpLoadResult, load_help_content
from keyseq.presentation.help.help_window import HelpWindow


class HelpWindowController:
    def __init__(
        self, app: tk.Misc, *,
        load_content: Callable[[], HelpLoadResult] = load_help_content,
    ) -> None:
        self.app = app
        self.load_content = load_content
        self._window: HelpWindow | None = None

    @property
    def window(self) -> HelpWindow | None:
        return self._window

    def open(self, tab: str) -> None:
        if self._window is None:
            self._window = HelpWindow(self.app, self.load_content())
            self._window.bind("<Destroy>", self._on_destroy, add="+")
            self._window.select_tab(tab)
            return
        self._window.deiconify()
        self._window.lift()
        self._window.focus_set()
        self._window.select_tab(tab)

    def close(self) -> None:
        if self._window is not None:
            self._window.destroy()

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is self._window:
            self._window = None
