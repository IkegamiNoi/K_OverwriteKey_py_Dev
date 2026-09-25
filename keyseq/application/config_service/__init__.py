from __future__ import annotations

import os
import shutil
from typing import Any

from keyseq.domain.config import (
    DEFAULT_CONFIG,
    DEFAULT_RUN_TO_END_DELAY_MS,
    HOOK_KEY_FIELDS,
    coerce_key_name,
    coerce_label,
    coerce_nonnegative_int,
    ensure_config_compatibility,
    normalize_actions,
    normalize_key_name,
    safe_deepcopy,
)
from keyseq.infrastructure.json_repository import JsonRepository
from keyseq.domain.keymap_triggers import (
    INTERNAL_TRIGGER_SET_DIRTY,
    INTERNAL_TRIGGER_SET_IMPORTED,
    trigger_set_members,
    ensure_active_triggers,
    get_active_triggers,
    migrate_single_json_triggers,
)
from . import keymap_set_history, orphan_scan, parent_refs_cleanup, quarantine, quarantine_manage, reference_scan, save_path_resolution, save_plan_execution, split_loading, split_payloads

from keyseq.application.save_plan import (
    CHILD_TRIGGER_SET,
    SavePlan,
    SavePlanError,
    split_sequence_key,
)


class ConfigService:
    KEYMAP_SET_RELATIVE_PATH = os.path.join("user", "keymap_sets", "default.json")
    KEYMAP_SET_HISTORY_RELATIVE_PATH = "keymap_set_history.json"
    TRIGGER_SETS_RELATIVE_DIR = os.path.join("user", "trigger_sets")
    HOTKEY_PRESETS_RELATIVE_PATH = os.path.join(
        "user", "hotkey_presets", "global", "default.json"
    )
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
    INTERNAL_LEGACY_TRIGGER_SET = "_legacy_trigger_set"

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
        ensure_active_triggers(data)
        return ensure_config_compatibility(data)

    def normalize_runtime_data(self, data: Any) -> dict[str, Any]:
        return ensure_config_compatibility(data)


    def load(self, path: str) -> dict[str, Any]:
        loaded = self.repository.load_json(path)
        normalized = ensure_config_compatibility(loaded)
        migrate_single_json_triggers(normalized)
        return normalized

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
        return split_loading.load_split_config(
            self,
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
        trigger_set_cache: dict[str, tuple[list[dict[str, Any]], list[str] | None, str]] | None = None,
    ) -> dict[str, Any]:
        raw_keymap = self.repository.load_json(path)
        if not isinstance(raw_keymap, dict):
            raise ValueError("keymap JSON の形式が不正です。")
        normalized = self._normalize_loaded_keymap(
            path, raw_keymap, used_keymap_ids=used_keymap_ids,
            imported=imported, config_root=config_root,
        )
        trigger_set_path = coerce_label(raw_keymap.get("trigger_set_path"))
        if trigger_set_path:
            split_loading.attach_trigger_set(
                self,
                normalized,
                trigger_set_path,
                config_root=config_root,
                trigger_sets=trigger_set_cache if trigger_set_cache is not None else {},
            )
        return normalized

    def _normalize_loaded_keymap(
        self,
        path: str,
        raw_keymap: dict[str, Any],
        *,
        used_keymap_ids: set[str] | None,
        imported: bool,
        config_root: str,
    ) -> dict[str, Any]:
        used_ids = used_keymap_ids if used_keymap_ids is not None else set()
        keymap_id = self._generate_keymap_id(path, raw_keymap, used_ids)
        mappings = raw_keymap.get("mappings")
        if not isinstance(mappings, dict):
            mappings = {}
        keymap = {
            "id": keymap_id,
            "label": coerce_label(raw_keymap.get("label")),
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
        runtime_data: dict[str, Any] | None = None,
        save_plan: SavePlan | None = None,
    ) -> dict[str, Any]:
        if runtime_data is not None and save_plan is not None:
            return self._save_keymap_with_plan(
                path,
                keymap,
                runtime_data=runtime_data,
                parent_ref=parent_ref,
                config_root=config_root,
                save_plan=save_plan,
            )
        return self._save_keymap_payload(path, keymap, parent_ref=parent_ref, config_root=config_root)

    def _save_keymap_payload(
        self,
        path: str,
        keymap: dict[str, Any],
        *,
        parent_ref: str,
        config_root: str,
    ) -> dict[str, Any]:
        resolved_path = self._resolve_config_relative_path(path, config_root)
        item = self._keymap_item_for_save(keymap)
        payload = split_payloads.build_keymap_file_payload(self,
            item,
            parent_ref=parent_ref,
            config_root=config_root,
            target_path=resolved_path,
        )
        self.repository.save_json(resolved_path, payload)
        return self._saved_keymap_result(item, path, resolved_path, config_root, payload)

    def _keymap_item_for_save(self, keymap: dict[str, Any]) -> dict[str, Any]:
        normalized = ensure_config_compatibility({"keymaps": [keymap]}).get("keymaps", [])
        if not normalized:
            raise ValueError("保存できる keymap がありません。")
        item = normalized[0]
        parent_refs = self._normalize_parent_refs(keymap.get(self.INTERNAL_KEYMAP_PARENT_REFS))
        if parent_refs is not None:
            item[self.INTERNAL_KEYMAP_PARENT_REFS] = parent_refs
        return item

    def _saved_keymap_result(
        self,
        item: dict[str, Any],
        path: str,
        resolved_path: str,
        config_root: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        saved = safe_deepcopy(item)
        if self.PARENT_REFS_KEY in payload:
            saved[self.INTERNAL_KEYMAP_PARENT_REFS] = safe_deepcopy(payload[self.PARENT_REFS_KEY])
        saved[self.INTERNAL_KEYMAP_SOURCE_PATH] = (
            self.to_config_relative_or_absolute(resolved_path, config_root)
            if config_root
            else path
        )
        saved[self.INTERNAL_KEYMAP_IMPORTED] = False
        saved[self.INTERNAL_KEYMAP_DIRTY] = False
        return saved

    def _save_keymap_with_plan(
        self,
        path: str,
        keymap: dict[str, Any],
        *,
        runtime_data: dict[str, Any],
        parent_ref: str,
        config_root: str,
        save_plan: SavePlan,
    ) -> dict[str, Any]:
        resolved_path = self._resolve_config_relative_path(path, config_root)
        root = os.path.abspath(config_root)
        payloads = self._build_keymap_save_payloads(
            runtime_data, parent_ref=parent_ref, config_root=root, save_plan=save_plan,
        )
        self._validate_requested_keymap_target(
            keymap, resolved_path, payloads, config_root=root,
        )
        self._validate_keymap_save_plan(
            runtime_data, payloads, config_root=root, parent_ref=parent_ref, save_plan=save_plan,
        )
        self._write_keymap_save_payloads(payloads)
        self._apply_keymap_save_payloads(runtime_data, payloads, config_root=root)
        saved = safe_deepcopy(keymap)
        self._apply_saved_keymap_state(saved, path, resolved_path, config_root, payloads)
        return saved

    def _validate_requested_keymap_target(
        self,
        keymap: dict[str, Any],
        resolved_path: str,
        payloads: dict[str, Any],
        *,
        config_root: str,
    ) -> None:
        item = next(
            (entry for entry in payloads["keymaps"] if entry.get("id") == keymap.get("id")),
            None,
        )
        if item is None or item["skip"] or self.canonical_path(
            item["resolved_path"], config_root
        ) != self.canonical_path(resolved_path, config_root):
            raise SavePlanError("キーマップの保存計画と保存先が一致しません。")

    def _build_keymap_save_payloads(
        self,
        runtime_data: dict[str, Any],
        *,
        parent_ref: str,
        config_root: str,
        save_plan: SavePlan,
    ) -> dict[str, Any]:
        return split_payloads.build_split_save_payloads(
            self, runtime_data, config_root=config_root, startup_data=None,
            keymap_set_path=parent_ref, keymap_set_name_path=parent_ref,
            legacy_path="", split_base_dir="", save_plan=save_plan,
        )

    def _validate_keymap_save_plan(
        self,
        runtime_data: dict[str, Any],
        payloads: dict[str, Any],
        *,
        config_root: str,
        parent_ref: str,
        save_plan: SavePlan,
    ) -> None:
        blocked = save_plan_execution.find_dependency_blocked_parents(
            self, runtime_data, config_root=config_root,
            keymap_set_path=parent_ref or self._default_keymap_set_path(config_root),
            save_plan=save_plan,
        )
        if any(kind == CHILD_TRIGGER_SET for kind, _ in blocked):
            raise SavePlanError("sequence の保存先変更には trigger_set の保存が必要です。")
        save_plan_execution.validate_save_plan(
            self, save_plan, runtime_data, payloads, config_root=config_root,
        )

    def _write_keymap_save_payloads(self, payloads: dict[str, Any]) -> None:
        for item in payloads["sequences"]:
            if not item["skip"]:
                self.repository.save_json(item["resolved_path"], item["payload"])
        for item in payloads["trigger_sets"]:
            if not item["skip"]:
                self.repository.save_json(item["resolved_path"], item["payload"])
        for item in payloads["keymaps"]:
            if not item["skip"]:
                self.repository.save_json(item["resolved_path"], item["payload"])

    def _apply_keymap_save_payloads(
        self, runtime_data: dict[str, Any], payloads: dict[str, Any], *, config_root: str,
    ) -> None:
        save_plan_execution.apply_saved_child_paths(self, runtime_data, payloads, config_root)
        self._clear_saved_keymap_child_state(runtime_data, payloads)

    def _clear_saved_keymap_child_state(
        self, runtime_data: dict[str, Any], payloads: dict[str, Any],
    ) -> None:
        saved_keymaps = self._clear_saved_keymap_states(runtime_data, payloads["keymaps"])
        self._clear_saved_trigger_set_states(runtime_data, payloads["trigger_sets"])
        self._clear_saved_sequence_states(runtime_data, payloads["sequences"])
        self._mark_deferred_keymap_states(
            runtime_data, payloads["trigger_sets"], saved_keymaps
        )

    def _clear_saved_keymap_states(
        self, runtime_data: dict[str, Any], items: list[dict[str, Any]],
    ) -> set[str]:
        saved_ids: set[str] = set()
        for item in items:
            keymap_id = str(item.get("id") or "")
            keymap = next(
                (entry for entry in runtime_data.get("keymaps", [])
                 if isinstance(entry, dict) and entry.get("id") == keymap_id),
                None,
            )
            if item["skip"] or keymap is None:
                continue
            saved_ids.add(keymap_id)
            keymap[self.INTERNAL_KEYMAP_IMPORTED] = False
            keymap[self.INTERNAL_KEYMAP_DIRTY] = False
            refs = item["payload"].get(self.PARENT_REFS_KEY)
            if refs is not None:
                keymap[self.INTERNAL_KEYMAP_PARENT_REFS] = safe_deepcopy(refs)
        return saved_ids

    def _clear_saved_trigger_set_states(
        self, runtime_data: dict[str, Any], items: list[dict[str, Any]],
    ) -> None:
        for item in items:
            if item["skip"]:
                continue
            for member in trigger_set_members(runtime_data, str(item["key"])):
                member[INTERNAL_TRIGGER_SET_DIRTY] = False
                member[INTERNAL_TRIGGER_SET_IMPORTED] = False
                refs = item["payload"].get(self.PARENT_REFS_KEY)
                if refs is not None:
                    member[self.INTERNAL_TRIGGER_SET_PARENT_REFS] = safe_deepcopy(refs)

    def _clear_saved_sequence_states(
        self, runtime_data: dict[str, Any], items: list[dict[str, Any]],
    ) -> None:
        for item in items:
            if item["skip"]:
                continue
            trigger_set_id, trigger_key = split_sequence_key(str(item["key"]))
            for member in trigger_set_members(runtime_data, trigger_set_id):
                for trigger in member.get("triggers", []):
                    if normalize_key_name(str(trigger.get("key") or "")) != trigger_key:
                        continue
                    trigger[self.INTERNAL_SEQUENCE_IMPORTED] = False
                    trigger[self.INTERNAL_SEQUENCE_DIRTY] = False
                    refs = item["payload"].get(self.PARENT_REFS_KEY)
                    if refs is not None:
                        trigger[self.INTERNAL_SEQUENCE_PARENT_REFS] = safe_deepcopy(refs)

    def _mark_deferred_keymap_states(
        self,
        runtime_data: dict[str, Any],
        trigger_sets: list[dict[str, Any]],
        saved_keymaps: set[str],
    ) -> None:
        for item in trigger_sets:
            if item["skip"] or not save_plan_execution.sequence_save_path_changed(item):
                continue
            for keymap_id in item["parent_ids"]:
                if keymap_id in saved_keymaps:
                    continue
                keymap = next(
                    (entry for entry in runtime_data.get("keymaps", [])
                     if isinstance(entry, dict) and entry.get("id") == keymap_id),
                    None,
                )
                if keymap is not None:
                    keymap[self.INTERNAL_KEYMAP_DIRTY] = True

    def _apply_saved_keymap_state(
        self,
        saved: dict[str, Any],
        path: str,
        resolved_path: str,
        config_root: str,
        payloads: dict[str, Any],
    ) -> None:
        saved[self.INTERNAL_KEYMAP_SOURCE_PATH] = self.to_config_relative_or_absolute(
            resolved_path, config_root
        ) if config_root else path
        saved[self.INTERNAL_KEYMAP_IMPORTED] = False
        saved[self.INTERNAL_KEYMAP_DIRTY] = False
        item = next(
            (entry for entry in payloads["keymaps"] if entry.get("id") == saved.get("id")),
            None,
        )
        if item is not None and self.PARENT_REFS_KEY in item["payload"]:
            saved[self.INTERNAL_KEYMAP_PARENT_REFS] = safe_deepcopy(
                item["payload"][self.PARENT_REFS_KEY]
            )

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
        triggers, _parent_refs = split_loading.load_triggers_from_trigger_set(
            self,
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
        raw_triggers = get_active_triggers(data)
        normalized_triggers = get_active_triggers(normalized)
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

        triggers = safe_deepcopy(get_active_triggers(normalized))
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
            for member in trigger_set_members(data):
                member[self.INTERNAL_TRIGGER_SET_PARENT_REFS] = safe_deepcopy(
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
        startup_entry_loaded: bool = False,
        keep_legacy_copy: bool = False,
        legacy_path: str = "",
        split_base_dir: str = "",
        migration_source_keymap_set_path: str = "",
        post_save_warnings: list[str] | None = None,
        save_plan: SavePlan | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        return save_plan_execution.save_runtime_data(
            self, keymap_set_path, data, config_root=config_root, startup_data=startup_data,
            startup_entry_loaded=startup_entry_loaded,
            keep_legacy_copy=keep_legacy_copy, legacy_path=legacy_path,
            split_base_dir=split_base_dir,
            migration_source_keymap_set_path=migration_source_keymap_set_path,
            post_save_warnings=post_save_warnings, save_plan=save_plan,
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

    def find_dependency_blocked_parents(self, data: Any, *, config_root: str,
        keymap_set_path: str, split_base_dir: str = "", save_plan: SavePlan,
    ) -> dict[tuple[str, str], list[str]]:
        return save_plan_execution.find_dependency_blocked_parents(
            self, data, config_root=config_root, keymap_set_path=keymap_set_path,
            split_base_dir=split_base_dir, save_plan=save_plan,
        )

    def read_parent_refs(self, path: str) -> list[str] | None:
        """子JSONの参照元を読み、読めない場合や未知の場合は None を返す。"""
        payload = self._load_optional_json(path)
        if not isinstance(payload, dict):
            return None
        return self._normalize_parent_refs(payload.get(self.PARENT_REFS_KEY))

    def inspect_parent_refs(
        self,
        runtime: dict[str, Any],
        *,
        config_root: str,
        keymap_set_path: str,
    ) -> list[Any]:
        return parent_refs_cleanup.inspect_parent_refs(
            self,
            runtime,
            config_root=config_root,
            keymap_set_path=keymap_set_path,
        )

    def prune_parent_refs(
        self,
        inspections: list[Any],
        *,
        runtime: dict[str, Any],
        config_root: str,
        keymap_set_path: str,
    ) -> Any:
        return parent_refs_cleanup.prune_parent_refs(
            self,
            inspections,
            runtime=runtime,
            config_root=config_root,
            keymap_set_path=keymap_set_path,
        )

    def collect_reference_paths(self, keymap_set_paths: list[str], *, config_root: str) -> Any:
        return reference_scan.collect_reference_paths(self, keymap_set_paths, config_root=config_root)

    def scan_orphans(
        self,
        *,
        config_root: str,
        scan_dirs: list[str],
        startup_keymap_set_path: str,
        current_keymap_set_path: str,
        protected_paths: list[str],
    ) -> Any:
        return orphan_scan.scan_orphans(
            self,
            config_root=config_root,
            scan_dirs=scan_dirs,
            startup_keymap_set_path=startup_keymap_set_path,
            current_keymap_set_path=current_keymap_set_path,
            protected_paths=protected_paths,
        )

    def collect_protected_paths(self, runtime: Any, *, keymap_set_path: str) -> Any:
        return orphan_scan.collect_protected_paths(self, runtime, keymap_set_path=keymap_set_path)

    def normalize_scan_dirs(self, values: Any, *, config_root: str) -> Any:
        return orphan_scan.normalize_scan_dirs(self, values, config_root=config_root)

    def quarantine_orphans(
        self,
        presented_paths: list[str],
        *,
        config_root: str,
        scan_dirs: list[str],
        startup_keymap_set_path: str,
        current_keymap_set_path: str,
        protected_paths: list[str],
    ) -> Any:
        return quarantine.quarantine_orphans(
            self,
            presented_paths,
            config_root=config_root,
            scan_dirs=scan_dirs,
            startup_keymap_set_path=startup_keymap_set_path,
            current_keymap_set_path=current_keymap_set_path,
            protected_paths=protected_paths,
        )

    def list_quarantine_units(self, *, config_root: str) -> Any:
        return quarantine_manage.list_quarantine_units(self, config_root=config_root)

    def restore_quarantine_unit(self, unit_id: str, *, config_root: str) -> Any:
        return quarantine_manage.restore_quarantine_unit(self, unit_id, config_root=config_root)

    def collect_unit_paths(self, unit_id: str, *, config_root: str) -> tuple[str, ...]:
        return quarantine_manage.collect_unit_paths(self, unit_id, config_root=config_root)

    def delete_quarantine_unit(
        self, unit_id: str, *, config_root: str, allow_invalid_manifest: bool = False,
    ) -> Any:
        return quarantine_manage.delete_quarantine_unit(self, unit_id, config_root=config_root, allow_invalid_manifest=allow_invalid_manifest)

    def _normalize_sequence_payload(self, sequence: dict[str, Any]) -> dict[str, Any]:
        return {
            "label": coerce_label(sequence.get("label")),
            "run_to_end": bool(sequence.get("run_to_end", False)),
            "run_to_end_delay_ms": self._coerce_nonnegative_int(
                sequence.get("run_to_end_delay_ms", DEFAULT_RUN_TO_END_DELAY_MS),
                DEFAULT_RUN_TO_END_DELAY_MS,
            ),
            "actions": normalize_actions(sequence.get("actions")),
        }

    def _sanitize_runtime_for_storage(self, data: dict[str, Any]) -> dict[str, Any]:
        sanitized = safe_deepcopy(data)
        sanitized.pop(self.INTERNAL_LEGACY_TRIGGER_SET, None)
        sanitized["triggers"] = []

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
                for key in (
                    self.INTERNAL_TRIGGER_SET_SOURCE_PATH,
                    self.INTERNAL_TRIGGER_SET_PARENT_REFS,
                    "_trigger_set_dirty", "_trigger_set_imported",
                ):
                    cleaned.pop(key, None)
                for trigger in cleaned.get("triggers", []):
                    for key in (
                        self.INTERNAL_SEQUENCE_SOURCE_PATH,
                        self.INTERNAL_SEQUENCE_IMPORTED,
                        self.INTERNAL_SEQUENCE_DIRTY,
                        self.INTERNAL_SEQUENCE_PARENT_REFS,
                    ):
                        trigger.pop(key, None)
                cleaned_keymaps.append(cleaned)
            sanitized["keymaps"] = cleaned_keymaps
        return sanitized

    def _generate_keymap_id(
        self,
        stored_path: str,
        raw_keymap: dict[str, Any],
        used_keymap_ids: set[str],
    ) -> str:
        preferred = coerce_key_name(raw_keymap.get("id"))
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
        os.makedirs(
            os.path.join(config_root, os.path.dirname(self.HOTKEY_PRESETS_RELATIVE_PATH)),
            exist_ok=True,
        )
        os.makedirs(os.path.join(config_root, "user", "sequences"), exist_ok=True)

    def apply_global_hook_key_defaults(
        self,
        runtime: dict[str, Any],
        *,
        config_root: str,
    ) -> dict[str, Any]:
        """個別指定 OFF の runtime へ config.json の hook キー全体デフォルトを注入する。"""
        runtime.setdefault("hook_keys_individual", False)
        if runtime.get("hook_keys_individual"):
            return runtime
        for field, value in zip(
            HOOK_KEY_FIELDS,
            split_loading.load_global_hook_keys(self, config_root=config_root),
        ):
            runtime[field] = value
        return runtime

    def apply_global_defaults(
        self,
        runtime: dict[str, Any],
        *,
        config_root: str,
    ) -> dict[str, Any]:
        """runtime を新規化・置換した直後に、config.json の全体デフォルトを注入する。"""
        self.apply_global_hook_key_defaults(runtime, config_root=config_root)
        hotkey_presets = split_loading.load_global_hotkey_presets(self, config_root=config_root)
        if hotkey_presets is not None:
            runtime["hotkey_presets"] = hotkey_presets
        return runtime

    def clear_individual_hotkey_presets(self, runtime: dict[str, Any]) -> dict[str, Any]:
        """個別プリセット指定を解除し、保存用の2キーを明示する。"""
        runtime["hotkey_presets_individual"] = False
        runtime["hotkey_presets_path"] = ""
        return runtime

    def relocate_individual_hotkey_presets(
        self,
        runtime: dict[str, Any],
        *,
        config_root: str,
        keymap_set_path: str,
    ) -> str:
        """別名保存先の個別プリセットパスを返し、必要な場合だけ実体を複製する。"""
        if runtime.get("hotkey_presets_individual") is not True:
            return ""

        destination_path = save_path_resolution.default_individual_hotkey_presets_path(
            self,
            keymap_set_path,
            config_root=config_root,
        )
        stored_destination_path = self.to_config_relative_or_absolute(
            destination_path,
            config_root,
        )
        stored_source_path = split_loading.resolve_individual_hotkey_presets_path(
            self,
            runtime,
            config_root=config_root,
        )
        if not stored_source_path:
            return stored_destination_path

        source_path = self.resolve_config_path(stored_source_path, config_root)
        if self.canonical_path(source_path, config_root) == self.canonical_path(
            destination_path,
            config_root,
        ):
            return stored_destination_path
        if os.path.exists(source_path) and not os.path.exists(destination_path):
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.copyfile(source_path, destination_path)
        return stored_destination_path

    def save_global_hotkey_presets(
        self,
        presets: list[Any],
        *,
        config_root: str,
    ) -> None:
        """config.json が指すグローバルプリセットファイルへ書き出す。"""
        stored_path = split_loading.load_global_hotkey_presets_path(
            self,
            config_root=config_root,
        )
        self.save_hotkey_presets(
            presets,
            config_root=config_root,
            stored_path=stored_path,
        )

    def save_hotkey_presets(
        self,
        presets: list[Any],
        *,
        config_root: str,
        stored_path: str,
    ) -> None:
        resolved_path = self.resolve_config_path(stored_path, config_root)
        self.repository.save_json(
            resolved_path,
            {"hotkey_presets": safe_deepcopy(presets)},
        )

    def load_keymap_set_history(self, *, config_root: str) -> tuple[dict[str, Any], str]:
        return keymap_set_history.load_history(self, config_root=config_root)

    def save_keymap_set_history(self, history: dict[str, Any], *, config_root: str) -> tuple[bool, str]:
        return keymap_set_history.save_history(self, history, config_root=config_root)

    def record_keymap_set_history(self, path: str, *, config_root: str) -> tuple[bool, str]:
        return keymap_set_history.record(self, path, config_root=config_root)

    def resolve_hotkey_presets_save_path(
        self,
        runtime: dict[str, Any],
        *,
        config_root: str,
        keymap_set_path: str,
        individual: bool | None = None,
    ) -> str:
        return split_loading.resolve_hotkey_presets_save_path(
            self,
            runtime,
            config_root=config_root,
            keymap_set_path=keymap_set_path,
            individual=individual,
        )

    def individual_hotkey_presets_save_rejection_reason(
        self,
        stored_path: str,
        *,
        config_root: str,
    ) -> str:
        return split_loading.individual_hotkey_presets_save_rejection_reason(
            self,
            stored_path,
            config_root=config_root,
        )

    def describe_individual_hotkey_presets_overwrite(
        self,
        stored_path: str,
        loaded_presets: list[Any] | None,
        *,
        config_root: str,
    ) -> dict[str, bool | list[Any] | None]:
        return split_loading.describe_individual_hotkey_presets_overwrite(
            self,
            stored_path,
            loaded_presets,
            config_root=config_root,
        )

    def load_global_hotkey_presets_path(self, *, config_root: str) -> str:
        return split_loading.load_global_hotkey_presets_path(self, config_root=config_root)

    def load_global_hotkey_presets(self, *, config_root: str) -> list[Any] | None:
        return split_loading.load_global_hotkey_presets(self, config_root=config_root)

    def load_individual_hotkey_presets(
        self,
        runtime: dict[str, Any],
        *,
        config_root: str,
    ) -> list | None:
        stored_path = split_loading.resolve_individual_hotkey_presets_read_path(runtime)
        return split_loading.load_hotkey_presets_file(
            self,
            stored_path,
            config_root=config_root,
        )

    def describe_hotkey_presets_source(
        self,
        runtime: dict[str, Any],
        *,
        config_root: str,
    ) -> dict[str, str]:
        return split_loading.describe_hotkey_presets_source(
            self,
            runtime,
            config_root=config_root,
        )

    def _startup_entry_path(self, config_root: str) -> str:
        return os.path.join(config_root, "config.json")

    def _default_keymap_set_path(self, config_root: str) -> str:
        return self._resolve_config_relative_path(self.KEYMAP_SET_RELATIVE_PATH, config_root)

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
        return save_path_resolution.slugify_file_stem(value)

    def _coerce_nonnegative_int(self, value: Any, default: int) -> int:
        return coerce_nonnegative_int(value, default)

    def _load_optional_json(self, path: str) -> Any:
        if not path or not os.path.exists(path):
            return None
        try:
            return self.repository.load_json(path)
        except Exception:
            return None
