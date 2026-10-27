"""ライセンス本文を表示する非モーダル窓と管理役。"""

import tkinter as tk
from tkinter import ttk

from keyseq.presentation.help.third_party import load_license_text, load_third_party


class LicenseWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("ライセンス")
        width = min(720, self.winfo_screenwidth())
        height = min(560, self.winfo_screenheight())
        self.geometry(f"{width}x{height}")
        self.minsize(420, 300)
        self._build_text()
        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build_text(self) -> None:
        frame = ttk.Frame(self, padding=8)
        frame.pack(fill="both", expand=True)
        self.text = tk.Text(frame, wrap="word", font="TkDefaultFont")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.text.insert("1.0", self._content())
        self.text.configure(state="disabled")

    @staticmethod
    def _content() -> str:
        lines = [
            "Key Replacer Sequencer",
            "Copyright (C) 2026 池上ノイ (Ikegami Noi)",
            "GNU General Public License v3",
            "",
            load_license_text() or "LICENSE を読み込めませんでした。",
        ]
        notices, error = load_third_party()
        if error:
            lines.extend(("", f"同梱物の一覧を読み込めませんでした。（{error}）"))
        else:
            lines.extend(("", "同梱物一覧"))
            lines.extend(
                f"{notice.entry.name} {notice.entry.version} — {notice.entry.license}"
                for notice in notices
            )
            for notice in notices:
                lines.extend(("", f"{notice.entry.name} {notice.entry.version}"))
                lines.append(
                    notice.text if notice.text is not None
                    else f"全文を読み込めませんでした。（{notice.error}）"
                )
        return "\n".join(lines)

    def apply_topmost(self, value: bool) -> None:
        self.attributes("-topmost", value)


class LicenseWindowController:
    def __init__(self, app: tk.Misc) -> None:
        self.app = app
        self._window: LicenseWindow | None = None

    @property
    def window(self) -> LicenseWindow | None:
        return self._window

    def open(self) -> LicenseWindow:
        if self._window is None:
            self._window = LicenseWindow(self.app)
            self._window.bind("<Destroy>", self._on_destroy, add="+")
        else:
            self._window.deiconify()
            self._window.lift()
            self._window.focus_set()
        self.apply_topmost()
        return self._window

    def close(self) -> None:
        if self._window is not None:
            self._window.destroy()

    def apply_topmost(self) -> None:
        if self._window is not None:
            self._window.apply_topmost(bool(self.app.ui_vars.always_on_top_var.get()))

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is self._window:
            self._window = None
