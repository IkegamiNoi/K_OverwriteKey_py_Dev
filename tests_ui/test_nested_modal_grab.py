"""実ダイアログのネスト経路で、子の閉鎖後の grab 復元を固定する。"""
import ast
import tkinter as tk
import unittest
from unittest.mock import patch
from tests_ui.dialog_discovery import DIALOGS, PRESENTATION, dialog_classes, find_calls, parse

from keyseq.presentation.app import App
from keyseq.presentation.controllers.config_io import hotkey_presets_io
from keyseq.presentation.dialogs.action_dialog import ActionDialog
from keyseq.presentation.dialogs.preset_dialog import PresetDialog
from keyseq.presentation.dialogs.preset_manager import PresetManagerDialog


def is_call(statement, name):
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and (
            isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == name
            or isinstance(statement.value.func, ast.Attribute)
            and statement.value.func.attr == name
        )
    )


def _unexpected_showerror(_title, message, *_args, **_kwargs):
    raise AssertionError(f"unexpected messagebox.showerror: {message}")


def _unexpected_askyesno(*_args, **_kwargs):
    raise AssertionError("unexpected messagebox.askyesno")


class NestedModalGrabTest(unittest.TestCase):
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
        self._patch(hotkey_presets_io.messagebox, "showerror", side_effect=_unexpected_showerror)
        self._patch(hotkey_presets_io.messagebox, "askyesno", side_effect=_unexpected_askyesno)
        self._patch(self.app.hook, "suspend_hook_for_dialog")
        self._patch(self.app.hook, "resume_hook_after_dialog")
        self.callback_error = self._patch(self.app, "report_callback_exception")
        # cleanup 中の Destroy コールバック例外も失敗として検出する。
        self.addCleanup(self.callback_error.assert_not_called)
        data = self.app.config_service.new_default_data()
        data["hotkey_presets"] = [{"label": "Copy", "value": "ctrl+c"}]
        data["hotkey_presets_individual"] = True
        data["hotkey_presets_path"] = "user/hotkey_presets/nested_modal.json"
        self._patch(self.app, "data", data)
        self._patch(self.app, "keymap_set_path", "user/keymap_sets/nested_modal.json")
        self.write_presets = self._patch(
            self.app.hotkey_presets_io, "write_presets",
            side_effect=AssertionError("unexpected preset write"),
        )

    def _patch(self, target, name, *args, **kwargs):
        patcher = patch.object(target, name, *args, **kwargs)
        mocked = patcher.start()
        self.addCleanup(patcher.stop)
        return mocked

    @staticmethod
    def cleanup_window(window):
        if window.winfo_exists():
            window.grab_release()
            window.destroy()

    def _preset_manager(self):
        dialog = PresetManagerDialog(self.app)
        self.addCleanup(self.cleanup_window, dialog)
        dialog.update_idletasks()
        self.assertTrue(dialog.winfo_viewable())
        self.assertIs(self.app.grab_current(), dialog)
        return dialog

    def test_preset_add_restores_manager_grab(self):
        dialog = self._preset_manager()
        original_init = PresetDialog.__init__
        children = []

        def init_and_schedule_close(child, *args, **kwargs):
            original_init(child, *args, **kwargs)
            child.after(0, child.destroy)
            self.addCleanup(self.cleanup_window, child)
            children.append(child)
            self.assertIs(self.app.grab_current(), child)

        with patch.object(PresetDialog, "__init__", init_and_schedule_close):
            dialog.add()

        self.assertEqual(len(children), 1)
        self.assertFalse(children[0].winfo_exists())
        self.assertTrue(dialog.winfo_exists())
        self.assertIs(self.app.grab_current(), dialog)

    def test_action_preset_manager_restores_action_grab(self):
        dialog = ActionDialog(self.app, title="アクション編集")
        self.addCleanup(self.cleanup_window, dialog)
        dialog.update_idletasks()
        self.assertTrue(dialog.winfo_viewable())
        self.assertIs(self.app.grab_current(), dialog)
        original_init = PresetManagerDialog.__init__
        children = []

        def init_and_schedule_close(child, *args, **kwargs):
            original_init(child, *args, **kwargs)
            child.after(0, child.destroy)
            self.addCleanup(self.cleanup_window, child)
            children.append(child)
            self.assertIs(self.app.grab_current(), child)

        with patch.object(PresetManagerDialog, "__init__", init_and_schedule_close), patch.object(
            dialog, "_rebuild_preset_buttons", wraps=dialog._rebuild_preset_buttons,
        ) as rebuild:
            dialog._open_preset_manager()

        rebuild.assert_called_once_with()
        self.assertEqual(len(children), 1)
        self.assertFalse(children[0].winfo_exists())
        self.assertTrue(dialog.winfo_exists())
        self.assertIs(self.app.grab_current(), dialog)

    def _overwrite_conflict(self):
        stored_path = "user/hotkey_presets/nested_modal.json"
        existing = [{"label": "Paste", "value": "ctrl+v"}]
        self._patch(
            self.app.config_service, "resolve_hotkey_presets_save_path", return_value=stored_path,
        )
        self._patch(
            self.app.config_service, "individual_hotkey_presets_save_rejection_reason",
            return_value="",
        )
        self._patch(
            self.app.config_service, "describe_individual_hotkey_presets_overwrite",
            return_value={"conflict": True, "existing": existing},
        )
        return stored_path, existing

    def _close_overwrite(self, manager, *, window_close=False, destroy_parent=False):
        before = set(self.app.winfo_children())
        confirmations = []

        def close_confirmation():
            windows = [window for window in self.app.winfo_children()
                       if window not in before and isinstance(window, tk.Toplevel)]
            try:
                self.assertEqual(len(windows), 1)
                child = windows[0]
                self.addCleanup(self.cleanup_window, child)
                confirmations.append(child)
                self.assertEqual(child.title(), "専用プリセットの上書き確認")
                self.assertIs(self.app.grab_current(), child)
                if destroy_parent:
                    manager.destroy()
                    self.assertFalse(manager.winfo_exists())
                    self.assertTrue(child.winfo_exists())
                if window_close:
                    handler = child.protocol("WM_DELETE_WINDOW")
                    self.assertTrue(handler)
                    child.tk.call(handler)
                    self.assertFalse(child.winfo_exists())
                else:
                    child.destroy()
            finally:
                # コールバック内のアサート失敗でも実 wait_window を解放する。
                for window in windows:
                    if window.winfo_exists():
                        window.destroy()

        after_id = self.app.after(0, close_confirmation)
        self.addCleanup(self.app.after_cancel, after_id)
        manager.on_ok()
        self.callback_error.assert_not_called()
        self.assertEqual(len(confirmations), 1)
        self.assertFalse(confirmations[0].winfo_exists())

    def test_overwrite_confirmation_is_transient_for_manager(self):
        """T3 (§5-2・§5-3): 前面維持先はマネージャ、所有者は App。"""
        manager = self._preset_manager()
        manager.individual_var.set(True)
        self._overwrite_conflict()
        original_wait = tk.Toplevel.wait_window
        confirmations = []

        def observe_and_wait(confirm, *args, **kwargs):
            self.addCleanup(self.cleanup_window, confirm)
            confirmations.append(confirm)
            confirm.update_idletasks()
            self.assertTrue(confirm.winfo_viewable())
            self.assertEqual(str(confirm.wm_transient()), str(manager))
            self.assertIs(confirm.master, self.app)
            return original_wait(confirm, *args, **kwargs)

        with patch.object(tk.Toplevel, "wait_window", observe_and_wait):
            self._close_overwrite(manager)

        self.assertEqual(len(confirmations), 1)
        self.callback_error.assert_not_called()
        self.write_presets.assert_not_called()

    def test_declined_overwrite_restores_live_manager_grab(self):
        dialog = self._preset_manager()
        dialog.individual_var.set(True)
        stored_path, existing = self._overwrite_conflict()
        with patch.object(
            self.app.hotkey_presets_io, "confirm_overwrite",
            wraps=self.app.hotkey_presets_io.confirm_overwrite,
        ) as confirm:
            self._close_overwrite(dialog)

        confirm.assert_called_once_with(stored_path=stored_path, existing=existing, transient_parent=dialog)
        self.write_presets.assert_not_called()
        self.assertTrue(dialog.winfo_exists())
        self.assertIs(self.app.grab_current(), dialog)

    def test_window_close_restores_grab_and_tolerates_destroyed_parent(self):
        self._overwrite_conflict()
        for destroy_parent in (False, True):
            with self.subTest(destroy_parent=destroy_parent):
                dialog = self._preset_manager()
                dialog.individual_var.set(True)
                self._close_overwrite(dialog, window_close=True, destroy_parent=destroy_parent)
                # TclError は直接送出ならテスト失敗、Tk callback 経由ならここで検出する。
                self.callback_error.assert_not_called()
                if destroy_parent:
                    self.assertFalse(dialog.winfo_exists())
                    self.assertIsNone(self.app.grab_current())
                else:
                    self.assertTrue(dialog.winfo_exists())
                    self.assertIs(self.app.grab_current(), dialog)
                    dialog.destroy()
        self.write_presets.assert_not_called()

    def test_initialization_failure_keeps_manager_grab_without_recovery(self):
        manager = self._preset_manager()
        failure = RuntimeError("preset initialization failed")
        children = []
        destroy_calls = []

        def fail_entry_creation(frame, *args, **kwargs):
            child = frame.master
            children.append(child)
            self.addCleanup(self.cleanup_window, child)
            destroy_calls.append(self._patch(child, "destroy", wraps=child.destroy))
            raise failure

        with patch.object(manager, "grab_set", wraps=manager.grab_set) as restore, patch(
            "keyseq.presentation.dialogs.preset_dialog.ttk.Entry",
            side_effect=fail_entry_creation,
        ) as entry:
            with self.assertRaises(RuntimeError) as raised:
                manager.add()
            self.assertIs(raised.exception, failure)
            entry.assert_called_once()
            self.assertEqual(len(children), 1)
            destroy_calls[0].assert_not_called()
            restore.assert_not_called()
            self.assertTrue(children[0].winfo_exists())
            self.assertTrue(manager.winfo_exists())
            self.assertIs(self.app.grab_current(), manager)

    def test_grab_modal_call_sites_are_dialogs_or_config_io(self):
        config_io = PRESENTATION / "controllers" / "config_io"
        for path in sorted(PRESENTATION.rglob("*.py")):
            grabs = find_calls(parse(path), "grab_modal")
            if grabs:
                self.assertIn(path.parent, (DIALOGS, config_io),
                              f"{path}:{grabs[0].lineno}: grab_modal は dialogs または config_io の直下だけ")

    def test_grab_modal_is_last_initialization_statement(self):
        classes = dialog_classes()
        self.assertGreaterEqual(
            len(classes), 11,
            f"{DIALOGS}:1: Toplevel 継承クラスは11件以上必要: "
            f"{[node.name for _, node in classes]}",
        )
        for path, dialog_class in classes:
            initializers = [node for node in dialog_class.body
                            if isinstance(node, ast.FunctionDef) and node.name == "__init__"]
            self.assertEqual(len(initializers), 1, f"{path}:{dialog_class.lineno}: __init__ が必要")
            initializer = initializers[0]
            grabs = find_calls(initializer, "grab_modal")
            self.assertEqual(len(grabs), 1, f"{path}:{initializer.lineno}: grab_modal は1回")
            last = initializer.body[-1]
            self.assertTrue(is_call(last, "grab_modal"),
                            f"{path}:{last.lineno}: __init__ の最後は grab_modal")
        total = sum(len(find_calls(parse(path), "grab_modal"))
                    for path in sorted(DIALOGS.glob("*.py")))
        self.assertEqual(total, len(classes),
                         f"{DIALOGS}:1: grab_modal の総数は発見したクラス数と一致すること")

    def test_config_io_grab_modal_is_followed_by_wait(self):
        config_io = PRESENTATION / "controllers" / "config_io"
        trees = {path: parse(path) for path in sorted(config_io.glob("*.py"))}
        expected_counts = {
            "child_save_dialog.py": 2, "io_dialogs.py": 1, "hotkey_presets_io.py": 1,
        }
        self.assertEqual(
            {path.name for path, tree in trees.items() if find_calls(tree, "grab_modal")},
            set(expected_counts),
            f"{config_io}:1: grab_modal を呼ぶファイルは期待件数の辞書と一致すること",
        )
        for filename, expected_count in expected_counts.items():
            path = config_io / filename
            tree = trees[path]
            calls = find_calls(tree, "grab_modal")
            self.assertEqual(len(calls), expected_count, f"{path}:1: grab_modal の全呼び出し数")
            grabs = [node for node in ast.walk(tree) if is_call(node, "grab_modal")]
            self.assertEqual(len(grabs), expected_count, f"{path}:1: grab_modal の適用箇所数")
            blocks = [node for node in ast.walk(tree)
                      if isinstance(node, (ast.FunctionDef, ast.Try))]
            for grab in grabs:
                owners = [node for node in blocks if grab in node.body]
                self.assertEqual(len(owners), 1,
                                 f"{path}:{grab.lineno}: grab_modal は初期化関数または try の直下")
                body = owners[0].body
                following = body[body.index(grab) + 1:]
                self.assertTrue(following, f"{path}:{grab.lineno}: 待機が必要")
                wait = following[0]
                if isinstance(wait, ast.Try):
                    self.assertFalse(wait.handlers or wait.orelse,
                                     f"{path}:{wait.lineno}: 待機以外の例外処理は禁止")
                    self.assertEqual(len(wait.body), 1,
                                     f"{path}:{wait.lineno}: try 内は待機だけ")
                    self.assertTrue(is_call(wait.body[0], "wait_window"),
                                    f"{path}:{wait.body[0].lineno}: wait_window が必要")
                    self.assertEqual(len(wait.finalbody), 1,
                                     f"{path}:{wait.lineno}: finally はフック再開だけ")
                    self.assertTrue(is_call(wait.finalbody[0], "resume_hook_after_dialog"),
                                    f"{path}:{wait.finalbody[0].lineno}: フック再開が必要")
                else:
                    self.assertTrue(is_call(wait, "wait_window"),
                                    f"{path}:{wait.lineno}: grab_modal の直後は待機だけ")
                # wait_window が初期化の終端。その後の結果処理は検査対象外。

    def test_non_lifo_manager_destroy_does_not_steal_confirmation_grab(self):
        action = ActionDialog(self.app, title="アクション編集")
        self.addCleanup(self.cleanup_window, action)
        action.update_idletasks()
        self.assertIs(action.master, self.app)
        self.assertTrue(action.winfo_viewable())
        self.assertIs(self.app.grab_current(), action)
        self._overwrite_conflict()
        original_init = PresetManagerDialog.__init__
        managers = []
        confirmations = []

        def open_confirmation(manager):
            before = set(self.app.winfo_children())

            def destroy_middle_and_close():
                windows = [window for window in self.app.winfo_children()
                           if window not in before and isinstance(window, tk.Toplevel)]
                try:
                    self.assertEqual(len(windows), 1)
                    child = windows[0]
                    self.addCleanup(self.cleanup_window, child)
                    confirmations.append(child)
                    self.assertEqual(child.title(), "専用プリセットの上書き確認")
                    self.assertIs(child.master, self.app)
                    self.assertIs(self.app.grab_current(), child)
                    manager.destroy()
                    self.assertFalse(manager.winfo_exists())
                    self.assertTrue(action.winfo_exists())
                    self.assertTrue(child.winfo_exists())
                    self.assertIs(self.app.grab_current(), child)
                    child.destroy()
                    self.assertIsNone(self.app.grab_current())
                finally:
                    for window in windows:
                        if window.winfo_exists():
                            window.destroy()

            after_id = self.app.after(0, destroy_middle_and_close)
            self.addCleanup(self.app.after_cancel, after_id)
            try:
                manager.on_ok()
            finally:
                # 内側のアサート失敗でも ActionDialog 側の実待機を解放する。
                if manager.winfo_exists():
                    manager.destroy()

        def init_and_schedule_confirmation(manager, *args, **kwargs):
            original_init(manager, *args, **kwargs)
            self.addCleanup(self.cleanup_window, manager)
            managers.append(manager)
            self.assertIs(manager.master, self.app)
            self.assertIs(self.app.grab_current(), manager)
            manager.individual_var.set(True)
            after_id = self.app.after(0, open_confirmation, manager)
            self.addCleanup(self.app.after_cancel, after_id)

        with patch.object(PresetManagerDialog, "__init__", init_and_schedule_confirmation):
            action._open_preset_manager()
        self.callback_error.assert_not_called()
        self.assertEqual(len(managers), 1)
        self.assertEqual(len(confirmations), 1)
        self.assertFalse(managers[0].winfo_exists())
        self.assertFalse(confirmations[0].winfo_exists())
        self.assertTrue(action.winfo_exists())
        self.assertIsNone(self.app.grab_current())
        self.write_presets.assert_not_called()

    def test_lifo_confirmation_and_manager_close_restore_each_parent_grab(self):
        action = ActionDialog(self.app, title="アクション編集")
        self.addCleanup(self.cleanup_window, action)
        action.update_idletasks()
        self.assertIs(action.master, self.app)
        self.assertTrue(action.winfo_viewable())
        self.assertIs(self.app.grab_current(), action)
        self._overwrite_conflict()
        original_init = PresetManagerDialog.__init__
        managers = []

        def open_confirmation(manager):
            try:
                # 復元先は viewable でなければ取り直されない（§3-2）。実利用では表示済みなので、
                # マネージャのマップ完了を待ってから確認ダイアログを開く。
                manager.update_idletasks()
                self.assertTrue(manager.winfo_viewable())
                self._close_overwrite(manager)
                self.assertTrue(manager.winfo_exists())
                self.assertTrue(action.winfo_exists())
                self.assertIs(self.app.grab_current(), manager)
                manager.destroy()
                self.assertFalse(manager.winfo_exists())
                self.assertIs(self.app.grab_current(), action)
            finally:
                # 内側のアサート失敗でも ActionDialog 側の実待機を解放する。
                if manager.winfo_exists():
                    manager.destroy()

        def init_and_schedule_confirmation(manager, *args, **kwargs):
            original_init(manager, *args, **kwargs)
            self.addCleanup(self.cleanup_window, manager)
            managers.append(manager)
            self.assertIs(manager.master, self.app)
            self.assertIs(self.app.grab_current(), manager)
            manager.individual_var.set(True)
            after_id = self.app.after(0, open_confirmation, manager)
            self.addCleanup(self.app.after_cancel, after_id)

        with patch.object(PresetManagerDialog, "__init__", init_and_schedule_confirmation):
            action._open_preset_manager()
        self.callback_error.assert_not_called()
        self.assertEqual(len(managers), 1)
        self.assertFalse(managers[0].winfo_exists())
        self.assertTrue(action.winfo_exists())
        self.assertIs(self.app.grab_current(), action)
        self.write_presets.assert_not_called()

    def test_tcl_destroy_preset_restores_manager_grab(self):
        manager = self._preset_manager()
        child = PresetDialog(manager, title="プリセット追加")
        self.addCleanup(self.cleanup_window, child)
        child.update_idletasks()
        self.assertTrue(child.winfo_viewable())
        self.assertIs(self.app.grab_current(), child)

        child.tk.call("destroy", str(child))

        self.callback_error.assert_not_called()
        self.assertFalse(child.winfo_exists())
        self.assertTrue(manager.winfo_exists())
        self.assertIs(self.app.grab_current(), manager)

    def test_callback_exception_keeps_child_grab_until_closed(self):
        manager = self._preset_manager()
        failure = RuntimeError("preset callback failed")
        with patch.object(PresetDialog, "_ok", side_effect=failure) as ok:
            child = PresetDialog(manager, title="プリセット追加")
            self.addCleanup(self.cleanup_window, child)
            child.update_idletasks()
            self.assertIs(self.app.grab_current(), child)
            widgets = list(child.winfo_children())
            buttons = []
            while widgets:
                widget = widgets.pop()
                widgets.extend(widget.winfo_children())
                if widget.winfo_class() == "TButton" and widget.cget("text") == "OK":
                    buttons.append(widget)
            self.assertEqual(len(buttons), 1)
            buttons[0].invoke()
            ok.assert_called_once_with()
            self.callback_error.assert_called_once()
            exception_type, exception, traceback = self.callback_error.call_args.args
            self.assertIs(exception_type, RuntimeError)
            self.assertIs(exception, failure)
            self.assertIsNotNone(traceback)
            self.assertTrue(child.winfo_exists())
            self.assertIs(self.app.grab_current(), child)
            # 期待した通知だけを消し、閉鎖・cleanup の予期しない通知は既存ガードで拾う。
            self.callback_error.reset_mock()
            child.destroy()
            self.assertFalse(child.winfo_exists())
            self.assertTrue(manager.winfo_exists())
            self.assertIs(self.app.grab_current(), manager)
