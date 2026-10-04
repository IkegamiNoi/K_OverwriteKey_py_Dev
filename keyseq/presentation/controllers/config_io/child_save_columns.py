"""子一覧ダイアログ専用の列幅・境界操作・初期サイズ。"""
from __future__ import annotations

from tkinter import font, ttk


HEADINGS = ("種別", "対象名", "保存先パス", "共有状況", "操作")
CELL_GAP = 8
OPENING_WIDTH = 960


class ChildSaveColumns:
    def __init__(self, dialog, header_frame, content, text_cells, scrollbar, overhead_width,
                 minimum_height, headers) -> None:
        self.dialog = dialog
        self.header_frame = header_frame
        self.content = content
        self.text_cells = text_cells
        self.overhead_width = overhead_width + scrollbar.winfo_reqwidth()
        self.minimum_height = minimum_height
        measure = font.nametofont("TkDefaultFont").measure
        self.minimums: list[int] = [measure(text) + CELL_GAP for text in HEADINGS]
        self.widths = self.minimums.copy()
        for cell in text_cells:
            column = cell["column"]
            if column != 2:
                self.widths[column] = max(self.widths[column], measure(cell["text"]) + CELL_GAP)
        self.widths[4] = max(self.minimums[4], content.grid_bbox(4, 0, 4, max(0, len(text_cells) // 4 - 1))[2])
        self._limit_name_width()
        self._shrink_to_screen()
        self._drag_start: tuple[int, int, int, int] | None = None
        self.handles: list[ttk.Frame] = []
        self._configure_columns()
        self._create_handles(headers)
        self.update_minimum_size()

    def _limit_name_width(self) -> None:
        # 対象名の上限は OPENING_WIDTH 基準の一覧幅の3割。
        cap = max(self.minimums[1], int((OPENING_WIDTH - self.overhead_width) * .3))
        self.widths[1] = min(self.widths[1], cap)

    def _shrink_to_screen(self) -> None:
        excess = self.minimum_width() - self.dialog.winfo_screenwidth()
        for column in (1, 3, 0):
            if excess <= 0:
                break
            reduction = min(excess, self.widths[column] - self.minimums[column])
            self.widths[column] -= reduction
            excess -= reduction

    def _configure_columns(self) -> None:
        for frame in (self.header_frame, self.content):
            for column, width in enumerate(self.widths):
                frame.columnconfigure(column, minsize=width, weight=1 if column == 2 else 0)

    def minimum_width(self) -> int:
        width = sum(self.widths[column] for column in (0, 1, 3, 4))
        return width + self.minimums[2] + self.overhead_width

    def update_minimum_size(self) -> None:
        self.dialog.minsize(self.minimum_width(), self.minimum_height)

    def _create_handles(self, headers) -> None:
        for column, header_column in ((0, 0), (1, 1), (3, 2)):
            handle = ttk.Frame(self.header_frame, cursor="sb_h_double_arrow")
            handle.bind("<ButtonPress-1>", lambda event, col=column: self._start_drag(event, col))
            handle.bind("<B1-Motion>", self._drag)
            handle.bind("<ButtonRelease-1>", self._end_drag)
            headers[header_column].bind(
                "<Configure>", lambda _event, h=handle, col=header_column: self._place_handle(h, col), add="+",
            )
            self.handles.append(handle)
            self._place_handle(handle, header_column)

    def _place_handle(self, handle, column: int) -> None:
        x, y, width, height = self.header_frame.grid_bbox(column, 0, column, 0)
        handle.place(x=x + width - 3, y=y, width=6, height=height)
        handle.lift()

    def _start_drag(self, event, column: int) -> str:
        path_width = self.header_frame.grid_bbox(2, 0, 2, 0)[2]
        self._drag_start = (event.x_root, column, self.widths[column], path_width)
        return "break"

    def _drag(self, event) -> str:
        if self._drag_start is None:
            return "break"
        start_x, column, start_width, path_width = self._drag_start
        delta = (event.x_root - start_x) * (-1 if column == 3 else 1)
        delta = max(self.minimums[column] - start_width, min(delta, path_width - self.minimums[2]))
        new_width = start_width + delta
        if new_width != self.widths[column]:
            self.widths[column] = new_width
            self._configure_columns()
            for cell in self.text_cells:
                if cell["column"] in (column, 2):
                    cell["last_fit_width"] = None
            self.update_minimum_size()
        return "break"

    def _end_drag(self, _event) -> str:
        self._drag_start = None
        return "break"


def _decoration_height(dialog) -> int:
    """上側のタイトルバー・枠に、下側の枠（横枠相当）を加える。"""
    top = max(0, dialog.winfo_rooty() - dialog.winfo_y())
    border = max(0, dialog.winfo_rootx() - dialog.winfo_x())
    return top + border


def size_action_dialog(dialog, frame, list_frame, header_frame, content, scrollbar,
                       headers, text_cells, row_count: int) -> None:
    dialog.update_idletasks()
    overhead_width = max(0, frame.winfo_reqwidth() - list_frame.winfo_reqwidth())
    overhead_height = max(0, frame.winfo_reqheight() - list_frame.winfo_reqheight())
    header_height = header_frame.grid_bbox(0, 0, 4, 0)[3]
    one_row_height = content.grid_bbox(0, 0, 4, 0)[3] if row_count else header_height
    minimum_height = header_height + one_row_height + overhead_height
    columns = ChildSaveColumns(dialog, header_frame, content, text_cells, scrollbar, overhead_width,
                               minimum_height, headers)
    dialog._child_save_columns = columns
    width = max(columns.minimum_width(), min(OPENING_WIDTH, dialog.winfo_screenwidth()))
    rows_height = content.grid_bbox(0, 0, 4, row_count - 1)[3] if row_count else 0
    full_height = header_height + rows_height + overhead_height
    limit = int(dialog.winfo_screenheight() * .6) - _decoration_height(dialog)
    height = max(minimum_height, min(full_height, limit))
    dialog.geometry(f"{width}x{height}")
    dialog.update_idletasks()
