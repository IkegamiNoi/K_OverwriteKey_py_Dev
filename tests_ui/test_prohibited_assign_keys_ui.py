import copy
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.config_io.keymap_set_io import KeymapSetIo
from keyseq.presentation.controllers.config_io.startup_io import StartupIo
from keyseq.presentation.dialogs.keymap_edit_dialog import KeymapEditDialog
from keyseq.presentation.dialogs.keymap_switch_batch_dialog import KeymapSwitchBatchDialog
from keyseq.presentation.keyboard_layouts import KeyboardLayoutEntry, load_layout_from_json


DE_LAYOUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "user"
    / "keylayout"
    / "de.json"
)


class ProhibitedAssignKeysUiTest(unittest.TestCase):
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
        self.dialogs = []
        self.app.layout.open_keyboard_window()
        self.window = self.app.layout.keyboard_window
        self.app.update()
        self.addCleanup(self._restore_state)

    def _restore_state(self):
        for dialog in self.dialogs:
            if dialog.winfo_exists():
                dialog.destroy()
        if self.app.layout.keyboard_window is not None:
            self.app.layout.keyboard_window._handle_close()
        self.app.data = self.original_data
        self.app.dirty_tracker.set_dirty(False)
        self.app.trigger_panel.refresh_triggers()
        self.app.trigger_panel.refresh_actions()

    def _click_key(self, key, handler):
        _, x1, y1, x2, y2 = next(bounds for bounds in self.window._key_bounds if bounds[0] == key)
        return handler(SimpleNamespace(x=(x1 + x2) / 2, y=(y1 + y2) / 2))

    def _rectangle_fill(self, key):
        _, x1, y1, x2, y2 = next(bounds for bounds in self.window._key_bounds if bounds[0] == key)
        center = ((x1 + x2) / 2, (y1 + y2) / 2)
        item = next(
            item for item in self.window.canvas.find_overlapping(*center, *center)
            if self.window.canvas.type(item) == "rectangle"
        )
        return self.window.canvas.itemcget(item, "fill")

    def _canvas_text_in_key(self, key):
        _, x1, y1, x2, y2 = next(bounds for bounds in self.window._key_bounds if bounds[0] == key)
        center = ((x1 + x2) / 2, (y1 + y2) / 2)
        return [
            self.window.canvas.itemcget(item, "text")
            for item in self.window.canvas.find_overlapping(*center, *center)
            if self.window.canvas.type(item) == "text"
        ]

    def test_windows_and_caps_keys_are_prohibited_color_and_trigger_color_wins(self):
        for key in ("left windows", "right windows", "caps lock"):
            self.assertEqual(self._rectangle_fill(key), "#e5e7eb")

        self.window._kind_map["caps lock"] = "trigger"
        self.window.redraw()
        self.assertEqual(self._rectangle_fill("caps lock"), self.window.set_key_color("trigger")[0])

    def test_prohibited_click_does_not_change_active_edit(self):
        self.assertEqual(self._click_key("caps lock", self.window._on_canvas_left_click), "break")
        self.assertIsNone(self.window._editing_source_key)
        self.window._editing_source_key = "a"
        self.assertEqual(self._click_key("caps lock", self.window._on_canvas_left_click), "break")
        self.assertEqual(self.window._editing_source_key, "a")

    def test_de_alt_gr_key_is_prohibited_and_has_no_right_alt_frame(self):
        controller = self.app.layout
        entries_before = dict(controller._keyboard_layout_entries)
        previous_layout_id = controller.keyboard_layout_id
        previous_data_layout_id = self.app.data.get("keyboard_layout")
        previous_layout = controller.get_current_keyboard_layout()
        layout = load_layout_from_json(str(DE_LAYOUT_PATH))
        controller._keyboard_layout_entries["de"] = KeyboardLayoutEntry(
            layout=layout, source="test", path=str(DE_LAYOUT_PATH)
        )
        try:
            controller.set_keyboard_layout_selection("de")
            self.assertEqual(controller.keyboard_layout_id, "de")
            self.assertIn("alt gr", [bounds[0] for bounds in self.window._key_bounds])
            self.assertIn("AltGr", self._canvas_text_in_key("alt gr"))
            self.assertEqual(self._rectangle_fill("alt gr"), "#e5e7eb")
            self.assertEqual(self._click_key("alt gr", self.window._on_canvas_left_click), "break")
            self.assertIsNone(self.window._editing_source_key)
            keys = [bounds[0] for bounds in self.window._key_bounds]
            self.assertNotIn("right alt", keys)
        finally:
            controller._keyboard_layout_entries.clear()
            controller._keyboard_layout_entries.update(entries_before)
            # 選択の表示（ui_vars・コンボ）と窓も元のレイアウトへ戻す（App はクラスで共有）。
            controller.set_keyboard_layout_selection(previous_layout_id)
            if previous_data_layout_id is None:
                self.app.data.pop("keyboard_layout", None)
            else:
                self.app.data["keyboard_layout"] = previous_data_layout_id
            self.window.update_layout(previous_layout)

    def test_existing_caps_mapping_is_rendered_and_cleared_by_right_click(self):
        keymap = self.app.keymap_service.get_active_keymap(self.app.data)
        keymap["mappings"]["caps lock"] = "a"
        self.window.update_from_config(self.app.data)
        self.assertIn("a", self._canvas_text_in_key("caps lock"))

        self._click_key("caps lock", self.window._on_canvas_right_click)

        self.assertNotIn("caps lock", keymap["mappings"])

    def test_assignment_entry_rejects_caps_without_changing_data(self):
        before = copy.deepcopy(self.app.data)
        with patch("keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.showerror"):
            self.assertFalse(self.app.keymap_panel.assign_keymap_from_keyboard_ui("caps lock", "a"))
        self.assertEqual(self.app.data, before)

    def test_switch_validation_rejects_new_caps_but_allows_unchanged_caps(self):
        controller = self.app.keymap_panel
        keymap = self.app.keymap_service.get_active_keymap(self.app.data)
        target_id = keymap["id"]
        self.app.keymap_service.set_keymap_switch_key(self.app.data, "caps lock", target_id)
        self.app.dirty_tracker.set_dirty(False)
        with patch("keyseq.presentation.controllers.keymap_panel.keymap_panel_controller.messagebox.showerror") as showerror:
            self.assertFalse(controller.validate_keymap_switch_assignment(
                "caps lock", target_id=target_id, exclude_switch_key=""
            ))
            self.assertTrue(controller.validate_keymap_switch_assignment(
                "caps lock", target_id=target_id, exclude_switch_key="caps lock"
            ))
        showerror.assert_called_once_with(
            "設定できません",
            "Windows キー・Caps Lock・AltGr は切替キーにできません:\ncaps lock",
            parent=None,
        )

    def test_capture_dialogs_ignore_caps_lock_and_continue(self):
        edit = KeymapEditDialog(self.app, "Edit")
        self.dialogs.append(edit)
        edit._start_capture()
        self.assertEqual(edit._on_capture_keypress(SimpleNamespace(keysym="Caps_Lock")), "break")
        self.assertEqual(edit.key_var.get(), "")
        self.assertTrue(edit._capturing)

        batch = KeymapSwitchBatchDialog(
            self.app, "Batch", [("新規", "Map", "", "")], lambda _values: None
        )
        self.dialogs.append(batch)
        batch._start_capture(0)
        self.assertEqual(batch._on_capture_keypress(SimpleNamespace(keysym="Caps_Lock")), "break")
        self.assertEqual(batch.key_vars[0].get(), "")
        self.assertTrue(batch._capturing)

    def test_capture_dialogs_ignore_unknown_keysym_and_continue(self):
        edit = KeymapEditDialog(self.app, "Edit")
        self.dialogs.append(edit)
        edit._start_capture()
        self.assertEqual(edit._on_capture_keypress(SimpleNamespace(keysym="??")), "break")
        self.assertEqual(edit.key_var.get(), "")
        self.assertTrue(edit._capturing)

        batch = KeymapSwitchBatchDialog(
            self.app, "Batch", [("新規", "Map", "", "")], lambda _values: None
        )
        self.dialogs.append(batch)
        batch._start_capture(0)
        self.assertEqual(batch._on_capture_keypress(SimpleNamespace(keysym="??")), "break")
        self.assertEqual(batch.key_vars[0].get(), "")
        self.assertTrue(batch._capturing)
