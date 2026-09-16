"""モーダルウィンドウの grab 取得と破棄時の復元。"""

import tkinter as tk

_active_modals: list[tk.Toplevel] = []
_custody_window: tk.Toplevel | None = None
_app_minimized: bool = False


def install_minimize_grab_custody(app: tk.Misc) -> None:
    """App の最小化中だけ非表示の保持者から grab を預かる。"""
    def take_custody(event: tk.Event) -> None:
        global _custody_window, _app_minimized
        if event.widget is not app:
            return
        _app_minimized = True
        if _custody_window is not None:
            return
        try:
            holder = app.grab_current()
        except (tk.TclError, KeyError):
            return
        if holder is None:
            return
        try:
            if not holder.winfo_exists() or holder.winfo_viewable():
                return
            holder.grab_release()
        except tk.TclError:
            return
        _custody_window = holder

    def return_custody(event: tk.Event) -> None:
        global _custody_window, _app_minimized
        if event.widget is not app:
            return
        _app_minimized = False
        if _custody_window is None:
            return
        recorded = _custody_window
        _custody_window = None
        try:
            current = app.grab_current()
        except (tk.TclError, KeyError):
            return
        if current is not None:
            return
        # 記録窓を優先し、非表示・破棄済みなら台帳の最内から探す。
        for candidate in (recorded, *reversed(_active_modals)):
            try:
                if not candidate.winfo_exists() or not candidate.winfo_viewable():
                    continue
            except tk.TclError:
                continue
            try:
                candidate.grab_set()
            except tk.TclError:
                pass
            return

    app.bind("<Unmap>", take_custody, add="+")
    app.bind("<Map>", return_custody, add="+")


def grab_modal(window: tk.Toplevel, parent: tk.Misc | None = None) -> None:
    """window をモーダル化し、破棄されたら直前の grab 保持者へ戻す。

    初期化の最後に呼び、grab 取得後に初期化処理を残さないこと。
    本関数の呼び出しより前で例外が出た場合、子はまだ grab を取得しておらず、
    親が grab を保持したまま残る。
    """
    global _custody_window

    def current_holder() -> tk.Misc | None:
        try:
            return window.grab_current()
        except (tk.TclError, KeyError):
            # 終了中や tkinter 管理外の保持者は解決できないため、保持者なしと扱う。
            return None

    previous = current_holder()
    if previous is window or _custody_window is window:
        # 二重呼び出しでは最初の保持者と破棄ハンドラを維持する（預かり中の窓も同じ扱い）。
        return
    if previous is None and _custody_window is not None:
        previous = _custody_window
        _custody_window = None
    if parent is not None:
        window.transient(parent)
    window.grab_set()
    _active_modals.append(window)
    restored = False

    def restore_grab(event: tk.Event) -> None:
        global _custody_window
        nonlocal restored
        if event.widget is not window or restored:
            return
        restored = True
        for index, active_modal in enumerate(_active_modals):
            if active_modal is window:
                del _active_modals[index]
                break
        if previous is None:
            return
        current = current_holder()
        if current is not None and current is not window:
            return
        try:
            if previous.winfo_exists():
                if previous.winfo_viewable():
                    previous.grab_set()
                elif _app_minimized and _custody_window is None:
                    _custody_window = previous
        except tk.TclError:
            # アプリ終了中や確認後の破棄・非表示化では復元できないため終了を妨げない。
            pass

    window.bind("<Destroy>", restore_grab, "+")
