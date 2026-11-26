"""実 Tk でヘルプとダイアログの grab の受け渡しを検査する。"""

import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from keyseq.infrastructure.os_backend import get_backend
from keyseq.presentation.help.grab_handoff import install_grab_handoff
from keyseq.presentation.help.help_content import HelpContent, HelpLoadResult
from keyseq.presentation.help.help_window_controller import HelpWindowController


class HelpGrabHandoffTest(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display is unavailable: {error}")
        self.addCleanup(self.root.destroy)
        self.addCleanup(self._release_grab)
        self.dialog = tk.Toplevel(self.root)
        self.help_window = tk.Toplevel(self.dialog)
        self.root.update()
        self.dialog.grab_set()

    def _release_grab(self) -> None:
        current = self.root.grab_current()
        if current is not None:
            current.grab_release()

    def _install(self, enabled: bool = True) -> None:
        with patch.object(
            get_backend().window, "hands_grab_to_active_child_window", return_value=enabled,
        ):
            install_grab_handoff(self.help_window, self.dialog)

    def _send(self, sequence: str) -> None:
        self.help_window.event_generate(sequence)
        self.root.update()

    def test_activate_hands_grab_to_help(self) -> None:
        self._install()
        self._send("<Activate>")
        self.assertIs(self.root.grab_current(), self.help_window)

    def test_deactivate_returns_grab_to_dialog(self) -> None:
        self._install()
        self._send("<Activate>")
        self.assertIs(self.root.grab_current(), self.help_window)
        self._send("<Deactivate>")
        self.assertIs(self.root.grab_current(), self.dialog)

    def test_destroy_returns_grab_to_dialog(self) -> None:
        self._install()
        self._send("<Activate>")
        self.assertIs(self.root.grab_current(), self.help_window)
        self.help_window.destroy()
        self.root.update()
        self.assertIs(self.root.grab_current(), self.dialog)

    def test_activate_preserves_another_windows_grab(self) -> None:
        other = tk.Toplevel(self.root)
        self.root.update()
        other.grab_set()
        self._install()
        self._send("<Activate>")
        self.assertIs(self.root.grab_current(), other)

    def test_disabled_backend_keeps_dialog_grab(self) -> None:
        self._install(enabled=False)
        self._send("<Activate>")
        self.assertIs(self.root.grab_current(), self.dialog)

    def test_controller_installs_once_for_reused_dialog_help(self) -> None:
        self.root.effective_always_on_top = lambda: False
        self.root.hook = Mock()
        controller = HelpWindowController(
            self.root, load_content=lambda: HelpLoadResult(HelpContent((), ())),
        )
        self.addCleanup(controller.close)
        with patch.object(
            get_backend().window, "hands_grab_to_active_child_window", return_value=True,
        ), patch(
            "keyseq.presentation.help.help_window_controller.install_grab_handoff",
            wraps=install_grab_handoff,
        ) as install:
            controller.open_for_dialog(self.dialog, "guide", "")
            window = controller.window
            install.assert_called_once_with(window, self.dialog)
            controller.open_for_dialog(self.dialog, "guide", "")
            self.assertIs(controller.window, window)
            install.assert_called_once_with(window, self.dialog)
