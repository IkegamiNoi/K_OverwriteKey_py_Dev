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

    def _always_on_top(self) -> bool:
        return bool(self.app.ui_vars.always_on_top_var.get())

    def apply_topmost(self) -> None:
        if self._window is not None:
            self._window.apply_topmost(self._always_on_top())

    def on_font_changed(self) -> None:
        if self._window is not None:
            self._window.on_font_changed()

    @property
    def window(self) -> HelpWindow | None:
        return self._window

    def open(self, tab: str) -> None:
        if self._window is None:
            self._create_window(self.app).select_tab(tab)
            return
        self._raise_window().select_tab(tab)

    def _create_window(self, master: tk.Misc) -> HelpWindow:
        self._window = HelpWindow(
            master, self.load_content(),
            # 呼び出し時に解決する（窓の寿命中に窓口が差し替わっても追従する）。
            suspend_hook=lambda: self.app.hook.suspend_hook_for_dialog(),
            resume_hook=lambda: self.app.hook.resume_hook_after_dialog(),
        )
        self._window.bind("<Destroy>", self._on_destroy, add="+")
        self.apply_topmost()
        return self._window

    def _raise_window(self) -> HelpWindow:
        assert self._window is not None
        self.apply_topmost()
        self._window.deiconify()
        self._window.lift()
        self._window.focus_set()
        return self._window

    def open_for_dialog(self, dialog: tk.Toplevel, tab: str, target_id: str) -> None:
        if self._window is not None and self._window.master is not dialog:
            self.close()
        window = (self._create_window(dialog) if self._window is None
                  else self._raise_window())
        window.select_tab(tab)
        window.clear_filter()
        window.reveal(tab, target_id)

    def close(self) -> None:
        if self._window is not None:
            self._window.destroy()

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is self._window:
            self._window = None
