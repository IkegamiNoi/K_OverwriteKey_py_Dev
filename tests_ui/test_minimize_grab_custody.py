"""実 App の結線を通して最小化中の grab 預かりを固定する。"""

from contextlib import ExitStack
import tkinter as tk
from tkinter import ttk
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
        self._patch(modal, "_opened_while_minimized", [])
        self._patch(modal, "_custody_window", None)
        self._patch(modal, "_app_minimized", False)
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

    def test_a10_destroyed_holder_and_new_modal_restore_outer_grab(self):
        """A10: 預かり窓と新モーダルの破棄後も外側へ grab を戻す。"""
        action = self._action()
        holder = self._manager(action)
        self._minimize(holder)
        child = self._track_window(tk.Toplevel(self.app))
        modal.grab_modal(child)
        self.assertIs(self.app.grab_current(), child)
        self.assertIsNone(modal._custody_window)

        holder.destroy()
        self.assertIs(self.app.grab_current(), child)
        child.destroy()
        self.app.update()
        self.assertFalse(holder.winfo_exists())
        self.assertFalse(child.winfo_exists())
        self.assertEqual(self.app.wm_state(), "iconic")
        self.assertIsNone(self.app.grab_current())
        self.assertIs(modal._custody_window, holder)

        self._restore_app()

        self.assertTrue(action.winfo_exists())
        self.assertTrue(action.winfo_viewable())
        self.assertIs(self.app.grab_current(), action)
        self.assertIsNone(modal._custody_window)

    def test_a11_unmap_unresolved_holder_does_not_take_custody(self):
        """A11: Unmap で保持者が解決不能なら解放も預かりもしない。"""
        dialog = self._action()
        dialog.withdraw()
        self.app.update()
        self.assertFalse(dialog.winfo_viewable())
        self.assertIs(self.app.grab_current(), dialog)
        with patch.object(self.app, "grab_current", side_effect=KeyError("unknown holder")) as current:
            with patch.object(dialog, "grab_release", wraps=dialog.grab_release) as release:
                self.app.event_generate("<Unmap>")
                current.assert_called_once_with()
                release.assert_not_called()
                self.assertIsNone(modal._custody_window)
                self.app.report_callback_exception.assert_not_called()
        self.assertIs(self.app.grab_current(), dialog)

    def test_a12_unmap_destroyed_holder_does_not_take_custody(self):
        """A12: Unmap が破棄済み保持者を得ても解放・預かりをしない。"""
        dialog = self._action()
        dialog.destroy()
        self.app.update()
        self.assertFalse(dialog.winfo_exists())
        with patch.object(self.app, "grab_current", return_value=dialog) as current:
            # 破棄済み窓への Tk 呼び出しを避け、存在判定のガードだけを検査する。
            with patch.object(dialog, "winfo_viewable", return_value=0):
                with patch.object(dialog, "grab_release") as release:
                    self.app.event_generate("<Unmap>")
                    current.assert_called_once_with()
                    release.assert_not_called()
                    self.assertIsNone(modal._custody_window)

    def test_a13_repeated_unmap_does_not_overwrite_custody(self):
        """A13: 預かり中の再 Unmap は別保持者で記録を上書きしない。"""
        dialog = self._action()
        self._minimize(dialog)
        other = self._track_window(tk.Toplevel(self.app))
        other.grab_set()
        other.withdraw()
        self.app.update()
        self.assertFalse(other.winfo_viewable())
        self.assertIs(self.app.grab_current(), other)
        self.assertIs(modal._custody_window, dialog)
        with patch.object(other, "grab_release", wraps=other.grab_release) as release:
            self.app.event_generate("<Unmap>")
            release.assert_not_called()
        self.assertIs(modal._custody_window, dialog)
        self.assertIs(self.app.grab_current(), other)

    def test_b1_custody_restores_value_entry_focus(self):
        """①: 預かった ActionDialog の具体的な初期欄へ戻す。"""
        dialog = self._action()
        self._minimize(dialog)
        with patch.object(dialog.value_entry, "focus_set", wraps=dialog.value_entry.focus_set) as focus:
            self._restore_app()
            focus.assert_called_once_with()

    def test_b2_no_custody_restores_entry_focus(self):
        """②: transient のない表示中の保持者は預かりなしでも復帰する。"""
        window = self._track_window(tk.Toplevel(self.app))
        entry = ttk.Entry(window)
        entry.pack()
        self.app.update()
        modal.grab_modal(window, focus=entry)
        self.app.update()
        self.app.iconify()
        self.app.update()
        self.assertEqual(self.app.wm_state(), "iconic")
        self.assertTrue(window.winfo_viewable())
        self.assertIsNone(modal._custody_window)
        self.assertIs(self.app.grab_current(), window)
        with patch.object(entry, "focus_set", wraps=entry.focus_set) as focus:
            self._restore_app()
            focus.assert_called_once_with()

    def test_b3_unregistered_grab_holder_does_not_receive_focus(self):
        """③・⑦: 台帳外の別窓が grab 中ならどちらにも要求しない。"""
        dialog = self._action()
        self._minimize(dialog)
        other = self._track_window(tk.Toplevel(self.app))
        other.grab_set()
        self.assertIs(modal._custody_window, dialog)
        with ExitStack() as patches:
            focuses = [
                patches.enter_context(patch.object(widget, "focus_set", wraps=widget.focus_set))
                for widget in (dialog.value_entry, dialog, other)
            ]
            self._restore_app()
            self.assertIs(self.app.grab_current(), other)
            for focus in focuses:
                focus.assert_not_called()

    def test_b4_closed_new_modal_restores_original_entry_focus(self):
        """④: 最小化中に開閉した子から元の ActionDialog へ戻す。"""
        dialog = self._action()
        self._minimize(dialog)
        child = self._track_window(tk.Toplevel(self.app))
        modal.grab_modal(child)
        self.assertTrue(any(opened is child for opened in modal._opened_while_minimized))
        child.destroy()
        self.app.update()
        self.assertFalse(any(opened is child for opened in modal._opened_while_minimized))
        self.assertIs(modal._custody_window, dialog)
        with patch.object(dialog.value_entry, "focus_set", wraps=dialog.value_entry.focus_set) as focus:
            self._restore_app()
            focus.assert_called_once_with()

    def test_b5_destroyed_holder_and_child_restore_outer_entry_focus(self):
        """⑤: 預かり窓と新しい子の破棄後は外側の具体的な欄へ戻す。"""
        action = self._action()
        holder = self._manager(action)
        self._minimize(holder)
        child = self._track_window(tk.Toplevel(self.app))
        modal.grab_modal(child)
        holder.destroy()
        self.assertIs(self.app.grab_current(), child)
        child.destroy()
        self.app.update()
        self.assertIs(modal._custody_window, holder)
        with patch.object(action.value_entry, "focus_set", wraps=action.value_entry.focus_set) as focus:
            self._restore_app()
            self.assertIs(self.app.grab_current(), action)
            focus.assert_called_once_with()

    def test_b6_unresolved_grab_holder_does_not_receive_focus(self):
        """⑥: grab 保持者の解決失敗時にはフォーカス要求を出さない。"""
        dialog = self._action()
        self._minimize(dialog)
        with ExitStack() as patches:
            patches.enter_context(patch.object(self.app, "grab_current", side_effect=KeyError("unknown holder")))
            focuses = [
                patches.enter_context(patch.object(widget, "focus_set", wraps=widget.focus_set))
                for widget in (self.app, dialog, dialog.value_entry)
            ]
            self._restore_app()
            for focus in focuses:
                focus.assert_not_called()

    def test_b8_modal_opened_while_minimized_keeps_initial_focus_request(self):
        """⑧: 最小化中に開いた窓の初期要求を復帰処理で上書きしない。"""
        dialog = self._action()
        self._minimize(dialog)
        child = self._track_window(tk.Toplevel(self.app))
        entry = ttk.Entry(child)
        entry.pack()
        modal.grab_modal(child, focus=entry)
        with ExitStack() as patches:
            focuses = [
                patches.enter_context(patch.object(widget, "focus_set", wraps=widget.focus_set))
                for widget in (entry, child)
            ]
            self._restore_app()
            self.assertIs(self.app.grab_current(), child)
            for focus in focuses:
                focus.assert_not_called()

    def test_b11_modal_opened_while_minimized_restores_entry_on_next_restore(self):
        """⑧の窓を開いたまま再最小化すると、次の復元では entry へ戻す。"""
        dialog = self._action()
        self._minimize(dialog)
        child = self._track_window(tk.Toplevel(self.app))
        entry = ttk.Entry(child)
        entry.pack()
        # 未マップの entry への要求は OS フォーカスの無い環境で保留のまま残るため、先にマップして記録させる。
        self.app.update()
        modal.grab_modal(child, focus=entry)
        self.assertTrue(any(opened is child for opened in modal._opened_while_minimized))
        with ExitStack() as patches:
            entry_focus = patches.enter_context(patch.object(
                entry, "focus_set", wraps=entry.focus_set,
            ))
            child_focus = patches.enter_context(patch.object(
                child, "focus_set", wraps=child.focus_set,
            ))
            self._restore_app()
            self.assertIs(self.app.grab_current(), child)
            entry_focus.assert_not_called()
            child_focus.assert_not_called()
            self.assertEqual(modal._opened_while_minimized, [])

            self.app.iconify()
            self.app.update()
            self.assertEqual(self.app.wm_state(), "iconic")
            self.assertTrue(child.winfo_viewable())
            self.assertIsNone(modal._custody_window)
            self.assertIs(self.app.grab_current(), child)

            self._restore_app()
            self.assertTrue(child.winfo_viewable())
            self.assertIs(self.app.grab_current(), child)
            entry_focus.assert_called_once_with()
            child_focus.assert_not_called()

    def test_b9_restores_last_label_entry_instead_of_initial_entry(self):
        """⑨: 初期欄から移した最後のフォーカス先を固定して検査する。"""
        dialog = self._action()
        dialog.action_label_entry.focus_set()
        self.app.update()
        self._minimize(dialog)
        with ExitStack() as patches:
            label_focus = patches.enter_context(patch.object(
                dialog.action_label_entry, "focus_set", wraps=dialog.action_label_entry.focus_set,
            ))
            value_focus = patches.enter_context(patch.object(
                dialog.value_entry, "focus_set", wraps=dialog.value_entry.focus_set,
            ))
            self._restore_app()
            label_focus.assert_called_once_with()
            value_focus.assert_not_called()

    def test_b10_three_nested_dialogs_restore_only_confirmation_focus(self):
        """ネスト3段: 最内の上書き確認へだけフォーカスを要求する。

        OS フォーカスが無い環境ではアクティブ化の経路を通らない。最終確認は実機目視。
        """
        action = self._action()
        manager = self._manager(action)

        def check(confirm):
            self._minimize(confirm)
            with ExitStack() as patches:
                confirm_focus = patches.enter_context(patch.object(
                    confirm, "focus_set", wraps=confirm.focus_set,
                ))
                outer_focuses = [
                    patches.enter_context(patch.object(window, "focus_set", wraps=window.focus_set))
                    for window in (action, manager)
                ]
                self._restore_app()
                for window in (action, manager, confirm):
                    self.assertTrue(window.winfo_viewable())
                self.assertIs(self.app.grab_current(), confirm)
                confirm_focus.assert_called_once_with()
                for focus in outer_focuses:
                    focus.assert_not_called()

        self._with_confirmation(manager, check)
