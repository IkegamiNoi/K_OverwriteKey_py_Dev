from __future__ import annotations

import json
import os
from typing import Any


class JsonRepository:
    def load_json(self, path: str) -> Any:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def save_json(self, path: str, data: Any) -> None:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

