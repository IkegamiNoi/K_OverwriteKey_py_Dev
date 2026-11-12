from unittest import TestCase
from unittest.mock import Mock, patch

from keyseq.presentation.tk_platform import (
    accelerator_text, is_aqua, key_label_font_family, primary_modifier, screen_distance,
)


class TkPlatformTests(TestCase):
    def widget(self, system):
        widget = Mock()
        widget.tk.call.return_value = system
        return widget

    def test_windows_results(self):
        widget = self.widget("win32")
        self.assertFalse(is_aqua(widget))
        self.assertEqual(primary_modifier(widget), "Control")
        self.assertEqual(accelerator_text(widget, "Ctrl+Shift+S"), "Ctrl+Shift+S")

    def test_aqua_results(self):
        widget = self.widget("aqua")
        self.assertTrue(is_aqua(widget))
        self.assertEqual(primary_modifier(widget), "Command")
        self.assertEqual(accelerator_text(widget, "Ctrl+Shift+S"), "Command-Shift-S")
        self.assertEqual(accelerator_text(widget, "Ctrl+Alt+P"), "Command-Option-P")

    def test_screen_distance_converts_unit_value_to_pixels(self):
        widget = Mock()
        widget.cget.return_value = "10c"
        widget.winfo_pixels.return_value = 378

        self.assertEqual(screen_distance(widget, "width"), 378)
        widget.winfo_pixels.assert_called_once_with("10c")

    def test_key_label_font_family_on_aqua(self):
        with patch("keyseq.presentation.tk_platform.tkfont.nametofont") as font:
            self.assertEqual(key_label_font_family(self.widget("aqua")), "Helvetica")
        font.assert_not_called()

    def test_key_label_font_family_on_other_platforms(self):
        for system in ("win32", "x11"):
            with self.subTest(system=system):
                widget = self.widget(system)
                with patch("keyseq.presentation.tk_platform.tkfont.nametofont") as font:
                    font.return_value.actual.return_value = "Default Family"
                    self.assertEqual(key_label_font_family(widget), "Default Family")
                font.assert_called_once_with("TkDefaultFont", root=widget)
                font.return_value.actual.assert_called_once_with("family")

    def test_screen_distance_returns_integer_pixel_value(self):
        widget = Mock()
        widget.cget.return_value = 300
        widget.winfo_pixels.return_value = "300"

        self.assertEqual(screen_distance(widget, "width"), 300)
        widget.winfo_pixels.assert_called_once_with(300)
