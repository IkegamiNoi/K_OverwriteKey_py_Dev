import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from keyseq.domain.keymap_triggers import ensure_active_triggers
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.keyboard_layouts import load_layout_from_json


JIS_LAYOUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "user"
    / "keylayout"
    / "jis.json"
)


class MakeOnlyKeyColorUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._patchers = [
            patch.object(StartupIo, "load_startup_and_config"),
            patch.object(StartupIo, "write_startup"),
            patch.object(KeymapSetIo, "save_keymap_set"),
            patch.object(KeymapSetIo, "save_keymap_set_to"),
        ]
        for patcher in cls._patchers:
            patcher.start()
        cls.app = app_module.App()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()
        for patcher in reversed(cls._patchers):
            patcher.stop()

    def setUp(self):
        self.original_data = copy.deepcopy(self.app.data)
        self.app.layout.open_keyboard_window()
        self.window = self.app.layout.keyboard_window
        self.window.update_layout(load_layout_from_json(str(JIS_LAYOUT_PATH)))
        self.app.update()
        self.addCleanup(self._restore_state)

    def _restore_state(self):
        if self.app.layout.keyboard_window is not None:
            self.app.layout.keyboard_window._handle_close()
        self.app.data = self.original_data
        self.app.dirty_tracker.set_dirty(False)
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()

    def _set_mapping(self, key):
        mappings = self.app.keymap_service.get_active_keymap(self.app.data)["mappings"]
        mappings[key] = "a"
        self.window.update_from_config(self.app.data)

    def _rectangle_fill(self, key):
        _, x1, y1, x2, y2 = next(bounds for bounds in self.window._key_bounds if bounds[0] == key)
        center = ((x1 + x2) / 2, (y1 + y2) / 2)
        item = next(
            item for item in self.window.canvas.find_overlapping(*center, *center)
            if self.window.canvas.type(item) == "rectangle"
        )
        return self.window.canvas.itemcget(item, "fill")

    def test_muhenkan_direct_assignment_uses_make_only_color(self):
        self._set_mapping("muhenkan")
        self.assertEqual(self._rectangle_fill("muhenkan"), "#e4ebe1")

    def test_henkan_direct_assignment_uses_make_only_color(self):
        self._set_mapping("henkan")
        self.assertEqual(self._rectangle_fill("henkan"), "#e4ebe1")

    def test_muhenkan_without_assignment_stays_white(self):
        mappings = self.app.keymap_service.get_active_keymap(self.app.data)["mappings"]
        mappings.pop("muhenkan", None)
        self.window.update_from_config(self.app.data)
        self.assertEqual(self._rectangle_fill("muhenkan"), self.window.set_key_color("normal")[0])

    def test_muhenkan_trigger_keeps_trigger_color(self):
        triggers = ensure_active_triggers(self.app.data)
        triggers[:] = [trigger for trigger in triggers if trigger.get("key") != "muhenkan"]
        triggers.append({"key": "muhenkan"})
        self.window.update_from_config(self.app.data)
        self.assertEqual(
            self._rectangle_fill("muhenkan"),
            self.window.set_key_color("trigger")[0],
        )

    def test_regular_key_direct_assignment_keeps_keymap_color(self):
        self._set_mapping("kana")
        self.assertEqual(self._rectangle_fill("kana"), self.window.set_key_color("keymap")[0])


if __name__ == "__main__":
    unittest.main()
