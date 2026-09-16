"""実 App の結線を通して最小化中の grab 預かりを固定する。"""

from contextlib import ExitStack
import tkinter as tk
import unittest
from unittest.mock import patch

from keyseq.presentation import modal
from keyseq.presentation.app import App
from keyseq.presentation.dialogs.action_dialog import ActionDialog
from keyseq.presentation.dialogs.preset_manager import PresetManagerDialog


class MinimizeGrabCustodyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.update()
        cls.app.destroy()

    def setUp(self):
        self._patch(modal, "_active_modals", [])
        self._patch(modal, "_custody_window", None)
        self._patch(self.app.hook, "suspend_hook_for_dialog")
        self._patch(self.app.hook, "resume_hook_after_dialog")
        callback_error = self._patch(self.app, "report_callback_exception")
        # LIFO cleanup: 窓の破棄・復帰を監視した後に patch を解除する。
        self.addCleanup(callback_error.assert_not_called)
        self.addCleanup(self._restore_app)
        self._restore_app()
        self.app.grab_release()

    def _patch(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def _restore_app(self):
        self.app.deiconify()
        self.app.update()

    @staticmethod
    def _cleanup_window(window):
        if window.winfo_exists():
            window.grab_release()
            window.destroy()

    def _track_window(self, window):
        self.addCleanup(self._cleanup_window, window)
        self.app.update()
        self.assertTrue(window.winfo_viewable())
        return window

    def _action(self):
        window = self._track_window(ActionDialog(self.app, title="アクション編集"))
        self.assertIs(self.app.grab_current(), window)
        return window

    def _manager(self, action):
        window = self._track_window(PresetManagerDialog(self.app, transient_parent=action))
        self.assertIs(self.app.grab_current(), window)
        return window

    def _minimize(self, holder):
        self.app.iconify()
        self.app.update()
        self.assertEqual(self.app.wm_state(), "iconic")
        self.assertFalse(holder.winfo_viewable())
        self.assertIsNone(self.app.grab_current())
        self.assertIs(modal._custody_window, holder)

    def _with_confirmation(self, manager, check):
        def inspect(dialog, *args, **kwargs):
            self._track_window(dialog)
            self.assertIs(self.app.grab_current(), dialog)
            try:
                check(dialog)
            finally:
                self._cleanup_window(dialog)

        # 実生成・grab 結線は通し、同期的な待機だけを検査に置き換える。
        with patch.object(tk.Toplevel, "wait_window", autospec=True, side_effect=inspect) as wait:
            self.app.hotkey_presets_io.confirm_overwrite(
                stored_path="user/hotkey_presets/custody.json",
                existing=[], transient_parent=manager,
            )
        wait.assert_called_once()

    def test_a1_real_dialog_restores_same_holder(self):
        """A1: 実 App の最小化・復元結線と実ダイアログ。"""
        dialog = self._action()
        self._minimize(dialog)

        self._restore_app()

        self.assertTrue(dialog.winfo_viewable())
        self.assertIs(self.app.grab_current(), dialog)
        self.assertIsNone(modal._custody_window)

    def test_a2_three_nested_dialogs_preserve_lifo(self):
        """A2: アクション → プリセット → 上書き確認の LIFO。"""
        action = self._action()
        manager = self._manager(action)

        def check(confirm):
            self._minimize(confirm)
            self._restore_app()
            for window in (action, manager, confirm):
                self.assertTrue(window.winfo_viewable())
            self.assertIs(self.app.grab_current(), confirm)
            confirm.destroy()
            self.app.update()
            self.assertIs(self.app.grab_current(), manager)
            manager.destroy()
            self.app.update()
            self.assertIs(self.app.grab_current(), action)

        self._with_confirmation(manager, check)

    def test_a3_destroyed_holder_falls_back_to_innermost(self):
        """A3: 預かり窓の破棄後は生存する最内窓を選ぶ。"""
        action = self._action()
        manager = self._manager(action)

        def check(confirm):
            self._minimize(confirm)
            confirm.destroy()
            self.app.update()
            self.assertFalse(confirm.winfo_exists())
            self.assertIsNone(self.app.grab_current())
            self._restore_app()
            self.assertTrue(action.winfo_viewable())
            self.assertTrue(manager.winfo_viewable())
            self.assertIs(self.app.grab_current(), manager)
            self.assertIsNone(modal._custody_window)

        self._with_confirmation(manager, check)

    def test_a4_map_does_not_force_window_visibility_or_focus(self):
        """A4: テスト自身の復帰呼出しを除き、3 操作は 0 回。"""
        dialog = self._action()
        self._minimize(dialog)
        restore = self.app.deiconify
        with ExitStack() as patches:
            operations = [
                patches.enter_context(patch.object(window, name, wraps=getattr(window, name)))
                for window in (self.app, dialog)
                for name in ("deiconify", "lift", "focus_force")
            ]
            # 保存した bound method でテスト側だけの deiconify を計測から除外する。
            restore()
            self.app.update()
            self.assertTrue(dialog.winfo_viewable())
            self.assertIs(self.app.grab_current(), dialog)
            self.assertIsNone(modal._custody_window)
            for operation in operations:
                operation.assert_not_called()

    def test_a5_unresolved_grab_holder_does_not_restore(self):
        """A5: grab_current の KeyError は保持者なしと同一視しない。"""
        dialog = self._action()
        self._minimize(dialog)
        with patch.object(self.app, "grab_current", side_effect=KeyError("unknown holder")) as current:
            with patch.object(dialog, "grab_set", wraps=dialog.grab_set) as restore:
                self._restore_app()
                self.assertTrue(dialog.winfo_viewable())
                current.assert_called()
                restore.assert_not_called()
                self.assertIsNone(modal._custody_window)
        self.assertIsNone(self.app.grab_current())

    def test_a6_existing_grab_holder_is_not_overwritten(self):
        """A6: 最小化中に別窓が取得した grab を維持する。"""
        dialog = self._action()
        self._minimize(dialog)
        other = self._track_window(tk.Toplevel(self.app))
        # grab_modal に預かりを消費させず、復元側の現保持者ガードを検査する。
        other.grab_set()
        self.assertIs(self.app.grab_current(), other)
        self.assertIs(modal._custody_window, dialog)
        with patch.object(dialog, "grab_set", wraps=dialog.grab_set) as restore:
            self._restore_app()
            self.assertTrue(dialog.winfo_viewable())
            restore.assert_not_called()
        self.assertIs(self.app.grab_current(), other)
        self.assertIsNone(modal._custody_window)

    def test_a7_withdrawn_recorded_holder_is_not_grabbed(self):
        """A7: 復帰時にも非表示の窓へ grab を戻さない。"""
        dialog = self._action()
        self._minimize(dialog)
        # transient 子は復元時に再表示され得るため、Map 時の非表示判定を固定する。
        with patch.object(dialog, "winfo_viewable", return_value=0) as viewable:
            with patch.object(dialog, "grab_set", wraps=dialog.grab_set) as restore:
                self._restore_app()
                self.assertTrue(dialog.winfo_exists())
                viewable.assert_called()
                restore.assert_not_called()
        self.assertIsNone(self.app.grab_current())
        self.assertIsNone(modal._custody_window)

    def test_a8_full_view_unmap_does_not_take_custody(self):
        """A8: 実 FullView の pack_forget による Unmap を除外する。"""
        dialog = self._action()
        frame = self.app.full_view
        self.assertTrue(frame.winfo_viewable())
        packing = frame.pack_info()
        self.addCleanup(frame.pack, **packing)
        dialog.withdraw()
        self.app.update()
        self.assertFalse(dialog.winfo_viewable())
        self.assertIs(self.app.grab_current(), dialog)
        self.assertIsNone(modal._custody_window)

        frame.pack_forget()
        self.app.update()

        self.assertFalse(frame.winfo_viewable())
        self.assertIs(self.app.grab_current(), dialog)
        self.assertIsNone(modal._custody_window)

    def test_a9_new_modal_closed_before_restore_returns_custody(self):
        """A9: 預かり中に開閉したモーダルから元の窓へ復帰する。"""
        dialog = self._action()
        self._minimize(dialog)
        child = self._track_window(tk.Toplevel(self.app))
        modal.grab_modal(child)
        self.assertIs(self.app.grab_current(), child)
        self.assertFalse(dialog.winfo_viewable())
        child.destroy()
        self.app.update()
        self.assertFalse(child.winfo_exists())
        self.assertEqual(self.app.wm_state(), "iconic")
        self.assertIsNone(self.app.grab_current())

        self._restore_app()

        self.assertTrue(dialog.winfo_viewable())
        self.assertIs(self.app.grab_current(), dialog)
        self.assertIsNone(modal._custody_window)
