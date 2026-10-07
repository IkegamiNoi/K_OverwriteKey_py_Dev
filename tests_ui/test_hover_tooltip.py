from __future__ import annotations

import tkinter
import unittest
from tkinter import ttk
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.presentation.hover_tooltip import bind_hover_tooltip


class HoverTooltipTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tkinter.Tk()
        except tkinter.TclError as error:
            self.skipTest(f"Tk を利用できません: {error}")
        self.root.geometry("400x100+20+20")
        self.root.deiconify()
        self.label = ttk.Label(self.root, text="表示")
        self.label.pack()
        self.root.update()

    def tearDown(self):
        if hasattr(self, "root"):
            try:
                self.root.destroy()
            except tkinter.TclError:
                pass

    def _enter(self):
        self.label.event_generate(
            "<Enter>",
            x=1,
            y=1,
            rootx=self.label.winfo_rootx() + 1,
            rooty=self.label.winfo_rooty() + 1,
        )
        self.root.update()

    def _show(self, tooltip):
        tooltip.show(
            SimpleNamespace(
                x_root=self.label.winfo_rootx() + 1,
                y_root=self.label.winfo_rooty() + 1,
            )
        )
        self.root.update_idletasks()

    def _tooltip_label(self, tooltip):
        return next(
            child
            for child in tooltip._window.winfo_children()
            if isinstance(child, ttk.Label)
        )

    def test_fixed_text_is_shown_with_left_justification(self):
        tooltip = bind_hover_tooltip(self.label, lambda: "全文\n次の行", lambda: True)

        self._show(tooltip)

        self.assertIsNotNone(tooltip._window)
        self.assertEqual(self._tooltip_label(tooltip).cget("text"), "全文\n次の行")
        self.assertEqual(str(self._tooltip_label(tooltip).cget("justify")), "left")
        tooltip.close()
        self.assertIsNone(tooltip._window)

    def test_refresh_replaces_text_and_closes_when_no_longer_applicable(self):
        content = {"text": "最初", "show": True}
        tooltip = bind_hover_tooltip(
            self.label,
            lambda: content["text"],
            lambda: content["show"],
        )
        self._show(tooltip)
        window = tooltip._window
        self.assertEqual(self._tooltip_label(tooltip).cget("text"), "最初")
        initial_position = window.geometry().rsplit("+", 2)[-2:]

        content["text"] = "更新\nされた全文"
        tooltip.refresh()
        self.assertIs(tooltip._window, window)
        self.assertEqual(self._tooltip_label(tooltip).cget("text"), "更新\nされた全文")
        self.assertEqual(window.geometry().rsplit("+", 2)[-2:], initial_position)

        content["show"] = False
        tooltip.refresh()
        self.assertIsNone(tooltip._window)
        self.assertFalse(window.winfo_exists())

    def test_empty_text_does_not_open_and_refresh_closes_empty_text(self):
        content = {"text": ""}
        tooltip = bind_hover_tooltip(self.label, lambda: content["text"], lambda: True)
        self._show(tooltip)
        self.assertIsNone(tooltip._window)

        content["text"] = "表示中"
        tooltip.show(SimpleNamespace(x_root=5, y_root=7))
        window = tooltip._window
        content["text"] = ""
        tooltip.refresh()
        self.assertIsNone(tooltip._window)
        self.assertFalse(window.winfo_exists())

    def test_leave_and_button_close_visible_tooltip(self):
        tooltip = bind_hover_tooltip(self.label, lambda: "全文", lambda: True)
        self._enter()
        self.assertIsNotNone(tooltip._window)
        self.label.event_generate("<Leave>")
        self.root.update_idletasks()
        self.assertIsNone(tooltip._window)
        tooltip.refresh()
        self.assertIsNone(tooltip._window)

        self._enter()
        self.assertIsNotNone(tooltip._window)
        self.label.event_generate("<Button>")
        self.root.update_idletasks()
        self.assertIsNone(tooltip._window)
        tooltip.refresh()
        self.assertIsNone(tooltip._window)

    def test_refresh_shows_tooltip_when_truncation_starts_while_hovered(self):
        content = {"show": False}
        tooltip = bind_hover_tooltip(self.label, lambda: "全文", lambda: content["show"])
        self._enter()
        self.assertIsNone(tooltip._window)

        content["show"] = True
        tooltip.refresh()

        self.assertIsNotNone(tooltip._window)
        self.assertEqual(self._tooltip_label(tooltip).cget("text"), "全文")

    def test_refresh_reopens_tooltip_when_truncation_returns_while_hovered(self):
        content = {"show": True}
        tooltip = bind_hover_tooltip(self.label, lambda: "全文", lambda: content["show"])
        self._enter()
        self.assertIsNotNone(tooltip._window)

        content["show"] = False
        tooltip.refresh()
        self.assertIsNone(tooltip._window)
        content["show"] = True
        tooltip.refresh()

        self.assertIsNotNone(tooltip._window)
        self.assertEqual(self._tooltip_label(tooltip).cget("text"), "全文")

    def test_tooltip_toplevel_is_topmost(self):
        tooltip = bind_hover_tooltip(self.label, lambda: "全文", lambda: True)
        self._show(tooltip)

        self.assertIsNotNone(tooltip._window)
        self.assertIn(str(tooltip._window.attributes("-topmost")), ("1", "True"))

    def test_refresh_does_nothing_when_tooltip_is_not_visible(self):
        calls = []
        tooltip = bind_hover_tooltip(
            self.label,
            lambda: calls.append("text") or "全文",
            lambda: calls.append("show") or True,
        )

        tooltip.refresh()

        self.assertEqual(calls, [])
        self.assertIsNone(tooltip._window)

    def test_widget_destroy_closes_visible_tooltip(self):
        tooltip = bind_hover_tooltip(self.label, lambda: "全文", lambda: True)
        self._show(tooltip)
        window = tooltip._window

        self.label.destroy()
        self.root.update()

        self.assertIsNone(tooltip._window)
        self.assertFalse(window.winfo_exists())

    def test_toplevel_creation_failure_leaves_no_tooltip(self):
        tooltip = bind_hover_tooltip(self.label, lambda: "全文", lambda: True)

        with patch("keyseq.presentation.hover_tooltip.tk.Toplevel", side_effect=RuntimeError):
            self._show(tooltip)

        self.assertIsNone(tooltip._window)
        self.assertEqual(
            [child for child in self.label.winfo_children() if isinstance(child, tkinter.Toplevel)],
            [],
        )


if __name__ == "__main__":
    unittest.main()
