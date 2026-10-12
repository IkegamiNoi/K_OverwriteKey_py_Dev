from __future__ import annotations

from tkinter import font as tkfont


# 透過色（#ff00fe）と重ならない暗い色。
LABEL_BACKING = "#14141c"


def center_font_for_rect(rect) -> tuple[str, int, str]:
    x1, y1, x2, y2 = rect
    size = min(x2 - x1, y2 - y1)
    return ("Segoe UI", 24 if size >= 160 else 16 if size >= 80 else 10, "bold")


def corner_label_font(widget) -> tkfont.Font:
    """左上表示の文字: アプリの UI フォント（拡大縮小の設定込み・暫定 40 §7）。"""
    return tkfont.nametofont("TkDefaultFont", root=widget)


def draw_cell_label(canvas, rect, key, *, position, fill, center_font, corner_font) -> None:
    """余白を含めて収まるキーだけを、指定した位置に描く。"""
    x1, y1, x2, y2 = rect
    font = corner_font if position == "top_left" else center_font
    if not isinstance(font, tkfont.Font):
        font = tkfont.Font(root=canvas, font=font)
    width, height = font.measure(key), font.metrics("linespace")
    if width + 8 > x2 - x1 or height + 8 > y2 - y1:
        return
    if position == "top_left":
        # 下地は枠の線のすぐ内側（左上の角）に付ける。
        left, top = x1 + 3, y1 + 2
        # 小さい文字でも背景の画面の上で読めるよう、左上の文字の下に暗い下地を敷く（暫定 40 §7）。
        canvas.create_rectangle(x1 + 1, y1 + 1, left + width + 2, top + height + 1,
                                fill=LABEL_BACKING, outline="")
        canvas.create_text(left, top, text=key, fill=fill, font=font, anchor="nw")
    else:
        canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2,
                           text=key, fill=fill, font=font, anchor="center")
