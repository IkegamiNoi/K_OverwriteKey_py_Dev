"""生成直後のダイアログの初期フォーカスを実 Tk で検査する。"""

import unittest
from contextlib import ExitStack
from unittest.mock import patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.dialogs.action_dialog import ActionDialog
from keyseq.presentation.dialogs.keymap_edit_dialog import KeymapEditDialog
from keyseq.presentation.dialogs.orphan_sweep_dialog import OrphanSweepDialog
from keyseq.presentation.dialogs.preset_dialog import PresetDialog
from keyseq.presentation.dialogs.quarantine_manage_dialog import QuarantineManageDialog
from keyseq.presentation.dialogs.reference_cleanup_dialog import ReferenceCleanupDialog
from keyseq.presentation.dialogs.trigger_dialog import TriggerDialog


class DialogInitialFocusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stack = ExitStack()
        cls.addClassCleanup(stack.close)
        # App の生成・破棄・遅延コールバックも含め、実ファイルの保存を遮断する。
        stack.enter_context(patch.object(app_module.JsonRepository, "save_json"))
        stack.enter_context(patch.object(ConfigService, "ensure_split_config_dirs"))
        stack.enter_context(patch.object(
            ConfigService, "load_keymap_set_history",
            return_value=({"recent": [], "categories": []}, contracts.HISTORY_OK),
        ))
        stack.enter_context(patch.object(
            ConfigService, "save_keymap_set_history",
            side_effect=AssertionError("unpatched history save"),
        ))
        cls.app = app_module.App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.update()
        cls.app.destroy()

    def setUp(self):
        self.app.update()
        for name in ("suspend_hook_for_dialog", "resume_hook_after_dialog"):
            patcher = patch.object(self.app.hook, name)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _require_app_focus(self):
        # 実使用は「アクティブな App からダイアログを開く」形なので、App 自身の前面化までは行う。
        # 一括実行では他テストの窓に OS フォーカスを奪われ、これが無いと全件 skip になる。
        # **ダイアログ側の focus_force はしない**（それをすると本件の欠落を隠す。idea_26 の発端）。
        if self.app.focus_displayof() is None:
            self.app.focus_force()
            self.app.update()
        if self.app.focus_displayof() is None:
            self.skipTest("アプリが OS の入力フォーカスを取れないため初期フォーカスを検査できない")

    def _assert_focus_inside(self, dialog):
        self.app.update()
        self.assertTrue(str(self.app.focus_get()).startswith(str(dialog)))

    def _close_dialog(self, dialog):
        if dialog.winfo_exists():
            dialog.grab_release()
            dialog.destroy()
        self.app.update()

    def test_orphan_sweep_initial_focus_is_window(self):
        self._require_app_focus()
        dialog = OrphanSweepDialog(self.app, scan_dirs=(), initial_dir="")
        self.addCleanup(self._close_dialog, dialog)
        self._assert_focus_inside(dialog)
        self.assertIs(self.app.focus_get(), dialog)

    def test_quarantine_manage_initial_focus_is_window(self):
        self._require_app_focus()
        dialog = QuarantineManageDialog(self.app, lines=(), unit_ids=())
        self.addCleanup(self._close_dialog, dialog)
        self._assert_focus_inside(dialog)
        self.assertIs(self.app.focus_get(), dialog)

    def test_reference_cleanup_initial_focus_is_window(self):
        self._require_app_focus()
        dialog = ReferenceCleanupDialog(self.app, title="確認", lines=("one",))
        self.addCleanup(self._close_dialog, dialog)
        self._assert_focus_inside(dialog)
        self.assertIs(self.app.focus_get(), dialog)

    def test_action_initial_focus_is_value_entry_in_all_modes(self):
        self._require_app_focus()
        for mode in ("hotkey", "text", "mouse_click"):
            with self.subTest(mode=mode):
                self._require_app_focus()
                dialog = ActionDialog(self.app, title="初期フォーカス", initial={"type": mode})
                self.addCleanup(self._close_dialog, dialog)
                try:
                    self._assert_focus_inside(dialog)
                    self.assertIs(self.app.focus_get(), dialog.value_entry)
                finally:
                    self._close_dialog(dialog)

    def test_keymap_edit_initial_focus_is_label_entry(self):
        self._require_app_focus()
        dialog = KeymapEditDialog(self.app, title="初期フォーカス")
        self.addCleanup(self._close_dialog, dialog)
        self._assert_focus_inside(dialog)
        self.assertIs(self.app.focus_get(), dialog.label_entry)

    def test_preset_initial_focus_is_value_entry(self):
        self._require_app_focus()
        dialog = PresetDialog(self.app, title="初期フォーカス")
        self.addCleanup(self._close_dialog, dialog)
        self._assert_focus_inside(dialog)
        self.assertIs(self.app.focus_get(), dialog.value_entry)

    def test_trigger_initial_focus_is_key_entry(self):
        self._require_app_focus()
        dialog = TriggerDialog(self.app, title="初期フォーカス")
        self.addCleanup(self._close_dialog, dialog)
        self._assert_focus_inside(dialog)
        self.assertIs(self.app.focus_get(), dialog.key_entry)


if __name__ == "__main__":
    unittest.main()
