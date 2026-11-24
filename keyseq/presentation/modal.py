"""モーダルウィンドウの grab 取得と破棄時の復元。"""

import tkinter as tk
import logging
from collections.abc import Callable

from keyseq.infrastructure.os_backend import get_backend

_active_modals: list[tk.Toplevel] = []
_opened_while_minimized: list[tk.Toplevel] = []
_custody_window: tk.Toplevel | None = None
_app_minimized: bool = False
_hidden_by_minimize: list[tk.Toplevel] = []
_minimize_check_id: str | None = None
_restore_check_id: str | None = None
_modal_presence_listener: Callable[[], None] | None = None
_message_boxes: int = 0
_detached_transients: dict[tk.Toplevel, str] = {}
_reattach_transients_id: str | None = None
_REATTACH_DELAY_MS = 300


def set_modal_presence_listener(callback: Callable[[], None] | None) -> None:
    global _modal_presence_listener
    _modal_presence_listener = callback


def is_modal_active() -> bool:
    return bool(_active_modals) or _message_boxes > 0


def enter_message_box() -> None:
    global _message_boxes
    was_active = is_modal_active()
    _message_boxes += 1
    if was_active != is_modal_active():
        _notify_modal_presence_changed()


def leave_message_box() -> None:
    global _message_boxes
    was_active = is_modal_active()
    _message_boxes = max(0, _message_boxes - 1)
    if was_active != is_modal_active():
        _notify_modal_presence_changed()


def _notify_modal_presence_changed() -> None:
    if _modal_presence_listener is None:
        return
    try:
        _modal_presence_listener()
    except Exception:
        logging.getLogger(__name__).exception("Could not notify modal presence listener")


def _is_app_foreground(app: tk.Misc) -> bool:
    """OS の前面窓が App のメイン窓である場合だけ真を返す。"""
    try:
        backend = get_backend().window
        foreground = backend.foreground_own_window()
        return foreground is not None and foreground == backend.window_handle(app)
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


def _belongs_to_app(app: tk.Misc, window: tk.Misc) -> bool:
    try:
        parent = str(window.wm_transient())
        for _ in range(32):
            if not parent:
                return False
            if parent == str(app):
                return True
            parent = str(app.nametowidget(parent).wm_transient())
    except (tk.TclError, KeyError):
        return False
    return False


def _transient_depth(app: tk.Misc, window: tk.Misc) -> int | None:
    try:
        parent = str(window.wm_transient())
        for depth in range(1, 33):
            if not parent:
                return None
            if parent == str(app):
                return depth
            parent = str(app.nametowidget(parent).wm_transient())
    except (tk.TclError, KeyError):
        return None
    return None


def _deferred_check(app: tk.Misc) -> None:
    global _custody_window, _minimize_check_id
    _minimize_check_id = None
    if not _app_minimized or app.wm_state() != "iconic":
        return
    if _custody_window is not None:
        return
    backend = get_backend().window
    if backend.detaches_deep_transients_during_minimize():
        _detach_deep_transients(app)
    hidden_windows: list[tk.Toplevel] = []
    for window in reversed(tuple(_active_modals)):
        try:
            if not window.winfo_exists() or not _belongs_to_app(app, window):
                continue
            if window.winfo_viewable():
                window.withdraw()
                get_backend().window.order_out(window)
                hidden_windows.append(window)
            else:
                get_backend().window.order_out(window)
        except tk.TclError:
            continue
    _hidden_by_minimize.extend(reversed(hidden_windows))
    # 切り離した深い窓と隠した窓を、開いた順（表示し直す順）に並べる。
    opened_order = {id(window): index for index, window in enumerate(_active_modals)}
    _hidden_by_minimize.sort(key=lambda window: opened_order.get(id(window), len(opened_order)))
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


def _detach_deep_transients(app: tk.Misc) -> None:
    candidates = []
    for window in tuple(_active_modals):
        if window in _detached_transients:
            candidates.append((window, None, True))
        else:
            try:
                parent_name = str(window.wm_transient())
            except tk.TclError:
                continue
            depth = _transient_depth(app, window)
            candidates.append((window, parent_name, depth is not None and depth >= 3))
    for window, parent_name, should_detach in candidates:
        if not should_detach:
            continue
        try:
            if not window.winfo_exists():
                continue
            if parent_name is not None:
                _detached_transients[window] = parent_name
                window.wm_transient("")
            window.withdraw()
            if window not in _hidden_by_minimize:
                _hidden_by_minimize.append(window)
        except tk.TclError:
            _detached_transients.pop(window, None)


def _take_custody(app: tk.Misc, event: tk.Event) -> None:
    global _app_minimized, _minimize_check_id, _restore_check_id, _reattach_transients_id
    if event.widget is not app:
        return
    _app_minimized = True
    if _restore_check_id is not None:
        try:
            app.after_cancel(_restore_check_id)
        except tk.TclError:
            pass
        _restore_check_id = None
    if _reattach_transients_id is not None:
        try:
            app.after_cancel(_reattach_transients_id)
        except tk.TclError:
            pass
        _reattach_transients_id = None
    if _minimize_check_id is None:
        _minimize_check_id = app.after(0, lambda: _deferred_check(app))


def _return_custody(app: tk.Misc, event: tk.Event) -> None:
    global _app_minimized, _minimize_check_id, _restore_check_id
    if event.widget is not app:
        return
    _app_minimized = False
    if _minimize_check_id is not None:
        try:
            app.after_cancel(_minimize_check_id)
        except tk.TclError:
            pass
        _minimize_check_id = None
    if _restore_check_id is None:
        _restore_check_id = app.after(0, lambda: _deferred_return(app))


def _deferred_return(app: tk.Misc) -> None:
    global _restore_check_id, _reattach_transients_id
    _restore_check_id = None
    if _app_minimized or app.wm_state() == "iconic":
        return
    shown = []
    for window in tuple(_hidden_by_minimize):
        try:
            if window.winfo_exists():
                window.deiconify()
                shown.append(window)
        except tk.TclError:
            continue
    _hidden_by_minimize.clear()
    _return_grab(app, shown=tuple(shown))
    if _detached_transients:
        if _reattach_transients_id is not None:
            try:
                app.after_cancel(_reattach_transients_id)
            except tk.TclError:
                pass
        _reattach_transients_id = app.after(_REATTACH_DELAY_MS, lambda: _reattach_transients(app))


def _reattach_transients(app: tk.Misc) -> None:
    global _reattach_transients_id
    _reattach_transients_id = None
    if _app_minimized or app.wm_state() == "iconic":
        return
    for window, parent_name in tuple(_detached_transients.items()):
        try:
            if not window.winfo_exists():
                _detached_transients.pop(window, None)
                continue
            parent = app.nametowidget(parent_name)
            if not parent.winfo_exists():
                _detached_transients.pop(window, None)
                continue
            window.wm_transient(parent)
            if window.wm_state() == "withdrawn":
                window.deiconify()
            _detached_transients.pop(window, None)
        except (tk.TclError, KeyError):
            _detached_transients.pop(window, None)


def install_minimize_grab_custody(app: tk.Misc) -> None:
    """App の最小化中だけ非表示の保持者から grab を預かる。"""
    get_backend().window.install_minimize_preparation(app)
    app.bind("<Unmap>", lambda event: _take_custody(app, event), add="+")
    app.bind("<Map>", lambda event: _return_custody(app, event), add="+")


def _return_grab(app: tk.Misc, shown: tuple[tk.Misc, ...] = ()) -> None:
    global _custody_window
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
        for candidate in (recorded, *reversed(_active_modals)):
            try:
                if not candidate.winfo_exists():
                    continue
                if not any(candidate is window for window in shown) and not candidate.winfo_viewable():
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
    get_backend().window.disable_minimize_button(window)
    window.grab_set()
    _apply_initial_focus(window, focus)
    was_active = is_modal_active()
    _active_modals.append(window)
    if was_active != is_modal_active():
        _notify_modal_presence_changed()
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
        for index, hidden in enumerate(_hidden_by_minimize):
            if hidden is window:
                del _hidden_by_minimize[index]
                break
        was_active = is_modal_active()
        for index, active_modal in enumerate(_active_modals):
            if active_modal is window:
                del _active_modals[index]
                break
        if was_active != is_modal_active():
            _notify_modal_presence_changed()
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
