from __future__ import annotations

import logging
import os
import tkinter

from .event_tap import load_quartz
from .key_table import COMMON_FLAGS
from .keyboard_backend import _physical_flags
from .ns_window import ns_window_for


_LOG = logging.getLogger(__name__)
_OVERLAY_ALPHA = 0.5


class MacWindowBackend:
    def __init__(self, *, quartz=None, appkit=None, notification_center=None) -> None:
        self._quartz = quartz
        self._appkit = appkit
        self._notification_center = notification_center
        self._minimize_observers: dict[object, object] = {}
        self._minimize_preparation_failure_logged = False
        self._foreground_failure_logged = False
        self._mouse_button_failure_logged = False
        self._window_failure_logged = False
        self._key_window_failure_logged = False
        self._overlay_reapply_failure_logged = False
        self._minimize_button_failure_logged = False
        self._order_out_failure_logged = False
        self._bring_to_front_failure_logged = False

    def bring_app_to_front(self) -> bool:
        try:
            # Deprecated on macOS 14+, but still works.
            self._get_appkit().NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            return True
        except Exception:
            if not self._bring_to_front_failure_logged:
                logging.getLogger(__name__).exception("Could not bring application to front")
                self._bring_to_front_failure_logged = True
            return False

    def releases_topmost_during_modal(self) -> bool:
        return True

    def detaches_deep_transients_during_minimize(self) -> bool:
        return False

    def hands_grab_to_active_child_window(self) -> bool:
        return True

    def install_minimize_preparation(self, window: tkinter.Misc) -> bool:
        try:
            from keyseq.infrastructure.os_backend.macos.minimize_observer import create_minimize_observer

            native = ns_window_for(window)
            if native is None:
                raise RuntimeError("Could not resolve native window")
            key = native  # NSWindow identity (windowNumber is -1 before first show and can be reused)
            if key in self._minimize_observers:
                return True
            center = self._notification_center
            if center is None:
                from Foundation import NSNotificationCenter
                center = NSNotificationCenter.defaultCenter()
                self._notification_center = center
            appkit = self._get_appkit()
            observer = create_minimize_observer()
            center.addObserver_selector_name_object_(
                observer, "willMiniaturize:", appkit.NSWindowWillMiniaturizeNotification, native
            )
            self._minimize_observers[key] = observer
            return True
        except Exception:
            if not self._minimize_preparation_failure_logged:
                _LOG.exception("Could not install minimize preparation")
                self._minimize_preparation_failure_logged = True
            return False

    def order_out(self, window: tkinter.Misc) -> bool:
        try:
            native = ns_window_for(window)
            if native is None:
                return False
            native.orderOut_(None)
            return True
        except Exception:
            if not self._order_out_failure_logged:
                _LOG.exception("Could not order window out")
                self._order_out_failure_logged = True
            return False

    def disable_minimize_button(self, window: tkinter.Misc) -> bool:
        try:
            stylemask = window.attributes("-stylemask")
            window.attributes(
                "-stylemask", tuple(item for item in stylemask if item != "miniaturizable")
            )
            return True
        except Exception:
            if not self._minimize_button_failure_logged:
                _LOG.exception("Could not disable minimize button")
                self._minimize_button_failure_logged = True
            return False

    def _log_overlay_reapply_failure(self) -> None:
        if not self._overlay_reapply_failure_logged:
            _LOG.exception("Could not reapply click-through overlay")
            self._overlay_reapply_failure_logged = True

    def _reapply_overlay_click_through(self, window) -> None:
        try:
            native = ns_window_for(window)
            if native is not None:
                native.setIgnoresMouseEvents_(True)
                native.setLevel_(self._get_appkit().NSStatusWindowLevel)
        except Exception:
            self._log_overlay_reapply_failure()

    def _overlay_mapped(self, window, event) -> None:
        try:
            if event.widget is window:
                window.after(0, lambda: self._reapply_overlay_click_through(window))
        except Exception:
            self._log_overlay_reapply_failure()

    def is_own_process_foreground(self) -> bool:
        try:
            appkit = self._appkit
            if appkit is None:
                from AppKit import NSWorkspace
            else:
                NSWorkspace = appkit.NSWorkspace
            application = NSWorkspace.sharedWorkspace().frontmostApplication()
            return application is None or application.processIdentifier() == os.getpid()
        except Exception:
            if not self._foreground_failure_logged:
                _LOG.exception("Could not determine frontmost application")
                self._foreground_failure_logged = True
            return False
    def _get_appkit(self):
        if self._appkit is None:
            import AppKit
            return AppKit
        return self._appkit

    def window_handle(self, window):
        native = ns_window_for(window)
        return self._window_number(native)

    @staticmethod
    def _window_number(native):
        try:
            number = int(native.windowNumber()) if native is not None else 0
            return number if number > 0 else None
        except Exception:
            return None

    def foreground_own_window(self):
        try:
            app = self._get_appkit().NSApplication.sharedApplication()
            native = app.keyWindow()
            return self._window_number(native) if app.isActive() and native is not None else None
        except Exception:
            if not self._key_window_failure_logged:
                _LOG.exception("Could not determine foreground window")
                self._key_window_failure_logged = True
            return None

    def place_window_below(self, window, above):
        if not isinstance(above, int):
            return False
        try:
            native = ns_window_for(window)
            if native is None:
                return False
            native.orderWindow_relativeTo_(self._get_appkit().NSWindowBelow, above)
            return True
        except Exception:
            return False

    def list_monitor_rects(self):
        try:
            screens = list(self._get_appkit().NSScreen.screens())
            if not screens:
                return []
            height = screens[0].frame().size.height
            result = []
            for index, screen in enumerate(screens):
                frame = screen.frame()
                x, y = frame.origin.x, frame.origin.y
                w, h = frame.size.width, frame.size.height
                result.append(((round(x), round(height-y-h), round(x+w), round(height-y)), index == 0))
            return result
        except Exception:
            if not self._window_failure_logged:
                _LOG.exception("Could not list monitors")
                self._window_failure_logged = True
            return []

    def make_click_through_overlay(self, window, transparent_color):
        try:
            pending = [window]
            while pending:
                widget = pending.pop()
                try:
                    if str(widget.cget("background")).lower() == transparent_color.lower():
                        widget.configure(background="#000000")
                except tkinter.TclError:
                    continue
                pending.extend(widget.winfo_children())
            window.attributes("-alpha", _OVERLAY_ALPHA)
            native = ns_window_for(window)
            if native is None:
                return False
            native.setIgnoresMouseEvents_(True)
            native.setLevel_(self._get_appkit().NSStatusWindowLevel)
            window.bind("<Map>", lambda event: self._overlay_mapped(window, event), add="+")
            return True
        except Exception:
            return False
    def is_mouse_button_down(self):
        try:
            q = self._quartz if self._quartz is not None else load_quartz()
            return bool(q.CGEventSourceButtonState(q.kCGEventSourceStateHIDSystemState, q.kCGMouseButtonLeft) or
                        q.CGEventSourceButtonState(q.kCGEventSourceStateHIDSystemState, q.kCGMouseButtonRight))
        except Exception:
            if not self._mouse_button_failure_logged:
                _LOG.exception("Could not read physical mouse buttons")
                self._mouse_button_failure_logged = True
            return False
    def is_shift_down(self) -> bool:
        return bool(_physical_flags(self._quartz) & COMMON_FLAGS["shift"])

    def is_ctrl_alt_win_down(self) -> bool:
        mask = COMMON_FLAGS["control"] | COMMON_FLAGS["option"] | COMMON_FLAGS["command"]
        return bool(_physical_flags(self._quartz) & mask)
