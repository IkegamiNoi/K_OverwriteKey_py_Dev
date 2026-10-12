"""押下中の表示と解放の配線。gateway は記録だけを行う。"""
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.config_service import ConfigService, contracts
from keyseq.infrastructure import win32_window
from keyseq.presentation import app as app_module
from keyseq.presentation.controllers.action_list_rendering import (
    build_action_rows, format_next_action_summary,
)
from keyseq.presentation.controllers.call_view_controller import CallViewController
from keyseq.presentation.controllers.hook_controller import HookController


class KeyHoldRenderingTests(unittest.TestCase):
    def test_call_view_uses_same_key_hold_row(self):
        frame = SimpleNamespace(action_list=Mock())
        app = SimpleNamespace(trigger_panel=SimpleNamespace(_resolve_call_target=Mock()))
        summary = SimpleNamespace(
            actions=[
                {"type": "key_hold", "edge": "down", "button": "right", "label": "保持"},
                {"type": "key_hold", "edge": "down", "value": "a", "repeat": True},
            ],
            loop_frames=(), counters={}, position=0,
        )
        CallViewController(app)._render_rows(frame, summary)
        self.assertEqual(frame.action_list.insert.call_args_list[0].args[1], "▶ 01. [押す] マウス右: 保持")
        self.assertEqual(frame.action_list.insert.call_args_list[1].args[1], "　 02. [押す] a (リピート)")

    def test_full_and_compact_rows_share_key_hold_format(self):
        actions = [
            {"type": "key_hold", "edge": "down", "value": "shift"},
            {"type": "key_hold", "edge": "down", "value": "a", "repeat": True},
            {"type": "key_hold", "edge": "up", "value": "shift", "label": "解除"},
            {"type": "key_hold", "edge": "down", "button": "left"},
            {"type": "key_hold", "edge": "up", "button": "middle", "x": 100, "y": 200},
        ]
        expected = [
            "01. [押す] shift", "02. [押す] a (リピート)", "03. [離す] shift: 解除",
            "04. [押す] マウス左", "05. [離す] マウス中 (100, 200)",
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

    def test_repeater_is_wired_to_held_inputs_and_os_timing(self):
        self.assertIs(self.app.held_inputs._repeater, self.app.key_repeater)
        self.assertIs(self.app.key_repeater._get_timing, app_module.keyboard_repeat_timing)
        self.assertIs(self.app.key_repeater._after.__self__, self.app)
        self.assertIs(self.app.key_repeater._after_cancel.__self__, self.app)
        self.assertIs(
            self.app.key_repeater._is_blocked,
            win32_window.is_own_process_foreground,
        )

    def test_repeat_error_uses_the_existing_action_error_notice(self):
        action = {"type": "key_hold", "edge": "down", "value": "a", "repeat": True}
        self.app.held_inputs._on_repeat_error(action, "repeat failed")
        self.errors.assert_called_once_with("", action, "repeat failed")

    def test_error_notices_suppress_repeat_until_they_close(self):
        repeater = self.app.key_repeater
        begin = Mock(wraps=repeater.begin_suppress)
        end = Mock(wraps=repeater.end_suppress)
        with patch.object(repeater, "begin_suppress", begin), patch.object(repeater, "end_suppress", end):
            def show_error(*_args):
                self.assertGreater(repeater._suppress_count, 0)
                repeater.start(("key", 97, False), "a", {"type": "key_hold"})
                self.assertFalse(repeater.has_target)
                HookController.show_action_error(self.app.hook, "", {}, RuntimeError("nested"))

            with patch.object(app_module.messagebox, "showerror", side_effect=show_error) as showerror:
                HookController.show_action_error(self.app.hook, "", {}, RuntimeError("outer"))
            showerror.assert_called_once()
            begin.assert_called_once_with()
            end.assert_called_once_with()
            self.assertEqual(repeater._suppress_count, 0)

    def test_runtime_error_notice_also_suppresses_repeat(self):
        repeater = self.app.key_repeater

        def show_error(*_args):
            self.assertGreater(repeater._suppress_count, 0)
            repeater.start(("key", 97, False), "a", {"type": "key_hold"})
            self.assertFalse(repeater.has_target)

        with patch.object(app_module.messagebox, "showerror", side_effect=show_error) as showerror:
            self.app.action_executor._on_runtime_error("エラー", "失敗")
        showerror.assert_called_once_with("エラー", "失敗")
        self.assertEqual(repeater._suppress_count, 0)

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
        held_before = self.app.held_inputs.display_names
        self.app.hook.stop_hook()
        # 離す送信が失敗したものは集合に残し、次の解放で送り直す（暫定 35 §2-22）。
        self.assertEqual(self.app.held_inputs.display_names, held_before)
        self.errors.assert_called_once()
        error = str(self.errors.call_args.args[2])
        self.assertIn("key failed", error)
        self.assertIn("mouse failed", error)
        self.gateway.release_key.side_effect = None
        self.gateway.mouse_up.side_effect = None
        self.assertEqual(self.app.held_inputs.release_all(), [])
        self.assertEqual(self.app.held_inputs.display_names, ())

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
        # 離す送信が失敗した shift は集合に残る（暫定 35 §2-22）。マウスは離れる。
        self.assertEqual(self.app.held_inputs.display_names, ("shift",))
        self.gateway.mouse_up.assert_called_once_with("left")
        self.errors.assert_called_once()
        self.assertIn("key failed", str(self.errors.call_args.args[2]))
        self.gateway.restore_ime_now.assert_called_once_with()
        destroy.assert_called_once_with()
        self.gateway.release_key.side_effect = None
        self.assertEqual(self.app.held_inputs.release_all(), [])
