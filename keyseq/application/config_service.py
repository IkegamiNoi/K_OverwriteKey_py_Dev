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

    def save(self, path: str, data: Any) -> dict[str, Any]:
        normalized = ensure_config_compatibility(data)
        self.repository.save_json(path, normalized)
        return normalized

