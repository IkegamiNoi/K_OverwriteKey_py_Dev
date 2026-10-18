from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from keyseq.presentation.controllers.layout_controller import LayoutController
from keyseq.presentation.keyboard_layouts import (
    KeyboardLayout,
    KeyboardLayoutEntry,
    KeySpec,
    load_layout_from_json,
    resolve_keyboard_layout,
)


JIS_LAYOUT_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "user" / "keylayout" / "jis.json"
)


class LayoutControllerScanCodeTest(unittest.TestCase):
    def _controller(self, layout, *, debug_enabled=True):
        controller = LayoutController.__new__(LayoutController)
        controller._app = SimpleNamespace(data={"debug_jis_special_key_events": debug_enabled})
        controller.get_current_keyboard_layout = lambda: layout
        return controller

    def _selection_controller(self, selected="new"):
        held_inputs = Mock()
        held_inputs.release_all.return_value = []
        hook = Mock()
        app = SimpleNamespace(
            data={"keyboard_layout": selected},
            base_dir="base",
            held_inputs=held_inputs,
            hook=hook,
            ui_vars=SimpleNamespace(keyboard_layout_var=Mock()),
        )
        controller = LayoutController.__new__(LayoutController)
        controller._app = app
        controller.keyboard_layout_id = "old"
        controller._keyboard_layout_entries = {"old": object(), "new": object()}
        controller._keyboard_layout_display_to_id = {"Old": "old", "New": "new"}
        controller._keyboard_layout_id_to_display = {"old": "Old", "new": "New"}
        controller._layout_combos = []
        controller.rebuild_keyboard_layout_display_maps = Mock()
        controller.refresh_keyboard_window = Mock()
        return controller, held_inputs, hook

    def test_reload_releases_held_inputs_before_replacing_layout_entries(self):
        controller, held_inputs, _hook = self._selection_controller()
        old_entries = controller._keyboard_layout_entries
        held_inputs.release_all.side_effect = lambda: self.assertIs(
            controller._keyboard_layout_entries, old_entries
        )
        controller.sync_keyboard_layout_controls = Mock()

        with patch(
            "keyseq.presentation.controllers.layout_controller.collect_keyboard_layouts",
            side_effect=lambda *_args, **_kwargs: {
                "replacement": object()
            },
        ) as collect:
            controller.reload_keyboard_layouts()

        held_inputs.release_all.assert_called_once_with()
        collect.assert_called_once_with([], base_dir="base")
        self.assertIsNot(controller._keyboard_layout_entries, old_entries)

    def test_set_selection_releases_before_changing_id(self):
        controller, held_inputs, _hook = self._selection_controller()
        held_inputs.release_all.side_effect = lambda: self.assertEqual(
            controller.keyboard_layout_id, "old"
        )

        controller.set_keyboard_layout_selection("new")

        held_inputs.release_all.assert_called_once_with()
        self.assertEqual(controller.keyboard_layout_id, "new")

    def test_set_selection_does_not_release_when_id_is_unchanged(self):
        controller, held_inputs, _hook = self._selection_controller(selected="old")

        controller.set_keyboard_layout_selection("old")

        held_inputs.release_all.assert_not_called()

    def test_sync_releases_only_when_selected_id_changes(self):
        controller, held_inputs, _hook = self._selection_controller()

        controller.sync_keyboard_layout_controls()

        held_inputs.release_all.assert_called_once_with()
        self.assertEqual(controller.keyboard_layout_id, "new")

        unchanged, unchanged_held, _hook = self._selection_controller(selected="old")
        unchanged.sync_keyboard_layout_controls()

        unchanged_held.release_all.assert_not_called()

    def test_release_errors_are_reported_and_selection_continues(self):
        controller, held_inputs, hook = self._selection_controller()
        held_inputs.release_all.return_value = [RuntimeError("release failed")]

        controller.set_keyboard_layout_selection("new")

        hook.show_action_error.assert_called_once()
        args = hook.show_action_error.call_args.args
        self.assertEqual(args[:2], ("", {"type": "key_hold", "value": "すべて解放"}))
        self.assertEqual(str(args[2]), "release failed")
        self.assertEqual(controller.keyboard_layout_id, "new")

    def test_selection_continues_when_app_has_no_held_inputs(self):
        controller, _held_inputs, _hook = self._selection_controller()
        del controller._app.held_inputs

        controller.set_keyboard_layout_selection("new")

        self.assertEqual(controller.keyboard_layout_id, "new")

    def test_resolve_key_name_uses_only_current_layout_scan_codes(self):
        us_controller = self._controller(resolve_keyboard_layout())
        for scan_code in (41, 123, 121, 112):
            with self.subTest(layout="us_tkl", scan_code=scan_code):
                self.assertEqual(us_controller.resolve_key_name_from_scan_code(scan_code), "")

        jis_controller = self._controller(load_layout_from_json(str(JIS_LAYOUT_PATH)))
        expected = {
            41: "zenkaku_hankaku",
            123: "muhenkan",
            121: "henkan",
            112: "kana",
        }
        for scan_code, key_name in expected.items():
            with self.subTest(layout="jis", scan_code=scan_code):
                self.assertEqual(jis_controller.resolve_key_name_from_scan_code(scan_code), key_name)

    def test_resolve_key_name_normalizes_custom_layout_ids(self):
        layout = KeyboardLayout(
            layout_id="custom",
            display_name="Custom",
            keys=(KeySpec(id="My_Key", label="My Key", x=0, y=0, scan_code=50),),
        )
        controller = self._controller(layout)

        self.assertEqual(controller.resolve_key_name_from_scan_code(50), "my_key")

    def test_resolve_scan_code_uses_registered_layout_without_reloading(self):
        layout = load_layout_from_json(str(JIS_LAYOUT_PATH))
        controller = self._controller(layout)
        controller.keyboard_layout_id = "jis"
        controller._keyboard_layout_entries = {
            "jis": KeyboardLayoutEntry(layout=layout, source="external")
        }
        controller.get_current_keyboard_layout = lambda: self.fail(
            "resolve_scan_code_from_key_name must not reload the current layout"
        )

        self.assertEqual(controller.resolve_scan_code_from_key_name("muhenkan"), 123)

    def test_resolve_scan_code_returns_none_for_unregistered_layout(self):
        layout = load_layout_from_json(str(JIS_LAYOUT_PATH))
        controller = self._controller(layout)
        controller.keyboard_layout_id = "missing"
        controller._keyboard_layout_entries = {"jis": KeyboardLayoutEntry(layout, "external")}

        self.assertIsNone(controller.resolve_scan_code_from_key_name("muhenkan"))

    def test_should_debug_special_key_event_requires_setting_and_key_down(self):
        layout = load_layout_from_json(str(JIS_LAYOUT_PATH))
        event = SimpleNamespace(event_type="down", scan_code=123, name="unrelated")
        enabled_controller = self._controller(layout)
        disabled_controller = self._controller(layout, debug_enabled=False)

        self.assertFalse(disabled_controller.should_debug_special_key_event(event, "muhenkan"))
        self.assertFalse(
            enabled_controller.should_debug_special_key_event(
                SimpleNamespace(event_type="up", scan_code=123, name="muhenkan"), "muhenkan"
            )
        )

    def test_should_debug_special_key_event_matches_layout_scan_code_only(self):
        jis_controller = self._controller(load_layout_from_json(str(JIS_LAYOUT_PATH)))
        self.assertTrue(
            jis_controller.should_debug_special_key_event(
                SimpleNamespace(event_type="down", scan_code=123, name="unrelated"), "unrelated"
            )
        )
        self.assertFalse(
            jis_controller.should_debug_special_key_event(
                SimpleNamespace(event_type="down", scan_code=30, name="muhenkan"), "muhenkan"
            )
        )

        us_controller = self._controller(resolve_keyboard_layout())
        self.assertFalse(
            us_controller.should_debug_special_key_event(
                SimpleNamespace(event_type="down", scan_code=123, name="muhenkan"), "muhenkan"
            )
        )

    def test_should_debug_special_key_event_rejects_unparseable_scan_codes(self):
        controller = self._controller(load_layout_from_json(str(JIS_LAYOUT_PATH)))
        for scan_code in (None, "not-a-scan-code"):
            with self.subTest(scan_code=scan_code):
                self.assertFalse(
                    controller.should_debug_special_key_event(
                        SimpleNamespace(event_type="down", scan_code=scan_code, name="muhenkan"),
                        "muhenkan",
                    )
                )


if __name__ == "__main__":
    unittest.main()
