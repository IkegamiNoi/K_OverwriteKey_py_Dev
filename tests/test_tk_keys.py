import unittest
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
from keyseq.domain.config import normalize_key_name
from keyseq.presentation.keyboard_layouts import load_layout_from_json, resolve_layout_key_id_from_scan_code

from keyseq.presentation.tk_keys import (
    is_unresolved_capture_key,
    normalize_key_hold_tk_key_event,
    normalize_key_hold_tk_keysym,
    normalize_tk_key_event,
    normalize_tk_keysym,
    numpad_name_from_tk_event,
    resolve_tk_event_key_name,
    resolve_modified_char_key_name,
)



def _mac_tk_keys_backend():
    """Mac の受信の表（key_table）で aqua の keycode（上位 8 ビット = vk）を引く偽の backend。"""
    from keyseq.infrastructure.os_backend.macos.key_table import key_for_vk
    from keyseq.infrastructure.os_backend.macos.tk_key_translator import MacTkKeyTranslator

    def key(keycode):
        return key_for_vk((int(keycode) >> 24) & 0xFF, jis=False)

    return SimpleNamespace(tk_keys=SimpleNamespace(
        modifier_name=MacTkKeyTranslator(SimpleNamespace(_jis=False)).modifier_name,
        numpad_name=lambda keycode, state: "",
        vk_to_scan_code=lambda kc: key(kc).scan_code if key(kc) else None,
        vk_to_char=lambda kc: key(kc).name if key(kc) and len(key(kc).name) == 1 else "",
    ))


class TkKeysTest(unittest.TestCase):
    def test_resolve_modified_char_key_name_uses_physical_key_and_symbol_name(self):
        backend = _mac_tk_keys_backend()
        layout = load_layout_from_json("config/user/keylayout/us_tkl.json")
        resolve_name = lambda sc: normalize_key_name(resolve_layout_key_id_from_scan_code(layout, sc))
        with patch("keyseq.presentation.tk_keys.get_backend", return_value=backend):
            self.assertEqual(resolve_modified_char_key_name(
                SimpleNamespace(char="å", keysym="aring", keycode=0 << 24, state=0), resolve_name
            ), "a")
            self.assertEqual(resolve_modified_char_key_name(
                SimpleNamespace(char="≤", keysym="lessthanequal", keycode=43 << 24, state=0), resolve_name
            ), "comma")

    def test_resolve_modified_char_key_name_skips_ascii_and_modifiers(self):
        backend = SimpleNamespace(tk_keys=SimpleNamespace(
            modifier_name=lambda keysym, *, sided: None,
            numpad_name=lambda keycode, state: "",
            vk_to_scan_code=Mock(),
        ))
        with patch("keyseq.presentation.tk_keys.get_backend", return_value=backend):
            for char, keysym in (("a", "a"), ("!", "exclam"), (",", "comma"), ("", "Alt_L"), ("", "Shift_R")):
                with self.subTest(keysym=keysym):
                    self.assertEqual(resolve_modified_char_key_name(
                        SimpleNamespace(char=char, keysym=keysym, keycode=42, state=0), lambda sc: ""
                    ), "")
            backend.tk_keys.vk_to_scan_code.assert_not_called()

    def test_resolve_modified_char_key_name_without_resolver(self):
        # レイアウトで引けない（us_tkl は文字キーに走査コードを持たない）・resolver なしでも、
        # backend の修飾なしの文字に戻る（キーマップ編集のグリッドと同じ順）。
        with patch("keyseq.presentation.tk_keys.get_backend", return_value=_mac_tk_keys_backend()):
            self.assertEqual(resolve_modified_char_key_name(
                SimpleNamespace(char="å", keysym="aring", keycode=0, state=0), None
            ), "a")

    def test_resolve_event_key_name_uses_physical_layout_key(self):
        backend = SimpleNamespace(tk_keys=SimpleNamespace(
            numpad_name=lambda keycode, state: "",
            vk_to_scan_code=lambda vk: 30 if vk == 0x00000061 else None,
        ))
        event = SimpleNamespace(keycode=0x00000061, state=0, keysym="aring")
        with patch("keyseq.presentation.tk_keys.get_backend", return_value=backend), patch(
            "keyseq.presentation.tk_keys.resolve_layout_key_id_from_scan_code",
            return_value="a",
        ) as resolve:
            self.assertEqual(resolve_tk_event_key_name(event, object()), "a")
            resolve.assert_called_once()

    def test_resolve_event_key_name_returns_empty_when_scan_code_missing(self):
        backend = SimpleNamespace(tk_keys=SimpleNamespace(
            numpad_name=lambda keycode, state: "", vk_to_scan_code=lambda vk: None,
        ))
        with patch("keyseq.presentation.tk_keys.get_backend", return_value=backend):
            self.assertEqual(resolve_tk_event_key_name(
                SimpleNamespace(keycode=255, state=0, keysym="aring"), object()
            ), "")

    def test_resolve_event_key_name_defers_known_keysyms_without_scanning(self):
        backend = SimpleNamespace(tk_keys=SimpleNamespace(
            numpad_name=lambda keycode, state: "",
            vk_to_scan_code=lambda vk: self.fail("known keysym must not scan"),
        ))
        with patch("keyseq.presentation.tk_keys.get_backend", return_value=backend):
            for keysym in ("Alt_L", "Super_L", "Return"):
                with self.subTest(keysym=keysym):
                    self.assertEqual(resolve_tk_event_key_name(
                        SimpleNamespace(keycode=42, state=0, keysym=keysym), object()
                    ), "")

    def test_resolve_event_key_name_preserves_numpad_name(self):
        backend = SimpleNamespace(tk_keys=SimpleNamespace(
            numpad_name=lambda keycode, state: "num 1",
        ))
        with patch("keyseq.presentation.tk_keys.get_backend", return_value=backend):
            self.assertEqual(resolve_tk_event_key_name(
                SimpleNamespace(keycode=97, state=0, keysym="End"), object()
            ), "num 1")

    def test_unresolved_capture_key(self):
        self.assertTrue(is_unresolved_capture_key("??"))
        self.assertFalse(is_unresolved_capture_key("a"))
        self.assertFalse(is_unresolved_capture_key(""))

    @unittest.skipUnless(sys.platform == "win32", "Windows の Tk keycode と extended ビットを検証する（暫定 57 §7）")
    def test_numpad_names_by_keycode_and_extended_state(self):
        cases = {
            **{keycode: f"num {digit}" for digit, keycode in enumerate(range(96, 106))},
            110: "num decimal",
            106: "num multiply",
            109: "num subtract",
            107: "num add",
            111: "num divide",
            45: "num 0",
            35: "num 1",
            40: "num 2",
            34: "num 3",
            37: "num 4",
            12: "num 5",
            39: "num 6",
            36: "num 7",
            38: "num 8",
            33: "num 9",
            46: "num decimal",
        }
        for keycode, expected in cases.items():
            with self.subTest(keycode=keycode):
                self.assertEqual(numpad_name_from_tk_event(keycode, 0), expected)
                if 96 <= keycode <= 111:
                    self.assertEqual(
                        numpad_name_from_tk_event(keycode, 0x40000), expected
                    )
        self.assertEqual(numpad_name_from_tk_event(35, 0x40000), "")
        self.assertEqual(numpad_name_from_tk_event(13, 0), "")
        self.assertEqual(numpad_name_from_tk_event(13, 0x40000), "num enter")
        self.assertEqual(numpad_name_from_tk_event(96, 0x40000), "num 0")
        for keycode, state in (("bad", 0), (96, "bad"), (None, 0), (96, None)):
            with self.subTest(keycode=keycode, state=state):
                self.assertEqual(numpad_name_from_tk_event(keycode, state), "")

    @unittest.skipUnless(sys.platform == "win32", "Windows の Tk keycode と extended ビットを検証する（暫定 57 §7）")
    def test_event_normalizers_prefer_numpad_and_fall_back_to_keysym(self):
        self.assertEqual(
            normalize_tk_key_event(SimpleNamespace(keysym="End", keycode=97, state=0)),
            "num 1",
        )
        self.assertEqual(
            normalize_key_hold_tk_key_event(
                SimpleNamespace(keysym="End", keycode=97, state=0)
            ),
            "num 1",
        )
        self.assertEqual(
            normalize_tk_key_event(SimpleNamespace(keysym="End", keycode=35, state=0x40000)),
            "end",
        )
        self.assertEqual(
            normalize_tk_key_event(SimpleNamespace(keysym="1", keycode=49, state=0)),
            "1",
        )
        self.assertEqual(
            normalize_tk_key_event(SimpleNamespace(keysym="Return")), "enter"
        )
        self.assertEqual(
            normalize_key_hold_tk_key_event(SimpleNamespace(keysym="Shift_L")),
            "left shift",
        )
        self.assertEqual(normalize_tk_keysym("Return"), "enter")
        self.assertEqual(normalize_tk_keysym("minus"), "-")
        self.assertEqual(normalize_key_hold_tk_keysym("Shift_L"), "left shift")

    def test_aqua_command_and_fn_keysyms(self):
        from keyseq.infrastructure.os_backend.macos.tk_key_translator import MacTkKeyTranslator

        widget = SimpleNamespace(tk=None)
        backend = SimpleNamespace(tk_keys=MacTkKeyTranslator(SimpleNamespace(_jis=False)))
        with patch("keyseq.presentation.tk_keys.get_backend", return_value=backend):
            self.assertEqual(normalize_tk_keysym("Meta_L", widget=widget), "command")
            self.assertEqual(normalize_key_hold_tk_keysym("Meta_L", widget=widget), "left command")
            self.assertEqual(normalize_tk_keysym("Meta_R", widget=widget), "command")
            self.assertEqual(normalize_key_hold_tk_keysym("Meta_R", widget=widget), "right command")
            for side in ("L", "R"):
                self.assertEqual(normalize_tk_keysym(f"Alt_{side}"), "option")
                self.assertEqual(normalize_key_hold_tk_keysym(f"Alt_{side}"),
                                 "left option" if side == "L" else "right option")
            self.assertEqual(normalize_tk_keysym("Super_L", widget=widget), "??")
            self.assertEqual(normalize_key_hold_tk_keysym("Super_L", widget=widget), "??")
            self.assertEqual(normalize_tk_keysym("Super_R", widget=widget), "??")
            self.assertEqual(normalize_key_hold_tk_keysym("Super_R", widget=widget), "??")
            self.assertEqual(
                normalize_tk_key_event(SimpleNamespace(keysym="Meta_L", widget=widget)),
                "command",
            )
            self.assertEqual(
                normalize_key_hold_tk_key_event(SimpleNamespace(keysym="Super_L", widget=widget)),
                "??",
            )
            self.assertEqual(
                normalize_tk_key_event(SimpleNamespace(keysym="Meta_R", widget=widget)),
                "command",
            )
            self.assertEqual(
                normalize_key_hold_tk_key_event(SimpleNamespace(keysym="Meta_R", widget=widget)),
                "right command",
            )
            self.assertEqual(
                normalize_tk_key_event(SimpleNamespace(keysym="Super_R", widget=widget)),
                "??",
            )

    def test_non_aqua_super_remains_windows(self):
        from keyseq.infrastructure.os_backend.windows.tk_key_translator import modifier_name

        widget = object()
        backend = SimpleNamespace(tk_keys=SimpleNamespace(modifier_name=modifier_name))
        with patch("keyseq.presentation.tk_keys.get_backend", return_value=backend):
            self.assertEqual(normalize_tk_keysym("Super_L", widget=widget), "windows")
            self.assertEqual(normalize_key_hold_tk_keysym("Super_L", widget=widget), "left windows")

    @unittest.skipUnless(sys.platform == "win32", "Windows backend の widget なしの解釈")
    def test_widgetless_super_keeps_legacy_mapping(self):
        self.assertEqual(normalize_tk_keysym("Super_L"), "windows")
        self.assertEqual(normalize_key_hold_tk_keysym("Super_R"), "right windows")
        self.assertEqual(normalize_tk_key_event(SimpleNamespace(keysym="Super_L")), "windows")
        self.assertEqual(
            normalize_key_hold_tk_key_event(SimpleNamespace(keysym="Super_R")),
            "right windows",
        )


if __name__ == "__main__":
    unittest.main()
