import unittest
from pathlib import Path

from keyseq.presentation.keyboard_layouts import (
    KeyboardLayout,
    KeySpec,
    keyboard_layout_from_dict,
    load_layout_from_json,
    resolve_layout_key_id_from_scan_code,
    resolve_layout_scan_code_from_key_name,
    resolve_keyboard_layout,
)


LAYOUT_DIR = Path(__file__).resolve().parents[1] / "config" / "user" / "keylayout"
LAYOUT_PATHS = {
    "de": LAYOUT_DIR / "de.json",
    "jis": LAYOUT_DIR / "jis.json",
}
_NO_SCAN_CODE_IDS = (
    "shift_",
    "ctrl_",
    "alt_",
    "windows_",
)


class KeyboardLayoutFilesTest(unittest.TestCase):
    @staticmethod
    def _layout_data(key_data):
        return {
            "layout_id": "extra_scan_test",
            "display_name": "Extra scan test",
            "keys": [
                {
                    "id": "custom",
                    "label": "Custom",
                    "x": 0,
                    "y": 0,
                    "w": 1,
                    "h": 1,
                    **key_data,
                }
            ],
        }

    def test_extra_scan_codes_load_as_empty_when_missing_or_null(self):
        for extra_scan_codes in ("missing", None):
            key_data = {} if extra_scan_codes == "missing" else {"extra_scan_codes": None}
            with self.subTest(extra_scan_codes=extra_scan_codes):
                layout = keyboard_layout_from_dict(self._layout_data(key_data))
                self.assertEqual(layout.keys[0].extra_scan_codes, ())

    def test_extra_scan_codes_are_coerced_to_integers(self):
        layout = keyboard_layout_from_dict(
            self._layout_data({"extra_scan_codes": [241, "242"]})
        )

        self.assertEqual(layout.keys[0].extra_scan_codes, (241, 242))

    def test_extra_scan_codes_reject_non_lists_and_non_integer_values(self):
        for extra_scan_codes in ("241", ["x"]):
            with self.subTest(extra_scan_codes=extra_scan_codes):
                with self.assertRaises(ValueError):
                    keyboard_layout_from_dict(
                        self._layout_data({"extra_scan_codes": extra_scan_codes})
                    )

    def test_extra_scan_codes_allow_negative_values(self):
        layout = keyboard_layout_from_dict(self._layout_data({"extra_scan_codes": [-26]}))

        self.assertEqual(layout.keys[0].extra_scan_codes, (-26,))

    def test_layout_scan_code_lookup_requires_a_scan_code_in_layout(self):
        layout = resolve_keyboard_layout()

        for scan_code in (41, 112, 121, 123):
            with self.subTest(scan_code=scan_code):
                self.assertEqual(resolve_layout_key_id_from_scan_code(layout, scan_code), "")
        self.assertEqual(resolve_layout_key_id_from_scan_code(layout, "invalid"), "")
        self.assertEqual(resolve_layout_key_id_from_scan_code(None, 41), "")

    def test_layout_scan_code_lookup_returns_matching_jis_id(self):
        layout = load_layout_from_json(str(LAYOUT_PATHS["jis"]))

        self.assertEqual(resolve_layout_key_id_from_scan_code(layout, 41), "zenkaku_hankaku")
        self.assertEqual(resolve_layout_key_id_from_scan_code(layout, 241), "muhenkan")
        self.assertEqual(resolve_layout_key_id_from_scan_code(layout, 242), "henkan")
        self.assertEqual(resolve_layout_key_id_from_scan_code(layout, 123), "muhenkan")
        self.assertEqual(resolve_layout_key_id_from_scan_code(layout, 121), "henkan")

    def test_extra_scan_code_only_row_is_used_for_receive_not_send(self):
        layout = KeyboardLayout(
            layout_id="test",
            display_name="Test",
            keys=(
                KeySpec(
                    id="receive_only",
                    label="Receive only",
                    x=0,
                    y=0,
                    extra_scan_codes=(241,),
                ),
            ),
        )

        self.assertEqual(resolve_layout_key_id_from_scan_code(layout, 241), "receive_only")
        self.assertIsNone(resolve_layout_scan_code_from_key_name(layout, "receive_only"))

    def test_receive_scan_code_lookup_uses_first_matching_row(self):
        layout = KeyboardLayout(
            layout_id="test",
            display_name="Test",
            keys=(
                KeySpec(id="first", label="First", x=0, y=0, scan_code=241),
                KeySpec(
                    id="second",
                    label="Second",
                    x=1,
                    y=0,
                    extra_scan_codes=(241,),
                ),
            ),
        )

        self.assertEqual(resolve_layout_key_id_from_scan_code(layout, 241), "first")

    def test_layout_scan_code_lookup_from_key_name(self):
        jis = load_layout_from_json(str(LAYOUT_PATHS["jis"]))
        us_tkl = resolve_keyboard_layout()
        self.assertEqual(resolve_layout_scan_code_from_key_name(jis, "muhenkan"), 123)
        self.assertEqual(resolve_layout_scan_code_from_key_name(jis, "henkan"), 121)
        self.assertEqual(resolve_layout_scan_code_from_key_name(jis, "MUHENKAN"), 123)
        self.assertEqual(resolve_layout_scan_code_from_key_name(jis, "zenkaku_hankaku"), 41)
        self.assertIsNone(resolve_layout_scan_code_from_key_name(us_tkl, "muhenkan"))
        self.assertIsNone(resolve_layout_scan_code_from_key_name(None, "muhenkan"))
        self.assertIsNone(resolve_layout_scan_code_from_key_name(jis, "  "))
        self.assertIsNone(resolve_layout_scan_code_from_key_name(jis, "a"))

    def test_layout_scan_code_lookup_uses_first_matching_row(self):
        layout = KeyboardLayout(
            layout_id="test",
            display_name="Test",
            keys=(
                KeySpec(id="same", label="First", x=0, y=0, scan_code=60),
                KeySpec(id="SAME", label="Second", x=1, y=0, scan_code=61),
            ),
        )
        self.assertEqual(resolve_layout_scan_code_from_key_name(layout, "same"), 60)

    def test_layout_scan_code_lookup_rejects_out_of_range_first_match(self):
        for scan_code in (0, 256):
            layout = KeyboardLayout(
                layout_id="test",
                display_name="Test",
                keys=(
                    KeySpec(id="same", label="Invalid", x=0, y=0, scan_code=scan_code),
                    KeySpec(id="same", label="Later", x=1, y=0, scan_code=60),
                ),
            )
            with self.subTest(scan_code=scan_code):
                self.assertIsNone(resolve_layout_scan_code_from_key_name(layout, "same"))

    def test_de_layout_loads_and_contains_alt_gr(self):
        layout = load_layout_from_json(str(LAYOUT_PATHS["de"]))

        self.assertEqual(layout.layout_id, "de")
        self.assertTrue(any(key.id == "alt_gr" for key in layout.keys))

    def test_layouts_have_unique_non_overlapping_keys(self):
        for name, path in LAYOUT_PATHS.items():
            with self.subTest(layout=name):
                layout = load_layout_from_json(str(path))
                self.assertEqual(len({key.id for key in layout.keys}), len(layout.keys))

                for index, first in enumerate(layout.keys):
                    for second in layout.keys[index + 1 :]:
                        overlaps_x = first.x < second.x + second.w and second.x < first.x + first.w
                        overlaps_y = first.y < second.y + second.h and second.y < first.y + first.h
                        self.assertFalse(overlaps_x and overlaps_y, f"{first.id} overlaps {second.id}")

    def test_modifier_and_prohibited_keys_have_no_scan_code(self):
        for name, path in LAYOUT_PATHS.items():
            with self.subTest(layout=name):
                layout = load_layout_from_json(str(path))
                for key in layout.keys:
                    if key.id.startswith(_NO_SCAN_CODE_IDS) or key.id in {"caps_lock", "alt_gr"}:
                        self.assertIsNone(key.scan_code, key.id)

    def test_jis_layout_contains_modifier_ids(self):
        layout = load_layout_from_json(str(LAYOUT_PATHS["jis"]))
        key_ids = {key.id for key in layout.keys}

        self.assertEqual(layout.layout_id, "jis")
        for key_id in (
            "ctrl_l",
            "ctrl_r",
            "alt_l",
            "alt_r",
            "windows_l",
            "windows_r",
            "shift_l",
            "shift_r",
        ):
            with self.subTest(key_id=key_id):
                self.assertIn(key_id, key_ids)


if __name__ == "__main__":
    unittest.main()
