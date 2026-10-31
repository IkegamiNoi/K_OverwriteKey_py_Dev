"""UI tests for status icon composition and state application."""

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from keyseq.presentation.status_icon import status_icon as status_icon_module
from keyseq.presentation.status_icon.status_icon import StatusIcon
from keyseq.presentation.status_icon.badge_shapes import BADGE_COLORS
from keyseq.presentation import app as app_module
from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation.controllers.config_io.startup_io import StartupIo


class StatusIconTest(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Tk display is unavailable: {error}")
        self.addCleanup(self.root.destroy)
        self.calls = []
        self.root.iconphoto = lambda *args: self.calls.append(args)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def test_repeated_state_is_skipped_and_failed_state_retries(self):
        icon = StatusIcon(self.root, Path(self.temp.name))
        icon.apply("on")
        icon.apply("on")
        self.assertEqual(len(self.calls), 1)
        self.assertIs(self.calls[0][0], True)

        self.calls.clear()
        attempts = []
        def fail_once(*args):
            attempts.append(args)
            if len(attempts) == 1:
                raise tk.TclError("temporary failure")
        self.root.iconphoto = fail_once
        icon.apply("off")
        icon.apply("off")
        self.assertEqual(len(attempts), 2)

    def test_fallback_creates_two_badged_sizes(self):
        icon = StatusIcon(self.root, Path(self.temp.name) / "missing")
        self.assertEqual([image.width() for image in icon._images["off"]], [16, 32])
        self.assertEqual([image.height() for image in icon._images["off"]], [16, 32])
        icon.apply("off")
        self.assertEqual(len(self.calls), 1)

    def _write_png(self, name, width, height=None, color="#123456"):
        image = tk.PhotoImage(master=self.root, width=width, height=height or width)
        image.put(color, to=(0, 0, width, height or width))
        path = Path(self.temp.name) / name
        image.write(str(path), format="png")
        return path

    def test_only_supported_square_base_images_are_used(self):
        self._write_png("app_icon_a.png", 16)
        self._write_png("app_icon_b.png", 32)
        self._write_png("app_icon_c.png", 24)
        self._write_png("app_icon_d.png", 16, 32)
        (Path(self.temp.name) / "app_icon_e.png").write_text("not png")
        icon = StatusIcon(self.root, Path(self.temp.name))
        self.assertEqual([image.width() for image in icon._images["on"]], [16, 32])
        self.assertEqual([image.height() for image in icon._images["on"]], [16, 32])

    def test_badge_and_base_pixels(self):
        self._write_png("app_icon_16.png", 16, color="#123456")
        icon = StatusIcon(self.root, Path(self.temp.name))
        image = icon._images["on"][0]
        self.assertEqual(image.get(15, 0), (255, 255, 255))
        self.assertEqual(image.get(12, 3), (30, 158, 62))
        self.assertEqual(image.get(0, 15), (18, 52, 86))

    def test_failed_off_application_then_on_is_reapplied(self):
        icon = StatusIcon(self.root, Path(self.temp.name))
        seen = []
        def fail_off_once(*args):
            seen.append(args)
            if len(seen) == 2:
                raise tk.TclError("off failed")
        self.root.iconphoto = fail_off_once
        icon.apply("on")
        icon.apply("off")
        icon.apply("on")
        self.assertEqual([call[1] for call in seen], [*icon._images["on"][:1], *icon._images["off"][:1], *icon._images["on"][:1]])

    def test_composition_failure_uses_badge_only_images(self):
        self._write_png("app_icon_16.png", 16)
        original = status_icon_module.badge_pixels
        def fail_on_base(size, state, *, full=False):
            if not full:
                raise RuntimeError("base composition failed")
            return original(size, state, full=full)
        with patch.object(status_icon_module, "badge_pixels", side_effect=fail_on_base):
            icon = StatusIcon(self.root, Path(self.temp.name))
        self.assertEqual([image.width() for image in icon._images["on"]], [16, 32])
        self.root.iconphoto = lambda *args: self.calls.append(args)
        icon.apply("on")
        self.assertEqual(len(self.calls), 1)


class StatusIconControllerWiringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stack = __import__("contextlib").ExitStack()
        cls.addClassCleanup(stack.close)
        stack.enter_context(patch.object(app_module.JsonRepository, "save_json"))
        stack.enter_context(patch.object(ConfigService, "ensure_split_config_dirs"))
        stack.enter_context(patch.object(app_module, "load_startup_settings", return_value={}))
        stack.enter_context(patch.object(StartupIo, "load_startup_and_config"))
        stack.enter_context(patch.object(StartupIo, "write_startup", return_value=True))
        stack.enter_context(patch.object(ConfigService, "load_keymap_set_history", return_value=({"recent": [], "categories": []}, contracts.HISTORY_OK)))
        stack.enter_context(patch.object(ConfigService, "save_keymap_set_history", return_value=True))
        try:
            cls.app = app_module.App()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display unavailable: {error}")
        cls.addClassCleanup(cls.app.destroy)

    def test_status_states_and_compact_mode_are_applied(self):
        app = self.app
        app.status_icon = Mock()
        for active, enabled, expected in ((True, True, "on"), (False, True, "off"), (True, False, "paused")):
            app.hook.hook_active = active
            app.hook.custom_input_enabled = enabled
            app.trigger_panel.update_status()
            self.assertEqual(app.status_icon.apply.call_args.args, (expected,))
        app._compact_mode = True
        app.hook.hook_active = False
        app.trigger_panel.update_status()
        self.assertEqual(app.status_icon.apply.call_args.args, ("off",))

    def test_missing_icon_attribute_is_allowed(self):
        from types import SimpleNamespace
        from keyseq.presentation.controllers.trigger_panel.trigger_panel_controller import TriggerPanelController
        fake = SimpleNamespace(
            hook=SimpleNamespace(hook_active=False, custom_input_enabled=True),
            _compact_mode=True,
            keymap_panel=Mock(get_active_keymap_name=Mock(return_value="Main")),
            held_inputs=SimpleNamespace(display_names=[]),
            ui_vars=SimpleNamespace(status_var=Mock(), status_full_var=Mock()),
        )
        controller = TriggerPanelController.__new__(TriggerPanelController)
        controller._app = fake
        controller.selected_trigger_key = Mock(return_value="f1")
        controller.selected_trigger_is_effective = Mock(return_value=False)
        controller.update_status()
