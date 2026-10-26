"""同梱データの場所を解決する。exe 化時は bundled_root だけを変更する。"""

from pathlib import Path


def bundled_root() -> Path:
    """同梱データの基準位置を返す。exe 化時の位置変更はこの関数に集約する。"""
    return Path(__file__).resolve().parents[3]


def license_path() -> Path:
    return bundled_root() / "LICENSE"


def help_content_dir() -> Path:
    return bundled_root() / "keyseq" / "presentation" / "help" / "content"


def help_content_path(lang: str = "ja") -> Path:
    return help_content_dir() / f"help_{lang}.json"


def third_party_dir() -> Path:
    return help_content_dir() / "third_party"
