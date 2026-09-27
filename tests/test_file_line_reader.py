from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from keyseq.application.file_line_reader import (
    FileLineError,
    MAX_FILE_LINE_BYTES,
    load_file_lines,
    normalize_file_line_options,
    pick_file_line,
    read_file_line,
    resolve_file_line_path,
    validate_file_line_request,
)


class FileLineReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.path = self.root / "lines.txt"

    def _write(self, content: bytes) -> str:
        self.path.write_bytes(content)
        return str(self.path)

    def _read(self, line_number: int, *, mode: str = "error", encoding: str = "utf-8") -> str | None:
        return read_file_line(str(self.path), line_number, encoding=encoding, out_of_range=mode)

    def test_reads_regular_lines_first_and_last(self) -> None:
        self._write(b"first\nsecond\nlast")
        self.assertEqual(self._read(1), "first")
        self.assertEqual(self._read(3), "last")

    def test_trailing_newline_does_not_add_a_line(self) -> None:
        self._write(b"first\nlast\n")
        self.assertEqual(self._read(2), "last")
        with self.assertRaisesRegex(FileLineError, "行数: 2"):
            self._read(3)

    def test_splits_crlf_cr_and_lf_without_splitting_other_controls(self) -> None:
        self._write(b"one\r\ntwo\rthree\nfour\x0bnot-a-break\x0cstill-same")
        self.assertEqual(self._read(1), "one")
        self.assertEqual(self._read(2), "two")
        self.assertEqual(self._read(3), "three")
        self.assertEqual(self._read(4), "four\x0bnot-a-break\x0cstill-same")

    def test_empty_line_is_returned_as_empty_string(self) -> None:
        self._write(b"before\n\nafter")
        self.assertEqual(self._read(2), "")

    def test_utf8_bom_is_removed(self) -> None:
        self._write(b"\xef\xbb\xbfhello")
        self.assertEqual(self._read(1), "hello")

    def test_shift_jis_uses_cp932_extensions(self) -> None:
        # cp932 の 0x8160 は U+FF5E（全角チルダ）へ復号される（Windows の慣例。U+301C 波ダッシュではない）
        self._write(b"\x87\x40\x81\x60")
        self.assertEqual(self._read(1, encoding="shift_jis"), "\u2460\uff5e")

    def test_decode_failure_has_encoding_and_path(self) -> None:
        self._write(b"\x81")
        with self.assertRaisesRegex(FileLineError, "shift_jis") as caught:
            self._read(1, encoding="shift_jis")
        self.assertIn(str(self.path), str(caught.exception))

    def test_size_limit_accepts_exact_limit_and_rejects_one_byte_more(self) -> None:
        self._write(b"a" * MAX_FILE_LINE_BYTES)
        self.assertEqual(len(self._read(1)), MAX_FILE_LINE_BYTES)
        self._write(b"a" * (MAX_FILE_LINE_BYTES + 1))
        with self.assertRaisesRegex(FileLineError, "上限 1 MB"):
            self._read(1)

    def test_missing_file_is_an_error(self) -> None:
        with self.assertRaisesRegex(FileLineError, "読み込めません"):
            read_file_line(str(self.path), 1, encoding="utf-8", out_of_range="error")

    def test_out_of_range_error_empty_and_wrap(self) -> None:
        self._write(b"one\ntwo\nthree")
        for number in (0, 4, -1):
            with self.subTest(number=number):
                with self.assertRaisesRegex(FileLineError, "行番号.*行数: 3"):
                    self._read(number)
                self.assertIsNone(self._read(number, mode="empty"))
        self.assertEqual(self._read(0, mode="wrap"), "three")
        self.assertEqual(self._read(4, mode="wrap"), "one")

    def test_wrap_on_empty_file_is_an_error(self) -> None:
        self._write(b"")
        with self.assertRaisesRegex(FileLineError, "行数: 0"):
            self._read(0, mode="wrap")

    def test_invalid_encoding_and_range_mode_are_errors(self) -> None:
        self._write(b"line")
        with self.assertRaisesRegex(FileLineError, "文字コード"):
            self._read(1, encoding="latin-1")
        with self.assertRaisesRegex(FileLineError, "範囲外の扱い"):
            self._read(1, mode="ignore")

    def test_resolves_absolute_relative_and_empty_paths(self) -> None:
        root = str(self.root)
        self.assertEqual(resolve_file_line_path(str(self.path), root), str(self.path))
        self.assertEqual(
            resolve_file_line_path("folder/../lines.txt", root),
            os.path.normpath(os.path.join(root, "folder/../lines.txt")),
        )
        self.assertEqual(resolve_file_line_path("", root), "")

    def test_normalizes_defaults_strings_and_invalid_types(self) -> None:
        self.assertEqual(normalize_file_line_options({}), ("", "", "utf-8", "error"))
        self.assertEqual(
            normalize_file_line_options(
                {"path": "  Data/File.txt ", "counter": " LoopA ", "encoding": " SHIFT_JIS ", "out_of_range": " WRAP "}
            ),
            ("Data/File.txt", "LoopA", "shift_jis", "wrap"),
        )
        self.assertEqual(
            normalize_file_line_options(
                {"path": 3, "counter": None, "encoding": " ", "out_of_range": []}
            ),
            ("", "", "utf-8", "error"),
        )

    def test_validate_rejects_invalid_values_in_existing_order(self) -> None:
        path = str(self.path)
        with self.assertRaises(FileLineError) as caught:
            validate_file_line_request(path, 1, encoding="invalid", out_of_range="invalid")
        self.assertEqual(str(caught.exception), f"文字コードが不正です: invalid（ファイル: {path}）")
        with self.assertRaises(FileLineError) as caught:
            validate_file_line_request(path, 1, encoding="utf-8", out_of_range="invalid")
        self.assertEqual(str(caught.exception), f"範囲外の扱いが不正です: invalid（ファイル: {path}）")
        for line_number in (True, "1", 1.0):
            with self.subTest(line_number=line_number):
                with self.assertRaises(FileLineError) as caught:
                    validate_file_line_request(
                        path, line_number, encoding="utf-8", out_of_range="error"
                    )
                self.assertEqual(
                    str(caught.exception),
                    f"行番号が整数ではありません: {line_number!r}（ファイル: {path}）",
                )

    def test_validate_does_not_access_file_and_preserves_exact_messages(self) -> None:
        path = str(self.root / "missing.txt")
        validate_file_line_request(path, 1, encoding="utf-8", out_of_range="error")
        with self.assertRaises(FileLineError) as caught:
            validate_file_line_request(path, 1, encoding="bad", out_of_range="bad")
        self.assertEqual(str(caught.exception), f"文字コードが不正です: bad（ファイル: {path}）")

    def test_load_file_lines_splits_all_newlines_and_ignores_trailing_break(self) -> None:
        self._write(b"one\r\ntwo\rthree\n")
        self.assertEqual(load_file_lines(str(self.path), encoding="utf-8"), ["one", "two", "three"])

    def test_load_file_lines_decodes_bom_and_cp932(self) -> None:
        self._write(b"\xef\xbb\xbfhello")
        self.assertEqual(load_file_lines(str(self.path), encoding="utf-8"), ["hello"])
        self._write(b"\x87\x40\x81\x60")
        self.assertEqual(load_file_lines(str(self.path), encoding="shift_jis"), ["\u2460\uff5e"])

    def test_load_file_lines_preserves_size_and_missing_file_errors(self) -> None:
        self._write(b"a" * (MAX_FILE_LINE_BYTES + 1))
        with self.assertRaisesRegex(FileLineError, "上限 1 MB"):
            load_file_lines(str(self.path), encoding="utf-8")
        missing_path = str(self.root / "missing.txt")
        with self.assertRaisesRegex(FileLineError, "読み込めません"):
            load_file_lines(missing_path, encoding="utf-8")

    def test_pick_file_line_handles_range_and_all_out_of_range_modes(self) -> None:
        lines = ["first", "last"]
        self.assertEqual(pick_file_line(lines, 2, out_of_range="error", path="test.txt"), "last")
        self.assertIsNone(pick_file_line(lines, 0, out_of_range="empty", path="test.txt"))
        self.assertEqual(pick_file_line(lines, 0, out_of_range="wrap", path="test.txt"), "last")
        self.assertEqual(pick_file_line(lines, 3, out_of_range="wrap", path="test.txt"), "first")
        with self.assertRaisesRegex(FileLineError, "行番号が範囲外です"):
            pick_file_line(lines, 3, out_of_range="error", path="test.txt")

    def test_pick_file_line_rejects_wrap_on_empty_lines(self) -> None:
        with self.assertRaisesRegex(FileLineError, "行数: 0"):
            pick_file_line([], 0, out_of_range="wrap", path="test.txt")


if __name__ == "__main__":
    unittest.main()
