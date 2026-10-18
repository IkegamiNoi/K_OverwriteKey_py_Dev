import unittest
from pathlib import Path

from keyseq.presentation.keyboard_layouts import (
    load_layout_from_json,
    resolve_layout_key_id_from_scan_code,
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
    def test_layout_scan_code_lookup_does_not_use_known_key_fallback(self):
        layout = resolve_keyboard_layout()

        for scan_code in (41, 112, 121, 123):
            with self.subTest(scan_code=scan_code):
                self.assertEqual(resolve_layout_key_id_from_scan_code(layout, scan_code), "")
        self.assertEqual(resolve_layout_key_id_from_scan_code(layout, "invalid"), "")
        self.assertEqual(resolve_layout_key_id_from_scan_code(None, 41), "")

    def test_layout_scan_code_lookup_returns_matching_jis_id(self):
        layout = load_layout_from_json(str(LAYOUT_PATHS["jis"]))

        self.assertEqual(resolve_layout_key_id_from_scan_code(layout, 41), "zenkaku_hankaku")

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
