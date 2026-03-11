from __future__ import annotations

import os
from typing import Any

from keyseq.domain.config import DEFAULT_CONFIG, ensure_config_compatibility, safe_deepcopy
from keyseq.infrastructure.json_repository import JsonRepository


class ConfigService:
    def __init__(self, repository: JsonRepository):
        self.repository = repository

    def new_default_data(self) -> dict[str, Any]:
        return safe_deepcopy(DEFAULT_CONFIG)

    def normalize_runtime_data(self, data: Any) -> dict[str, Any]:
        return ensure_config_compatibility(data)

    def load_if_exists(self, path: str) -> tuple[dict[str, Any], bool]:
        if not os.path.exists(path):
            return self.new_default_data(), False
        return self.load(path), True

    def load(self, path: str) -> dict[str, Any]:
        loaded = self.repository.load_json(path)
        return ensure_config_compatibility(loaded)

    def load_startup(self, startup_path: str) -> dict[str, Any]:
        if not os.path.exists(startup_path):
            return {}
        return self.repository.load_json(startup_path)

    def save_startup(self, path: str, data: Any) -> None:
        self.repository.save_json(path, data)

    def resolve_startup_config_path(self, startup: dict[str, Any], base_dir: str, default_path: str) -> str:
        config_path = default_path
        if not isinstance(startup, dict):
            return config_path
        cfg = startup.get("config_path")
        if not cfg:
            return config_path
        cfg_path = cfg if os.path.isabs(cfg) else os.path.join(base_dir, cfg)
        if os.path.exists(cfg_path):
            return cfg_path
        return config_path

    def resolve_startup_relative_path(self, path: str, base_dir: str) -> str:
        try:
            rel = os.path.relpath(path, base_dir)
            if rel.startswith(".."):
                return path
            return rel
        except Exception:
            return path

    def save(self, path: str, data: Any) -> dict[str, Any]:
        normalized = ensure_config_compatibility(data)
        self.repository.save_json(path, normalized)
        return normalized
