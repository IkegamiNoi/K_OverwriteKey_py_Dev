import unittest

from keyseq.application.config_service import contracts
from keyseq.presentation.quarantine_manage_text import (
    format_delete_plan, format_delete_result,
    format_restore_plan, format_restore_result, format_unit_list,
)


class QuarantineManageTextTest(unittest.TestCase):
    def setUp(self):
        self.unit = contracts.QuarantineUnit("20260906_101500", "2026-09-06T10:15:00", 3, 2, True)

    def test_unit_lines_keep_order_date_and_counts_and_mark_invalid_manifest(self):
        invalid = contracts.QuarantineUnit("20260906_101500_2", "", 0, 0, False)
        lines = format_unit_list((self.unit, invalid))
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "20260906_101500  作成: 2026-09-06T10:15:00  残り 2/3 件")
        self.assertIn("マニフェスト不正（復元できません）", lines[1])
        self.assertEqual(format_unit_list(()), ())

    def test_restore_plan_identifies_unit_remaining_count_and_no_overwrite(self):
        lines = format_restore_plan(self.unit)
        self.assertEqual(lines[0], format_unit_list((self.unit,))[0])
        self.assertIn("2 件を元の場所へ復元", lines[1])
        self.assertIn("上書きせずスキップ", lines[2])

    def test_result_groups_skip_reasons_and_keeps_unknown_codes(self):
        reasons = (contracts.RESTORE_SKIPPED_EXISTS, contracts.RESTORE_SKIPPED_EXISTS,
                   contracts.RESTORE_REJECTED_TARGET, contracts.RESTORE_SOURCE_MISSING,
                   contracts.RESTORE_FAILED, "future_code")
        result = contracts.QuarantineRestoreResult(
            self.unit.unit_id, (("keymap", "user/keymaps/MixedCase.json"),),
            tuple((f"user/keymaps/{index}.json", reason) for index, reason in enumerate(reasons)),
            False, "",
        )
        lines = format_restore_result(result)
        self.assertEqual(lines[0], "復元しました: 1 件")
        self.assertIn("スキップ: 6 件", lines)
        self.assertIn("  復元先に同名ファイルがあります: 2 件", lines)
        self.assertIn("  復元先が対象外です: 1 件", lines)
        self.assertIn("  隔離側にファイルがありません（復元済み等）: 1 件", lines)
        self.assertIn("  復元できませんでした: 1 件", lines)
        self.assertIn("  future_code: 1 件", lines)
        self.assertEqual(lines[-1], "実行単位は残っています。")

    def test_abort_notice_comes_first_with_zero_restores(self):
        for reason in (contracts.RESTORE_ABORTED_INVALID_ID, contracts.RESTORE_ABORTED_NO_MANIFEST, "unknown"):
            lines = format_restore_result(contracts.QuarantineRestoreResult("id", (), (), False, reason))
            self.assertTrue(lines[0].startswith("復元を中止しました:"))
            self.assertEqual(lines[1], "1 件も戻していません。")
            if reason == "unknown":
                self.assertIn(reason, lines[0])

    def test_delete_plan_starts_with_irreversible_warning(self):
        # 確認 14
        lines = format_delete_plan(self.unit, (), manifest_valid=True)
        self.assertEqual(lines[0], "この操作は取り消せません。")
        self.assertIn(f"削除する実行単位: {self.unit.unit_id}", lines)

    def test_delete_plan_lists_every_path_including_manifest(self):
        # 確認 15
        paths = tuple(f"quarantine/{self.unit.unit_id}/Nested/MixedCase{index}.json" for index in range(50))
        paths += (f"quarantine/{self.unit.unit_id}/manifest.json",)
        lines = format_delete_plan(self.unit, paths, manifest_valid=True)
        self.assertEqual(lines[2:], tuple(f"  {path}" for path in paths))

    def test_delete_plan_invalid_manifest_adds_separate_warning_lines(self):
        # 確認 16
        paths = ("quarantine/unit/keep.txt",)
        normal = format_delete_plan(self.unit, paths, manifest_valid=True)
        invalid = format_delete_plan(self.unit, paths, manifest_valid=False)
        warnings = ("マニフェストが読めないため、中身を確認できません。", "ディレクトリごと削除します。")
        for warning in warnings:
            self.assertIn(warning, invalid)
            self.assertNotIn(warning, normal)
        self.assertEqual(tuple(line for line in invalid if line not in warnings), normal)

    def test_delete_result_labels_success_rejections_failure_and_unknown_code(self):
        # 確認 17
        success = contracts.QuarantineDeleteResult(self.unit.unit_id, True, "")
        self.assertEqual(format_delete_result(success), (f"削除しました: {self.unit.unit_id}",))
        labels = ((contracts.DELETE_REJECTED_INVALID_ID, "実行単位 ID が不正、または実在しません"),
                  (contracts.DELETE_REJECTED_IS_ROOT, "隔離ルート自身、または隔離ルート外を指しています"),
                  (contracts.DELETE_REJECTED_NO_MANIFEST, "マニフェストが読めません"),
                  (contracts.DELETE_FAILED, "削除できませんでした"), ("future_code", "future_code"))
        for reason, label in labels:
            with self.subTest(reason=reason):
                lines = format_delete_result(contracts.QuarantineDeleteResult(self.unit.unit_id, False, reason))
                self.assertIn(label, lines[0])
                if reason == contracts.DELETE_FAILED:
                    self.assertIn("一部が削除されている可能性があります。", lines)
                else:
                    self.assertIn("削除していません。", lines)

    def test_delete_formatters_return_string_tuples_and_keep_stored_spelling(self):
        # 確認 18
        stored = "quarantine/20260906_101500/Nested/./MixedCase.json"
        outputs = [format_delete_plan(self.unit, (stored,), manifest_valid=valid) for valid in (True, False)]
        for reason in ("", contracts.DELETE_REJECTED_INVALID_ID, contracts.DELETE_REJECTED_IS_ROOT,
                       contracts.DELETE_REJECTED_NO_MANIFEST, contracts.DELETE_FAILED, "future_code"):
            outputs.append(format_delete_result(contracts.QuarantineDeleteResult(self.unit.unit_id, not reason, reason)))
        for output in outputs:
            self.assertIsInstance(output, tuple)
            self.assertTrue(all(isinstance(line, str) for line in output))
            self.assertNotIn("  quarantine/20260906_101500/Nested/MixedCase.json", output)
            self.assertNotIn("  quarantine/20260906_101500/nested/mixedcase.json", output)
        for output in outputs[:2]:
            self.assertIn(f"  {stored}", output)

    def test_functions_return_string_tuples_without_converting_stored_paths(self):
        stored = "user/keymaps/./MixedCase.json"
        result = contracts.QuarantineRestoreResult("id", (("keymap", stored),), (), True, "")
        outputs = (format_unit_list((self.unit,)), format_restore_plan(self.unit), format_restore_result(result))
        for output in outputs:
            self.assertIsInstance(output, tuple)
            self.assertTrue(all(isinstance(line, str) for line in output))
        self.assertIn(f"  {stored}", outputs[-1])
        self.assertNotIn("  user/keymaps/MixedCase.json", outputs[-1])
        self.assertEqual(outputs[-1][-1], "実行単位を片付けました。")


if __name__ == "__main__":
    unittest.main()
