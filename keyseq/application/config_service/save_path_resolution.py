from __future__ import annotations

import os
import re
from typing import Any

from keyseq.application.save_plan import ACTION_SAVE_AS, CHILD_TRIGGER_SET, SavePlan


def resolve_trigger_set_save_path(
    service,
    runtime: dict[str, Any],
    *,
    config_root: str,
    keymap_set_path: str,
    split_base_dir: str,
    save_plan: SavePlan,
) -> str:
    entry = save_plan.entry_for(CHILD_TRIGGER_SET)
    if entry is not None and entry.action == ACTION_SAVE_AS:
        return os.path.abspath(
            service._resolve_config_relative_path(entry.target_path, config_root)
        )
    source_path = str(runtime.get(service.INTERNAL_TRIGGER_SET_SOURCE_PATH) or "").strip()
    if source_path:
        return service._resolve_config_relative_path(source_path, config_root)
    return default_trigger_set_path(
        service,
        keymap_set_path,
        config_root=config_root,
        split_base_dir=split_base_dir,
    )


def resolve_sequence_save_path(
    service,
    trigger: dict[str, Any],
    *,
    config_root: str,
    trigger_set_path: str,
    sequences_dir: str,
    used_paths: set[str],
) -> str:
    source_path = str(trigger.get(service.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
    if source_path:
        resolved_source_path = service._resolve_config_relative_path(source_path, config_root)
        stored_source_path = service.to_config_relative_or_absolute(resolved_source_path, config_root)
        collision_key = service.canonical_path(stored_source_path, config_root)
        if collision_key not in used_paths:
            used_paths.add(collision_key)
            return stored_source_path

    base_name = resolve_sequence_file_base_name(service, trigger)
    if is_default_trigger_set_area(service, trigger_set_path, config_root):
        return allocate_unique_relative_path(
            service,
            service.SEQUENCES_RELATIVE_DIR,
            base_name,
            "sequence",
            used_paths,
            config_root,
        )

    sequence_dir = sequences_dir or os.path.join(os.path.dirname(os.path.abspath(trigger_set_path)), "sequences")
    return allocate_unique_absolute_path(service, sequence_dir, base_name, "sequence", used_paths, config_root)


def resolve_sequence_file_base_name(service, trigger: dict[str, Any]) -> str:
    for candidate in (trigger.get("label"), trigger.get("key"), "sequence"):
        slug = slugify_file_stem(candidate)
        if slug:
            return slug
    return "sequence"


def is_default_trigger_set_area(service, trigger_set_path: str, config_root: str) -> bool:
    return service.is_path_within(
        trigger_set_path,
        os.path.join(config_root, "user", "trigger_sets"),
        config_root,
    )


def allocate_unique_relative_path(
    service,
    relative_dir: str,
    base_name: str,
    fallback: str,
    used_paths: set[str],
    config_root: str,
) -> str:
    stem = slugify_file_stem(base_name) or fallback
    index = 1
    while True:
        suffix = "" if index == 1 else f"_{index}"
        candidate = os.path.join(relative_dir, f"{stem}{suffix}.json")
        stored_candidate = service._normalize_path_separators(candidate)
        collision_key = service.canonical_path(stored_candidate, config_root)
        if collision_key not in used_paths:
            used_paths.add(collision_key)
            return stored_candidate
        index += 1


def allocate_unique_absolute_path(
    service,
    directory: str,
    base_name: str,
    fallback: str,
    used_paths: set[str],
    config_root: str,
) -> str:
    stem = slugify_file_stem(base_name) or fallback
    index = 1
    while True:
        suffix = "" if index == 1 else f"_{index}"
        candidate = os.path.join(directory, f"{stem}{suffix}.json")
        stored = service.to_config_relative_or_absolute(candidate, config_root)
        collision_key = service.canonical_path(stored, config_root)
        if collision_key not in used_paths:
            used_paths.add(collision_key)
            return stored
        index += 1


def resolve_keymap_file_base_name(service, keymap: dict[str, Any]) -> str:
    source_path = str(keymap.get(service.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
    if source_path:
        normalized_source = service._normalize_path_separators(source_path)
        source_prefix = service._normalize_path_separators(service.KEYMAPS_RELATIVE_DIR) + "/"
        if normalized_source.startswith(source_prefix):
            filename = os.path.splitext(os.path.basename(normalized_source))[0]
            slug = slugify_file_stem(filename)
            if slug:
                return slug

    for candidate in (keymap.get("id"), keymap.get("label"), "keymap"):
        slug = slugify_file_stem(candidate)
        if slug:
            return slug
    return "keymap"


def allocate_unique_keymap_path(
    service,
    base_name: str,
    used_relative_paths: set[str],
    config_root: str,
) -> str:
    stem = slugify_file_stem(base_name) or "keymap"
    index = 1
    while True:
        suffix = "" if index == 1 else f"_{index}"
        candidate = os.path.join(service.KEYMAPS_RELATIVE_DIR, f"{stem}{suffix}.json")
        stored_candidate = service._normalize_path_separators(candidate)
        collision_key = service.canonical_path(stored_candidate, config_root)
        if collision_key not in used_relative_paths:
            used_relative_paths.add(collision_key)
            return stored_candidate
        index += 1


def default_trigger_set_path(
    service,
    keymap_set_path: str,
    *,
    config_root: str,
    split_base_dir: str,
) -> str:
    stem = slugify_file_stem(os.path.splitext(os.path.basename(keymap_set_path))[0])
    filename = f"{stem or 'default'}.json"
    if split_base_dir:
        return os.path.join(split_base_dir, "trigger_sets", filename)
    return service._resolve_config_relative_path(
        os.path.join(service.TRIGGER_SETS_RELATIVE_DIR, filename),
        config_root,
    )


def slugify_file_stem(value: Any) -> str:
    normalized = str(value or "").strip()
    normalized = re.sub(r'[\\/:*?"<>|]+', "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip(" ._")
    if not normalized:
        return ""
    reserved_names = {
        "con",
        "prn",
        "aux",
        "nul",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
    }
    if normalized.lower() in reserved_names:
        normalized = f"{normalized}_"
    return normalized
