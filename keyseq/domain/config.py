from __future__ import annotations

import json
from typing import Any


DEFAULT_RUN_TO_END_DELAY_MS = 300
DEFAULT_DRAG_SPEED_PX_PER_SEC = 1000
DEFAULT_KEYBOARD_LAYOUT_ID = "us_tkl"


def coerce_nonnegative_int(value: Any, default: int) -> int:
    try:
        number = int(value)
    except Exception:
        number = int(default)
    if number < 0:
        number = 0
    return number


DEFAULT_CONFIG: dict[str, Any] = {
    "triggers": [],
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
    "hook_keys_individual": False,
    "hotkey_presets_individual": False,
    "hotkey_presets_path": "",
    "keyboard_layout": DEFAULT_KEYBOARD_LAYOUT_ID,
    "keyboard_show_physical_key_labels": False,
    "debug_jis_special_key_events": False,
    "external_keyboard_layouts": [],
    "keymaps": [{
        "id": "keymap_1", "label": "", "mappings": {},
        "triggers": [
            {
                "key": "f1",
                "suppress": True,
                "label": "",
                "run_to_end": False,
                "run_to_end_delay_ms": DEFAULT_RUN_TO_END_DELAY_MS,
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
                "run_to_end_delay_ms": DEFAULT_RUN_TO_END_DELAY_MS,
                "actions": [
                    {"type": "text", "value": "sequence_1"},
                    {"type": "hotkey", "value": "ctrl+v"},
                ],
            },
        ],
    }],
    "active_keymap_id": "keymap_1",
    "keymap_switch_keys": {},
}


def normalize_key_name(value: str) -> str:
    return (value or "").strip().lower()


def coerce_key_name(value: Any) -> str:
    return normalize_key_name(value) if isinstance(value, str) else ""


def coerce_label(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


HOOK_STOP_KEY = "hook_stop_key"
HOOK_TOGGLE_KEY = "hook_toggle_key"
HOOK_KEY_FIELDS: tuple[str, str] = (HOOK_STOP_KEY, HOOK_TOGGLE_KEY)


def normalize_hook_key_pair(stop_key: Any, toggle_key: Any) -> tuple[str, str]:
    """hook キーの対を正規化して (stop, toggle) で返す。"""
    return (
        normalize_key_name(str(stop_key or "")),
        normalize_key_name(str(toggle_key or "")),
    )


def resolve_hook_keys_individual(source: Any) -> bool:
    """hook キーを個別指定するかを決める（暫定仕様 06 §2 の移行規則）。

    明示フラグ hook_keys_individual があればそれに従う。
    無ければ「正規化後に stop / toggle の少なくとも一方が非空」なら個別指定 ON とみなす。
    """
    if not isinstance(source, dict):
        return False
    if "hook_keys_individual" in source:
        return bool(source["hook_keys_individual"])
    hook_stop_key, hook_toggle_key = normalize_hook_key_pair(
        source.get(HOOK_STOP_KEY, ""),
        source.get(HOOK_TOGGLE_KEY, ""),
    )
    return bool(hook_stop_key or hook_toggle_key)


def safe_deepcopy(obj: Any) -> Any:
    return json.loads(json.dumps(obj, ensure_ascii=False))


def normalize_hotkey_presets(presets: Any) -> list[dict[str, Any]]:
    """プリセット一覧を正規化する（非 dict 要素は除去・label は trim・value は trim + 小文字化）。"""
    if not isinstance(presets, list):
        return []

    normalized_presets: list[dict[str, Any]] = []
    for preset in presets:
        if not isinstance(preset, dict):
            continue
        p = safe_deepcopy(preset)
        label = p.get("label")
        value = p.get("value")
        if (label is not None and not isinstance(label, str)) or (
            value is not None and not isinstance(value, str)
        ):
            continue
        p["label"] = (label or "").strip()
        p["value"] = (value or "").strip().lower()
        normalized_presets.append(p)
    return normalized_presets


def normalize_actions(actions: Any) -> list[dict[str, Any]]:
    if not isinstance(actions, list):
        actions = []
    normalized_actions: list[dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        a = safe_deepcopy(action)
        a["label"] = coerce_label(a.get("label"))
        if "type" in a:
            a["type"] = coerce_label(a["type"])
        if "button" in a:
            a["button"] = coerce_label(a["button"])
        normalized_actions.append(a)
    return normalized_actions


def normalize_triggers(raw_triggers: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_triggers, list):
        raw_triggers = []
    normalized_triggers: list[dict[str, Any]] = []
    for trigger in raw_triggers:
        if not isinstance(trigger, dict):
            continue
        t = safe_deepcopy(trigger)
        t["key"] = coerce_key_name(t.get("key"))
        t["label"] = coerce_label(t.get("label"))
        t["suppress"] = bool(t.get("suppress", True))
        t["run_to_end"] = bool(t.get("run_to_end", False))

        t["run_to_end_delay_ms"] = coerce_nonnegative_int(
            t.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
            DEFAULT_RUN_TO_END_DELAY_MS,
        )

        t["actions"] = normalize_actions(t.get("actions"))
        if "_sequence_source_path" in trigger:
            t["_sequence_source_path"] = coerce_label(trigger["_sequence_source_path"])
        for key in (
            "_sequence_imported",
            "_sequence_dirty",
        ):
            if key in trigger:
                t[key] = safe_deepcopy(trigger.get(key))
        normalized_triggers.append(t)
    return normalized_triggers


def ensure_config_compatibility(data: Any) -> dict[str, Any]:
    from keyseq.domain.keymap_triggers import (
        INTERNAL_TRIGGER_SET_DIRTY,
        INTERNAL_TRIGGER_SET_IMPORTED,
        INTERNAL_TRIGGER_SET_PARENT_REFS,
        INTERNAL_TRIGGER_SET_SOURCE_PATH,
    )

    if not isinstance(data, dict):
        data = {}
    config = safe_deepcopy(data)
    config.pop(INTERNAL_TRIGGER_SET_SOURCE_PATH, None)
    config.pop(INTERNAL_TRIGGER_SET_PARENT_REFS, None)

    if "triggers" not in config and "trigger_key" in config:
        old_key = coerce_key_name(config.get("trigger_key", "f1"))
        old_actions = config.get("actions", [])
        if not isinstance(old_actions, list):
            old_actions = []
        config["triggers"] = [
            {
                "key": old_key,
                "label": "",
                "suppress": True,
                "run_to_end": False,
                "run_to_end_delay_ms": DEFAULT_RUN_TO_END_DELAY_MS,
                "actions": old_actions,
            }
        ]

    config["triggers"] = normalize_triggers(config.get("triggers"))

    raw_presets = config.get("hotkey_presets")
    if not isinstance(raw_presets, list):
        config["hotkey_presets"] = safe_deepcopy(DEFAULT_CONFIG["hotkey_presets"])
    else:
        config["hotkey_presets"] = normalize_hotkey_presets(raw_presets)

    config[HOOK_STOP_KEY] = coerce_key_name(config.get(HOOK_STOP_KEY, ""))
    config[HOOK_TOGGLE_KEY] = coerce_key_name(config.get(HOOK_TOGGLE_KEY, ""))
    config["hook_keys_individual"] = resolve_hook_keys_individual(config)
    hotkey_presets_individual = config.get("hotkey_presets_individual", False)
    config["hotkey_presets_individual"] = (
        hotkey_presets_individual if isinstance(hotkey_presets_individual, bool) else False
    )
    hotkey_presets_path = config.get("hotkey_presets_path", "")
    config["hotkey_presets_path"] = (
        hotkey_presets_path.strip() if isinstance(hotkey_presets_path, str) else ""
    )
    config.pop("hook_keymap_toggle_key", None)
    layout_id = config.get("keyboard_layout", DEFAULT_KEYBOARD_LAYOUT_ID)
    if not isinstance(layout_id, str):
        layout_id = DEFAULT_KEYBOARD_LAYOUT_ID
    layout_id = layout_id.strip() or DEFAULT_KEYBOARD_LAYOUT_ID
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
                path = coerce_label(item.get("path"))
            else:
                continue
            if not path:
                continue
            normalized_external_layouts.append({"path": path})
    config["external_keyboard_layouts"] = normalized_external_layouts

    raw_keymaps = data.get("keymaps")
    trigger_memo: dict[int, list[dict[str, Any]]] = {}
    normalized_keymaps: list[dict[str, Any]] = []
    seen_keymap_ids: set[str] = set()
    if isinstance(raw_keymaps, list):
        for item in raw_keymaps:
            if not isinstance(item, dict):
                continue

            keymap_id = coerce_key_name(item.get("id"))
            if not keymap_id or keymap_id in seen_keymap_ids:
                continue

            raw_mappings = item.get("mappings")
            normalized_mappings: dict[str, str] = {}
            if isinstance(raw_mappings, dict):
                for raw_source, raw_target in raw_mappings.items():
                    source = normalize_key_name(str(raw_source or ""))
                    target = coerce_key_name(raw_target)
                    if not source or not target:
                        continue
                    normalized_mappings[source] = target

            normalized_keymaps.append(
                {
                    "id": keymap_id,
                    "label": coerce_label(item.get("label")),
                    "mappings": normalized_mappings,
                }
            )
            if "triggers" in item:
                raw = item["triggers"]
                if isinstance(raw, list):
                    identity = id(raw)
                    if identity not in trigger_memo:
                        trigger_memo[identity] = normalize_triggers(raw)
                    normalized_keymaps[-1]["triggers"] = trigger_memo[identity]
                else:
                    normalized_keymaps[-1]["triggers"] = []
            for key in (
                INTERNAL_TRIGGER_SET_PARENT_REFS,
                INTERNAL_TRIGGER_SET_DIRTY, INTERNAL_TRIGGER_SET_IMPORTED,
            ):
                if key in item:
                    normalized_keymaps[-1][key] = safe_deepcopy(item[key])
            if INTERNAL_TRIGGER_SET_SOURCE_PATH in item:
                normalized_keymaps[-1][INTERNAL_TRIGGER_SET_SOURCE_PATH] = coerce_label(
                    item[INTERNAL_TRIGGER_SET_SOURCE_PATH]
                )
            if "_keymap_source_path" in item:
                normalized_keymaps[-1]["_keymap_source_path"] = coerce_label(item["_keymap_source_path"])
            for key in (
                "_keymap_imported",
                "_keymap_dirty",
            ):
                if key in item:
                    normalized_keymaps[-1][key] = safe_deepcopy(item.get(key))
            seen_keymap_ids.add(keymap_id)
    config["keymaps"] = normalized_keymaps

    active_keymap_id = coerce_key_name(config.get("active_keymap_id", ""))
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
            keymap_id = coerce_key_name(raw_keymap_id)
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
        if bool(action.get("drag")):
            to_x = action.get("to_x", "")
            to_y = action.get("to_y", "")
            speed = action.get("drag_speed", DEFAULT_DRAG_SPEED_PX_PER_SEC)
            value_display = f"({x}, {y})→({to_x}, {to_y}) {button} {speed}px/s"
        else:
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



