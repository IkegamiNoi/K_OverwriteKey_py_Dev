import unittest

from keyseq.domain.config import (
    DEFAULT_CONFIG,
    ensure_config_compatibility,
    format_action_list_item,
    format_preset_list_item,
    format_trigger_list_item,
    normalize_key_name,
)


class NormalizeKeyNameTest(unittest.TestCase):
    def test_strip_and_lower(self):
        self.assertEqual(normalize_key_name("  F1 "), "f1")

    def test_none_returns_empty(self):
        self.assertEqual(normalize_key_name(None), "")


class EnsureConfigCompatibilityTest(unittest.TestCase):
    def test_empty_input_returns_defaults(self):
        config = ensure_config_compatibility({})
        self.assertEqual(config["triggers"], [])
        self.assertEqual(config["hotkey_presets"], DEFAULT_CONFIG["hotkey_presets"])
        self.assertEqual(config["hook_stop_key"], "")
        self.assertEqual(config["hook_toggle_key"], "")
        self.assertEqual(config["keyboard_layout"], "us_tkl")
        self.assertEqual(config["external_keyboard_layouts"], [])
        self.assertEqual(config["keymaps"], [])
        self.assertEqual(config["active_keymap_id"], "")
        self.assertEqual(config["keymap_switch_keys"], {})

    def test_non_dict_input_treated_as_empty(self):
        config = ensure_config_compatibility(None)
        self.assertEqual(config["triggers"], [])

    def test_legacy_single_trigger_converted(self):
        legacy = {
            "trigger_key": "F1",
            "actions": [{"type": "text", "value": "a"}],
        }
        config = ensure_config_compatibility(legacy)
        self.assertEqual(len(config["triggers"]), 1)
        trigger = config["triggers"][0]
        self.assertEqual(trigger["key"], "f1")
        self.assertTrue(trigger["suppress"])
        self.assertFalse(trigger["run_to_end"])
        self.assertEqual(trigger["run_to_end_delay_ms"], 300)
        self.assertEqual(trigger["actions"], [{"type": "text", "value": "a", "label": ""}])

    def test_delay_coercion(self):
        def delay_of(value):
            config = ensure_config_compatibility(
                {"triggers": [{"key": "a", "run_to_end_delay_ms": value, "actions": []}]}
            )
            return config["triggers"][0]["run_to_end_delay_ms"]

        self.assertEqual(delay_of("abc"), 300)
        self.assertEqual(delay_of(-5), 0)
        self.assertEqual(delay_of("120"), 120)

    def test_trigger_internal_keys_preserved(self):
        config = ensure_config_compatibility(
            {"triggers": [{"key": "a", "actions": [], "_sequence_dirty": True}]}
        )
        self.assertTrue(config["triggers"][0]["_sequence_dirty"])

    def test_keymap_normalization(self):
        config = ensure_config_compatibility(
            {
                "keymaps": [
                    {"id": "KM1", "label": " main ", "mappings": {"A": "B", "": "x", "c": ""}},
                    {"id": "km1", "mappings": {}},
                    {"mappings": {}},
                    "not-a-dict",
                ],
                "active_keymap_id": "zzz",
                "keymap_switch_keys": {"1": "km1", "2": "km1", "3": "unknown"},
            }
        )
        self.assertEqual(len(config["keymaps"]), 1)
        keymap = config["keymaps"][0]
        self.assertEqual(keymap["id"], "km1")
        self.assertEqual(keymap["label"], "main")
        self.assertEqual(keymap["mappings"], {"a": "b"})
        self.assertEqual(config["active_keymap_id"], "km1")
        self.assertEqual(config["keymap_switch_keys"], {"1": "km1"})


class FormatListItemTest(unittest.TestCase):
    def test_trigger_with_label(self):
        self.assertEqual(format_trigger_list_item(0, {"key": "F1", "label": "copy"}), "01. f1: copy")

    def test_trigger_without_label(self):
        self.assertEqual(format_trigger_list_item(9, {"key": "f2"}), "10. f2")

    def test_action_hotkey(self):
        self.assertEqual(
            format_action_list_item(0, {"type": "hotkey", "value": "ctrl+c"}),
            "01. [hotkey] ctrl+c",
        )

    def test_action_mouse_click(self):
        action = {"type": "mouse_click", "x": 10, "y": 20, "button": "left", "clicks": 2}
        self.assertEqual(format_action_list_item(0, action), "01. [mouse_click] (10, 20) left x2")

    def test_action_with_label(self):
        self.assertEqual(
            format_action_list_item(1, {"type": "text", "value": "abc", "label": "memo"}),
            "02. [text] abc: memo",
        )

    def test_preset(self):
        self.assertEqual(
            format_preset_list_item(0, {"label": "Win+D", "value": "windows+d"}),
            "01. windows+d: Win+D",
        )


if __name__ == "__main__":
    unittest.main()
