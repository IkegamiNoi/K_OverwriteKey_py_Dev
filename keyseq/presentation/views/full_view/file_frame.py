from __future__ import annotations

from tkinter import ttk
from keyseq.shared.i18n import tr
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class FileFrame(ttk.LabelFrame):
    def __init__(self, parent, app: App):
        super().__init__(parent, text=tr("view.file.title"), padding=(10, 6))

        ttk.Button(self, text=tr("common.save"), width=18, command=app.keymap_set_io.save_keymap_set).pack(fill="x", pady=(0, 4))
        ttk.Button(self, text=tr("common.save_as"), width=18, command=app.keymap_set_io.save_as).pack(fill="x", pady=4)
        ttk.Button(self, text=tr("common.load"), width=18, command=app.keymap_set_io.load_keymap_set_from).pack(fill="x", pady=4)

        ttk.Button(self, text=tr("menu.file.new"), width=18, command=app.keymap_set_io.new_config).pack(fill="x", pady=4)
