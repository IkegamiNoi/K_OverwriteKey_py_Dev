import unittest

from keyseq.domain.config import (
    DEFAULT_CONFIG,
    coerce_key_name,
    coerce_label,
    ensure_config_compatibility,
    format_action_list_item,
    format_preset_list_item,
    format_trigger_list_item,
    normalize_actions,
    normalize_hotkey_presets,
    normalize_key_name,
    resolve_hook_keys_individual,
)


class NormalizeKeyNameTest(unittest.TestCase):
    def test_strip_and_lower(self):
        self.assertEqual(normalize_key_name("  F1 "), "f1")

    def test_none_returns_empty(self):
        self.assertEqual(normalize_key_name(None), "")


class CoerceStringFieldsTest(unittest.TestCase):
    def test_non_strings_and_empty_string_return_empty(self):
        for value in (None, "", 0, False, [], {}, 123, True, ["a"], {"a": 1}):
            with self.subTest(value=value):
                self.assertEqual(coerce_key_name(value), "")
                self.assertEqual(coerce_label(value), "")

    def test_strings_keep_existing_normalization(self):
        self.assertEqual(coerce_key_name("  F1  "), "f1")
        self.assertEqual(coerce_label("  x  "), "x")
        self.assertEqual(coerce_label("  Copy 日本語  "), "Copy 日本語")


class NormalizeActionsTest(unittest.TestCase):
    def test_non_string_labels_become_empty(self):
        for label in (None, 0, False, [], {}, 123, ["a"], {"a": 1}):
            with self.subTest(label=label):
                self.assertEqual(
                    normalize_actions([{"type": "text", "label": label}]),
                    [{"type": "text", "label": ""}],
                )

    def test_empty_and_non_list_inputs_return_empty(self):
        for actions in ([], None, "x"):
            with self.subTest(actions=actions):
                self.assertEqual(normalize_actions(actions), [])

    def test_removes_non_dict_items_and_adds_empty_label(self):
        actions = [{"type": "text", "value": "a"}, "bad", 1, None, ["x"]]
        self.assertEqual(
            normalize_actions(actions),
            [{"type": "text", "value": "a", "label": ""}],
        )

    def test_strips_label(self):
        self.assertEqual(
            normalize_actions([{"type": "text", "label": "  x  "}]),
            [{"type": "text", "label": "x"}],
        )

    def test_does_not_mutate_input_and_deep_copies_items(self):
        actions = [{"type": "text", "label": "  x  ", "extra": {"values": ["a"]}}]
        normalized = normalize_actions(actions)
        self.assertEqual(actions[0]["label"], "  x  ")
        normalized[0]["label"] = "changed"
        normalized[0]["extra"]["values"].append("b")
        self.assertEqual(
            actions,
            [{"type": "text", "label": "  x  ", "extra": {"values": ["a"]}}],
        )

    def test_compatibility_normalization_is_equivalent_and_idempotent(self):
        actions = [{"type": "text", "label": "  x  "}, "bad", 1, None, ["x"]]
        normalized = normalize_actions(actions)
        self.assertEqual(normalize_actions(normalized), normalized)
        for trigger_actions in (actions, normalized):
            with self.subTest(actions=trigger_actions):
                config = ensure_config_compatibility(
                    {"triggers": [{"key": "f1", "actions": trigger_actions}]}
                )
                self.assertEqual(config["triggers"][0]["actions"], normalized)


class NormalizeHotkeyPresetsTest(unittest.TestCase):
    def test_removes_non_dict_items_and_normalizes_label_and_value(self):
        presets = [
            {"label": "  Paste  ", "value": " CTRL+V ", "extra": "kept"},
            "garbage",
            {"label": "  Copy", "value": "CTRL+C  "},
        ]

        self.assertEqual(
            normalize_hotkey_presets(presets),
            [
                {"label": "Paste", "value": "ctrl+v", "extra": "kept"},
                {"label": "Copy", "value": "ctrl+c"},
            ],
        )

    def test_non_list_input_returns_empty_list(self):
        for presets in (None, {"label": "Paste"}, "ctrl+v"):
            with self.subTest(presets=presets):
                self.assertEqual(normalize_hotkey_presets(presets), [])

    def test_removes_items_with_non_string_label_or_value(self):
        presets = [
            {"label": 1, "value": "ctrl+a"},
            {"label": {"name": "copy"}, "value": "ctrl+c"},
            {"label": "Paste", "value": ["ctrl", "v"]},
            {"label": "  Keep  ", "value": " CTRL+K "},
        ]

        self.assertEqual(
            normalize_hotkey_presets(presets),
            [{"label": "Keep", "value": "ctrl+k"}],
        )

    def test_none_and_missing_label_or_value_become_empty_strings(self):
        presets = [
            {"label": None, "value": None},
            {"label": "Copy"},
            {"value": "CTRL+V"},
            {},
        ]

        self.assertEqual(
            normalize_hotkey_presets(presets),
            [
                {"label": "", "value": ""},
                {"label": "Copy", "value": ""},
                {"value": "ctrl+v", "label": ""},
                {"label": "", "value": ""},
            ],
        )

    def test_is_idempotent(self):
        presets = [{"label": "  Paste  ", "value": " CTRL+V "}, "garbage"]

        self.assertEqual(
            normalize_hotkey_presets(normalize_hotkey_presets(presets)),
            normalize_hotkey_presets(presets),
        )


class ResolveHookKeysIndividualTest(unittest.TestCase):
    def test_missing_flag_with_stop_key_returns_true(self):
        self.assertTrue(resolve_hook_keys_individual({"hook_stop_key": "f1", "hook_toggle_key": ""}))

    def test_missing_flag_with_toggle_key_returns_true(self):
        self.assertTrue(resolve_hook_keys_individual({"hook_stop_key": "", "hook_toggle_key": "f2"}))

    def test_missing_flag_with_empty_keys_returns_false(self):
        self.assertFalse(resolve_hook_keys_individual({"hook_stop_key": "", "hook_toggle_key": ""}))

    def test_missing_flag_with_whitespace_only_keys_returns_false(self):
        self.assertFalse(resolve_hook_keys_individual({"hook_stop_key": "  ", "hook_toggle_key": "  "}))

    def test_explicit_false_flag_takes_precedence(self):
        self.assertFalse(resolve_hook_keys_individual({"hook_keys_individual": False, "hook_stop_key": "f1"}))

    def test_explicit_true_flag_takes_precedence(self):
        self.assertTrue(resolve_hook_keys_individual({"hook_keys_individual": True, "hook_stop_key": "", "hook_toggle_key": ""}))

    def test_non_dict_input_returns_false(self):
        for source in (None, [], "x"):
            with self.subTest(source=source):
                self.assertFalse(resolve_hook_keys_individual(source))


class EnsureConfigCompatibilityTest(unittest.TestCase):
    def test_non_string_hook_stop_key_becomes_empty(self):
        config = ensure_config_compatibility({"hook_stop_key": 123})
        self.assertEqual(config["hook_stop_key"], "")

    def test_non_string_hook_toggle_key_becomes_empty(self):
        config = ensure_config_compatibility({"hook_toggle_key": ["a"]})
        self.assertEqual(config["hook_toggle_key"], "")

    def test_non_string_active_keymap_id_becomes_empty(self):
        config = ensure_config_compatibility({"active_keymap_id": 7})
        self.assertEqual(config["active_keymap_id"], "")

    def test_non_string_legacy_trigger_key_becomes_empty(self):
        config = ensure_config_compatibility({"trigger_key": 123, "actions": []})
        self.assertEqual(len(config["triggers"]), 1)
        self.assertEqual(config["triggers"][0]["key"], "")
        self.assertEqual(config["triggers"][0]["actions"], [])

    def test_falsy_non_string_key_fields_keep_empty_behavior(self):
        for field in ("hook_stop_key", "hook_toggle_key", "active_keymap_id", "trigger_key"):
            for value in (0, False, [], {}, None):
                with self.subTest(field=field, value=value):
                    config = ensure_config_compatibility({field: value, "actions": []})
                    if field == "trigger_key":
                        self.assertEqual(len(config["triggers"]), 1)
                        self.assertEqual(config["triggers"][0]["key"], "")
                    else:
                        self.assertEqual(config[field], "")

    def test_string_key_fields_keep_existing_normalization(self):
        config = ensure_config_compatibility(
            {
                "hook_stop_key": " F12 ",
                "hook_toggle_key": " F11 ",
                "keymaps": [{"id": "km1"}, {"id": "km2"}],
                "active_keymap_id": " KM2 ",
            }
        )
        self.assertEqual(config["hook_stop_key"], "f12")
        self.assertEqual(config["hook_toggle_key"], "f11")
        self.assertEqual(config["active_keymap_id"], "km2")

    def test_legacy_string_trigger_with_empty_actions_converted(self):
        config = ensure_config_compatibility({"trigger_key": "F1", "actions": []})
        self.assertEqual(
            config["triggers"],
            [{"key": "f1", "label": "", "suppress": True, "run_to_end": False,
              "run_to_end_delay_ms": 300, "actions": []}],
        )

    def test_non_string_trigger_fields_become_empty(self):
        for value in (None, 0, False, [], {}, 5, ["a"], {"a": 1}):
            with self.subTest(value=value):
                config = ensure_config_compatibility(
                    {"triggers": [{"key": value, "label": value}]}
                )
                self.assertEqual(config["triggers"][0]["key"], "")
                self.assertEqual(config["triggers"][0]["label"], "")

    def test_non_string_keymap_ids_are_dropped_and_labels_become_empty(self):
        for value in (None, 0, False, [], {}, 7, [1], {"a": 1}):
            with self.subTest(value=value):
                config = ensure_config_compatibility(
                    {"keymaps": [{"id": value, "label": [1]},
                                 {"id": " KM1 ", "label": value}]}
                )
                self.assertEqual(
                    config["keymaps"], [{"id": "km1", "label": "", "mappings": {}}]
                )

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

    def test_non_string_hotkey_preset_label_is_removed(self):
        config = ensure_config_compatibility(
            {
                "hotkey_presets": [
                    {"label": 1, "value": "ctrl+a"},
                    {"label": "Keep", "value": "CTRL+K"},
                ]
            }
        )

        self.assertEqual(config["hotkey_presets"], [{"label": "Keep", "value": "ctrl+k"}])

    def test_hook_keys_individual_defaults_to_false(self):
        config = ensure_config_compatibility({})
        self.assertFalse(config["hook_keys_individual"])

    def test_hook_keys_individual_uses_normalized_keys(self):
        config = ensure_config_compatibility({"hook_stop_key": "F1"})
        self.assertEqual(config["hook_stop_key"], "f1")
        self.assertTrue(config["hook_keys_individual"])

    def test_hook_keys_individual_is_idempotent_when_keys_are_empty(self):
        config = ensure_config_compatibility({"hook_keys_individual": True})
        result = ensure_config_compatibility(config)
        self.assertTrue(result["hook_keys_individual"])

    def test_hotkey_preset_individual_fields_are_normalized(self):
        for raw_flag, raw_path, expected_flag, expected_path in (
            (True, "  user/hotkey_presets/personal.json  ", True, "user/hotkey_presets/personal.json"),
            ("true", 1, False, ""),
            (1, None, False, ""),
            (None, [], False, ""),
        ):
            with self.subTest(raw_flag=raw_flag, raw_path=raw_path):
                config = ensure_config_compatibility(
                    {
                        "hotkey_presets_individual": raw_flag,
                        "hotkey_presets_path": raw_path,
                    }
                )

                self.assertIs(config["hotkey_presets_individual"], expected_flag)
                self.assertEqual(config["hotkey_presets_path"], expected_path)

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

    def test_mouse_drag_keys_preserved(self):
        config = ensure_config_compatibility(
            {"triggers": [{"key": "a", "actions": [{
                "type": "mouse_click", "x": 100, "y": 200,
                "button": "right", "clicks": 1, "drag": True,
                "to_x": 400, "to_y": 500, "drag_speed": 750,
            }]}]}
        )
        action = config["triggers"][0]["actions"][0]
        self.assertIs(action["drag"], True)
        self.assertEqual(action["to_x"], 400)
        self.assertEqual(action["to_y"], 500)
        self.assertEqual(action["drag_speed"], 750)

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


class PathFieldCoercionTest(unittest.TestCase):
    def test_external_layout_paths_drop_non_strings(self):
        for value in (None, 0, False, [], {}, 123, True, ["a"], {"a": 1}):
            with self.subTest(value=value):
                config = ensure_config_compatibility({
                    "external_keyboard_layouts": [{"path": value}, {"path": "ok.json"}],
                })
                self.assertEqual(config["external_keyboard_layouts"], [{"path": "ok.json"}])

    def test_external_layout_legacy_and_dict_paths_preserve_case(self):
        for path in ("ok.json", "User/Keymaps/A.json", "C:/User/Keymaps/A.json"):
            for entry in (f"  {path}  ", {"path": f"  {path}  "}):
                with self.subTest(entry=entry):
                    config = ensure_config_compatibility({"external_keyboard_layouts": [entry]})
                    self.assertEqual(config["external_keyboard_layouts"], [{"path": path}])

    def test_non_string_switch_targets_rejected_even_with_matching_ids(self):
        for value in (None, 0, False, [], {}, 123, True, ["a"], {"a": 1}):
            with self.subTest(value=value):
                keymap_id = str(value).lower()
                config = ensure_config_compatibility({
                    "keymaps": [{"id": keymap_id, "mappings": {}}],
                    "keymap_switch_keys": {"F1": value, "F2": f"  {keymap_id}  "},
                })
                self.assertEqual(config["keymaps"][0]["id"], keymap_id)
                self.assertEqual(config["keymap_switch_keys"], {"f2": keymap_id})


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

    def test_action_mouse_drag(self) -> None:
        action = {"type": "mouse_click", "x": 100, "y": 200, "to_x": 400,
                  "to_y": 500, "button": "left", "drag": True, "drag_speed": 1000}
        self.assertEqual(format_action_list_item(0, action),
                         "01. [mouse_click] (100, 200)→(400, 500) left 1000px/s")

    def test_action_mouse_drag_default_speed(self) -> None:
        action = {"type": "mouse_click", "x": 100, "y": 200, "to_x": 400,
                  "to_y": 500, "button": "left", "drag": True}
        self.assertEqual(format_action_list_item(0, action),
                         "01. [mouse_click] (100, 200)→(400, 500) left 1000px/s")

    def test_action_mouse_drag_disabled_or_absent(self) -> None:
        for extra in ({"drag": False}, {}):
            with self.subTest(extra=extra):
                action = {"type": "mouse_click", "x": 10, "y": 20,
                          "button": "left", "clicks": 2, **extra}
                self.assertEqual(format_action_list_item(0, action),
                                 "01. [mouse_click] (10, 20) left x2")

    def test_preset(self):
        self.assertEqual(
            format_preset_list_item(0, {"label": "Win+D", "value": "windows+d"}),
            "01. windows+d: Win+D",
        )


if __name__ == "__main__":
    unittest.main()
