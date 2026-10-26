"""ヘルプ本文の形式、読み込み、および出荷前の文字検査。"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import unicodedata

from keyseq.presentation.help.bundled_paths import help_content_path


@dataclass(frozen=True)
class HelpBlock:
    kind: str
    text: str = ""
    items: tuple[str, ...] = ()


@dataclass(frozen=True)
class HelpItem:
    id: str
    title: str
    body: tuple[HelpBlock, ...]


@dataclass(frozen=True)
class HelpCategory:
    id: str
    title: str
    items: tuple[HelpItem, ...]


@dataclass(frozen=True)
class HelpContent:
    guide: tuple[HelpCategory, ...]
    faq: tuple[HelpCategory, ...]


@dataclass(frozen=True)
class HelpLoadResult:
    content: HelpContent | None
    error: str = ""


def _object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{location} は object でなければなりません")
    return value


def _nonempty_string(value: object, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{location} は空でない文字列でなければなりません")
    return value


def _array(value: object, location: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{location} は配列でなければなりません")
    return value


def _unique_id(identifier: str, location: str, seen: set[str]) -> None:
    if identifier in seen:
        raise ValueError(f"{location} が重複しています: {identifier}")
    seen.add(identifier)


def _parse_block(value: object, location: str) -> HelpBlock:
    block = _object(value, location)
    kind = block.get("type")
    if kind == "p":
        text = block.get("text")
        if not isinstance(text, str):
            raise ValueError(f"{location}.text は文字列でなければなりません")
        return HelpBlock("p", text=text)
    if kind == "list":
        values = _array(block.get("items"), f"{location}.items")
        if not values:
            raise ValueError(f"{location}.items は空にできません")
        if any(not isinstance(value, str) for value in values):
            raise ValueError(f"{location}.items の要素はすべて文字列でなければなりません")
        return HelpBlock("list", items=tuple(values))
    raise ValueError(f'{location}.type が不正です: {kind!r}')


def _parse_item(value: object, location: str, category_id: str, seen: set[str]) -> HelpItem:
    item = _object(value, location)
    identifier = _nonempty_string(item.get("id"), f"{location}.id")
    prefix = f"{category_id}."
    if not identifier.startswith(prefix) or not identifier[len(prefix):]:
        raise ValueError(f'{location}.id は "{prefix}名前" の形式でなければなりません')
    _unique_id(identifier, f"{location}.id", seen)
    title = _nonempty_string(item.get("title"), f"{location}.title")
    body = _array(item.get("body"), f"{location}.body")
    blocks = tuple(_parse_block(block, f"{location}.body[{i}]") for i, block in enumerate(body))
    return HelpItem(identifier, title, blocks)


def _parse_category(value: object, location: str, seen: set[str]) -> HelpCategory:
    category = _object(value, location)
    identifier = _nonempty_string(category.get("id"), f"{location}.id")
    _unique_id(identifier, f"{location}.id", seen)
    title = _nonempty_string(category.get("title"), f"{location}.title")
    items = _array(category.get("items"), f"{location}.items")
    parsed = tuple(
        _parse_item(item, f"{location}.items[{i}]", identifier, seen)
        for i, item in enumerate(items)
    )
    return HelpCategory(identifier, title, parsed)


def _parse_categories(value: object, tab: str, seen: set[str]) -> tuple[HelpCategory, ...]:
    categories = _array(value, f"tabs.{tab}")
    return tuple(
        _parse_category(category, f"tabs.{tab}[{i}]", seen)
        for i, category in enumerate(categories)
    )


def parse_help_content(data: object) -> HelpContent:
    """形式を検査し、全タブのデータを不変のデータクラスへ変換する。"""
    root = _object(data, "ルート")
    format_value = root.get("format")
    if type(format_value) is not int or format_value != 1:
        raise ValueError("format は整数の 1 でなければなりません")
    tabs = _object(root.get("tabs"), "tabs")
    if "guide" not in tabs or "faq" not in tabs:
        raise ValueError("tabs に guide と faq が必要です")
    seen: set[str] = set()
    guide = _parse_categories(tabs["guide"], "guide", seen)
    faq = _parse_categories(tabs["faq"], "faq", seen)
    return HelpContent(guide, faq)


def load_help_content(path: Path | None = None) -> HelpLoadResult:
    """UTF-8 の本文を読み込み、失敗理由を含む結果として返す。"""
    source = path if path is not None else help_content_path("ja")
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
        return HelpLoadResult(parse_help_content(data))
    except OSError as exc:
        return HelpLoadResult(None, f"ファイルを読み込めません: {exc}")
    except UnicodeDecodeError as exc:
        return HelpLoadResult(None, f"UTF-8 として読み込めません: {exc}")
    except json.JSONDecodeError as exc:
        return HelpLoadResult(None, f"JSON の形式が不正です: {exc}")
    except ValueError as exc:
        return HelpLoadResult(None, str(exc))


def item_plain_text(item: HelpItem) -> str:
    """本文ブロックを、箇条記号なしの検索・表示用テキストへ変換する。"""
    parts = [block.text if block.kind == "p" else "\n".join(block.items) for block in item.body]
    return "\n".join(parts)


def _text_values(content: HelpContent) -> list[str]:
    values: list[str] = []
    for category in (*content.guide, *content.faq):
        values.append(category.title)
        for item in category.items:
            values.append(item.title)
            for block in item.body:
                values.extend((block.text,) if block.kind == "p" else block.items)
    return values


def find_text_issues(content: HelpContent) -> list[str]:
    """表示文字列の NFC と、NFKC 後に結合文字を含まない条件を検査する。"""
    issues: list[str] = []
    for index, value in enumerate(_text_values(content)):
        if not unicodedata.is_normalized("NFC", value):
            issues.append(f"表示文字列[{index}] {value[:20]!r} が NFC ではありません")
        normalized_chars = (unicodedata.normalize("NFKC", char) for char in value)
        if any(unicodedata.category(char).startswith("M") for chunk in normalized_chars for char in chunk):
            issues.append(f"表示文字列[{index}] {value[:20]!r} の NFKC に結合文字が含まれています")
    return issues
