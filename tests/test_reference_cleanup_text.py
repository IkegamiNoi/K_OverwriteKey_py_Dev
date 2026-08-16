import unittest

from keyseq.application.config_service.parent_refs_cleanup import (
    CLEANUP_ALL_STALE,
    CLEANUP_PROTECTED,
    CLEANUP_TARGET,
    PRUNE_FAILURE_INVALID_DATA,
    PRUNE_FAILURE_SAVE_FAILED,
    PRUNE_FAILURE_UNREADABLE,
    ParentRefsCleanupInspection,
    ParentRefsPruneResult,
)
from keyseq.presentation.reference_cleanup_text import (
    CLEANUP_EMPTY_MESSAGE,
    format_cleanup_plan,
    format_cleanup_result,
)


class ReferenceCleanupTextTest(unittest.TestCase):
    def test_empty_plan_uses_empty_message(self):
        self.assertEqual(format_cleanup_plan([]), (CLEANUP_EMPTY_MESSAGE,))

    def test_plan_lists_all_stale_refs_in_input_order_and_keeps_stored_paths(self):
        inspections = [
            ParentRefsCleanupInspection(
                kind="keymap",
                stored_path="user/keymaps/main.json",
                alive_refs=(),
                stale_refs=("missing-a.json", "missing-b.json", "missing-c.json"),
                protected_refs=(),
                state=CLEANUP_TARGET,
            ),
            ParentRefsCleanupInspection(
                kind="trigger_set",
                stored_path="D:/shared/triggers.json",
                alive_refs=(),
                stale_refs=("missing-trigger.json",),
                protected_refs=(),
                state=CLEANUP_TARGET,
            ),
            ParentRefsCleanupInspection(
                kind="sequence",
                stored_path="user/sequences/copy.json",
                alive_refs=(),
                stale_refs=(),
                protected_refs=("user/trigger_sets/current.json",),
                state=CLEANUP_PROTECTED,
            ),
        ]

        lines = format_cleanup_plan(inspections)
        text = "\n".join(lines)

        self.assertEqual(lines[0], "対象ファイル: 2 件、消える参照元: 4 件")
        for path in (
            "missing-a.json",
            "missing-b.json",
            "missing-c.json",
            "missing-trigger.json",
            "user/keymaps/main.json",
            "D:/shared/triggers.json",
        ):
            self.assertIn(path, text)
        self.assertNotIn("ほか", text)
        self.assertLess(lines.index("キーマップ: user/keymaps/main.json"), lines.index("トリガー一覧: D:/shared/triggers.json"))
        self.assertLess(lines.index("トリガー一覧: D:/shared/triggers.json"), lines.index("出力シーケンス: user/sequences/copy.json"))

    def test_plan_keeps_protected_refs_out_of_disappearing_section(self):
        inspection = ParentRefsCleanupInspection(
            kind="keymap",
            stored_path="user/keymaps/main.json",
            alive_refs=(),
            stale_refs=("missing.json",),
            protected_refs=("user/keymap_sets/current.json",),
            state=CLEANUP_TARGET,
        )

        lines = format_cleanup_plan([inspection])
        disappearing_end = lines.index("保護のため残す参照元:")

        self.assertIn("  missing.json", lines[:disappearing_end])
        self.assertNotIn("  user/keymap_sets/current.json", lines[:disappearing_end])
        self.assertIn("  user/keymap_sets/current.json", lines[disappearing_end:])

    def test_protected_only_plan_has_no_disappearing_section(self):
        inspection = ParentRefsCleanupInspection(
            kind="sequence",
            stored_path="user/sequences/copy.json",
            alive_refs=(),
            stale_refs=(),
            protected_refs=("user/trigger_sets/current.json",),
            state=CLEANUP_PROTECTED,
        )

        lines = format_cleanup_plan([inspection])

        self.assertNotIn("消える参照元:", lines)
        self.assertIn("保護のため残す参照元:", lines)

    def test_target_file_count_excludes_protected_only_child(self):
        inspection = ParentRefsCleanupInspection(
            kind="sequence",
            stored_path="user/sequences/copy.json",
            alive_refs=(),
            stale_refs=(),
            protected_refs=("user/trigger_sets/current.json",),
            state=CLEANUP_PROTECTED,
        )

        lines = format_cleanup_plan([inspection])

        self.assertEqual(lines[0], "対象ファイル: 0 件、消える参照元: 0 件")

    def test_plan_uses_cleanup_state_to_add_all_stale_warning(self):
        all_stale = ParentRefsCleanupInspection(
            kind="trigger_set",
            stored_path="user/trigger_sets/main.json",
            alive_refs=(),
            stale_refs=("missing.json",),
            protected_refs=(),
            state=CLEANUP_ALL_STALE,
        )
        target = ParentRefsCleanupInspection(
            kind="keymap",
            stored_path="user/keymaps/main.json",
            alive_refs=("user/keymap_sets/current.json",),
            stale_refs=("missing.json",),
            protected_refs=(),
            state=CLEANUP_TARGET,
        )

        all_stale_text = "\n".join(format_cleanup_plan([all_stale]))
        target_text = "\n".join(format_cleanup_plan([target]))

        self.assertIn("参照元が 0 件になります", all_stale_text)
        self.assertIn("子ファイル自体は削除しません", all_stale_text)
        self.assertIn("孤児かどうかはこの検査範囲では判定できません", all_stale_text)
        self.assertNotIn("参照元が 0 件になります", target_text)

    def test_result_reports_counts_and_translates_all_failure_reasons(self):
        result = ParentRefsPruneResult(
            updated_files=(("user/keymaps/main.json", 2), ("user/sequences/copy.json", 1)),
            failed_files=(
                ("unreadable.json", PRUNE_FAILURE_UNREADABLE),
                ("invalid.json", PRUNE_FAILURE_INVALID_DATA),
                ("save-failed.json", PRUNE_FAILURE_SAVE_FAILED),
            ),
        )

        lines = format_cleanup_result(result)
        text = "\n".join(lines)

        self.assertEqual(lines[0], "更新したファイル: 2 件、除去した参照元: 3 件")
        self.assertIn("失敗したファイル:", lines)
        self.assertIn("unreadable.json: 読み直せませんでした", text)
        self.assertIn("invalid.json: JSON の形式が不正です", text)
        self.assertIn("save-failed.json: 保存できませんでした", text)

    def test_result_omits_failure_section_when_no_files_failed(self):
        result = ParentRefsPruneResult(
            updated_files=(("user/keymaps/main.json", 1),),
            failed_files=(),
        )

        lines = format_cleanup_result(result)

        self.assertEqual(lines, ("更新したファイル: 1 件、除去した参照元: 1 件",))


if __name__ == "__main__":
    unittest.main()
