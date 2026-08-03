from __future__ import annotations

import os
import re
from typing import Any

from keyseq.domain.config import (
    DEFAULT_CONFIG,
    DEFAULT_RUN_TO_END_DELAY_MS,
    coerce_nonnegative_int,
    ensure_config_compatibility,
    normalize_key_name,
    safe_deepcopy,
)
from keyseq.infrastructure.json_repository import JsonRepository
from . import save_plan_execution, split_payloads

from keyseq.application.save_plan import (
    ACTION_SAVE_AS,
    CHILD_TRIGGER_SET,
    SavePlan,
)


class ConfigService:
    KEYMAP_SET_RELATIVE_PATH = os.path.join("user", "keymap_sets", "default.json")
    TRIGGER_SETS_RELATIVE_DIR = os.path.join("user", "trigger_sets")
    HOTKEY_PRESETS_RELATIVE_PATH = os.path.join("user", "hotkey_presets", "default.json")
    KEYMAPS_RELATIVE_DIR = os.path.join("user", "keymaps")
    SEQUENCES_RELATIVE_DIR = os.path.join("user", "sequences")
    LEGACY_CONFIG_RELATIVE_PATH = os.path.join("user", "config.json")
    INTERNAL_KEYMAP_SOURCE_PATH = "_keymap_source_path"
    INTERNAL_KEYMAP_IMPORTED = "_keymap_imported"
    INTERNAL_KEYMAP_DIRTY = "_keymap_dirty"
    INTERNAL_SEQUENCE_SOURCE_PATH = "_sequence_source_path"
    INTERNAL_SEQUENCE_IMPORTED = "_sequence_imported"
    INTERNAL_SEQUENCE_DIRTY = "_sequence_dirty"
    INTERNAL_TRIGGER_SET_SOURCE_PATH = "_trigger_set_source_path"
    PARENT_REFS_KEY = "_parent_refs"
    INTERNAL_KEYMAP_PARENT_REFS = "_keymap_parent_refs"
    INTERNAL_SEQUENCE_PARENT_REFS = "_sequence_parent_refs"
    INTERNAL_TRIGGER_SET_PARENT_REFS = "_trigger_set_parent_refs"

    def __init__(self, repository: JsonRepository):
        self.repository = repository

    def new_default_data(self) -> dict[str, Any]:
        return safe_deepcopy(DEFAULT_CONFIG)

    def new_empty_data(self) -> dict[str, Any]:
        data = self.new_default_data()
        data["triggers"] = []
        data["hotkey_presets"] = []
        data["keymaps"] = []
        data["active_keymap_id"] = ""
        data["keymap_switch_keys"] = {}
        return ensure_config_compatibility(data)

    def normalize_runtime_data(self, data: Any) -> dict[str, Any]:
        return ensure_config_compatibility(data)


    def load(self, path: str) -> dict[str, Any]:
        loaded = self.repository.load_json(path)
        return ensure_config_compatibility(loaded)

    def load_legacy_runtime_data(self, path: str) -> dict[str, Any]:
        return self.load(path)


    def load_runtime_data_from_keymap_set_path(
        self,
        keymap_set_path: str,
        *,
        config_root: str | None = None,
    ) -> dict[str, Any]:
        resolved_keymap_set_path = os.path.abspath(keymap_set_path)
        resolved_config_root = os.path.abspath(config_root) if config_root else self._infer_config_root_from_keymap_set_path(resolved_keymap_set_path)
        if not os.path.exists(resolved_keymap_set_path):
            raise FileNotFoundError(resolved_keymap_set_path)
        return self._load_split_config(
            config_root=resolved_config_root,
            keymap_set_path=resolved_keymap_set_path,
        )


    def load_startup(self, startup_path: str) -> dict[str, Any]:
        if not os.path.exists(startup_path):
            return {}
        return self.repository.load_json(startup_path)

    def save_startup(self, path: str, data: Any) -> None:
        self.repository.save_json(path, data)


    def resolve_startup_relative_path(self, path: str, base_dir: str) -> str:
        try:
            rel = os.path.relpath(path, base_dir)
            if rel.startswith(".."):
                return path
            return rel
        except Exception:
            return path


    def export_runtime_data(self, path: str, data: Any) -> dict[str, Any]:
        normalized = ensure_config_compatibility(data)
        self.repository.save_json(path, self._sanitize_runtime_for_storage(normalized))
        return normalized

    def load_keymap_file(
        self,
        path: str,
        *,
        used_keymap_ids: set[str] | None = None,
        imported: bool = True,
        config_root: str = "",
    ) -> dict[str, Any]:
        raw_keymap = self.repository.load_json(path)
        if not isinstance(raw_keymap, dict):
            raise ValueError("keymap JSON の形式が不正です。")
        used_ids = used_keymap_ids if used_keymap_ids is not None else set()
        keymap_id = self._generate_keymap_id(path, raw_keymap, used_ids)
        mappings = raw_keymap.get("mappings")
        if not isinstance(mappings, dict):
            mappings = {}
        keymap = {
            "id": keymap_id,
            "label": str(raw_keymap.get("label") or "").strip(),
            "mappings": safe_deepcopy(mappings),
            self.INTERNAL_KEYMAP_SOURCE_PATH: (
                self.to_config_relative_or_absolute(path, config_root)
                if config_root
                else path
            ),
            self.INTERNAL_KEYMAP_IMPORTED: bool(imported),
            self.INTERNAL_KEYMAP_DIRTY: False,
        }
        parent_refs = self._normalize_parent_refs(raw_keymap.get(self.PARENT_REFS_KEY))
        normalized = ensure_config_compatibility({"keymaps": [keymap]}).get("keymaps", [keymap])[0]
        if parent_refs is not None:
            normalized[self.INTERNAL_KEYMAP_PARENT_REFS] = parent_refs
        return normalized

    def save_keymap_file(
        self,
        path: str,
        keymap: dict[str, Any],
        *,
        parent_ref: str = "",
        config_root: str = "",
    ) -> dict[str, Any]:
        resolved_path = self._resolve_config_relative_path(path, config_root)
        stored_path = (
            self.to_config_relative_or_absolute(resolved_path, config_root)
            if config_root
            else path
        )
        normalized = ensure_config_compatibility({"keymaps": [keymap]}).get("keymaps", [])
        if not normalized:
            raise ValueError("保存できる keymap がありません。")
        item = normalized[0]
        parent_refs = self._normalize_parent_refs(keymap.get(self.INTERNAL_KEYMAP_PARENT_REFS))
        if parent_refs is not None:
            item[self.INTERNAL_KEYMAP_PARENT_REFS] = parent_refs
        payload = split_payloads.build_keymap_file_payload(self,
            item,
            parent_ref=parent_ref,
            config_root=config_root,
            target_path=resolved_path,
        )
        self.repository.save_json(resolved_path, payload)
        saved = safe_deepcopy(item)
        if self.PARENT_REFS_KEY in payload:
            saved[self.INTERNAL_KEYMAP_PARENT_REFS] = safe_deepcopy(payload[self.PARENT_REFS_KEY])
        saved[self.INTERNAL_KEYMAP_SOURCE_PATH] = stored_path
        saved[self.INTERNAL_KEYMAP_IMPORTED] = False
        saved[self.INTERNAL_KEYMAP_DIRTY] = False
        return saved

    def load_sequence_file(
        self,
        path: str,
        *,
        imported: bool = True,
        config_root: str = "",
    ) -> dict[str, Any]:
        raw_sequence = self.repository.load_json(path)
        if not isinstance(raw_sequence, dict):
            raise ValueError("sequence JSON の形式が不正です。")
        sequence = self._normalize_sequence_payload(raw_sequence)
        parent_refs = self._normalize_parent_refs(raw_sequence.get(self.PARENT_REFS_KEY))
        if parent_refs is not None:
            sequence[self.INTERNAL_SEQUENCE_PARENT_REFS] = parent_refs
        sequence[self.INTERNAL_SEQUENCE_SOURCE_PATH] = (
            self.to_config_relative_or_absolute(path, config_root)
            if config_root
            else path
        )
        sequence[self.INTERNAL_SEQUENCE_IMPORTED] = bool(imported)
        sequence[self.INTERNAL_SEQUENCE_DIRTY] = False
        return sequence

    def save_sequence_file(
        self,
        path: str,
        trigger: dict[str, Any],
        *,
        parent_ref: str = "",
        config_root: str = "",
    ) -> dict[str, Any]:
        resolved_path = self._resolve_config_relative_path(path, config_root)
        stored_path = (
            self.to_config_relative_or_absolute(resolved_path, config_root)
            if config_root
            else path
        )
        payload = split_payloads.build_sequence_payload(self,
            trigger,
            parent_ref=parent_ref,
            config_root=config_root,
            target_path=resolved_path,
        )
        self.repository.save_json(resolved_path, payload)
        sequence = self._normalize_sequence_payload(payload)
        if self.PARENT_REFS_KEY in payload:
            sequence[self.INTERNAL_SEQUENCE_PARENT_REFS] = safe_deepcopy(payload[self.PARENT_REFS_KEY])
        sequence[self.INTERNAL_SEQUENCE_SOURCE_PATH] = stored_path
        sequence[self.INTERNAL_SEQUENCE_IMPORTED] = False
        sequence[self.INTERNAL_SEQUENCE_DIRTY] = False
        return sequence

    def load_trigger_set_file(
        self,
        path: str,
        *,
        config_root: str,
        imported: bool = True,
    ) -> list[dict[str, Any]]:
        payload = self.repository.load_json(path)
        if not isinstance(payload, dict):
            raise ValueError("trigger_set JSON の形式が不正です。")
        triggers, _parent_refs = self._load_triggers_from_trigger_set(
            payload,
            config_root=config_root,
            imported=imported,
        )
        return triggers

    def save_trigger_set_file(
        self,
        path: str,
        data: dict[str, Any],
        *,
        config_root: str,
        parent_ref: str = "",
        save_plan: SavePlan | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        resolved_path = self._resolve_config_relative_path(path, config_root)
        normalized = ensure_config_compatibility(data)
        raw_triggers = data.get("triggers") if isinstance(data.get("triggers"), list) else []
        normalized_triggers = normalized.get("triggers", [])
        for raw_trigger, trigger in zip(
            (item for item in raw_triggers if isinstance(item, dict)),
            normalized_triggers,
        ):
            parent_refs = self._normalize_parent_refs(raw_trigger.get(self.INTERNAL_SEQUENCE_PARENT_REFS))
            if parent_refs is not None:
                trigger[self.INTERNAL_SEQUENCE_PARENT_REFS] = parent_refs
        trigger_payload, sequence_items = split_payloads.build_trigger_set_payloads(self,
            normalized,
            config_root=os.path.abspath(config_root),
            trigger_set_path=resolved_path,
            parent_ref=parent_ref,
            save_plan=save_plan or SavePlan(),
        )
        for item in sequence_items:
            if item["skip"]:
                continue
            self.repository.save_json(str(item["resolved_path"]), item["payload"])
        self.repository.save_json(resolved_path, trigger_payload)

        triggers = safe_deepcopy(normalized.get("triggers", [])) if isinstance(normalized.get("triggers"), list) else []
        by_key = {
            normalize_key_name(str(item.get("key") or "")): item
            for item in sequence_items
            if isinstance(item, dict) and not item["skip"]
        }
        for trigger in triggers:
            key = normalize_key_name(str(trigger.get("key") or ""))
            sequence_item = by_key.get(key)
            if not isinstance(sequence_item, dict):
                continue
            trigger[self.INTERNAL_SEQUENCE_SOURCE_PATH] = str(sequence_item.get("path") or "")
            if self.PARENT_REFS_KEY in sequence_item.get("payload", {}):
                trigger[self.INTERNAL_SEQUENCE_PARENT_REFS] = safe_deepcopy(
                    sequence_item["payload"][self.PARENT_REFS_KEY]
                )
            trigger[self.INTERNAL_SEQUENCE_IMPORTED] = False
            trigger[self.INTERNAL_SEQUENCE_DIRTY] = False
        if self.PARENT_REFS_KEY in trigger_payload:
            data[self.INTERNAL_TRIGGER_SET_PARENT_REFS] = safe_deepcopy(
                trigger_payload[self.PARENT_REFS_KEY]
            )
        return triggers, trigger_payload

    def save_runtime_data(
        self,
        keymap_set_path: str,
        data: Any,
        *,
        config_root: str,
        startup_data: Any = None,
        keep_legacy_copy: bool = False,
        legacy_path: str = "",
        split_base_dir: str = "",
        save_plan: SavePlan | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        return save_plan_execution.save_runtime_data(
            self, keymap_set_path, data, config_root=config_root, startup_data=startup_data,
            keep_legacy_copy=keep_legacy_copy, legacy_path=legacy_path,
            split_base_dir=split_base_dir, save_plan=save_plan,
        )

    def resolve_child_save_targets(
        self,
        data: Any,
        *,
        config_root: str,
        keymap_set_path: str,
        split_base_dir: str = "",
        save_plan: SavePlan | None = None,
    ) -> dict[tuple[str, str], str]:
        """ACTION_SAVE 時の子ファイル保存先を、書き込まずに解決する。"""
        return save_plan_execution.resolve_child_save_targets(
            self, data, config_root=config_root, keymap_set_path=keymap_set_path,
            split_base_dir=split_base_dir, save_plan=save_plan,
        )

    def find_dependency_blocked_sequences(
        self,
        data: Any,
        *,
        config_root: str,
        keymap_set_path: str,
        split_base_dir: str = "",
        save_plan: SavePlan,
    ) -> list[str]:
        """trigger_set を保存しない計画で、保存先が変わる sequence を返す。"""
        return save_plan_execution.find_dependency_blocked_sequences(
            self, data, config_root=config_root, keymap_set_path=keymap_set_path,
            split_base_dir=split_base_dir, save_plan=save_plan,
        )

    def read_parent_refs(self, path: str) -> list[str] | None:
        """子JSONの参照元を読み、読めない場合や未知の場合は None を返す。"""
        payload = self._load_optional_json(path)
        if not isinstance(payload, dict):
            return None
        return self._normalize_parent_refs(payload.get(self.PARENT_REFS_KEY))

    def _load_split_config(self, *, config_root: str, keymap_set_path: str) -> dict[str, Any]:
        keymap_set = self._load_optional_json(keymap_set_path)
        if not isinstance(keymap_set, dict):
            raise ValueError("keymap_set.json の読込に失敗しました。")
        return self._build_runtime_data_from_split(keymap_set, config_root=config_root)

    def _build_runtime_data_from_split(
        self,
        keymap_set: dict[str, Any],
        *,
        config_root: str,
    ) -> dict[str, Any]:
        runtime = self.new_default_data()

        for key in (
            "hook_stop_key",
            "hook_toggle_key",
            "keyboard_layout",
            "keyboard_show_physical_key_labels",
            "debug_jis_special_key_events",
        ):
            if key in keymap_set:
                runtime[key] = safe_deepcopy(keymap_set.get(key))

        runtime["external_keyboard_layouts"] = self._normalize_external_keyboard_layouts(
            keymap_set.get("external_keyboard_layouts"),
            config_root=config_root,
        )
        triggers, trigger_set_parent_refs = self._load_trigger_set(
            keymap_set.get("trigger_set_path"),
            config_root=config_root,
        )
        runtime["triggers"] = triggers
        trigger_set_path = str(keymap_set.get("trigger_set_path") or "").strip()
        if trigger_set_path:
            runtime[self.INTERNAL_TRIGGER_SET_SOURCE_PATH] = trigger_set_path
        if trigger_set_parent_refs is not None:
            runtime[self.INTERNAL_TRIGGER_SET_PARENT_REFS] = trigger_set_parent_refs
        runtime["hotkey_presets"] = self._load_named_list(
            keymap_set.get("hotkey_presets_path"),
            root_key="hotkey_presets",
            config_root=config_root,
        )

        keymaps: list[dict[str, Any]] = []
        keymap_switch_keys: dict[str, str] = {}
        loaded_keymap_ids_by_path: dict[str, str] = {}
        used_keymap_ids: set[str] = set()

        active_keymap_path = str(keymap_set.get("active_keymap_path") or "").strip()
        active_keymap_resolved_path = (
            self._resolve_config_relative_path(active_keymap_path, config_root)
            if active_keymap_path
            else ""
        )

        raw_keymaps = keymap_set.get("keymaps")
        if isinstance(raw_keymaps, list):
            for entry in raw_keymaps:
                loaded_entry = self._load_keymap_entry(
                    entry,
                    config_root=config_root,
                    used_keymap_ids=used_keymap_ids,
                )
                if loaded_entry is None:
                    continue

                keymap = loaded_entry["keymap"]
                keymaps.append(keymap)
                loaded_keymap_ids_by_path[loaded_entry["resolved_path"]] = str(keymap.get("id") or "")

                switch_key = normalize_key_name(loaded_entry["switch_key"])
                if switch_key:
                    keymap_switch_keys[switch_key] = str(keymap.get("id") or "")

        active_keymap_id = loaded_keymap_ids_by_path.get(active_keymap_resolved_path, "")
        if not active_keymap_id and active_keymap_resolved_path and os.path.exists(active_keymap_resolved_path):
            active_keymap = self._load_keymap_entry(
                {"path": active_keymap_path},
                config_root=config_root,
                used_keymap_ids=used_keymap_ids,
            )
            if active_keymap is not None:
                keymaps.append(active_keymap["keymap"])
                active_keymap_id = str(active_keymap["keymap"].get("id") or "")

        runtime["keymaps"] = keymaps
        runtime["active_keymap_id"] = active_keymap_id
        runtime["keymap_switch_keys"] = keymap_switch_keys
        normalized = ensure_config_compatibility(runtime)
        normalized_keymaps = normalized.get("keymaps", [])
        for keymap, normalized_keymap in zip(keymaps, normalized_keymaps):
            parent_refs = self._normalize_parent_refs(keymap.get(self.INTERNAL_KEYMAP_PARENT_REFS))
            if parent_refs is not None:
                normalized_keymap[self.INTERNAL_KEYMAP_PARENT_REFS] = parent_refs
        return normalized

    def _load_keymap_entry(
        self,
        entry: Any,
        *,
        config_root: str,
        used_keymap_ids: set[str],
    ) -> dict[str, Any] | None:
        if isinstance(entry, dict):
            stored_path = str(entry.get("path") or "").strip()
            switch_key = str(entry.get("switch_key") or "").strip()
        else:
            stored_path = str(entry or "").strip()
            switch_key = ""

        if not stored_path:
            return None

        resolved_path = self._resolve_config_relative_path(stored_path, config_root)
        raw_keymap = self._load_optional_json(resolved_path)
        if not isinstance(raw_keymap, dict):
            return None

        keymap_id = self._generate_keymap_id(stored_path, raw_keymap, used_keymap_ids)
        used_keymap_ids.add(keymap_id)

        mappings = raw_keymap.get("mappings")
        if not isinstance(mappings, dict):
            mappings = {}

        loaded_entry = {
            "resolved_path": resolved_path,
            "switch_key": switch_key,
            "keymap": {
                "id": keymap_id,
                "label": str(raw_keymap.get("label") or "").strip(),
                "mappings": safe_deepcopy(mappings),
                self.INTERNAL_KEYMAP_SOURCE_PATH: stored_path,
                self.INTERNAL_KEYMAP_IMPORTED: False,
                self.INTERNAL_KEYMAP_DIRTY: False,
            },
        }
        parent_refs = self._normalize_parent_refs(raw_keymap.get(self.PARENT_REFS_KEY))
        if parent_refs is not None:
            loaded_entry["keymap"][self.INTERNAL_KEYMAP_PARENT_REFS] = parent_refs
        return loaded_entry

    def _load_trigger_set(
        self,
        path_value: Any,
        *,
        config_root: str,
    ) -> tuple[list[dict[str, Any]], list[str] | None]:
        stored_path = str(path_value or "").strip()
        if not stored_path:
            return [], None

        resolved_path = self._resolve_config_relative_path(stored_path, config_root)
        loaded = self._load_optional_json(resolved_path)
        if not isinstance(loaded, dict):
            return [], None
        return self._load_triggers_from_trigger_set(loaded, config_root=config_root, imported=False)

    def _load_triggers_from_trigger_set(
        self,
        trigger_set: dict[str, Any],
        *,
        config_root: str,
        imported: bool,
    ) -> tuple[list[dict[str, Any]], list[str] | None]:
        trigger_set_parent_refs = self._normalize_parent_refs(trigger_set.get(self.PARENT_REFS_KEY))
        raw_triggers = trigger_set.get("triggers")
        if not isinstance(raw_triggers, list):
            return [], trigger_set_parent_refs

        triggers: list[dict[str, Any]] = []
        for raw_trigger in raw_triggers:
            if not isinstance(raw_trigger, dict):
                continue

            trigger = {
                "key": normalize_key_name(str(raw_trigger.get("key") or "")),
                "suppress": bool(raw_trigger.get("suppress", True)),
                "label": str(raw_trigger.get("label") or "").strip(),
                "run_to_end": bool(raw_trigger.get("run_to_end", False)),
                "run_to_end_delay_ms": self._coerce_nonnegative_int(
                    raw_trigger.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
                    DEFAULT_RUN_TO_END_DELAY_MS,
                ),
                "actions": safe_deepcopy(raw_trigger.get("actions", []))
                if isinstance(raw_trigger.get("actions"), list)
                else [],
            }
            sequence_path = str(raw_trigger.get("sequence_path") or "").strip()
            if sequence_path:
                resolved_sequence_path = self._resolve_config_relative_path(sequence_path, config_root)
                sequence = self._load_optional_json(resolved_sequence_path)
                if isinstance(sequence, dict):
                    normalized_sequence = self._normalize_sequence_payload(sequence)
                    trigger.update(normalized_sequence)
                    parent_refs = self._normalize_parent_refs(sequence.get(self.PARENT_REFS_KEY))
                    if parent_refs is not None:
                        trigger[self.INTERNAL_SEQUENCE_PARENT_REFS] = parent_refs
                    trigger[self.INTERNAL_SEQUENCE_SOURCE_PATH] = (
                        self.to_config_relative_or_absolute(sequence_path, config_root)
                        if config_root
                        else sequence_path
                    )
                    trigger[self.INTERNAL_SEQUENCE_IMPORTED] = bool(imported)
                    trigger[self.INTERNAL_SEQUENCE_DIRTY] = False
            triggers.append(trigger)

        normalized = ensure_config_compatibility({"triggers": triggers}).get("triggers", [])
        for trigger, normalized_trigger in zip(triggers, normalized):
            parent_refs = self._normalize_parent_refs(trigger.get(self.INTERNAL_SEQUENCE_PARENT_REFS))
            if parent_refs is not None:
                normalized_trigger[self.INTERNAL_SEQUENCE_PARENT_REFS] = parent_refs
        return normalized, trigger_set_parent_refs

    def _load_named_list(
        self,
        path_value: Any,
        *,
        root_key: str,
        config_root: str,
    ) -> list[Any]:
        stored_path = str(path_value or "").strip()
        if not stored_path:
            return []

        resolved_path = self._resolve_config_relative_path(stored_path, config_root)
        loaded = self._load_optional_json(resolved_path)
        if not isinstance(loaded, dict):
            return []

        items = loaded.get(root_key)
        if not isinstance(items, list):
            return []
        return safe_deepcopy(items)

    def _resolve_trigger_set_save_path(
        self,
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
                self._resolve_config_relative_path(entry.target_path, config_root)
            )
        source_path = str(runtime.get(self.INTERNAL_TRIGGER_SET_SOURCE_PATH) or "").strip()
        if source_path:
            return self._resolve_config_relative_path(source_path, config_root)
        return self._default_trigger_set_path(
            keymap_set_path,
            config_root=config_root,
            split_base_dir=split_base_dir,
        )

    def _resolve_sequence_save_path(
        self,
        trigger: dict[str, Any],
        *,
        config_root: str,
        trigger_set_path: str,
        sequences_dir: str,
        used_paths: set[str],
    ) -> str:
        source_path = str(trigger.get(self.INTERNAL_SEQUENCE_SOURCE_PATH) or "").strip()
        if source_path:
            resolved_source_path = self._resolve_config_relative_path(source_path, config_root)
            stored_source_path = self.to_config_relative_or_absolute(resolved_source_path, config_root)
            collision_key = self.canonical_path(stored_source_path, config_root)
            if collision_key not in used_paths:
                used_paths.add(collision_key)
                return stored_source_path

        base_name = self._resolve_sequence_file_base_name(trigger)
        if self._is_default_trigger_set_area(trigger_set_path, config_root):
            return self._allocate_unique_relative_path(
                self.SEQUENCES_RELATIVE_DIR,
                base_name,
                "sequence",
                used_paths,
                config_root,
            )

        sequence_dir = sequences_dir or os.path.join(os.path.dirname(os.path.abspath(trigger_set_path)), "sequences")
        return self._allocate_unique_absolute_path(sequence_dir, base_name, "sequence", used_paths, config_root)

    def _normalize_sequence_payload(self, sequence: dict[str, Any]) -> dict[str, Any]:
        return {
            "label": str(sequence.get("label") or "").strip(),
            "run_to_end": bool(sequence.get("run_to_end", False)),
            "run_to_end_delay_ms": self._coerce_nonnegative_int(
                sequence.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
                DEFAULT_RUN_TO_END_DELAY_MS,
            ),
            "actions": safe_deepcopy(sequence.get("actions", []))
            if isinstance(sequence.get("actions"), list)
            else [],
        }

    def _resolve_sequence_file_base_name(self, trigger: dict[str, Any]) -> str:
        for candidate in (trigger.get("label"), trigger.get("key"), "sequence"):
            slug = self.slugify_file_stem(candidate)
            if slug:
                return slug
        return "sequence"

    def _is_default_trigger_set_area(self, trigger_set_path: str, config_root: str) -> bool:
        return self.is_path_within(
            trigger_set_path,
            os.path.join(config_root, "user", "trigger_sets"),
            config_root,
        )

    def _allocate_unique_relative_path(
        self,
        relative_dir: str,
        base_name: str,
        fallback: str,
        used_paths: set[str],
        config_root: str,
    ) -> str:
        stem = self.slugify_file_stem(base_name) or fallback
        index = 1
        while True:
            suffix = "" if index == 1 else f"_{index}"
            candidate = os.path.join(relative_dir, f"{stem}{suffix}.json")
            stored_candidate = self._normalize_path_separators(candidate)
            collision_key = self.canonical_path(stored_candidate, config_root)
            if collision_key not in used_paths:
                used_paths.add(collision_key)
                return stored_candidate
            index += 1

    def _allocate_unique_absolute_path(
        self,
        directory: str,
        base_name: str,
        fallback: str,
        used_paths: set[str],
        config_root: str,
    ) -> str:
        stem = self.slugify_file_stem(base_name) or fallback
        index = 1
        while True:
            suffix = "" if index == 1 else f"_{index}"
            candidate = os.path.join(directory, f"{stem}{suffix}.json")
            stored = self.to_config_relative_or_absolute(candidate, config_root)
            collision_key = self.canonical_path(stored, config_root)
            if collision_key not in used_paths:
                used_paths.add(collision_key)
                return stored
            index += 1

    def _resolve_keymap_file_base_name(self, keymap: dict[str, Any]) -> str:
        source_path = str(keymap.get(self.INTERNAL_KEYMAP_SOURCE_PATH) or "").strip()
        if source_path:
            normalized_source = self._normalize_path_separators(source_path)
            source_prefix = self._normalize_path_separators(self.KEYMAPS_RELATIVE_DIR) + "/"
            if normalized_source.startswith(source_prefix):
                filename = os.path.splitext(os.path.basename(normalized_source))[0]
                slug = self.slugify_file_stem(filename)
                if slug:
                    return slug

        for candidate in (keymap.get("id"), keymap.get("label"), "keymap"):
            slug = self.slugify_file_stem(candidate)
            if slug:
                return slug
        return "keymap"

    def _allocate_unique_keymap_path(
        self,
        base_name: str,
        used_relative_paths: set[str],
        config_root: str,
    ) -> str:
        stem = self.slugify_file_stem(base_name) or "keymap"
        index = 1
        while True:
            suffix = "" if index == 1 else f"_{index}"
            candidate = os.path.join(self.KEYMAPS_RELATIVE_DIR, f"{stem}{suffix}.json")
            stored_candidate = self._normalize_path_separators(candidate)
            collision_key = self.canonical_path(stored_candidate, config_root)
            if collision_key not in used_relative_paths:
                used_relative_paths.add(collision_key)
                return stored_candidate
            index += 1

    def _sanitize_runtime_for_storage(self, data: dict[str, Any]) -> dict[str, Any]:
        sanitized = safe_deepcopy(data)
        sanitized.pop(self.INTERNAL_TRIGGER_SET_SOURCE_PATH, None)
        sanitized.pop(self.INTERNAL_TRIGGER_SET_PARENT_REFS, None)
        raw_triggers = sanitized.get("triggers")
        if isinstance(raw_triggers, list):
            cleaned_triggers: list[dict[str, Any]] = []
            for trigger in raw_triggers:
                if not isinstance(trigger, dict):
                    continue
                cleaned = safe_deepcopy(trigger)
                cleaned.pop(self.INTERNAL_SEQUENCE_SOURCE_PATH, None)
                cleaned.pop(self.INTERNAL_SEQUENCE_IMPORTED, None)
                cleaned.pop(self.INTERNAL_SEQUENCE_DIRTY, None)
                cleaned.pop(self.INTERNAL_SEQUENCE_PARENT_REFS, None)
                cleaned_triggers.append(cleaned)
            sanitized["triggers"] = cleaned_triggers

        raw_keymaps = sanitized.get("keymaps")
        if isinstance(raw_keymaps, list):
            cleaned_keymaps: list[dict[str, Any]] = []
            for keymap in raw_keymaps:
                if not isinstance(keymap, dict):
                    continue
                cleaned = safe_deepcopy(keymap)
                cleaned.pop(self.INTERNAL_KEYMAP_SOURCE_PATH, None)
                cleaned.pop(self.INTERNAL_KEYMAP_IMPORTED, None)
                cleaned.pop(self.INTERNAL_KEYMAP_DIRTY, None)
                cleaned.pop(self.INTERNAL_KEYMAP_PARENT_REFS, None)
                cleaned_keymaps.append(cleaned)
            sanitized["keymaps"] = cleaned_keymaps
        return sanitized

    def _normalize_external_keyboard_layouts(
        self,
        registrations: Any,
        *,
        config_root: str,
    ) -> list[dict[str, str]]:
        if not isinstance(registrations, list):
            return []

        base_dir = os.path.dirname(config_root)
        normalized: list[dict[str, str]] = []
        for item in registrations:
            if isinstance(item, dict):
                stored_path = str(item.get("path") or "").strip()
            else:
                stored_path = str(item or "").strip()
            if not stored_path:
                continue

            resolved_path = self._resolve_config_relative_path(stored_path, config_root)
            runtime_path = resolved_path
            try:
                relative_path = os.path.relpath(runtime_path, base_dir)
                if not relative_path.startswith(".."):
                    runtime_path = self._normalize_path_separators(relative_path)
            except Exception:
                runtime_path = self._normalize_path_separators(runtime_path)
            normalized.append({"path": runtime_path})
        return normalized

    def _generate_keymap_id(
        self,
        stored_path: str,
        raw_keymap: dict[str, Any],
        used_keymap_ids: set[str],
    ) -> str:
        preferred = normalize_key_name(raw_keymap.get("id", ""))
        if not preferred:
            preferred = normalize_key_name(os.path.splitext(os.path.basename(stored_path))[0])
        if not preferred:
            preferred = "keymap"

        candidate = preferred
        suffix = 2
        while candidate in used_keymap_ids:
            candidate = f"{preferred}_{suffix}"
            suffix += 1
        return candidate

    def ensure_split_config_dirs(self, config_root: str) -> None:
        os.makedirs(config_root, exist_ok=True)
        os.makedirs(os.path.join(config_root, "user"), exist_ok=True)
        os.makedirs(os.path.join(config_root, "user", "keymap_sets"), exist_ok=True)
        os.makedirs(os.path.join(config_root, "user", "keymaps"), exist_ok=True)
        os.makedirs(os.path.join(config_root, "user", "trigger_sets"), exist_ok=True)
        os.makedirs(os.path.join(config_root, "user", "hotkey_presets"), exist_ok=True)
        os.makedirs(os.path.join(config_root, "user", "sequences"), exist_ok=True)

    def _startup_entry_path(self, config_root: str) -> str:
        return os.path.join(config_root, "config.json")

    def _default_keymap_set_path(self, config_root: str) -> str:
        return self._resolve_config_relative_path(self.KEYMAP_SET_RELATIVE_PATH, config_root)

    def _default_trigger_set_path(
        self,
        keymap_set_path: str,
        *,
        config_root: str,
        split_base_dir: str,
    ) -> str:
        stem = self.slugify_file_stem(os.path.splitext(os.path.basename(keymap_set_path))[0])
        filename = f"{stem or 'default'}.json"
        if split_base_dir:
            return os.path.join(split_base_dir, "trigger_sets", filename)
        return self._resolve_config_relative_path(
            os.path.join(self.TRIGGER_SETS_RELATIVE_DIR, filename),
            config_root,
        )

    def _default_legacy_config_path(self, config_root: str) -> str:
        return self._resolve_config_relative_path(self.LEGACY_CONFIG_RELATIVE_PATH, config_root)

    def _infer_config_root_from_keymap_set_path(self, keymap_set_path: str) -> str:
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(keymap_set_path))))

    def resolve_config_path(self, path: str, config_root: str) -> str:
        """記録用の表記（config 相対を含む）を書き込み・存在確認に使える形へ解決する。"""
        return self._resolve_config_relative_path(path, config_root)

    def to_config_relative_or_absolute(self, path: str, config_root: str) -> str:
        absolute_path = os.path.abspath(self._resolve_config_relative_path(path, config_root))
        absolute_config_root = os.path.abspath(config_root)
        if self.is_path_within(absolute_path, absolute_config_root, config_root):
            relative_path = os.path.relpath(absolute_path, absolute_config_root)
            return self._normalize_path_separators(relative_path)
        return self._normalize_path_separators(absolute_path)

    def canonical_path(self, path: str, config_root: str) -> str:
        """比較専用の正規形。相対は config_root から解決し、normpath → normcase を適用する。

        戻り値を保存値や表示値には使用しない。
        """
        if not path:
            return ""
        resolved_path = path
        if not os.path.isabs(resolved_path) and config_root:
            resolved_path = os.path.join(config_root, resolved_path)
        return os.path.normcase(os.path.normpath(os.path.abspath(resolved_path)))

    def is_path_within(self, path: str, ancestor_dir: str, config_root: str = "") -> bool:
        """path が ancestor_dir 配下（同一パスを含む）かを canonical identity で判定する。"""
        canonical_path = self.canonical_path(path, config_root)
        canonical_ancestor = self.canonical_path(ancestor_dir, config_root)
        if not canonical_path or not canonical_ancestor:
            return False
        try:
            return os.path.commonpath([canonical_path, canonical_ancestor]) == canonical_ancestor
        except Exception:
            return False


    def _resolve_config_relative_path(self, path: str, config_root: str) -> str:
        normalized = str(path or "").strip()
        if not normalized:
            return ""
        if os.path.isabs(normalized):
            return normalized
        return os.path.normpath(os.path.join(config_root, normalized))

    def _normalize_path_separators(self, path: str) -> str:
        return str(path or "").replace("\\", "/")

    def _normalize_parent_refs(self, value: Any) -> list[str] | None:
        if not isinstance(value, list):
            return None
        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            parent_ref = item.strip()
            if parent_ref and parent_ref not in normalized:
                normalized.append(parent_ref)
        return normalized

    def _merge_parent_ref(
        self,
        refs: list[str] | None,
        parent_path: str,
        *,
        config_root: str,
    ) -> list[str]:
        merged = list(refs) if refs is not None else []
        if not parent_path:
            return merged
        parent_ref = self.to_config_relative_or_absolute(parent_path, config_root)
        canonical_parent_ref = self.canonical_path(parent_ref, config_root)
        if not any(
            self.canonical_path(existing, config_root) == canonical_parent_ref
            for existing in merged
        ):
            merged.append(parent_ref)
        return merged

    def _parent_refs_for_save(
        self,
        refs: list[str] | None,
        *,
        target_path: str,
        parent_ref: str,
        config_root: str,
    ) -> list[str] | None:
        if not parent_ref:
            return refs
        # §4「現在の上位パスを集合へ追加」= 追加先は **保存先ファイル**の集合。
        # 保存元（in-memory）の旧参照元は足さない（別名保存で他所の所有記録を捏造しないため）。
        existing_refs = self.read_parent_refs(target_path) if target_path else None
        merged = list(existing_refs) if existing_refs is not None else []
        return self._merge_parent_ref(merged, parent_ref, config_root=config_root)

    def slugify_file_stem(self, value: Any) -> str:
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

    def _coerce_nonnegative_int(self, value: Any, default: int) -> int:
        return coerce_nonnegative_int(value, default)

    def _load_optional_json(self, path: str) -> Any:
        if not path or not os.path.exists(path):
            return None
        try:
            return self.repository.load_json(path)
        except Exception:
            return None
