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

