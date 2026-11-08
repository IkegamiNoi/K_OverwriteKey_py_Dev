import unittest
from unittest.mock import patch

from keyseq.application.config_service import ConfigService
from keyseq.domain.config import (
    DEFAULT_KEYBOARD_LAYOUT_ID,
    DEFAULT_RUN_TO_END_DELAY_MS,
    build_base_config,
    build_sample_config,
    safe_deepcopy,
)
from keyseq.infrastructure.json_repository import JsonRepository
from keyseq.shared.i18n import fix_language, tr
from keyseq.shared.i18n.catalog import current_language


fix_language("ja")


class SampleConfigTest(unittest.TestCase):
    def setUp(self):
        language = current_language()
        self.addCleanup(fix_language, language)
        fix_language("ja")

    def test_sample_keymaps_and_settings(self):
        data = build_sample_config()
        self.assertEqual(data["active_keymap_id"], "keymap_1")
        self.assertEqual(data["keymap_switch_keys"], {
            "1": "keymap_1", "2": "keymap_2", "3": "keymap_3",
        })
        self.assertEqual(data["keyboard_layout"], DEFAULT_KEYBOARD_LAYOUT_ID)
        self.assertEqual(data["triggers"], [])
        self.assertTrue(data["hook_keys_individual"])
        self.assertEqual(data["hook_stop_key"], "f12")
        self.assertEqual(data["hook_toggle_key"], "f1")
        first, right, numpad = data["keymaps"]
        self.assertEqual([item["id"] for item in data["keymaps"]], [
            "keymap_1", "keymap_2", "keymap_3",
        ])
        self.assertEqual(first["mappings"], {})
        self.assertEqual(right["mappings"], {
            "q": "p", "w": "o", "e": "i", "r": "u", "t": "y", "a": "l",
            "s": "k", "d": "j", "f": "h", "z": "m", "x": "n", "c": "b",
        })
        self.assertEqual(numpad["mappings"], {
            "z": "0", "x": "1", "c": "2", "v": "3", "a": "plus", "q": "-",
            "s": "4", "d": "5", "f": "6", "w": "7", "e": "8", "r": "9",
            "b": "enter", "g": "asterisk", "t": "slash",
        })
        self.assertEqual(data["hotkey_presets"], build_base_config()["hotkey_presets"])

    def test_all_sequences(self):
        data = build_sample_config()
        expected = [
            ("r", "select_line", True, 30, ["home", "shift+end"]),
            ("c", "copy", False, DEFAULT_RUN_TO_END_DELAY_MS, ["ctrl+c"]),
            ("v", "paste", False, DEFAULT_RUN_TO_END_DELAY_MS, ["ctrl+v"]),
            ("t", "switch_app", False, DEFAULT_RUN_TO_END_DELAY_MS, ["alt+tab"]),
            ("a", "paste_line_to_app", True, 300,
             ["home", "shift+end", "ctrl+c", "alt+tab", "ctrl+v", "alt+tab"]),
        ]
        triggers = data["keymaps"][0]["triggers"]
        self.assertEqual(len(triggers), len(expected))
        for trigger, (key, name, continuous, delay, values) in zip(triggers, expected):
            self.assertEqual(trigger, {
                "key": key, "label": tr(f"sample.sequence.{name}"),
                "suppress": True, "select_before_run": False,
                "run_to_end": continuous, "run_to_end_delay_ms": delay,
                "actions": [{"type": "hotkey", "value": value} for value in values],
            })
        for keymap, name in zip(data["keymaps"][1:], ("right_hand", "numpad")):
            self.assertEqual(keymap["triggers"], [{
                "key": "h", "label": tr(f"sample.sequence.{name}_guide"),
                "suppress": True, "select_before_run": False, "run_to_end": False,
                "run_to_end_delay_ms": DEFAULT_RUN_TO_END_DELAY_MS,
                "actions": [{"type": "text", "value": tr(f"sample.guide.{name}")}],
            }])

    def test_language_changes_only_labels_and_guide_text(self):
        japanese = build_sample_config()
        fix_language("en")
        english = build_sample_config()
        for ja_map, en_map in zip(japanese["keymaps"], english["keymaps"]):
            self.assertNotEqual(ja_map.pop("label"), en_map.pop("label"))
            for ja_trigger, en_trigger in zip(ja_map["triggers"], en_map["triggers"]):
                self.assertNotEqual(ja_trigger.pop("label"), en_trigger.pop("label"))
                if ja_trigger["actions"][0]["type"] == "text":
                    ja_text = ja_trigger["actions"][0].pop("value")
                    en_text = en_trigger["actions"][0].pop("value")
                    self.assertNotEqual(ja_text, en_text)
                    for value in (ja_text, en_text):
                        self.assertNotIn("\n", value)
                        self.assertIn("F1", value)
                        self.assertIn("F12", value)
                        without_function_keys = value.replace("F12", "").replace("F1", "")
                        self.assertFalse(any(char.isdigit() for char in without_function_keys))
        self.assertEqual(japanese, english)

    def test_welcome_sample_copy_and_guides_reference_display_keyboard_ui(self):
        japanese_description = tr("welcome.sample_description")
        self.assertNotIn(" ", japanese_description)
        for guide_name in ("right_hand", "numpad"):
            guide = tr(f"sample.guide.{guide_name}")
            self.assertIn(tr("view.display.title"), guide)
            self.assertIn(tr("view.display.keyboard_ui"), guide)

        fix_language("en")
        self.assertEqual(tr("welcome.sample_settings"), "Sample Settings")
        for guide_name in ("right_hand", "numpad"):
            guide = tr(f"sample.guide.{guide_name}")
            self.assertIn(tr("view.display.title"), guide)
            self.assertIn(tr("view.display.keyboard_ui"), guide)

    def test_each_builder_returns_independent_nested_data(self):
        service = ConfigService(JsonRepository())
        for build in (build_base_config, build_sample_config,
                      service.new_base_data, service.new_default_data, service.new_empty_data):
            with self.subTest(builder=build.__name__):
                baseline = safe_deepcopy(build())
                changed = build()
                changed["keymaps"][0]["mappings"]["changed"] = "x"
                if changed["keymaps"][0]["triggers"]:
                    changed["keymaps"][0]["triggers"][0]["actions"][0]["value"] = "changed"
                changed["keymaps"][0]["triggers"].append({"actions": []})
                changed["keymap_switch_keys"]["changed"] = "x"
                if changed["hotkey_presets"]:
                    changed["hotkey_presets"][0]["value"] = "changed"
                changed["hotkey_presets"].append({"label": "changed"})
                self.assertEqual(build(), baseline)

    def test_base_does_not_translate_or_include_sample(self):
        with patch("keyseq.domain.config.tr") as translate:
            data = build_base_config()
        translate.assert_not_called()
        self.assertEqual(data["keymaps"], [{
            "id": "keymap_1", "label": "", "mappings": {}, "triggers": [],
        }])
        self.assertEqual(data["triggers"], [])
        self.assertEqual(data["active_keymap_id"], "keymap_1")
        self.assertEqual(data["keymap_switch_keys"], {})
        self.assertEqual(data["hook_stop_key"], "")
        self.assertEqual(data["hook_toggle_key"], "")
        self.assertFalse(data["hook_keys_individual"])

    def test_service_uses_current_language_on_each_default_call(self):
        service = ConfigService(JsonRepository())
        japanese = service.new_default_data()
        fix_language("en")
        english = service.new_default_data()
        self.assertEqual(english, build_sample_config())
        self.assertNotEqual(japanese["keymaps"][0]["label"], english["keymaps"][0]["label"])
        self.assertEqual(service.new_base_data(), build_base_config())
