import os
import unittest

from keyseq.application.config_service.orphan_scan import (
    KIND_HOTKEY_PRESETS, KIND_KEYMAP, KIND_SEQUENCE, KIND_TRIGGER_SET,
    ORPHAN_CANDIDATE, ORPHAN_EXCLUDED, ORPHAN_PROTECTED, ORPHAN_REFERENCED,
    OrphanEntry, OrphanScanResult,
)
from keyseq.application.config_service.reference_scan import SOURCE_MISSING, SOURCE_UNREADABLE
from keyseq.presentation.orphan_sweep_text import (
    ORPHAN_SWEEP_EMPTY_MESSAGE, SCAN_SCOPE_NOTE,
    format_orphan_notice, format_orphan_plan, format_scan_warnings,
)


def _result(**overrides):
    fields = dict(entries=(), unreadable_sources=(), non_keymap_set_sources=(), missing_scan_dirs=())
    fields.update(overrides)
    return OrphanScanResult(**fields)


class OrphanSweepTextTest(unittest.TestCase):
    def test_unreadable_warning_is_first_in_warnings_and_plan(self):
        result = _result(unreadable_sources=(
            ("missing.json", SOURCE_MISSING), ("broken.json", SOURCE_UNREADABLE),
        ))
        for formatter in (format_scan_warnings, format_orphan_plan):
            with self.subTest(formatter=formatter.__name__):
                lines = formatter(result)
                self.assertEqual(lines[0], "警告: 読めなかった構成セット / トリガー一覧が 2 件あります。")
                self.assertEqual(lines[1], "それらが参照していた子ファイルを孤児と誤判定している可能性があります。")
                self.assertIn("  missing.json: ファイルが見つかりません", lines)
                self.assertIn("  broken.json: 読み取り / JSON 解析に失敗しました", lines)

    def test_unknown_source_reason_is_preserved(self):
        lines = format_scan_warnings(_result(unreadable_sources=(("other.json", "new_reason"),)))
        self.assertIn("  other.json: new_reason", lines)

    def test_missing_directories_are_counted_and_listed_without_warning(self):
        lines = format_scan_warnings(_result(missing_scan_dirs=(" Missing/../One ", "Two")))
        self.assertEqual(lines[:3], ("見つからなかった走査ディレクトリ: 2 件", "   Missing/../One ", "  Two"))
        self.assertNotIn("警告", "\n".join(lines))

    def test_non_sets_show_only_count(self):
        lines = format_scan_warnings(_result(non_keymap_set_sources=("one.json", "two.json")))
        self.assertIn("構成セットとして解釈できなかった JSON: 2 件", lines)
        for path in ("one.json", "two.json"):
            self.assertNotIn(path, "\n".join(lines))

    def test_scope_note_is_always_last_warning(self):
        for result in (_result(), _result(missing_scan_dirs=("missing",))):
            self.assertEqual(format_scan_warnings(result)[-1], SCAN_SCOPE_NOTE)
        self.assertEqual(format_scan_warnings(_result()), (SCAN_SCOPE_NOTE,))

    def test_plan_lists_only_candidates(self):
        result = _result(entries=(
            OrphanEntry(KIND_KEYMAP, "candidate.json", ORPHAN_CANDIDATE),
            OrphanEntry(KIND_KEYMAP, "referenced.json", ORPHAN_REFERENCED),
            OrphanEntry(KIND_KEYMAP, "protected.json", ORPHAN_PROTECTED),
        ))
        self.assertEqual(format_orphan_plan(result), (
            SCAN_SCOPE_NOTE, "孤児候補: 1 件", "キーマップ: candidate.json",
        ))

    def test_excluded_entries_show_only_count(self):
        result = _result(entries=(
            OrphanEntry(KIND_SEQUENCE, "invalid-one.json", ORPHAN_EXCLUDED),
            OrphanEntry(KIND_SEQUENCE, "invalid-two.json", ORPHAN_EXCLUDED),
        ))
        lines = format_orphan_plan(result)
        self.assertIn("形状検証で対象外: 2 件", lines)
        self.assertNotIn("invalid-", "\n".join(lines))

    def test_empty_notice_includes_all_scan_diagnostics(self):
        result = _result(unreadable_sources=(("missing.json", SOURCE_MISSING),),
                         missing_scan_dirs=("missing-dir",), non_keymap_set_sources=("other.json",))
        self.assertEqual(format_orphan_notice(result), (
            ORPHAN_SWEEP_EMPTY_MESSAGE, *format_scan_warnings(result),
        ))

    def test_all_kind_labels_and_unknown_kind(self):
        kinds = ((KIND_KEYMAP, "キーマップ"), (KIND_TRIGGER_SET, "トリガー一覧"),
                 (KIND_SEQUENCE, "出力シーケンス"), (KIND_HOTKEY_PRESETS, "個別プリセット"),
                 ("new_kind", "new_kind"))
        result = _result(entries=tuple(
            OrphanEntry(kind, f"{kind}.json", ORPHAN_CANDIDATE) for kind, _ in kinds
        ))
        self.assertEqual(format_orphan_plan(result)[2:], tuple(
            f"{label}: {kind}.json" for kind, label in kinds
        ))

    def test_all_formatters_return_string_tuples_without_canonical_paths(self):
        stored = "user/Keymaps/../Keymaps/Mixed.JSON"
        source = "user/KeymapSets/../KeymapSets/Missing.JSON"
        result = _result(entries=(OrphanEntry(KIND_KEYMAP, stored, ORPHAN_CANDIDATE),),
                         unreadable_sources=((source, SOURCE_MISSING),))
        for formatter in (format_scan_warnings, format_orphan_plan, format_orphan_notice):
            with self.subTest(formatter=formatter.__name__):
                lines = formatter(result)
                self.assertIsInstance(lines, tuple)
                self.assertTrue(all(isinstance(line, str) for line in lines))
                text = "\n".join(lines)
                self.assertIn(source, text)
                for path in (stored, source):
                    self.assertNotIn(os.path.normcase(os.path.abspath(path)), text)
        self.assertIn(f"キーマップ: {stored}", format_orphan_plan(result))


if __name__ == "__main__":
    unittest.main()
