import os
import unittest

from keyseq.application.config_service.orphan_scan import (
    KIND_HOTKEY_PRESETS, KIND_KEYMAP, KIND_SEQUENCE, KIND_TRIGGER_SET,
    ORPHAN_CANDIDATE, ORPHAN_EXCLUDED, ORPHAN_PROTECTED, ORPHAN_REFERENCED,
    OrphanEntry, OrphanScanResult,
)
from keyseq.application.config_service.quarantine import (
    QUARANTINE_MANIFEST_WRITE_FAILED, QUARANTINE_MOVE_FAILED, QuarantineResult,
    QUARANTINE_SOURCE_REJECTED, QUARANTINE_UNIT_DIR_FAILED,
)
from keyseq.application.config_service.reference_scan import SOURCE_MISSING, SOURCE_UNREADABLE
from keyseq.presentation.orphan_sweep_text import (
    ORPHAN_SWEEP_EMPTY_MESSAGE, SCAN_SCOPE_NOTE,
    format_orphan_notice, format_orphan_plan, format_quarantine_result, format_scan_warnings,
)


def _result(**overrides):
    fields = dict(entries=(), unreadable_sources=(), non_keymap_set_sources=(), missing_scan_dirs=())
    fields.update(overrides)
    return OrphanScanResult(**fields)


def _quarantine_result(**overrides):
    fields = dict(unit_id="20260906_101500", moved=(), failed=(),
                  dropped_paths=(), newly_orphan_count=0, aborted_reason="")
    fields.update(overrides)
    return QuarantineResult(**fields)


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
        self.assertIn("対象外: 2 件", lines)
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


class QuarantineResultTextTest(unittest.TestCase):
    def test_moved_entries_are_counted_and_listed_with_kind_labels(self):
        result = _quarantine_result(moved=(
            (KIND_KEYMAP, "user/keymaps/foo.json"),
            ("new_kind", "user/other/bar.json"),
        ))
        self.assertEqual(format_quarantine_result(result), (
            "隔離しました: 2 件（実行単位: 20260906_101500）",
            "キーマップ: user/keymaps/foo.json",
            "new_kind: user/other/bar.json",
        ))

    def test_failed_entries_show_reason_labels_and_keep_unknown_codes(self):
        result = _quarantine_result(failed=(
            ("user/keymaps/foo.json", QUARANTINE_MOVE_FAILED),
            ("quarantine/20260906_101500/manifest.json", QUARANTINE_MANIFEST_WRITE_FAILED),
            ("user/keymaps/bar.json", "new_reason"),
        ))
        lines = format_quarantine_result(result)
        self.assertEqual(lines[1], "移動できなかったファイル:")
        self.assertEqual(lines[2], "  user/keymaps/foo.json: 移動できませんでした")
        self.assertEqual(lines[3], "  user/keymaps/bar.json: new_reason")
        self.assertEqual(lines[4], "警告: マニフェストを書き込めず、隔離の記録が古い可能性があります。")
        self.assertEqual(lines[5],
                         "  quarantine/20260906_101500/manifest.json: マニフェストを書き込めませんでした")

    def test_manifest_failure_after_move_is_separate_from_move_failures(self):
        result = _quarantine_result(moved=((KIND_KEYMAP, "child.json"),), failed=(
            ("quarantine/unit/manifest.json", QUARANTINE_MANIFEST_WRITE_FAILED),
        ))
        lines = format_quarantine_result(result)
        self.assertTrue(lines[0].startswith("隔離しました: 1 件"))
        self.assertNotIn("移動できなかったファイル:", lines)
        self.assertIn("隔離の記録が古い可能性があります", "\n".join(lines))
        self.assertIn("quarantine/unit/manifest.json", "\n".join(lines))

    def test_all_failed_headline_does_not_claim_success(self):
        result = _quarantine_result(failed=(("child.json", QUARANTINE_SOURCE_REJECTED),))
        lines = format_quarantine_result(result)
        self.assertTrue(lines[0].startswith("隔離できませんでした: 0 件"))
        self.assertNotIn("隔離しました", "\n".join(lines))
        self.assertIn("  child.json: 移動直前の安全確認で対象外になりました", lines)

    def test_unit_directory_failure_has_japanese_abort_label(self):
        result = _quarantine_result(unit_id="", aborted_reason=QUARANTINE_UNIT_DIR_FAILED)
        self.assertEqual(format_quarantine_result(result)[:2], (
            "隔離を中止しました: 隔離の実行単位ディレクトリを作成できませんでした",
            "ファイルは 1 件も移動していません。",
        ))

    def test_rescan_warning_precedes_success_and_abort_with_paths_and_reasons(self):
        sources = (("Missing.JSON", SOURCE_MISSING), ("broken.json", SOURCE_UNREADABLE),
                   ("other.json", "new_reason"))
        for abort in ("", QUARANTINE_UNIT_DIR_FAILED):
            with self.subTest(abort=abort):
                result = _quarantine_result(aborted_reason=abort, rescan_unreadable_sources=sources)
                lines = format_quarantine_result(result)
                self.assertEqual(lines[0], "警告: 隔離の直前にも読めない参照側が 3 件ありました。")
                self.assertEqual(lines[2:5], (
                    "  Missing.JSON: ファイルが見つかりません",
                    "  broken.json: 読み取り / JSON 解析に失敗しました",
                    "  other.json: new_reason",
                ))
                self.assertTrue(lines[5].startswith("隔離"))

    def test_dropped_and_newly_orphan_show_counts_without_paths(self):
        result = _quarantine_result(dropped_paths=("user/keymaps/foo.json", "user/keymaps/bar.json"),
                                    newly_orphan_count=3)
        lines = format_quarantine_result(result)
        self.assertEqual(lines[-2], "提示後に対象外になったため隔離しなかった: 2 件")
        self.assertEqual(lines[-1], "再判定で新たに孤児候補になったため今回は隔離しなかった: 3 件")
        for path in result.dropped_paths:
            self.assertNotIn(path, "\n".join(lines))

    def test_zero_counts_are_omitted(self):
        lines = format_quarantine_result(_quarantine_result())
        self.assertEqual(lines, ("隔離しました: 0 件（実行単位: 20260906_101500）",))
        self.assertEqual(format_quarantine_result(_quarantine_result(unit_id="")),
                         ("隔離しました: 0 件",))

    def test_aborted_result_states_that_nothing_was_moved(self):
        result = _quarantine_result(unit_id="", aborted_reason=QUARANTINE_MANIFEST_WRITE_FAILED,
                                    dropped_paths=("user/keymaps/foo.json",))
        lines = format_quarantine_result(result)
        self.assertEqual(lines[:2], (
            "隔離を中止しました: マニフェストを書き込めませんでした",
            "ファイルは 1 件も移動していません。",
        ))
        self.assertNotIn("隔離しました", "\n".join(lines))
        self.assertEqual(lines[-1], "提示後に対象外になったため隔離しなかった: 1 件")

    def test_unknown_abort_reason_is_preserved(self):
        lines = format_quarantine_result(_quarantine_result(unit_id="", aborted_reason="new_reason"))
        self.assertEqual(lines[0], "隔離を中止しました: new_reason")


if __name__ == "__main__":
    unittest.main()
