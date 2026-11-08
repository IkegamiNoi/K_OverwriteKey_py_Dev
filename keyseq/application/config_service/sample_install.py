from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

from keyseq.application.save_plan import (
    ACTION_SAVE_AS,
    CHILD_KEYMAP,
    CHILD_SEQUENCE,
    CHILD_TRIGGER_SET,
    ChildSaveEntry,
    SavePlan,
    compose_sequence_key,
)


SAMPLE_DIR = "sample"
SAMPLE_KEYMAP_SET_RELATIVE_PATH = "sample/keymap_sets/sample.json"


@dataclass(frozen=True)
class SampleInstallResult:
    status: Literal["written", "existing", "incomplete", "failed"]
    keymap_set_path: str
    error: str = ""


def sample_keymap_set_path(config_root: str) -> str:
    return os.path.abspath(os.path.join(config_root, SAMPLE_KEYMAP_SET_RELATIVE_PATH))


def _sample_save_plan(config_root: str) -> SavePlan:
    entries: list[ChildSaveEntry] = []
    for keymap_id, name in (
        ("keymap_1", "shortcuts"), ("keymap_2", "right_hand"), ("keymap_3", "numpad"),
    ):
        for kind, directory in ((CHILD_KEYMAP, "keymaps"), (CHILD_TRIGGER_SET, "trigger_sets")):
            entries.append(ChildSaveEntry(
                kind, keymap_id, ACTION_SAVE_AS,
                os.path.abspath(os.path.join(config_root, SAMPLE_DIR, directory, name + ".json")),
            ))
    for keymap_id, trigger_key, name in (
        ("keymap_1", "r", "select_line"), ("keymap_1", "c", "copy"),
        ("keymap_1", "v", "paste"), ("keymap_1", "t", "switch_app"),
        ("keymap_1", "a", "paste_line_to_app"),
        ("keymap_2", "h", "right_hand_guide"), ("keymap_3", "h", "numpad_guide"),
    ):
        entries.append(ChildSaveEntry(
            CHILD_SEQUENCE, compose_sequence_key(keymap_id, trigger_key), ACTION_SAVE_AS,
            os.path.abspath(os.path.join(config_root, SAMPLE_DIR, "sequences", name + ".json")),
        ))
    return SavePlan(entries=tuple(entries))


def install_sample(
    service, *, config_root: str, keyboard_layout_id: str, external_layout_path: str = "",
) -> SampleInstallResult:
    path = sample_keymap_set_path(config_root)
    try:
        if os.path.exists(path):
            if check_sample_complete(service, config_root=config_root):
                return SampleInstallResult("existing", path)
            return SampleInstallResult("incomplete", path, "Sample references are missing or unreadable")
        data = service.new_default_data()
        data["keyboard_layout"] = keyboard_layout_id
        if external_layout_path:
            data["external_keyboard_layouts"] = [{"path": external_layout_path}]
        service.save_runtime_data(
            path, data, config_root=config_root,
            split_base_dir=os.path.abspath(os.path.join(config_root, SAMPLE_DIR)),
            save_plan=_sample_save_plan(config_root), write_startup_entry=False,
        )
        return SampleInstallResult("written", path)
    except Exception as exc:
        return SampleInstallResult("failed", path, f"{type(exc).__name__}: {exc}")


def _load_object(service, path: str, config_root: str) -> dict[str, Any]:
    resolved = service.resolve_config_path(path, config_root)
    data = service.repository.load_json(resolved)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {resolved}")
    return data


def _entry_path(entry: Any) -> str:
    value = entry.get("path") if isinstance(entry, dict) else entry
    return value.strip() if isinstance(value, str) else ""


def check_sample_complete(service, *, config_root: str) -> bool:
    """構成セットから子JSONを辿る。外部配列ファイルはサンプルの子に含めない。"""
    try:
        root = _load_object(service, sample_keymap_set_path(config_root), config_root)
        if not any(key in root for key in ("keymaps", "active_keymap_path", "trigger_set_path")):
            return False
        keymap_paths = {_entry_path(entry) for entry in root.get("keymaps", [])}
        keymap_paths.add(_entry_path(root.get("active_keymap_path")))
        keymaps = [_load_object(service, path, config_root) for path in keymap_paths if path]
        trigger_paths = {_entry_path(item.get("trigger_set_path")) for item in [root, *keymaps]}
        trigger_sets = [_load_object(service, path, config_root) for path in trigger_paths if path]
        sequence_paths = {
            _entry_path(trigger.get("sequence_path"))
            for item in trigger_sets for trigger in item.get("triggers", [])
            if isinstance(trigger, dict)
        }
        for path in sequence_paths:
            if path:
                _load_object(service, path, config_root)
        return True
    except Exception:
        # 読めない参照元・子があっても既存のサンプルは変更しない。
        return False
