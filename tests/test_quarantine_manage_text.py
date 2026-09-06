import unittest

from keyseq.application.config_service import quarantine_manage as manage
from keyseq.presentation.quarantine_manage_text import (
    format_restore_plan, format_restore_result, format_unit_list,
)


class QuarantineManageTextTest(unittest.TestCase):
    def setUp(self):
        self.unit = manage.QuarantineUnit("20260906_101500", "2026-09-06T10:15:00", 3, 2, True)

    def test_unit_lines_keep_order_date_and_counts_and_mark_invalid_manifest(self):
        invalid = manage.QuarantineUnit("20260906_101500_2", "", 0, 0, False)
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
        reasons = (manage.RESTORE_SKIPPED_EXISTS, manage.RESTORE_SKIPPED_EXISTS,
                   manage.RESTORE_REJECTED_TARGET, manage.RESTORE_SOURCE_MISSING,
                   manage.RESTORE_FAILED, "future_code")
        result = manage.QuarantineRestoreResult(
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
        for reason in (manage.RESTORE_ABORTED_INVALID_ID, manage.RESTORE_ABORTED_NO_MANIFEST, "unknown"):
            lines = format_restore_result(manage.QuarantineRestoreResult("id", (), (), False, reason))
            self.assertTrue(lines[0].startswith("復元を中止しました:"))
            self.assertEqual(lines[1], "1 件も戻していません。")
            if reason == "unknown":
                self.assertIn(reason, lines[0])

    def test_functions_return_string_tuples_without_converting_stored_paths(self):
        stored = "user/keymaps/./MixedCase.json"
        result = manage.QuarantineRestoreResult("id", (("keymap", stored),), (), True, "")
        outputs = (format_unit_list((self.unit,)), format_restore_plan(self.unit), format_restore_result(result))
        for output in outputs:
            self.assertIsInstance(output, tuple)
            self.assertTrue(all(isinstance(line, str) for line in output))
        self.assertIn(f"  {stored}", outputs[-1])
        self.assertNotIn("  user/keymaps/MixedCase.json", outputs[-1])
        self.assertEqual(outputs[-1][-1], "実行単位を片付けました。")


if __name__ == "__main__":
    unittest.main()
