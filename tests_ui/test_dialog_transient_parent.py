"""プリセット編集の前面維持先と App 所有の非変更を固定する。"""
import unittest
from unittest.mock import patch

from keyseq.presentation.app import App
from keyseq.presentation.dialogs.action_dialog import ActionDialog
from keyseq.presentation.dialogs.preset_manager import PresetManagerDialog


class DialogTransientParentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()
        cls.app.update_idletasks()

    @classmethod
    def tearDownClass(cls):
        cls.app.update()
        cls.app.destroy()

    def setUp(self):
        self._patch(self.app.hook, "suspend_hook_for_dialog")
        self._patch(self.app.hook, "resume_hook_after_dialog")
        self.callback_error = self._patch(self.app, "report_callback_exception")
        # ウィンドウ cleanup 中のコールバック例外も検出する。
        self.addCleanup(self.callback_error.assert_not_called)
        data = self.app.config_service.new_default_data()
        data["hotkey_presets"] = [{"label": "Copy", "value": "ctrl+c"}]
        self._patch(self.app, "data", data)
        self._patch(self.app, "keymap_set_path", "")

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

    def test_action_preset_manager_is_transient_for_action(self):
        """T1 (§5-1・§5-3): 前面維持先は ActionDialog、所有者は App。"""
        action = ActionDialog(self.app, title="アクション編集")
        self.addCleanup(self.cleanup_window, action)
        action.update_idletasks()
        self.assertTrue(action.winfo_viewable())
        original_init = PresetManagerDialog.__init__
        managers = []

        def init_and_schedule_close(manager, *args, **kwargs):
            original_init(manager, *args, **kwargs)
            self.addCleanup(self.cleanup_window, manager)
            managers.append(manager)
            manager.update_idletasks()
            self.assertTrue(manager.winfo_viewable())
            self.assertEqual(str(manager.wm_transient()), str(action))
            self.assertIs(manager.master, self.app)
            after_id = self.app.after(0, manager.destroy)
            self.addCleanup(self.app.after_cancel, after_id)

        with patch.object(PresetManagerDialog, "__init__", init_and_schedule_close):
            action._open_preset_manager()

        self.callback_error.assert_not_called()
        self.assertEqual(len(managers), 1)
        self.assertFalse(managers[0].winfo_exists())

    def test_default_preset_manager_is_transient_for_app(self):
        """T2 (§5-4): 引数省略時の前面維持先・所有者は App。"""
        manager = PresetManagerDialog(self.app)
        self.addCleanup(self.cleanup_window, manager)
        manager.update_idletasks()
        self.assertTrue(manager.winfo_viewable())
        self.assertEqual(str(manager.wm_transient()), str(self.app))
        self.assertIs(manager.master, self.app)
        self.callback_error.assert_not_called()
