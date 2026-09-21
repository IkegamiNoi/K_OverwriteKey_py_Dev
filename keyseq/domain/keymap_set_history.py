"""構成セットの読み込み履歴を扱う、I/O に依存しない規則。"""

from __future__ import annotations

from copy import deepcopy as _deepcopy
from typing import Any, Callable

__all__ = [
    "MAX_RECENT", "normalize_history", "is_recent_head", "push_recent",
    "remove_recent_at", "add_category", "rename_category", "remove_category",
    "add_to_category", "remove_category_entry_at", "sorted_categories",
]

MAX_RECENT: int = 20


def _label(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _entries(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    result = []
    for entry in raw:
        if isinstance(entry, dict):
            path = _label(entry.get("path"))
            if path:
                result.append({"path": path})
    return result


def _category_index(history: dict[str, Any], name: str) -> int | None:
    for index, category in enumerate(history["categories"]):
        if category["name"] == name:
            return index
    return None


def normalize_history(
    raw: Any, *, max_recent: int = MAX_RECENT,
) -> dict[str, Any]:
    """型不正と未知キーを除去し、保存順を保って正規化する。"""
    if not isinstance(raw, dict):
        return {"recent": [], "categories": []}
    categories = []
    names: set[str] = set()
    raw_categories = raw.get("categories")
    if isinstance(raw_categories, list):
        for category in raw_categories:
            if not isinstance(category, dict):
                continue
            name = _label(category.get("name"))
            if not name or name in names:
                continue
            names.add(name)
            categories.append({"name": name, "entries": _entries(category.get("entries"))})
    return {
        "recent": _entries(raw.get("recent"))[:max_recent],
        "categories": categories,
    }


def is_recent_head(
    history: dict[str, Any], path: str, *, key_of: Callable[[str], str],
) -> bool:
    """比較キーにより直近の先頭との一致を判定する。"""
    recent = history["recent"]
    return bool(recent) and key_of(recent[0]["path"]) == key_of(path)


def push_recent(
    history: dict[str, Any], path: str, *, key_of: Callable[[str], str],
    max_recent: int = MAX_RECENT,
) -> dict[str, Any]:
    """同一パスをすべて除去して先頭へ積み、上限を適用する。"""
    result = _deepcopy(history)
    key = key_of(path)
    recent = [entry for entry in result["recent"] if key_of(entry["path"]) != key]
    result["recent"] = ([{"path": path}] + recent)[:max_recent]
    return result


def remove_recent_at(history: dict[str, Any], index: int) -> dict[str, Any] | None:
    """指定位置の直近履歴だけを除去する。"""
    if not 0 <= index < len(history["recent"]):
        return None
    result = _deepcopy(history)
    del result["recent"][index]
    return result


def add_category(history: dict[str, Any], name: str) -> dict[str, Any] | None:
    """空名と同名を拒否し、trim 済みの分類を末尾へ追加する。"""
    name = _label(name)
    if not name or any(_label(c["name"]) == name for c in history["categories"]):
        return None
    result = _deepcopy(history)
    result["categories"].append({"name": name, "entries": []})
    return result


def rename_category(
    history: dict[str, Any], old_name: str, new_name: str,
) -> dict[str, Any] | None:
    """分類名を変更する。変更なしや同名衝突は None を返す。"""
    index = _category_index(history, old_name)
    new_name = _label(new_name)
    if index is None or not new_name:
        return None
    if any(_label(c["name"]) == new_name for c in history["categories"]):
        return None
    result = _deepcopy(history)
    result["categories"][index]["name"] = new_name
    return result


def remove_category(history: dict[str, Any], name: str) -> dict[str, Any] | None:
    """分類を配下のエントリごと除去する。"""
    index = _category_index(history, name)
    if index is None:
        return None
    result = _deepcopy(history)
    del result["categories"][index]
    return result


def add_to_category(
    history: dict[str, Any], name: str, path: str, *, key_of: Callable[[str], str],
) -> dict[str, Any] | None:
    """分類内の重複を拒否し、エントリを末尾へ追加する。"""
    index = _category_index(history, name)
    if index is None:
        return None
    key = key_of(path)
    if any(key_of(e["path"]) == key for e in history["categories"][index]["entries"]):
        return None
    result = _deepcopy(history)
    result["categories"][index]["entries"].append({"path": path})
    return result


def remove_category_entry_at(
    history: dict[str, Any], name: str, index: int,
) -> dict[str, Any] | None:
    """指定分類の指定位置だけを除去する。"""
    category_index = _category_index(history, name)
    if category_index is None:
        return None
    entries = history["categories"][category_index]["entries"]
    if not 0 <= index < len(entries):
        return None
    result = _deepcopy(history)
    del result["categories"][category_index]["entries"][index]
    return result


def sorted_categories(history: dict[str, Any]) -> list[dict[str, Any]]:
    """表示用に casefold 昇順の安定ソートを行う。"""
    return sorted(_deepcopy(history["categories"]), key=lambda c: c["name"].casefold())
