"""同梱ライセンス文書の読み込み。"""

from dataclasses import dataclass
import json
from pathlib import Path

from keyseq.presentation.bundled_paths import license_path, third_party_dir
from keyseq.shared.i18n import tr


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
        raise ValueError(tr("help.third_party.array_required"))
    entries: list[ThirdPartyEntry] = []
    required = {"name", "version", "license", "file"}
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError(tr("help.third_party.entry_invalid", index=index + 1))
        if any(not isinstance(item[key], str) or not item[key].strip() for key in required):
            raise ValueError(tr("help.third_party.entry_values_invalid", index=index + 1))
        filename = item["file"]
        if "/" in filename or "\\" in filename or ".." in filename:
            raise ValueError(tr("help.third_party.filename_invalid", index=index + 1))
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
