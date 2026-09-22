"""Escape の実配送をフォーカス確保後に検証する UI テスト用ヘルパ。"""

import time
import tkinter as tk


def _acquire_focus(app, dialog, focus_timeout, progress):
    """期限まで再試行し、待機中も Tk のイベントを処理する。"""
    deadline = time.monotonic() + focus_timeout
    while time.monotonic() < deadline:
        progress["attempts"] += 1
        dialog.focus_force()
        app.update()
        focused = app.focus_get()
        # パスの区切りまで比較し、似た名前の別ダイアログを除外する。
        if focused is not None and (
            focused is dialog or str(focused).startswith(f"{dialog}.")
        ):
            return
        retry_at = min(deadline, time.monotonic() + 0.01)
        while time.monotonic() < retry_at:
            app.update()
            remaining = retry_at - time.monotonic()
            if remaining > 0:
                time.sleep(min(0.001, remaining))
    raise TimeoutError("dialog did not acquire focus before deadline")


def send_escape(test_case, app, dialog, *, focus_timeout=2.0, timeout=2.0):
    """フォーカス確保・Escape 送信・破棄待ちの失敗を診断付きで通知する。"""
    started = time.monotonic()
    progress = {"attempts": 0}
    stage = "focus acquisition"
    try:
        _acquire_focus(app, dialog, focus_timeout, progress)

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
        f"attempts={progress['attempts']}; elapsed={time.monotonic() - started:.3f}s; "
        f"focus_timeout={focus_timeout}s; timeout={timeout}s; {diagnostics}"
    )
