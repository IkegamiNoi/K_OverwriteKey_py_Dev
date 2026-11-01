from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence

from keyseq.shared.i18n import tr

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


def validate_file_line_request(
    path: str,
    line_number: int,
    *,
    encoding: str,
    out_of_range: str,
) -> None:
    if encoding not in (ENCODING_UTF_8, ENCODING_SHIFT_JIS):
        raise FileLineError(tr("application.file_line.encoding_invalid", encoding=encoding or tr("application.file_line.empty"), path=path))
    if out_of_range not in (OUT_OF_RANGE_ERROR, OUT_OF_RANGE_EMPTY, OUT_OF_RANGE_WRAP):
        raise FileLineError(tr("application.file_line.out_of_range_invalid", value=out_of_range or tr("application.file_line.empty"), path=path))
    if not isinstance(line_number, int) or isinstance(line_number, bool):
        raise FileLineError(tr("application.file_line.line_number_invalid", line_number=repr(line_number), path=path))


def load_file_lines(path: str, *, encoding: str) -> list[str]:
    content_bytes = _read_bytes(path)
    try:
        codec = "utf-8-sig" if encoding == ENCODING_UTF_8 else "cp932"
        content = content_bytes.decode(codec)
    except UnicodeDecodeError as exc:
        raise FileLineError(
            tr("application.file_line.decode_failed", encoding=encoding, path=path)
        ) from exc
    return _split_lines(content)


def pick_file_line(
    lines: Sequence[str],
    line_number: int,
    *,
    out_of_range: str,
    path: str,
) -> str | None:
    line_count = len(lines)
    if 1 <= line_number <= line_count:
        return lines[line_number - 1]
    if out_of_range == OUT_OF_RANGE_EMPTY:
        return None
    if out_of_range == OUT_OF_RANGE_WRAP:
        if line_count == 0:
            raise FileLineError(
                tr("application.file_line.empty_wrap", line_number=line_number, path=path)
            )
        return lines[((line_number - 1) % line_count)]
    raise FileLineError(
        tr("application.file_line.line_out_of_range", line_number=line_number, line_count=line_count, path=path)
    )


def read_file_line(
    path: str,
    line_number: int,
    *,
    encoding: str,
    out_of_range: str,
) -> str | None:
    validate_file_line_request(
        path,
        line_number,
        encoding=encoding,
        out_of_range=out_of_range,
    )
    lines = load_file_lines(path, encoding=encoding)
    return pick_file_line(lines, line_number, out_of_range=out_of_range, path=path)


def _read_bytes(path: str) -> bytes:
    try:
        size = os.path.getsize(path)
        if size > MAX_FILE_LINE_BYTES:
            raise FileLineError(
                tr("application.file_line.too_large_bytes", size=size, path=path)
            )
        with open(path, "rb") as file:
            content = file.read(MAX_FILE_LINE_BYTES + 1)
    except FileLineError:
        raise
    except (OSError, ValueError) as exc:
        raise FileLineError(tr("application.file_line.read_failed", path=path, error=exc)) from exc
    if len(content) > MAX_FILE_LINE_BYTES:
        raise FileLineError(
            tr("application.file_line.too_large_over", path=path)
        )
    return content


def _split_lines(content: str) -> list[str]:
    if not content:
        return []
    lines = _NEWLINE_PATTERN.split(content)
    if content.endswith(("\r", "\n")):
        lines.pop()
    return lines
