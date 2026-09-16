from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from keyseq.presentation.pane_width_rules import SASH_WIDTH
from keyseq.presentation.views.full_view.display_frame import FullDisplayFrame
from keyseq.presentation.views.full_view.file_frame import FileFrame
from keyseq.presentation.views.full_view.hook_frame import FullHookFrame
from keyseq.presentation.views.full_view.keymap_box import KeymapBox
from keyseq.presentation.views.full_view.sequence_box import SequenceBox
from keyseq.presentation.views.full_view.trigger_box import FullTriggerBox


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class FullView(ttk.Frame):
    """フル画面UI"""
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        # header
        self.header_area = ttk.Frame(self, padding=0)
        self.header_area.pack(fill="x", expand=False, pady=(12, 0))

        # フックラベルフレーム
        self.hook_frame = FullHookFrame(self.header_area, app)
        self.hook_frame.pack(side="left", fill="y")

        # 表示ラベルフレーム
        self.display_frame = FullDisplayFrame(self.header_area, app)
        self.display_frame.pack(side="left", fill="both", expand=True, padx=(12, 0))

        # ファイル操作（表示フレームの右側）
        self.file_frame = FileFrame(self.header_area, app)
        self.file_frame.pack(side="right", fill="y", padx=(12, 0))

        # main
        self.main_area = ttk.Frame(self)
        self.main_area.pack(fill="both", expand=True, pady=(12, 0))

        self.panes = tk.PanedWindow(
            self.main_area, orient="horizontal", borderwidth=0,
            sashwidth=SASH_WIDTH, sashpad=0, showhandle=False, sashrelief="flat",
        )
        background = ttk.Style(self).lookup(".", "background")
        if background:
            self.panes.configure(background=background)
        self.panes.pack(fill="both", expand=True)
        self.keymap_box = KeymapBox(self.panes, app)
        self.trigger_box = FullTriggerBox(self.panes, app)
        self.sequence_box = SequenceBox(self.panes, app)
        self.action_list = self.sequence_box.action_list
        self.panes.add(self.keymap_box, stretch="never")
        self.panes.add(self.trigger_box, stretch="always")
        self.panes.add(self.sequence_box, stretch="never")
