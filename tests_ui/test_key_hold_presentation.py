"""押下中の表示と解放の配線。gateway は記録だけを行う。"""
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.action_list_rendering import (
    build_action_rows, format_next_action_summary,
)
from keyseq.presentation.controllers.call_view_controller import CallViewController


class KeyHoldRenderingTests(unittest.TestCase):
    def test_call_view_uses_same_key_hold_row(self):
        frame = SimpleNamespace(action_list=Mock())
        app = SimpleNamespace(trigger_panel=SimpleNamespace(_resolve_call_target=Mock()))
        summary = SimpleNamespace(
            actions=[{"type": "key_hold", "edge": "down", "button": "right", "label": "保持"}],
            loop_frames=(), counters={}, position=0,
        )
        CallViewController(app)._render_rows(frame, summary)
        self.assertEqual(frame.action_list.insert.call_args.args[1], "▶ 01. [押す] マウス右: 保持")

    def test_full_and_compact_rows_share_key_hold_format(self):
        actions = [
            {"type": "key_hold", "edge": "down", "value": "shift"},
            {"type": "key_hold", "edge": "up", "value": "shift", "label": "解除"},
            {"type": "key_hold", "edge": "down", "button": "left"},
            {"type": "key_hold", "edge": "up", "button": "middle", "x": 100, "y": 200},
        ]
        expected = [
            "01. [押す] shift", "02. [離す] shift: 解除",
            "03. [押す] マウス左", "04. [離す] マウス中 (100, 200)",
        ]
        rows = build_action_rows(actions, loop_iterations={}, counters={})
        self.assertEqual([row[0] for row in rows], expected)
        for index, action in enumerate(actions):
            self.assertEqual(format_next_action_summary(
                index, action, loop_iterations={}, counters={},
            ), expected[index])


class KeyHoldPresentationTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(app_module.JsonRepository, "save_json"))
        stack.enter_context(patch.object(ConfigService, "ensure_split_config_dirs"))
        stack.enter_context(patch.object(
            ConfigService, "load_keymap_set_history",
            return_value=({"recent": [], "categories": []}, contracts.HISTORY_OK),
        ))
        stack.enter_context(patch.object(
            ConfigService, "save_keymap_set_history",
            side_effect=AssertionError("unexpected history save"),
        ))
        self.gateway = Mock(spec=app_module.InputGateway)
        self.gateway.key_identity.side_effect = lambda key: (ord(key[0]), False)
        stack.enter_context(patch.object(app_module, "InputGateway", return_value=self.gateway))
        self.app = app_module.App()
        self.addCleanup(self.app.destroy)
        self.app.update()
        self.addCleanup(self.app.compact_window.cancel_save)
        self.addCleanup(self.app.pane_layout.cancel_window_width_save)
        stack.enter_context(patch.object(self.app.hook_coordinator, "stop"))
        self.errors = stack.enter_context(patch.object(self.app.hook, "show_action_error"))

    def press_inputs(self):
        self.app.held_inputs.press_key("f1", "shift")
        self.app.held_inputs.press_mouse("f1", "left")

    def test_shared_instance_and_change_notification_updates_both_views(self):
        self.assertIs(self.app.action_executor.held_inputs, self.app.held_inputs)
        self.assertIs(self.app.sequence_runner.held_inputs, self.app.held_inputs)
        self.press_inputs()
        self.app.update()
        self.assertTrue(self.app.ui_vars.status_var.get().endswith(" / 押下中: shift, マウス左"))
        self.app._compact_mode = True
        self.app.trigger_panel.update_status()
        for variable in (self.app.ui_vars.status_var, self.app.ui_vars.status_full_var):
            self.assertTrue(variable.get().split("\n")[0].endswith(" / 押下中: shift, マウス左"))
        self.app.held_inputs.release_all()
        self.app.update()
        self.assertNotIn("押下中:", self.app.ui_vars.status_var.get())
        self.assertNotIn("押下中:", self.app.ui_vars.status_full_var.get())

    def test_status_change_is_scheduled(self):
        with patch.object(self.app.trigger_panel, "update_status") as update:
            self.app.held_inputs.press_key("f1", "shift")
            update.assert_not_called()
            self.app.update()
            update.assert_called_once_with()

    def test_stop_hook_releases_inputs_after_hook_stop(self):
        self.press_inputs()
        order = Mock()
        order.attach_mock(self.app.hook_coordinator.stop, "stop")
        order.attach_mock(self.gateway.release_key, "key_up")
        order.attach_mock(self.gateway.mouse_up, "mouse_up")
        with patch.object(self.app.held_inputs, "release_all", wraps=self.app.held_inputs.release_all) as release:
            self.app.hook.stop_hook()
            release.assert_called_once_with()
        self.assertEqual([item[0] for item in order.mock_calls], ["stop", "key_up", "mouse_up"])
        self.assertEqual(self.app.held_inputs.display_names, ())
        self.errors.assert_not_called()

    def test_pause_releases_but_resume_does_not(self):
        self.app.hook.hook_active = True
        self.press_inputs()
        with patch.object(self.app.held_inputs, "release_all", wraps=self.app.held_inputs.release_all) as release:
            self.app.hook.toggle_custom_input_enabled()
            release.assert_called_once_with()
            self.assertFalse(self.app.hook.custom_input_enabled)
            self.assertEqual(self.app.held_inputs.display_names, ())
            with patch.object(self.app.hook_coordinator, "can_enable_custom_input", return_value=True):
                self.app.hook.toggle_custom_input_enabled()
            self.assertEqual(release.call_count, 1)

    def test_release_errors_are_aggregated_after_all_inputs_are_released(self):
        self.press_inputs()
        self.gateway.release_key.side_effect = RuntimeError("key failed")
        self.gateway.mouse_up.side_effect = RuntimeError("mouse failed")
        self.app.hook.stop_hook()
        self.assertEqual(self.app.held_inputs.display_names, ())
        self.errors.assert_called_once()
        error = str(self.errors.call_args.args[2])
        self.assertIn("key failed", error)
        self.assertIn("mouse failed", error)

    def test_dialog_suspend_releases_inputs(self):
        self.app.hook.hook_active = True
        self.press_inputs()
        self.app.hook.suspend_hook_for_dialog()
        self.assertEqual(self.app.held_inputs.display_names, ())
        self.app.hook.begin_shutdown()
        self.app.hook.resume_hook_after_dialog()

    def test_close_releases_even_when_stop_fails(self):
        self.press_inputs()
        with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True), \
                patch.object(self.app.hook, "stop_hook", side_effect=RuntimeError("stop failed")), \
                patch.object(self.app, "destroy") as destroy:
            with self.assertRaisesRegex(RuntimeError, "stop failed"):
                self.app.on_close()
        self.assertEqual(self.app.held_inputs.display_names, ())
        self.gateway.release_key.assert_called_once_with("shift")
        self.gateway.mouse_up.assert_called_once_with("left")
        self.gateway.restore_ime_now.assert_called_once_with()
        destroy.assert_called_once_with()

    def test_close_reports_release_errors_and_still_restores_and_destroys(self):
        self.press_inputs()
        self.gateway.release_key.side_effect = RuntimeError("key failed")
        with patch.object(self.app.keymap_set_io, "confirm_save_if_dirty", return_value=True), \
                patch.object(self.app.hook, "stop_hook"), \
                patch.object(self.app, "destroy") as destroy:
            self.app.on_close()
        self.assertEqual(self.app.held_inputs.display_names, ())
        self.gateway.mouse_up.assert_called_once_with("left")
        self.errors.assert_called_once()
        self.assertIn("key failed", str(self.errors.call_args.args[2]))
        self.gateway.restore_ime_now.assert_called_once_with()
        destroy.assert_called_once_with()
