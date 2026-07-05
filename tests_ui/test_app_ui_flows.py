"""App を実際に生成して、ダイアログを出さない範囲の UI 挙動を固定する。

- グローバルフックは一切開始しない（start_hook を呼ばない）
- ファイル保存を伴う操作は行わない（config/ を汚さない）
- GUI が開ける環境（通常のデスクトップセッション）で実行すること
"""
import unittest

from keyseq.presentation.app import App


class AppUiFlowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = App()
        cls.app.update_idletasks()
        # 実環境の構成に依存しないよう、テスト用データへ差し替える
        cls.app.data = cls.app.config_service.normalize_runtime_data(
            {
                "triggers": [
                    {"key": "f1", "label": "one", "actions": [{"type": "text", "value": "a"}]},
                    {"key": "f2", "label": "two", "actions": []},
                ],
                "keymaps": [{"id": "km1", "label": "Main", "mappings": {"a": "b"}}],
                "active_keymap_id": "km1",
            }
        )
        cls.app.state.reset_indices()
        cls.app._refresh_triggers()
        cls.app._refresh_actions()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app._set_dirty(False)
        finally:
            cls.app.destroy()

    def test_trigger_lists_populated(self):
        self.assertEqual(self.app.full_view.trigger_list.size(), 2)
        self.assertEqual(self.app.compact_view.trigger_list.size(), 2)

    def test_selection_updates_status(self):
        self.app._set_selected_trigger_index(1)
        self.assertIn("選択中: f2", self.app.status_var.get())
        self.app._set_selected_trigger_index(0)
        self.assertIn("選択中: f1", self.app.status_var.get())

    def test_status_shows_hook_off(self):
        self.app._update_status()
        self.assertIn("フック: OFF", self.app.status_var.get())

    def test_dirty_flag_reflected_in_file_status(self):
        self.app._set_dirty(True)
        self.assertIn("未保存", self.app.file_status_var.get())
        self.app._set_dirty(False)
        self.assertIn("保存済み", self.app.file_status_var.get())

    def test_compact_and_full_view_switch(self):
        self.app.show_compact_view()
        self.assertTrue(self.app._compact_mode)
        self.assertIn("選択:", self.app.status_var.get())
        self.app.show_full_view()
        self.assertFalse(self.app._compact_mode)

    def test_hook_suspend_counter_nesting(self):
        self.assertEqual(self.app._get_hook_pause_count(), 0)
        self.app.suspend_hook_for_dialog()
        self.app.suspend_hook_for_dialog()
        self.assertEqual(self.app._get_hook_pause_count(), 2)
        self.app.resume_hook_after_dialog()
        self.app.resume_hook_after_dialog()
        self.assertEqual(self.app._get_hook_pause_count(), 0)

    def test_stop_key_capture_start_and_cancel(self):
        self.app._start_stop_key_capture()
        self.assertTrue(self.app._capturing_stop_key)
        self.assertEqual(self.app._get_hook_pause_count(), 1)
        self.app._stop_stop_key_capture(cancel=True)
        self.assertFalse(self.app._capturing_stop_key)
        self.assertEqual(self.app._get_hook_pause_count(), 0)

    def test_keymap_list_shows_active_marker(self):
        self.app._refresh_keymap_list_ui()
        first = self.app.keymap_listbox.get(0)
        self.assertTrue(first.startswith("> "))
        self.assertIn("Main", first)

    def test_keyboard_window_opens_and_closes(self):
        self.app.open_keyboard_window()
        self.assertIsNotNone(self.app.keyboard_window)
        self.app.keyboard_window._handle_close()
        self.assertIsNone(self.app.keyboard_window)


if __name__ == "__main__":
    unittest.main()
