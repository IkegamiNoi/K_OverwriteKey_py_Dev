import logging
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.infrastructure.os_backend.macos import ns_window
from keyseq.infrastructure.os_backend.macos.backend import MacWindowBackend


class MacWindowBackendTests(unittest.TestCase):
    def setUp(self):
        self.native = Mock()
        self.native.windowNumber.return_value = 42
        self.window = Mock()
        self.window.winfo_toplevel.return_value = self.window
        self.window.winfo_id.return_value = 7
        self.backend = MacWindowBackend(appkit=Mock())

    def resolve(self, native=None):
        return patch("keyseq.infrastructure.os_backend.macos.backend.ns_window_for", return_value=native or self.native)

    def test_releases_topmost_during_modal(self):
        self.assertTrue(self.backend.releases_topmost_during_modal())

    def test_bring_app_to_front_activates_application(self):
        application = Mock()
        appkit = Mock()
        appkit.NSApplication.sharedApplication.return_value = application
        backend = MacWindowBackend(appkit=appkit)
        self.assertTrue(backend.bring_app_to_front())
        application.activateIgnoringOtherApps_.assert_called_once_with(True)

    def test_bring_app_to_front_logs_failure_once(self):
        appkit = Mock()
        appkit.NSApplication.sharedApplication.side_effect = RuntimeError("failure")
        backend = MacWindowBackend(appkit=appkit)
        with self.assertLogs("keyseq.infrastructure.os_backend.macos.backend", level="ERROR") as logs:
            self.assertFalse(backend.bring_app_to_front())
            self.assertFalse(backend.bring_app_to_front())
        self.assertEqual(len(logs.records), 1)

    def test_ns_window_for_null_exception_missing_and_logs_once(self):
        class ObjC:
            objc_object = staticmethod(lambda **kwargs: object())
        saved = (ns_window._lookup_attempted, ns_window._function, ns_window._failure_logged)
        self.addCleanup(lambda: setattr(ns_window, "_lookup_attempted", saved[0]) or
                        setattr(ns_window, "_function", saved[1]) or setattr(ns_window, "_failure_logged", saved[2]))
        ns_window._lookup_attempted, ns_window._function, ns_window._failure_logged = False, None, False
        with self.assertLogs("keyseq.infrastructure.os_backend.macos.ns_window", logging.ERROR) as logs:
            self.assertIsNone(ns_window.ns_window_for(self.window, function=lambda _: 0, objc=ObjC))
            self.assertIsNone(ns_window.ns_window_for(self.window, function=Mock(side_effect=ValueError()), objc=ObjC))
            # The Tk symbol is missing: never call the real C function with a fake drawable.
            with patch.object(ns_window.ctypes, "CDLL", return_value=SimpleNamespace()):
                self.assertIsNone(ns_window.ns_window_for(self.window, function=None, objc=ObjC))
        self.assertEqual(len(logs.records), 1)

    def test_window_handle_requires_positive_number_and_native_window(self):
        with self.resolve(): self.assertEqual(self.backend.window_handle(self.window), 42)
        for number in (0, -1):  # -1 = a window that has never been shown (measured)
            self.native.windowNumber.return_value = number
            with self.resolve(): self.assertIsNone(self.backend.window_handle(self.window))
        with patch("keyseq.infrastructure.os_backend.macos.backend.ns_window_for", return_value=None):
            self.assertIsNone(self.backend.window_handle(self.window))

    def test_minimize_preparation_registers_once_and_handles_missing_window(self):
        center = Mock()
        appkit = SimpleNamespace(NSWindowWillMiniaturizeNotification="will-minimize")
        backend = MacWindowBackend(appkit=appkit, notification_center=center)
        with patch("keyseq.infrastructure.os_backend.macos.backend.ns_window_for", return_value=self.native), patch(
            "keyseq.infrastructure.os_backend.macos.minimize_observer.create_minimize_observer", return_value="observer"
        ):
            self.assertTrue(backend.install_minimize_preparation(self.window))
            self.assertTrue(backend.install_minimize_preparation(self.window))
        center.addObserver_selector_name_object_.assert_called_once_with(
            "observer", "willMiniaturize:", "will-minimize", self.native
        )
        with patch("keyseq.infrastructure.os_backend.macos.backend.ns_window_for", return_value=None):
            self.assertFalse(MacWindowBackend(appkit=appkit, notification_center=center).install_minimize_preparation(self.window))

    def test_minimize_observer_recursively_detaches_children(self):
        from keyseq.infrastructure.os_backend.macos import minimize_observer

        class NSObject:
            @classmethod
            def alloc(cls): return cls()
            def init(self): return self

        with patch.dict("sys.modules", {"Foundation": SimpleNamespace(NSObject=NSObject)}):
            minimize_observer._observer_class = None
            observer = minimize_observer.create_minimize_observer()
        grandchild, child, root = Mock(), Mock(), Mock()
        root.childWindows.return_value = [child]
        child.childWindows.return_value = [grandchild]
        grandchild.childWindows.return_value = []
        observer.willMiniaturize_(SimpleNamespace(object=lambda: root))
        child.removeChildWindow_.assert_called_once_with(grandchild)
        root.removeChildWindow_.assert_called_once_with(child)

    def test_disable_minimize_button_removes_style_and_handles_tcl_error(self):
        self.window.attributes.return_value = ("titled", "miniaturizable", "closable")
        self.assertTrue(self.backend.disable_minimize_button(self.window))
        self.window.attributes.assert_called_with("-stylemask", ("titled", "closable"))
        self.window.attributes.side_effect = __import__("tkinter").TclError()
        self.assertFalse(self.backend.disable_minimize_button(self.window))

    def test_order_out_calls_native_and_handles_missing_or_exception(self):
        with self.resolve():
            self.assertTrue(self.backend.order_out(self.window))
        self.native.orderOut_.assert_called_once_with(None)
        with patch("keyseq.infrastructure.os_backend.macos.backend.ns_window_for", return_value=None):
            self.assertFalse(self.backend.order_out(self.window))
        self.native.orderOut_.side_effect = RuntimeError()
        with self.resolve():
            self.assertFalse(self.backend.order_out(self.window))

    def test_foreground_window_reads_key_window_number(self):
        app = Mock(); app.isActive.return_value = True; app.keyWindow.return_value = self.native
        self.backend._appkit = SimpleNamespace(NSApplication=SimpleNamespace(sharedApplication=lambda: app))
        self.assertEqual(self.backend.foreground_own_window(), 42)
        app.isActive.return_value = False; self.assertIsNone(self.backend.foreground_own_window())
        app.isActive.return_value = True; app.keyWindow.return_value = None
        self.assertIsNone(self.backend.foreground_own_window())
        app.isActive.side_effect = RuntimeError()
        self.assertIsNone(self.backend.foreground_own_window())

    def test_place_window_below_and_failures(self):
        with self.resolve(): self.assertTrue(self.backend.place_window_below(self.window, 19))
        self.native.orderWindow_relativeTo_.assert_called_with(self.backend._get_appkit().NSWindowBelow, 19)
        self.assertFalse(self.backend.place_window_below(self.window, "19"))
        with patch("keyseq.infrastructure.os_backend.macos.backend.ns_window_for", return_value=None):
            self.assertFalse(self.backend.place_window_below(self.window, 19))
        self.native.orderWindow_relativeTo_.side_effect = RuntimeError()
        with self.resolve(): self.assertFalse(self.backend.place_window_below(self.window, 19))

    def test_monitor_rects_convert_all_sides_and_round(self):
        def screen(x, y, w, h):
            return SimpleNamespace(frame=lambda: SimpleNamespace(origin=SimpleNamespace(x=x,y=y), size=SimpleNamespace(width=w,height=h)))
        for second, expected in [(screen(0, 1100, 100, 100), (0,-116,100,-16)), (screen(0,-100,100,100),(0,1084,100,1184)), (screen(-100,0,100,100),(-100,984,0,1084)), (screen(100,0,100,100),(100,984,200,1084))]:
            self.backend._appkit = SimpleNamespace(NSScreen=SimpleNamespace(screens=lambda: [screen(0,0,100.4,1084.4), second]))
            rects = self.backend.list_monitor_rects()
            self.assertEqual(rects[0], ((0,0,100,1084), True)); self.assertEqual(rects[1], (expected, False))
        self.backend._appkit.NSScreen.screens = lambda: []
        self.assertEqual(self.backend.list_monitor_rects(), [])
        self.backend._appkit.NSScreen.screens = Mock(side_effect=RuntimeError())
        self.assertEqual(self.backend.list_monitor_rects(), [])

    def test_click_through_recolors_descendants_and_handles_failures(self):
        child, grandchild, no_bg = Mock(), Mock(), Mock()
        self.window.winfo_children.return_value = [child]
        child.winfo_children.return_value = [grandchild, no_bg]
        grandchild.winfo_children.return_value = []; no_bg.winfo_children.return_value = []
        for widget in (self.window, child): widget.cget.return_value = "other"
        grandchild.cget.return_value = "#FF00FE"; no_bg.cget.side_effect = __import__("tkinter").TclError()
        with self.resolve(): self.assertTrue(self.backend.make_click_through_overlay(self.window, "#ff00fe"))
        grandchild.configure.assert_called_once_with(background="#000000")
        self.window.attributes.assert_called_once_with("-alpha", 0.5)
        self.assertNotIn("-transparent", [call.args[0] for call in self.window.attributes.call_args_list])
        self.native.setIgnoresMouseEvents_.assert_called_with(True)
        self.native.setLevel_.assert_called_with(self.backend._get_appkit().NSStatusWindowLevel)
        with patch("keyseq.infrastructure.os_backend.macos.backend.ns_window_for", return_value=None):
            self.assertFalse(self.backend.make_click_through_overlay(self.window, "#ff00fe"))
        self.window.attributes.side_effect = __import__("tkinter").TclError()
        self.assertFalse(self.backend.make_click_through_overlay(self.window, "#ff00fe"))

    def test_click_through_reapplies_after_map(self):
        self.window.winfo_children.return_value = []
        with self.resolve():
            self.assertTrue(self.backend.make_click_through_overlay(self.window, "#ff00fe"))
        self.window.bind.assert_called_once()
        sequence, handler = self.window.bind.call_args.args
        self.assertEqual(sequence, "<Map>")
        self.assertEqual(self.window.bind.call_args.kwargs, {"add": "+"})

        self.window.after.reset_mock()
        handler(SimpleNamespace(widget=object()))
        self.window.after.assert_not_called()

        handler(SimpleNamespace(widget=self.window))
        self.window.after.assert_called_once()
        delay, callback = self.window.after.call_args.args
        self.assertEqual(delay, 0)
        with self.resolve():
            callback()
        self.native.setIgnoresMouseEvents_.assert_called_with(True)
        self.native.setLevel_.assert_called_with(self.backend._get_appkit().NSStatusWindowLevel)

        for result in (None, RuntimeError("lookup failed")):
            with patch(
                "keyseq.infrastructure.os_backend.macos.backend.ns_window_for",
                side_effect=result if isinstance(result, Exception) else None,
                return_value=None if result is None else None,
            ):
                handler(SimpleNamespace(widget=self.window))
                scheduled = self.window.after.call_args.args[1]
                scheduled()
