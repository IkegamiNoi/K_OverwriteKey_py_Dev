"""ヘルプ窓と、前面のダイアログへの付け替えを管理する。"""

from collections.abc import Callable
import logging
import tkinter as tk

from keyseq.presentation import modal
from keyseq.presentation.help.grab_handoff import install_grab_handoff
from keyseq.presentation.help.help_content import HelpLoadResult, load_help_content
from keyseq.presentation.help.help_window import HelpWindow


class HelpWindowController:
    def __init__(
        self, app: tk.Misc, *,
        load_content: Callable[[], HelpLoadResult] = load_help_content,
    ) -> None:
        self.app = app
        self.load_content = load_content
        self._window: HelpWindow | None = None
        self._state: dict | None = None
        self._content: HelpLoadResult | None = None
        self._following = True
        self._restoring = False
        self._running = False
        self._follow_id: str | None = None
        self._save_id: str | None = None
        self._parent_destroyed = False
        self._orphan_parent: tk.Misc | None = None
        self._destroy_reasons: dict[HelpWindow, str] = {}

    def _owner(self) -> tk.Misc:
        return modal.front_modal() or self.app

    def _always_on_top(self) -> bool:
        return self.app.effective_always_on_top()

    def apply_topmost(self) -> None:
        if self._window is not None:
            self._window.apply_topmost(self._always_on_top())

    def on_font_changed(self) -> None:
        if self._window is not None:
            self._window.on_font_changed()

    @property
    def window(self) -> HelpWindow | None:
        return self._window

    def open(self, tab: str) -> None:
        window = self._open_for_owner(self._owner())
        if window is not None:
            self._raise_window().select_tab(tab)

    def _open_for_owner(self, owner: tk.Misc) -> HelpWindow | None:
        if self._window is None and not self._parent_destroyed:
            self._content = self.load_content()
        if self._window is None or self._window.master is not owner:
            self._replace(owner)
        if self._window is not None and self._window.master is owner:
            return self._window
        return None

    def _raise_window(self) -> HelpWindow:
        assert self._window is not None
        self.apply_topmost()
        window = self._window
        # Tk 9.1（macOS）は、この窓に deiconify すると TkWmMapWindow で落ちることがある（task_05 の probe）。
        # 最小化・非表示なら deiconify せず、控えから同じ持ち主の子として作り直して出す（§4.6「最小化を解除して前面へ出す」）。
        if window.wm_state() in ("iconic", "withdrawn"):
            window = self._recreate_shown(window)
        window.lift()
        window.focus_set()
        return window

    def _recreate_shown(self, window: HelpWindow) -> HelpWindow:
        self._save_state(window)
        if self._state is not None:
            self._state = {**self._state, "window_state": "normal"}
        self._replace(window.master)
        # 作り直せなかったときは古い窓が残る（§3.4）。
        return self._window if self._window is not None else window

    def open_for_dialog(self, dialog: tk.Toplevel, tab: str, target_id: str) -> None:
        window = self._open_for_owner(dialog)
        if window is not None:
            window = self._raise_window()
            window.select_tab(tab)
            window.clear_filter()
            window.reveal(tab, target_id)

    def on_modal_front_changed(self) -> None:
        if self._following and self._follow_id is None:
            self._follow_id = self.app.after_idle(self._follow)

    def _follow(self) -> None:
        self._follow_id = None
        if not self._following or self._running:
            return
        if self._window is None and not self._parent_destroyed:
            return
        if self._window is None and self._orphan_parent_alive():
            # 親は生きている = 親と一緒に消えたのではない（暫定 63 §3.5）。作り直さず控えを捨てる。
            self._forget_closed()
            return
        try:
            owner = self._owner()
            if self._window is None or self._window.master is not owner:
                self._replace(owner)
        except Exception:
            logging.getLogger(__name__).exception("Could not follow modal help owner")

    def _replace(self, owner: tk.Misc) -> None:
        if self._running:
            return
        old = self._window
        self._running = True
        replaced = False
        try:
            window = self._build(owner)
            # wait_visibility のイベントループ中の利用者の閉じ・終了を尊重する。
            if self._content is None or not self._following:
                self._destroy(window, "failed")
                return
            self._window = window
            replaced = True
            self._parent_destroyed = False
            self._orphan_parent = None
            if old is not None and old.winfo_exists():
                self._destroy(old, "replaced")
            self._save_state(window)
        except Exception:
            logging.getLogger(__name__).exception("Could not rebuild help window")
        finally:
            self._running = False
            if replaced:
                # 失敗したときは古い窓を残す（§3.4）ので、予約し直さない（し直すと失敗を繰り返す）。
                self._refollow_if_owner_changed()

    def _refollow_if_owner_changed(self) -> None:
        # 作り直しの最中（wait_visibility の間）に持ち主が変わると、その知らせは再入の防止で空振りする。
        window = self._window
        try:
            if self._following and window is not None and window.master is not self._owner():
                self.on_modal_front_changed()
        except tk.TclError:
            logging.getLogger(__name__).exception("Could not re-check help owner")

    def _build(self, owner: tk.Misc) -> HelpWindow:
        assert self._content is not None
        children = set(owner.winfo_children())
        self._restoring = True
        window: HelpWindow | None = None
        try:
            window = HelpWindow(
                # 控えが無い = 新しく開く（初期フォーカスを入れる）。作り直しでは入れない（暫定 63 §3.4）。
                owner, self._content, initial_focus=self._state is None,
                suspend_hook=lambda: self.app.hook.suspend_hook_for_dialog(),
                resume_hook=lambda: self.app.hook.resume_hook_after_dialog(),
                on_state_changed=lambda: self._schedule_save(window),
                on_user_close=self.close,
            )
            window.bind("<Destroy>", self._on_destroy, add="+")
            window.withdraw()
            if self._state is not None:
                window.apply_state(self._state)
            else:
                window.deiconify()
            self._place_window(window, owner)
            if self._state is not None:
                # 表示と配置が済んでから、もう一度スクロールを戻す（task_05 の検証で割合がずれた）。
                window.restore_scroll(self._state)
            modal.mark_grab_delegate(window)
            if owner is not self.app:
                install_grab_handoff(window, owner)
            window.apply_topmost(self._always_on_top())
            return window
        except Exception:
            self._discard_build(owner, children, window)
            raise
        finally:
            self._restoring = False

    def _place_window(self, window: HelpWindow, owner: tk.Misc) -> None:
        if (owner is self.app or not owner.winfo_viewable()
                or self.app.wm_state() in ("iconic", "withdrawn")  # App は state を AppState で上書きしている
                or window.wm_state() != "normal"):
            return
        if not window.winfo_viewable():
            window.wait_visibility()
        if not self._following or self._content is None:
            return
        window.lower(owner)
        target = modal.last_input(owner)
        if target is not None and modal.is_app_foreground(self.app):
            target.focus_force()

    def _discard_build(
        self, owner: tk.Misc, children: set[tk.Misc], window: HelpWindow | None,
    ) -> None:
        # __init__ 自体が失敗しても、Tk に作られた途中の窓を回収する。
        candidates = [window] if window is not None else [
            child for child in owner.winfo_children() if child not in children
        ]
        for candidate in candidates:
            try:
                self._destroy(candidate, "failed")
            except Exception:
                logging.getLogger(__name__).exception("Could not discard partial help window")

    def _schedule_save(self, window: HelpWindow | None) -> None:
        # <Map> / <Configure> の中で窓の状態を読むと、deiconify の途中で Tk 9.1（macOS）が落ちる
        # （task_05 の probe）。控えは処理が一段落してから 1 回にまとめて取る。
        if self._restoring or self._save_id is not None:
            return
        self._save_id = self.app.after_idle(self._run_scheduled_save, window)

    def _run_scheduled_save(self, window: HelpWindow | None) -> None:
        self._save_id = None
        try:
            if window is not None and window.winfo_exists():
                self._save_state(window)
        except tk.TclError:
            logging.getLogger(__name__).exception("Could not snapshot help window state")

    def _save_state(self, window: HelpWindow | None) -> None:
        if (self._restoring or self._content is None
                or window is None or window is not self._window):
            return
        try:
            self._state = window.export_state()
        except tk.TclError:
            logging.getLogger(__name__).exception("Could not snapshot help window state")

    def _destroy(self, window: HelpWindow, reason: str) -> None:
        self._destroy_reasons[window] = reason
        try:
            window.destroy()
        finally:
            self._destroy_reasons.pop(window, None)

    def _orphan_parent_alive(self) -> bool:
        parent = self._orphan_parent
        try:
            return parent is not None and bool(parent.winfo_exists())
        except tk.TclError:
            return False

    def _forget_closed(self) -> None:
        self._state = None
        self._content = None
        self._parent_destroyed = False
        self._orphan_parent = None

    def close(self) -> None:
        self._forget_closed()
        if self._window is not None:
            self._destroy(self._window, "user")

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is not self._window:
            return
        window = self._window
        reason = self._destroy_reasons.get(window)
        self._window = None
        if reason is None:
            self._parent_destroyed = True
            self._orphan_parent = window.master
            self.on_modal_front_changed()

    def stop_following(self) -> None:
        self._following = False
        if self._follow_id is not None:
            self.app.after_cancel(self._follow_id)
            self._follow_id = None
