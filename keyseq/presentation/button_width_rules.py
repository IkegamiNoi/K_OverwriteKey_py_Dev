"""文言が切り替わるボタンを最大文言幅で固定する幅（ttk の文字数単位）。

暫定仕様17 §3-3 に基づく。
"""

from typing import Sequence


def fixed_button_width_chars(text_widths: Sequence[int], zero_width: int) -> int:
    """最大文言幅を「0」の幅で割り、整数演算で切り上げる。"""
    if not text_widths:
        raise ValueError("text_widths must not be empty")
    if zero_width <= 0:
        raise ValueError("zero_width must be positive")
    return (max(text_widths) + zero_width - 1) // zero_width
