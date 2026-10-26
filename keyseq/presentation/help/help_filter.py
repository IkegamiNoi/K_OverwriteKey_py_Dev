"""Tk に依存しないヘルプ検索と元文字列上のハイライト計算。"""

from dataclasses import dataclass
from collections.abc import Sequence
import unicodedata


def normalize_text(s: str) -> str:
    return unicodedata.normalize("NFKC", s).casefold()


def parse_query(query: str) -> tuple[str, ...]:
    return tuple(normalize_text(query).split())


@dataclass(frozen=True)
class NormalizedText:
    text: str
    positions: tuple[int, ...]


def normalize_with_positions(s: str) -> NormalizedText:
    chunks = [normalize_text(char) for char in s]
    text = "".join(chunks)
    positions = tuple(index for index, chunk in enumerate(chunks) for _ in chunk)
    return NormalizedText(text, positions)


def _contains_term(text: str, term: str) -> bool:
    return bool(term) and term in text


def item_matches(fields: Sequence[str], terms: Sequence[str]) -> bool:
    if not terms:
        return True
    normalized = "\n".join(normalize_with_positions(field).text for field in fields)
    return all(_contains_term(normalized, normalize_text(term)) for term in terms)


def _term_ranges(text: str, term: str) -> list[tuple[int, int]]:
    if not term:
        return []
    ranges: list[tuple[int, int]] = []
    start = 0
    while True:
        index = text.find(term, start)
        if index < 0:
            return ranges
        ranges.append((index, index + len(term)))
        start = index + 1


def highlight_ranges(s: str, terms: Sequence[str]) -> list[tuple[int, int]]:
    if not terms:
        return []
    normalized = normalize_with_positions(s)
    ranges: set[tuple[int, int]] = set()
    for term in terms:
        for start, end in _term_ranges(normalized.text, normalize_text(term)):
            ranges.add((normalized.positions[start], normalized.positions[end - 1] + 1))
    return sorted(ranges)
