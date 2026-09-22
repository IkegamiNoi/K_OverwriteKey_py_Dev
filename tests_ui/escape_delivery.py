"""Escape の実配送をフォーカス確保後に検証する UI テスト用ヘルパ。"""

import time
import tkinter as tk


def send_escape(test_case, app, dialog, *, attempts=20, timeout=2.0):
    """フォーカス確保・Escape 送信・破棄待ちの失敗を診断付きで通知する。"""
    started = time.monotonic()
    attempt = 0
    stage = "focus acquisition"
    try:
        for attempt in range(1, attempts + 1):
            dialog.focus_force()
            app.update()
            focused = app.focus_get()
            # パスの区切りまで比較し、似た名前の別ダイアログを除外する。
            if focused is not None and (
                focused is dialog or str(focused).startswith(f"{dialog}.")
            ):
                break
        else:
            raise TimeoutError("dialog did not acquire focus")

        stage = "Escape delivery"
        dialog.event_generate("<Escape>")
        app.update()

        stage = "dialog destruction"
        wait_started = time.monotonic()
        while dialog.winfo_exists():
            if time.monotonic() - wait_started >= timeout:
                raise TimeoutError("dialog was not destroyed before timeout")
            app.update()
        return
    except (tk.TclError, KeyError, TimeoutError) as exc:
        reason = f"{type(exc).__name__}: {exc}"

    # 破棄済みの Tk や未知のフォーカス先でも、元の失敗理由を失わない。
    diagnostics = {}
    for name, query in (
        ("focus_get", app.focus_get),
        ("focus_displayof", app.focus_displayof),
        ("winfo_exists", dialog.winfo_exists),
    ):
        try:
            diagnostics[name] = str(query())
        except (tk.TclError, KeyError) as exc:
            diagnostics[name] = f"{type(exc).__name__}: {exc}"
    test_case.fail(
        f"send_escape failed during {stage}: {reason}; "
        f"attempts={attempt}/{attempts}; elapsed={time.monotonic() - started:.3f}s; "
        f"timeout={timeout}s; {diagnostics}"
    )
