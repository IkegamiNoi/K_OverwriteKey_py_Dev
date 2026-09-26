from __future__ import annotations

import os
import re
from collections.abc import Mapping

from keyseq.domain.sequence_control import (
    DEFAULT_ENCODING,
    DEFAULT_OUT_OF_RANGE,
    ENCODING_SHIFT_JIS,
    ENCODING_UTF_8,
    OUT_OF_RANGE_EMPTY,
    OUT_OF_RANGE_ERROR,
    OUT_OF_RANGE_WRAP,
)


MAX_FILE_LINE_BYTES = 1_048_576
_NEWLINE_PATTERN = re.compile(r"\r\n|\r|\n")


class FileLineError(Exception):
    """Raised when a file_line action cannot resolve a line to send."""


def resolve_file_line_path(path: str, config_root: str) -> str:
    if not path:
        return ""
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(config_root, path))


def normalize_file_line_options(action: Mapping) -> tuple[str, str, str, str]:
    path = _option_string(action, "path")
    counter = _option_string(action, "counter")
    encoding = _option_string(action, "encoding").lower() or DEFAULT_ENCODING
    out_of_range = _option_string(action, "out_of_range").lower() or DEFAULT_OUT_OF_RANGE
    return path, counter, encoding, out_of_range


def _option_string(action: Mapping, key: str) -> str:
    value = action.get(key)
    return value.strip() if isinstance(value, str) else ""


def read_file_line(
    path: str,
    line_number: int,
    *,
    encoding: str,
    out_of_range: str,
) -> str | None:
    if encoding not in (ENCODING_UTF_8, ENCODING_SHIFT_JIS):
        raise FileLineError(f"文字コードが不正です: {encoding or '(空)'}（ファイル: {path}）")
    if out_of_range not in (OUT_OF_RANGE_ERROR, OUT_OF_RANGE_EMPTY, OUT_OF_RANGE_WRAP):
        raise FileLineError(f"範囲外の扱いが不正です: {out_of_range or '(空)'}（ファイル: {path}）")
    if not isinstance(line_number, int) or isinstance(line_number, bool):
        raise FileLineError(f"行番号が整数ではありません: {line_number!r}（ファイル: {path}）")

    content_bytes = _read_bytes(path)
    try:
        codec = "utf-8-sig" if encoding == ENCODING_UTF_8 else "cp932"
        content = content_bytes.decode(codec)
    except UnicodeDecodeError as exc:
        raise FileLineError(
            f"ファイルを文字コード {encoding} で復号できません（ファイル: {path}）"
        ) from exc

    lines = _split_lines(content)
    line_count = len(lines)
    if 1 <= line_number <= line_count:
        return lines[line_number - 1]
    if out_of_range == OUT_OF_RANGE_EMPTY:
        return None
    if out_of_range == OUT_OF_RANGE_WRAP:
        if line_count == 0:
            raise FileLineError(
                f"空ファイルでは行番号を折り返せません（行番号: {line_number}, 行数: 0, ファイル: {path}）"
            )
        return lines[((line_number - 1) % line_count)]
    raise FileLineError(
        f"行番号が範囲外です（行番号: {line_number}, 行数: {line_count}, ファイル: {path}）"
    )


def _read_bytes(path: str) -> bytes:
    try:
        size = os.path.getsize(path)
        if size > MAX_FILE_LINE_BYTES:
            raise FileLineError(
                f"ファイルサイズが上限 1 MB を超えています（サイズ: {size} バイト, ファイル: {path}）"
            )
        with open(path, "rb") as file:
            content = file.read(MAX_FILE_LINE_BYTES + 1)
    except FileLineError:
        raise
    except (OSError, ValueError) as exc:
        raise FileLineError(f"ファイルを読み込めません（ファイル: {path}）: {exc}") from exc
    if len(content) > MAX_FILE_LINE_BYTES:
        raise FileLineError(
            f"ファイルサイズが上限 1 MB を超えています（サイズ: 1 MB 超, ファイル: {path}）"
        )
    return content


def _split_lines(content: str) -> list[str]:
    if not content:
        return []
    lines = _NEWLINE_PATTERN.split(content)
    if content.endswith(("\r", "\n")):
        lines.pop()
    return lines
