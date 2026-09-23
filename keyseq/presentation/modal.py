"""モーダルウィンドウの grab 取得と破棄時の復元。"""

import ctypes
import ctypes.wintypes
from functools import cache
import tkinter as tk
from typing import Callable

_active_modals: list[tk.Toplevel] = []
_opened_while_minimized: list[tk.Toplevel] = []
_custody_window: tk.Toplevel | None = None
_app_minimized: bool = False


@cache
def _foreground_window_fn() -> Callable[[], int | None]:
    """共有 windll を変更せず、HWND を返す専用関数を生成する。"""
    function = ctypes.WinDLL("user32").GetForegroundWindow
    function.argtypes = []
    function.restype = ctypes.wintypes.HWND
    return function


def _is_app_foreground(app: tk.Misc) -> bool:
    """OS の前面窓が App のメイン窓である場合だけ真を返す。"""
    try:
        foreground = _foreground_window_fn()()
        return foreground is not None and foreground == int(app.wm_frame(), 16)
    except (AttributeError, OSError, tk.TclError, ValueError):
        # 取得不能（非 Windows を含む）ならフォーカスを強制しない。
        return False


def _restore_modal_focus(app: tk.Misc) -> None:
    """表示中の台帳内 grab 保持者へ最後のフォーカスを戻す。"""
    try:
        window = app.grab_current()
        if not any(active is window for active in _active_modals):
            return
        if any(opened is window for opened in _opened_while_minimized):
            return
        if not window.winfo_exists() or not window.winfo_viewable():
            return
        target = window.focus_lastfor() or window
        target.focus_set()
        if app.focus_get() is None and _is_app_foreground(app):
            target.focus_force()
    except (tk.TclError, KeyError):
        # 破棄中や tkinter 管理外の名前解決失敗は復元を妨げない。
        pass
    finally:
        _opened_while_minimized.clear()


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
        try:
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
        finally:
            app.after_idle(_restore_modal_focus, app)

    app.bind("<Unmap>", take_custody, add="+")
    app.bind("<Map>", return_custody, add="+")


def _apply_initial_focus(window: tk.Toplevel, focus: tk.Misc | None) -> None:
    target = window if focus is None else focus
    try:
        target.focus_set()
    except tk.TclError:
        # 破棄中の窓では TclError になるため、終了を妨げない。
        pass


def grab_modal(
    window: tk.Toplevel, parent: tk.Misc | None = None, *, focus: tk.Misc | None = None
) -> None:
    """window をモーダル化し、破棄されたら直前の grab 保持者へ戻す。

    初期化の最後に呼び、grab 取得後に初期化処理を残さないこと。
    初期フォーカスもここで設定する（省略時は窓自身）。
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
    _apply_initial_focus(window, focus)
    _active_modals.append(window)
    if _app_minimized:
        _opened_while_minimized.append(window)
    restored = False

    def restore_grab(event: tk.Event) -> None:
        global _custody_window
        nonlocal restored
        if event.widget is not window or restored:
            return
        restored = True
        for index, opened in enumerate(_opened_while_minimized):
            if opened is window:
                del _opened_while_minimized[index]
                break
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
            if previous.winfo_exists() and previous.winfo_viewable():
                previous.grab_set()
                return
        except tk.TclError:
            # アプリ終了中や確認後の破棄・非表示化では復元できないため終了を妨げない。
            pass

        if _app_minimized and _custody_window is None:
            _custody_window = previous

    window.bind("<Destroy>", restore_grab, "+")
