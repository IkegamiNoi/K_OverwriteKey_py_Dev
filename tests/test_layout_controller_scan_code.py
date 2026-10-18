import unittest
from pathlib import Path
from types import SimpleNamespace

from keyseq.presentation.controllers.layout_controller import LayoutController
from keyseq.presentation.keyboard_layouts import (
    KeyboardLayout,
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
