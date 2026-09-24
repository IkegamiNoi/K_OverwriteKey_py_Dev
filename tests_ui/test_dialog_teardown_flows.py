"""phase 15 task_03: 実ダイアログの解除経路と限定した AST 検査。"""
import ast
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import unittest
from unittest.mock import patch
from tests_ui.dialog_discovery import DIALOGS, dialog_classes, find_calls, parse
from tests_ui.escape_delivery import send_escape
from tests_ui.hook_resume_wait import wait_for_hook_pause_count

from keyseq.presentation.app import App
from keyseq.presentation.dialogs.action_dialog import ActionDialog
from keyseq.presentation.dialogs.preset_dialog import PresetDialog
from keyseq.presentation.dialogs.preset_manager import PresetManagerDialog
from keyseq.presentation.dialogs.quarantine_manage_dialog import QuarantineManageDialog


NESTED_CHILD_DIALOGS = frozenset({"PresetDialog", "CategoryChooserDialog"})

# T2（ウィジェットに触る後始末）が残るため destroy override を保持するファイル。
T2_DIALOG_FILES = (
    "action_dialog.py",
    "keymap_edit_dialog.py",
    "orphan_sweep_dialog.py",
    "trigger_dialog.py",
)


class DialogTeardownFlowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        # 破棄前に保留中の after(0) を流し、後続モジュールへ持ち越さない。
        cls.app.update()
        cls.app.destroy()

    def setUp(self):
        # 共有 App に残った after(0) を、状態を仕込む前に消化する。
        self.app.update()
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)
        self.callback_error = self._patch(self.app, "report_callback_exception")
        self.addCleanup(self.callback_error.assert_not_called)
        self._patch(messagebox, "showerror", side_effect=AssertionError("unexpected showerror"))
        self._patch(messagebox, "askyesno", side_effect=AssertionError("unexpected askyesno"))
        self._patch(self.app, "data", self.app.config_service.new_default_data())
        self._patch(self.app, "_dialog_result", None, create=True)
        self._patch(self.app.hook, "hook_active", True)
        self._patch(self.app.hook, "_shutting_down", False)
        self._patch(self.app.hook_coordinator, "stop")
        # ガード変異時も実 OS フックは登録せず、start の呼び出しを検出する。
        self.coordinator_start = self._patch(self.app.hook_coordinator, "start", return_value=True)

    def _patch(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    def cleanup_window(self, window):
        if window.winfo_exists():
            window.grab_release()
            window.destroy()
        # 各テストの patch が有効なうちに解除を消化する。
        self.app.update()

    def test_t1_tcl_close_defers_resume_for_manager_and_action(self):
        """T1 / §7-1・§4-2: × 直後は1、イベント処理後は0。"""
        self._patch(self.app.hook, "start_hook")
        for dialog_class in (PresetManagerDialog, ActionDialog):
            with self.subTest(dialog=dialog_class.__name__):
                wait_for_hook_pause_count(self, self.app, 0)
                self.app.hook.hook_active = True
                dialog = dialog_class(self.app, title="解除確認")
                self.addCleanup(self.cleanup_window, dialog)
                dialog.update_idletasks()
                self.assertTrue(dialog.winfo_viewable())
                self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
                dialog.tk.call("destroy", str(dialog))
                self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
                wait_for_hook_pause_count(self, self.app, 0)

    def test_t2_close_paths_resume_exactly_once(self):
        """T2 / §7-2: 代表2クラスの OK / キャンセル / destroy / ×。"""
        self._patch(self.app.hook, "start_hook")
        self._patch(self.app, "save_hotkey_presets", return_value=True)
        resume = self._patch(
            self.app.hook, "resume_hook_after_dialog",
            wraps=self.app.hook.resume_hook_after_dialog,
        )
        for dialog_class in (PresetManagerDialog, ActionDialog):
            for route in ("OK", "キャンセル", "destroy", "×"):
                with self.subTest(dialog=dialog_class.__name__, route=route):
                    wait_for_hook_pause_count(self, self.app, 0)
                    self.app.hook.hook_active = True
                    resume.reset_mock()
                    dialog = dialog_class(self.app, title="解除確認")
                    self.addCleanup(self.cleanup_window, dialog)
                    if isinstance(dialog, ActionDialog):
                        dialog.type_var.set("text")
                        dialog.value_var.set("test")
                    dialog.update_idletasks()
                    self.assertTrue(dialog.winfo_viewable())
                    self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
                    if route in ("OK", "キャンセル"):
                        widgets = list(dialog.winfo_children())
                        buttons = []
                        while widgets:
                            widget = widgets.pop()
                            widgets.extend(widget.winfo_children())
                            if widget.winfo_class() == "TButton" and widget.cget("text") == route:
                                buttons.append(widget)
                        self.assertEqual(len(buttons), 1)
                        buttons[0].invoke()
                    elif route == "destroy":
                        dialog.destroy()
                    else:
                        dialog.tk.call("destroy", str(dialog))
                    wait_for_hook_pause_count(self, self.app, 0)
                    self.assertFalse(dialog.winfo_exists())
                    resume.assert_called_once_with()

    def test_t2_escape_resumes_quarantine_once(self):
        """T2 / §7-2: Escape 結線済みクラスの代表。"""
        self._patch(self.app.hook, "start_hook")
        resume = self._patch(
            self.app.hook, "resume_hook_after_dialog",
            wraps=self.app.hook.resume_hook_after_dialog,
        )
        dialog = QuarantineManageDialog(self.app, lines=(), unit_ids=())
        self.addCleanup(self.cleanup_window, dialog)
        dialog.update_idletasks()
        self.assertTrue(dialog.winfo_viewable())
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        send_escape(self, self.app, dialog)
        wait_for_hook_pause_count(self, self.app, 0)
        self.assertFalse(dialog.winfo_exists())
        resume.assert_called_once_with()

    def test_t3_child_widget_destroy_keeps_dialog_paused(self):
        """T3 / §7-3: 子ウィジェットの Destroy は解除しない。"""
        self._patch(self.app.hook, "start_hook")
        dialog = PresetManagerDialog(self.app)
        self.addCleanup(self.cleanup_window, dialog)
        dialog.update_idletasks()
        self.assertTrue(dialog.winfo_viewable())
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        dialog.listbox.destroy()
        self.app.update()
        self.assertTrue(dialog.winfo_exists())
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)

    def test_t4a_shutdown_blocks_dialog_hook_restart(self):
        """T4a / §7-4: 遅延解除は実 start_hook 内の終了ガードを通す。"""
        self._patch(self.app.hook, "validate_hook_configuration", return_value=True)
        dialog = PresetManagerDialog(self.app)
        self.addCleanup(self.cleanup_window, dialog)
        dialog.update_idletasks()
        self.assertTrue(dialog.winfo_viewable())
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        self.app.hook.begin_shutdown()
        dialog.destroy()
        wait_for_hook_pause_count(self, self.app, 0)
        self.assertEqual(self.coordinator_start.call_count, 0)
        self.assertFalse(self.app.hook.hook_active)

    def test_t4b_shutdown_blocks_child_save_finally_hook_restart(self):
        """T4b / §7-4: 実 wait_window 中に終了し、finally の同期解除を見る。"""
        self._patch(self.app.hook, "validate_hook_configuration", return_value=True)
        before = set(self.app.winfo_children())
        closed = []

        def shutdown_and_close():
            windows = [window for window in self.app.winfo_children()
                       if window not in before and isinstance(window, tk.Toplevel)]
            try:
                self.assertEqual(len(windows), 1)
                dialog = windows[0]
                self.addCleanup(self.cleanup_window, dialog)
                dialog.update_idletasks()
                self.assertTrue(dialog.winfo_viewable())
                self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
                self.app.hook.begin_shutdown()
                dialog.destroy()
                closed.append(dialog)
                # wait_window が戻るまでは finally に到達していない。
                self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
            finally:
                for window in windows:
                    if window.winfo_exists():
                        window.destroy()

        after_id = self.app.after(0, shutdown_and_close)
        self.addCleanup(self.app.after_cancel, after_id)
        self.app.child_save_dialog.ask_child_save_actions([])
        # update より前に観測し、finally の同期解除を固定する。
        self.callback_error.assert_not_called()
        self.assertEqual(len(closed), 1)
        self.assertEqual(self.coordinator_start.call_count, 0)
        self.assertFalse(self.app.hook.hook_active)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 0)

    def test_t5_tcl_child_close_restores_manager_grab_and_pause(self):
        """T5 / §7-8: suspend / resume の実結線で phase 14 の非退行。"""
        self._patch(self.app.hook, "start_hook")
        manager = PresetManagerDialog(self.app)
        self.addCleanup(self.cleanup_window, manager)
        manager.update_idletasks()
        self.assertTrue(manager.winfo_viewable())
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)
        child = PresetDialog(manager, title="プリセット追加")
        self.addCleanup(self.cleanup_window, child)
        child.update_idletasks()
        self.assertTrue(child.winfo_viewable())
        self.assertIs(self.app.grab_current(), child)
        child.tk.call("destroy", str(child))
        self.app.update()
        self.assertFalse(child.winfo_exists())
        self.assertTrue(manager.winfo_exists())
        self.assertIs(self.app.grab_current(), manager)
        self.assertEqual(self.app.hook.get_hook_pause_count(), 1)


class DialogTeardownStaticTest(unittest.TestCase):
    def test_static_1_dialog_suspend_passes_self_once(self):
        """static-check-1 / §7-5: 発見した親は suspend(self) が各1件、子は0件。"""
        classes = dialog_classes()
        names = {node.name for _, node in classes}
        self.assertTrue(NESTED_CHILD_DIALOGS <= names,
                        f"{DIALOGS}:1: ネストした子がすべて発見されること: {sorted(names)}")
        top_level = [node for _, node in classes if node.name not in NESTED_CHILD_DIALOGS]
        self.assertGreaterEqual(
            len(top_level), 9,
            f"{DIALOGS}:1: トップレベルのダイアログは9件以上必要: "
            f"{[node.name for node in top_level]}",
        )
        for path, dialog_class in classes:
            with self.subTest(class_name=dialog_class.name):
                calls = find_calls(dialog_class, "suspend_hook_for_dialog")
                if dialog_class.name in NESTED_CHILD_DIALOGS:
                    self.assertEqual(len(calls), 0,
                                     f"{path}:{dialog_class.lineno}: 子は suspend を呼ばない")
                    continue
                self.assertEqual(len(calls), 1,
                                 f"{path}:{dialog_class.lineno}: suspend は1回")
                call = calls[0]
                self.assertEqual(len(call.args), 1, f"{path}:{call.lineno}: 引数は self のみ")
                self.assertIsInstance(call.args[0], ast.Name,
                                      f"{path}:{call.lineno}: 引数は self")
                self.assertEqual(call.args[0].id, "self", f"{path}:{call.lineno}: 引数は self")
                self.assertEqual(call.keywords, [], f"{path}:{call.lineno}: キーワード引数は禁止")
        total = sum(len(find_calls(parse(path), "suspend_hook_for_dialog"))
                    for path in sorted(DIALOGS.glob("*.py")))
        self.assertEqual(total, len(top_level),
                         f"{DIALOGS}:1: suspend の総数はトップレベルのクラス数と一致すること")

    def test_static_2_dialogs_do_not_call_resume(self):
        """static-check-2 / §7-6: dialogs/*.py 全体で明示 resume が0件。"""
        for path in sorted(DIALOGS.glob("*.py")):
            with self.subTest(filename=path.name):
                calls = find_calls(parse(path), "resume_hook_after_dialog")
                lineno = calls[0].lineno if calls else 1
                self.assertEqual(calls, [], f"{path}:{lineno}: resume は呼ばない")


    def test_static_3_t2_dialogs_keep_destroy_override(self):
        """static-check-3 / §7-7: T2 が残る4ファイルで destroy override を保持。"""
        dialogs = Path(__file__).resolve().parents[1] / "keyseq" / "presentation" / "dialogs"
        for filename in T2_DIALOG_FILES:
            with self.subTest(filename=filename):
                path = dialogs / filename
                tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
                overrides = [node for node in ast.walk(tree)
                             if isinstance(node, ast.FunctionDef) and node.name == "destroy"]
                self.assertEqual(len(overrides), 1)
