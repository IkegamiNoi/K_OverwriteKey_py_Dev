from __future__ import annotations

from tkinter import ttk
from typing import TYPE_CHECKING

from keyseq.presentation.views.compact_view.display_frame import CompactDisplayFrame
from keyseq.presentation.views.compact_view.hook_frame import CompactHookFrame
from keyseq.presentation.views.compact_view.trigger_box import CompactTriggerBox


if TYPE_CHECKING:
    from keyseq.presentation.app import App


class CompactView(ttk.Frame):
    """省略画面UI（開始/停止、通常トリガーON/OFF、制御キー表示、ステータス、常に手前、フル復帰、トリガー一覧）"""
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        # 縦並びで “トリガー一覧程度の幅” を想定（geometryはApp側で調整）
        self.header_area = ttk.Frame(self, padding=0)
        self.header_area.pack(fill="x", expand=False, pady=(12, 0))

        # フックラベルフレーム
        self.hook_frame = CompactHookFrame(self.header_area, app)
        self.hook_frame.pack(side="top", fill="x", expand=False)

        self.display_frame = CompactDisplayFrame(self.header_area, app)
        self.display_frame.pack(side="top", fill="x", expand=False, pady=(8, 0))

        # トリガー一覧のみ
        self.main_area = ttk.Frame(self)
        self.main_area.pack(fill="both", expand=True, pady=(12, 0))
        self.trigger_box = CompactTriggerBox(self.main_area, app)
        self.trigger_list = self.trigger_box.trigger_list
        self.trigger_box.pack(side="top", fill="both", expand=True)
