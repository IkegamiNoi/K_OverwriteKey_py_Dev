"""Pure validation for a batch of keymap switch-key assignments."""

from __future__ import annotations

from typing import Any

from keyseq.application.key_overlap import analyze_key_overlaps
from keyseq.domain.config import normalize_key_name


def validate_switch_batch(
    runtime: dict[str, Any],
    stop_key: str,
    toggle_key: str,
    new_keymaps: list[dict[str, Any]],
    row_keys: list[str],
    row_keymap_ids: list[str],
) -> tuple[int, str] | None:
    """Return the first invalid row (zero-based), or ``None`` when all pass."""
    completed_runtime = _runtime_with_new_keymaps(runtime, new_keymaps)
    analysis = analyze_key_overlaps(completed_runtime, stop_key, toggle_key)
    target_ids = {normalize_key_name(keymap_id) for keymap_id in row_keymap_ids}
    external_switches = _external_switches(completed_runtime, target_ids)
    normalized_keys: list[str] = []

    for index, raw_key in enumerate(row_keys):
        key = normalize_key_name(raw_key)
        error = _validate_row_key(
            key,
            index,
            normalize_key_name(stop_key),
            normalize_key_name(toggle_key),
            analysis.all_trigger_keys,
            analysis.all_source_keys,
            external_switches,
            normalized_keys,
        )
        if error is not None:
            return error
        normalized_keys.append(key)
    return None


def _runtime_with_new_keymaps(runtime: dict[str, Any], new_keymaps: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a shallow runtime copy whose keymap list includes the candidates."""
    completed_runtime = dict(runtime)
    existing_keymaps = runtime.get("keymaps")
    completed_keymaps = list(existing_keymaps) if isinstance(existing_keymaps, list) else []
    completed_keymaps.extend(new_keymaps)
    completed_runtime["keymaps"] = completed_keymaps
    return completed_runtime


def _external_switches(runtime: dict[str, Any], target_ids: set[str]) -> dict[str, str]:
    raw_switches = runtime.get("keymap_switch_keys")
    if not isinstance(raw_switches, dict):
        return {}
    keymaps = runtime.get("keymaps")
    names = {
        normalize_key_name(keymap.get("id", "")): str(keymap.get("label") or "").strip()
        or normalize_key_name(keymap.get("id", ""))
        for keymap in keymaps
        if isinstance(keymap, dict)
    } if isinstance(keymaps, list) else {}
    return {
        normalize_key_name(str(raw_key or "")): names.get(
            normalize_key_name(str(target_id or "")), normalize_key_name(str(target_id or ""))
        )
        for raw_key, target_id in raw_switches.items()
        if normalize_key_name(str(raw_key or ""))
        and normalize_key_name(str(target_id or "")) not in target_ids
    }


def _validate_row_key(
    key: str,
    row_number: int,
    stop_key: str,
    toggle_key: str,
    trigger_keys: frozenset[str],
    source_keys: frozenset[str],
    external_switches: dict[str, str],
    previous_keys: list[str],
) -> tuple[int, str] | None:
    if not key:
        return row_number, "切替キーは必須です。"
    if key == stop_key and stop_key:
        return row_number, f"直接切替キーが停止キーと重複しています:\n{key}"
    if key == toggle_key and toggle_key:
        return row_number, f"直接切替キーが一時停止/再開キーと重複しています:\n{key}"
    if key in trigger_keys:
        return row_number, f"直接切替キーが通常トリガーと重複しています:\n{key}"
    if key in source_keys:
        return row_number, f"直接切替キーがキーマップ元キーと重複しています:\n{key}"
    existing_target_name = external_switches.get(key)
    if existing_target_name:
        return row_number, f"この切替キーは既に使用されています:\n{key} -> {existing_target_name}"
    if key in previous_keys:
        return row_number, f"直接切替キーは既に使用されています:\n{key}"
    return None
