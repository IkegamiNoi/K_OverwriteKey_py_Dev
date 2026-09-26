from __future__ import annotations

import os
from typing import Any

from keyseq.domain.config import normalize_hotkey_presets
from . import save_path_resolution


def load_global_hotkey_presets_path(service, *, config_root: str) -> str:
    """config/config.json（起動エントリ）のグローバルプリセットパスを返す。

    返すのは保存されている表記のまま。未設定・空・非文字列・読込失敗・config_root 空
    のときは既定へ縮退する。
    """
    default_path = service.HOTKEY_PRESETS_RELATIVE_PATH
    if not config_root:
        return default_path

    startup = service._load_optional_json(service._startup_entry_path(config_root))
    if not isinstance(startup, dict):
        return default_path

    raw_hotkey_presets_path = startup.get("hotkey_presets_path")
    if not isinstance(raw_hotkey_presets_path, str):
        return default_path

    return raw_hotkey_presets_path.strip() or default_path


def load_hotkey_presets_file(
    service,
    stored_path: Any,
    *,
    config_root: str,
) -> list[Any] | None:
    """プリセットファイルを読み、読めた場合だけ正規化済みの list を返す。"""
    if not isinstance(stored_path, str) or not stored_path.strip():
        return None

    try:
        resolved_path = service._resolve_config_relative_path(stored_path, config_root)
        loaded = service._load_optional_json(resolved_path)
    except Exception:
        return None

    if not isinstance(loaded, dict):
        return None
    items = loaded.get("hotkey_presets")
    if not isinstance(items, list):
        return None
    return normalize_hotkey_presets(items)


def load_global_hotkey_presets(service, *, config_root: str) -> list[Any] | None:
    """config.json が指すグローバルプリセットを、読めた場合だけ返す。"""
    try:
        stored_path = load_global_hotkey_presets_path(service, config_root=config_root)
    except Exception:
        return None
    return load_hotkey_presets_file(service, stored_path, config_root=config_root)


def resolve_individual_hotkey_presets_path(
    service,
    runtime: dict[str, Any],
    *,
    config_root: str,
) -> str:
    """有効な個別プリセットの保存表記パスだけを返す。"""
    if runtime.get("hotkey_presets_individual") is not True or not config_root:
        return ""

    stored_path = runtime.get("hotkey_presets_path")
    if not isinstance(stored_path, str) or not stored_path.strip():
        return ""

    resolved_path = service._resolve_config_relative_path(stored_path, config_root)
    if not service.is_path_within(resolved_path, config_root, config_root):
        return ""
    return stored_path


def resolve_individual_hotkey_presets_read_path(runtime: dict[str, Any]) -> str:
    """config 外を含む個別プリセットの読み出し用保存表記パスを返す。"""
    if runtime.get("hotkey_presets_individual") is not True:
        return ""

    stored_path = runtime.get("hotkey_presets_path")
    if not isinstance(stored_path, str) or not stored_path.strip():
        return ""
    return stored_path


def resolve_hotkey_presets_save_path(
    service,
    runtime: dict[str, Any],
    *,
    config_root: str,
    keymap_set_path: str,
    individual: bool | None = None,
) -> str:
    """個別プリセットの保存表記パス、またはグローバル用の空文字を返す。"""
    use_individual = (
        runtime.get("hotkey_presets_individual") is True
        if individual is None
        else individual
    )
    effective_runtime = runtime
    if individual is not None:
        effective_runtime = {**runtime, "hotkey_presets_individual": use_individual}

    individual_path = resolve_individual_hotkey_presets_path(
        service,
        effective_runtime,
        config_root=config_root,
    )
    if individual_path:
        return individual_path

    if (
        not use_individual
        or not config_root
    ):
        return ""

    default_path = save_path_resolution.default_individual_hotkey_presets_path(
        service,
        keymap_set_path,
        config_root=config_root,
    )
    return service.to_config_relative_or_absolute(default_path, config_root)


def individual_hotkey_presets_save_rejection_reason(
    service,
    stored_path: str,
    *,
    config_root: str,
) -> str:
    """個別プリセットの最終保存先がグローバル領域と衝突する理由を返す。"""
    if not stored_path or not config_root:
        return ""

    resolved_path = service.resolve_config_path(stored_path, config_root)
    global_dir = os.path.dirname(service.HOTKEY_PRESETS_RELATIVE_PATH)
    if service.is_path_within(resolved_path, global_dir, config_root):
        return "reserved_dir"

    global_stored_path = load_global_hotkey_presets_path(
        service,
        config_root=config_root,
    )
    global_resolved_path = service.resolve_config_path(global_stored_path, config_root)
    if service.canonical_path(resolved_path, config_root) == service.canonical_path(
        global_resolved_path,
        config_root,
    ):
        return "global_conflict"
    return ""


def describe_individual_hotkey_presets_overwrite(
    service,
    stored_path: str,
    loaded_presets: list[Any] | None,
    *,
    config_root: str,
) -> dict[str, bool | list[Any] | None]:
    """個別プリセットの上書き確認要否と保存先の既存内容を返す。"""
    existing_presets = None

    resolved_path = service.resolve_config_path(stored_path, config_root)
    exists = bool(resolved_path and os.path.exists(resolved_path))
    if exists:
        existing_presets = load_hotkey_presets_file(
            service,
            stored_path,
            config_root=config_root,
        )

    conflict = (
        loaded_presets is not None
        and exists
        and (
            existing_presets is None
            or existing_presets != normalize_hotkey_presets(loaded_presets)
        )
    )
    return {"conflict": conflict, "existing": existing_presets}


def describe_hotkey_presets_source(
    service,
    runtime: dict[str, Any],
    *,
    config_root: str,
) -> dict[str, str]:
    """個別プリセットの状態と、現在表示中の一覧の出どころを返す。"""
    individual_enabled = runtime.get("hotkey_presets_individual") is True
    individual_path = resolve_individual_hotkey_presets_read_path(runtime)
    individual_presets = None

    if not individual_enabled:
        individual_state = "off"
    elif individual_path:
        individual_presets = load_hotkey_presets_file(
            service,
            individual_path,
            config_root=config_root,
        )
        individual_save_path = resolve_individual_hotkey_presets_path(
            service,
            runtime,
            config_root=config_root,
        )
        if individual_save_path:
            individual_state = "active" if individual_presets is not None else "missing"
        else:
            individual_state = "external" if individual_presets is not None else "external_missing"
    else:
        individual_state = "missing"

    if individual_presets is not None:
        displayed_source = "individual"
    elif load_global_hotkey_presets(service, config_root=config_root) is not None:
        displayed_source = "global"
    else:
        displayed_source = "builtin"

    return {
        "individual_state": individual_state,
        "displayed_source": displayed_source,
    }
