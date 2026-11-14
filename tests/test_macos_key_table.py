from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from keyseq.domain.numpad_keys import numpad_key_spec
from keyseq.infrastructure.os_backend.macos.key_table import (
    KEY_TABLE,
    JIS_KEY_TABLE,
    MODIFIER_NAMES,
    SHIFTED_JIS,
    SHIFTED_US,
    MacKey,
    is_jis_layout,
    key_for_vk,
    vk_for_name,
)


ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PATH = ROOT / "config" / "user" / "keylayout" / "us_tkl.json"
NO_MAC_PHYSICAL_KEY = {"print screen", "scroll lock", "pause", "menu", "caps lock"}


class MacKeyTableTests(unittest.TestCase):
    def test_table_covers_physical_us_layout_ids(self) -> None:
        layout = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
        expected_ids = {
            entry["id"]
            for entry in layout["keys"]
            if entry["id"] not in NO_MAC_PHYSICAL_KEY
        }
        received_names = {key.name for key in KEY_TABLE.values()}
        expected_names = {
            MODIFIER_NAMES.get(key_id, key_id) for key_id in expected_ids
        }
        expected_names.update({"yen", "ro", "muhenkan", "henkan"})
        expected_names.update({
            "num 0", "num 1", "num 2", "num 3", "num 4", "num 5",
            "num 6", "num 7", "num 8", "num 9", "num decimal",
            "num multiply", "num subtract", "num add", "num divide",
            "num enter",
        })

        self.assertEqual(received_names, expected_names)

    def test_modifier_scan_codes_and_receive_names(self) -> None:
        expected = {
            "shift_l": (42, "shift"),
            "shift_r": (54, "right shift"),
            "ctrl_l": (29, "ctrl"),
            "ctrl_r": (29, "right ctrl"),
            "alt_l": (56, "alt"),
            "alt_r": (56, "right alt"),
            "windows_l": (91, "left windows"),
            "windows_r": (92, "right windows"),
        }
        self.assertEqual(set(MODIFIER_NAMES), set(expected))
        by_name = {key.name: key for key in KEY_TABLE.values()}

        for layout_id, (scan_code, receive_name) in expected.items():
            with self.subTest(layout_id=layout_id):
                self.assertEqual(MODIFIER_NAMES[layout_id], receive_name)
                self.assertEqual(by_name[receive_name].scan_code, scan_code)

    def test_arrows_are_not_keypad_keys(self) -> None:
        by_name = {key.name: key for key in KEY_TABLE.values()}
        for name, scan in (("up", 72), ("left", 75), ("right", 77), ("down", 80)):
            with self.subTest(name=name):
                self.assertEqual(by_name[name].scan_code, scan)
                self.assertFalse(by_name[name].is_keypad)

    def test_us_symbol_vk_values_and_help_identity(self) -> None:
        expected = {50: "`", 27: "-", 24: "=", 33: "[", 30: "]", 42: "\\",
                    41: ";", 39: "'", 43: ",", 47: ".", 44: "/"}
        for vk, name in expected.items():
            self.assertEqual(KEY_TABLE[vk].name, name)
        self.assertEqual(KEY_TABLE[114], MacKey(82, False, "insert"))

    def test_jis_only_vk_entries_use_compatibility_scan_codes(self) -> None:
        expected = {
            93: (125, "yen"),
            94: (115, "ro"),
            102: (123, "muhenkan"),
            104: (121, "henkan"),
        }
        for vk, (scan_code, name) in expected.items():
            with self.subTest(vk=vk):
                self.assertEqual(KEY_TABLE[vk], MacKey(scan_code, False, name))

    def test_keys_without_supported_physical_mapping_are_absent(self) -> None:
        for vk in (57, 63, 95, 10, 179, 64, 71, 81, 105, 107, 113):
            with self.subTest(vk=vk):
                self.assertNotIn(vk, KEY_TABLE)

    def test_vk_for_name_is_the_unique_reverse_lookup(self) -> None:
        by_name: dict[str, list[int]] = {}
        for vk, key in KEY_TABLE.items():
            by_name.setdefault(key.name, []).append(vk)

        for name, vks in by_name.items():
            with self.subTest(name=name):
                self.assertEqual(
                    vk_for_name(name, jis=False),
                    vks[0] if len(vks) == 1 else None,
                )
        self.assertIsNone(vk_for_name("not a mapped key", jis=False))

    def test_ambiguous_name_has_no_reverse_lookup(self) -> None:
        original_vk, original_key = next(iter(KEY_TABLE.items()))
        duplicate_vk = max(KEY_TABLE) + 1
        with patch.dict(
            KEY_TABLE,
            {
                duplicate_vk: MacKey(
                    original_key.scan_code,
                    original_key.is_keypad,
                    original_key.name,
                )
            },
        ):
            self.assertIsNone(vk_for_name(original_key.name, jis=False))
        self.assertIn(original_vk, KEY_TABLE)

    def test_jis_layout_detection_uses_physical_key_ids(self) -> None:
        layouts = {}
        for name in ("jis", "us_tkl", "de", "jis_test"):
            path = ROOT / "config" / "user" / "keylayout" / f"{name}.json"
            layout = json.loads(path.read_text(encoding="utf-8"))
            layouts[name] = frozenset(entry["id"] for entry in layout["keys"])

        self.assertTrue(is_jis_layout(layouts["jis"]))
        self.assertFalse(is_jis_layout(layouts["us_tkl"]))
        self.assertFalse(is_jis_layout(layouts["de"]))
        self.assertFalse(is_jis_layout(layouts["jis_test"]))
        self.assertTrue(is_jis_layout(frozenset({"a", "yen"})))
        self.assertTrue(is_jis_layout(frozenset({"ro"})))

    def test_jis_overrides_keep_compatibility_scan_codes(self) -> None:
        expected = {
            50: MacKey(41, False, "zenkaku_hankaku"),
            24: MacKey(13, False, "^"),
            33: MacKey(26, False, "@"),
            30: MacKey(27, False, "["),
            42: MacKey(43, False, "]"),
            39: MacKey(40, False, ":"),
        }
        self.assertEqual(JIS_KEY_TABLE, expected)
        for vk, key in expected.items():
            with self.subTest(vk=vk):
                self.assertEqual(key_for_vk(vk, jis=True), key)
                self.assertEqual(key_for_vk(vk, jis=False), KEY_TABLE[vk])

    def test_keypad_table_covers_domain_numpad_keys(self) -> None:
        expected = {
            "num 0": (82, 82), "num 1": (83, 79), "num 2": (84, 80),
            "num 3": (85, 81), "num 4": (86, 75), "num 5": (87, 76),
            "num 6": (88, 77), "num 7": (89, 71), "num 8": (91, 72),
            "num 9": (92, 73), "num decimal": (65, 83),
            "num multiply": (67, 55), "num subtract": (78, 74),
            "num add": (69, 78), "num divide": (75, 53),
            "num enter": (76, 28),
        }
        for name, (vk, scan_code) in expected.items():
            with self.subTest(name=name):
                self.assertEqual(KEY_TABLE[vk], MacKey(scan_code, True, name))
                numpad_spec = numpad_key_spec(name)
                self.assertIsNotNone(numpad_spec)
                self.assertEqual(numpad_spec[0], scan_code)
                self.assertEqual(vk_for_name(name, jis=False), vk)
        self.assertNotIn(71, KEY_TABLE)  # Keypad Clear is unsupported.
        self.assertNotIn(81, KEY_TABLE)  # Keypad = is unsupported.

    def test_jis_reverse_lookup_uses_replaced_rows(self) -> None:
        expected = {
            "[": 30, "]": 42, "@": 33, "^": 24, ":": 39,
            "zenkaku_hankaku": 50,
        }
        for name, vk in expected.items():
            with self.subTest(name=name):
                self.assertEqual(vk_for_name(name, jis=True), vk)
        self.assertEqual(vk_for_name("[", jis=False), 33)

    def test_send_aliases_and_shifted_character_tables(self) -> None:
        self.assertEqual(vk_for_name("windows"), 55)
        self.assertEqual(vk_for_name("left shift"), 56)
        self.assertEqual(vk_for_name("left ctrl"), 59)
        self.assertEqual(vk_for_name("left alt"), 58)
        self.assertEqual(SHIFTED_US["@"], "2")
        self.assertNotIn("@", SHIFTED_JIS)
        self.assertEqual(SHIFTED_JIS["!"], "1")
        self.assertEqual(SHIFTED_JIS["_"], "ro")


if __name__ == "__main__":
    unittest.main()
