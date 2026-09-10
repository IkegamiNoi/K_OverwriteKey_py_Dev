"""モーダルウィンドウの grab 取得と破棄時の復元。"""

import tkinter as tk


def grab_modal(window: tk.Toplevel, parent: tk.Misc | None = None) -> None:
    """window をモーダル化し、破棄されたら直前の grab 保持者へ戻す。

    初期化の最後に呼ぶ。呼び出し後に初期化を続けて例外が出ても、
    破棄フックは自動で発火せず grab を握ったまま残るため、呼び出し側で
    子を破棄してから例外を再送出する必要がある。
    """
    def current_holder() -> tk.Misc | None:
        try:
            return window.grab_current()
        except (tk.TclError, KeyError):
            # 終了中や tkinter 管理外の保持者は解決できないため、保持者なしと扱う。
            return None

    previous = current_holder()
    if previous is window:
        # 二重呼び出しでは最初の保持者と破棄ハンドラを維持する。
        return
    if parent is not None:
        window.transient(parent)
    window.grab_set()
    restored = False

    def restore_grab(event: tk.Event) -> None:
        nonlocal restored
        if event.widget is not window or restored:
            return
        restored = True
        if previous is None:
            return
        current = current_holder()
        if current is not None and current is not window:
            return
        try:
            if previous.winfo_exists() and previous.winfo_viewable():
                previous.grab_set()
        except tk.TclError:
            # アプリ終了中や確認後の破棄・非表示化では復元できないため終了を妨げない。
            pass

    window.bind("<Destroy>", restore_grab)
