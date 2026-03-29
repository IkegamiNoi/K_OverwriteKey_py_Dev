from __future__ import annotations

import json
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "triggers": [
        {
            "key": "f1",
            "suppress": True,
            "label": "",
            "run_to_end": False,
            "run_to_end_delay_ms": 300,
            "actions": [
                {"type": "hotkey", "value": "ctrl+c"},
                {"type": "hotkey", "value": "alt+tab"},
                {"type": "hotkey", "value": "ctrl+tab"},
                {"type": "hotkey", "value": "ctrl+c"},
                {"type": "hotkey", "value": "f2"},
                {"type": "text", "value": "sample_text"},
            ],
        },
        {
            "key": "f2",
            "suppress": True,
            "label": "",
            "run_to_end": False,
            "run_to_end_delay_ms": 300,
            "actions": [
                {"type": "text", "value": "sequence_1"},
                {"type": "hotkey", "value": "ctrl+v"},
            ],
        },
    ],
    "hotkey_presets": [
        {"label": "Alt+Tab", "value": "alt+tab"},
        {"label": "Win+D", "value": "windows+d"},
        {"label": "Win+E", "value": "windows+e"},
        {"label": "Ctrl+Shift+Esc", "value": "ctrl+shift+esc"},
        {"label": "Win+R", "value": "windows+r"},
        {"label": "Win+Tab", "value": "windows+tab"},
        {"label": "Win+X", "value": "windows+x"},
        {"label": "Alt+F4", "value": "alt+f4"},
    ],
    "hook_stop_key": "",
    "hook_toggle_key": "",
    "keyboard_layout": "us_tkl",
    "keyboard_show_physical_key_labels": False,
    "debug_jis_special_key_events": False,
    "external_keyboard_layouts": [],
    "keymaps": [],
    "active_keymap_id": "",
    "keymap_switch_keys": {},
}


def normalize_key_name(value: str) -> str:
    return (value or "").strip().lower()


def safe_deepcopy(obj: Any) -> Any:
    return json.loads(json.dumps(obj, ensure_ascii=False))


def ensure_config_compatibility(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        data = {}
    config = safe_deepcopy(data)

    if "triggers" not in config and "trigger_key" in config:
        old_key = normalize_key_name(config.get("trigger_key", "f1"))
        old_actions = config.get("actions", [])
        if not isinstance(old_actions, list):
            old_actions = []
        config["triggers"] = [
            {
                "key": old_key,
                "label": "",
                "suppress": True,
                "run_to_end": False,
                "run_to_end_delay_ms": 300,
                "actions": old_actions,
            }
        ]

    raw_triggers = config.get("triggers")
    if not isinstance(raw_triggers, list):
        raw_triggers = []
    normalized_triggers: list[dict[str, Any]] = []
    for trigger in raw_triggers:
        if not isinstance(trigger, dict):
            continue
        t = safe_deepcopy(trigger)
        t["key"] = normalize_key_name(t.get("key", ""))
        t["label"] = (t.get("label") or "").strip()
        t["suppress"] = bool(t.get("suppress", True))
        t["run_to_end"] = bool(t.get("run_to_end", False))

        delay = t.get("run_to_end_delay_ms", 300)
        try:
            delay = int(delay)
        except Exception:
            delay = 300
        if delay < 0:
            delay = 0
        t["run_to_end_delay_ms"] = delay

        actions = t.get("actions")
        if not isinstance(actions, list):
            actions = []
        normalized_actions: list[dict[str, Any]] = []
        for action in actions:
            if not isinstance(action, dict):
                continue
            a = safe_deepcopy(action)
            a["label"] = (a.get("label") or "").strip()
            normalized_actions.append(a)
        t["actions"] = normalized_actions
        normalized_triggers.append(t)
    config["triggers"] = normalized_triggers

    raw_presets = config.get("hotkey_presets")
    if not isinstance(raw_presets, list):
        config["hotkey_presets"] = safe_deepcopy(DEFAULT_CONFIG["hotkey_presets"])
    else:
        normalized_presets: list[dict[str, Any]] = []
        for preset in raw_presets:
            if not isinstance(preset, dict):
                continue
            p = safe_deepcopy(preset)
            p["label"] = (p.get("label") or "").strip()
            p["value"] = (p.get("value") or "").strip().lower()
            normalized_presets.append(p)
        config["hotkey_presets"] = normalized_presets

    config["hook_stop_key"] = normalize_key_name(config.get("hook_stop_key", ""))
    config["hook_toggle_key"] = normalize_key_name(config.get("hook_toggle_key", ""))
    config.pop("hook_keymap_toggle_key", None)
    layout_id = config.get("keyboard_layout", "us_tkl")
    if not isinstance(layout_id, str):
        layout_id = "us_tkl"
    layout_id = layout_id.strip() or "us_tkl"
    config["keyboard_layout"] = layout_id
    config["keyboard_show_physical_key_labels"] = bool(config.get("keyboard_show_physical_key_labels", False))
    config["debug_jis_special_key_events"] = bool(config.get("debug_jis_special_key_events", False))

    raw_external_layouts = config.get("external_keyboard_layouts")
    normalized_external_layouts: list[dict[str, str]] = []
    if isinstance(raw_external_layouts, list):
        for item in raw_external_layouts:
            if isinstance(item, str):
                path = item.strip()
            elif isinstance(item, dict):
                path = str(item.get("path") or "").strip()
            else:
                continue
            if not path:
                continue
            normalized_external_layouts.append({"path": path})
    config["external_keyboard_layouts"] = normalized_external_layouts

    raw_keymaps = config.get("keymaps")
    normalized_keymaps: list[dict[str, Any]] = []
    seen_keymap_ids: set[str] = set()
    if isinstance(raw_keymaps, list):
        for item in raw_keymaps:
            if not isinstance(item, dict):
                continue

            keymap_id = normalize_key_name(item.get("id", ""))
            if not keymap_id or keymap_id in seen_keymap_ids:
                continue

            raw_mappings = item.get("mappings")
            normalized_mappings: dict[str, str] = {}
            if isinstance(raw_mappings, dict):
                for raw_source, raw_target in raw_mappings.items():
                    source = normalize_key_name(str(raw_source or ""))
                    target = normalize_key_name(str(raw_target or ""))
                    if not source or not target:
                        continue
                    normalized_mappings[source] = target

            normalized_keymaps.append(
                {
                    "id": keymap_id,
                    "label": (item.get("label") or "").strip(),
                    "mappings": normalized_mappings,
                }
            )
            seen_keymap_ids.add(keymap_id)
    config["keymaps"] = normalized_keymaps

    active_keymap_id = normalize_key_name(config.get("active_keymap_id", ""))
    keymap_ids = [str(item.get("id") or "") for item in normalized_keymaps]
    if active_keymap_id and active_keymap_id not in keymap_ids:
        active_keymap_id = ""
    if not active_keymap_id and keymap_ids:
        active_keymap_id = keymap_ids[0]
    config["active_keymap_id"] = active_keymap_id

    raw_keymap_switch_keys = config.get("keymap_switch_keys")
    normalized_keymap_switch_keys: dict[str, str] = {}
    seen_switch_target_ids: set[str] = set()
    if isinstance(raw_keymap_switch_keys, dict):
        for raw_key, raw_keymap_id in raw_keymap_switch_keys.items():
            switch_key = normalize_key_name(str(raw_key or ""))
            keymap_id = normalize_key_name(str(raw_keymap_id or ""))
            if not switch_key or not keymap_id:
                continue
            if keymap_id not in keymap_ids:
                continue
            if keymap_id in seen_switch_target_ids:
                continue
            normalized_keymap_switch_keys[switch_key] = keymap_id
            seen_switch_target_ids.add(keymap_id)
    config["keymap_switch_keys"] = normalized_keymap_switch_keys
    return config


def format_trigger_list_item(index: int, trigger: dict[str, Any]) -> str:
    key = normalize_key_name(trigger.get("key", ""))
    label = (trigger.get("label") or "").strip()
    if label:
        return f"{index + 1:02d}. {key}: {label}"
    return f"{index + 1:02d}. {key}"


def format_action_list_item(index: int, action: dict[str, Any]) -> str:
    action_type = (action.get("type") or "").strip().lower()
    if action_type == "mouse_click":
        x = action.get("x", "")
        y = action.get("y", "")
        button = action.get("button", "left")
        clicks = action.get("clicks", 1)
        value_display = f"({x}, {y}) {button} x{clicks}"
    else:
        value_display = action.get("value", "")

    label = (action.get("label") or "").strip()
    if label:
        return f"{index + 1:02d}. [{action_type}] {value_display}: {label}"
    return f"{index + 1:02d}. [{action_type}] {value_display}"


def format_preset_list_item(index: int, preset: dict[str, Any]) -> str:
    label = (preset.get("label") or "").strip()
    value = (preset.get("value") or "").strip()
    if label:
        return f"{index + 1:02d}. {value}: {label}"
    return f"{index + 1:02d}. {value}"



