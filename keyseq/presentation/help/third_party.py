"""同梱ライセンス文書の読み込み。"""

from dataclasses import dataclass
import json
from pathlib import Path

from keyseq.presentation.help.bundled_paths import license_path, third_party_dir


@dataclass(frozen=True)
class ThirdPartyEntry:
    name: str
    version: str
    license: str
    file: str


@dataclass(frozen=True)
class ThirdPartyNotice:
    entry: ThirdPartyEntry
    text: str | None
    error: str = ""


def _parse_entries(value: object) -> list[ThirdPartyEntry]:
    if not isinstance(value, list):
        raise ValueError("third_party.json の形式が配列ではありません。")
    entries: list[ThirdPartyEntry] = []
    required = {"name", "version", "license", "file"}
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError(f"{index + 1} 件目の項目が不正です。")
        if any(not isinstance(item[key], str) or not item[key].strip() for key in required):
            raise ValueError(f"{index + 1} 件目に空または文字列以外の値があります。")
        filename = item["file"]
        if "/" in filename or "\\" in filename or ".." in filename:
            raise ValueError(f"{index + 1} 件目の file 名が不正です。")
        entries.append(ThirdPartyEntry(**item))
    return entries


def load_third_party(
    directory: Path | None = None,
) -> tuple[list[ThirdPartyNotice], str]:
    """一覧を読み、個別の全文が読めない場合も他の項目を返す。"""
    try:
        root = third_party_dir() if directory is None else directory
        raw = json.loads((root / "third_party.json").read_text(encoding="utf-8"))
        entries = _parse_entries(raw)
    except Exception as error:
        return [], str(error)
    notices: list[ThirdPartyNotice] = []
    for entry in entries:
        try:
            text = (root / entry.file).read_text(encoding="utf-8")
            notices.append(ThirdPartyNotice(entry, text))
        except Exception as error:
            notices.append(ThirdPartyNotice(entry, None, str(error)))
    return notices, ""


def load_license_text() -> str | None:
    """リポジトリ直下の LICENSE を読み込む。"""
    try:
        return license_path().read_text(encoding="utf-8")
    except Exception:
        return None
