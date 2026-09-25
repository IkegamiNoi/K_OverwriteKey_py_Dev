import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.hook_coordinator import HookCoordinator
from keyseq.application.input_router import SendKeyAction, StopHookAction
from keyseq.application.key_overlap import AssignmentConflict, analyze_key_overlaps
from keyseq.presentation.controllers.hook_controller import HookController


def make_runtime(
    stop="",
    toggle="",
    *,
    active_has_trigger=True,
    other_has_trigger=True,
    include_mappings=True,
    active_stop_overlap=False,
):
    active_mappings = {"a": "b"} if include_mappings else {}
    other_mappings = {"c": "d"} if include_mappings else {}
    if active_stop_overlap:
        active_mappings["f1"] = "z"
    return {
        "keymaps": [
            {"id": "km1", "label": "Main", "triggers": ([{"key": "f1", "actions": [{"type": "text"}]}] if active_has_trigger else []), "mappings": active_mappings},
            {"id": "km2", "label": "Other", "triggers": ([{"key": "f2", "actions": [{"type": "text"}]}] if other_has_trigger else []), "mappings": other_mappings},
        ],
        "active_keymap_id": "km1",
        "keymap_switch_keys": {"f3": "km2"},
        "hook_stop_key": stop,
        "hook_toggle_key": toggle,
    }


class HookCoordinatorTest(unittest.TestCase):
    def test_start_accepts_all_map_triggers_and_replacement_sources(self):
        data = make_runtime(active_has_trigger=False, include_mappings=False)
        controller = HookController(
            SimpleNamespace(
                data=data,
                key_state_manager=SimpleNamespace(clear=Mock()),
                hook_coordinator=SimpleNamespace(start=Mock(return_value=True)),
                layout=SimpleNamespace(refresh_keyboard_window=Mock()),
                trigger_panel=SimpleNamespace(update_status=Mock()),
            )
        )
        controller.sync_hook_toggle_buttons = Mock()
        controller.sync_trigger_toggle_buttons = Mock()

        controller.start_hook()

        start_args = controller._app.hook_coordinator.start.call_args.kwargs
        self.assertEqual([item["key"] for item in start_args["triggers"]], ["f2"])
        self.assertFalse(start_args["has_keymaps"])
        self.assertTrue(start_args["has_trigger_keys"])
        self.assertTrue(controller.hook_active)

    def test_hook_controller_only_rejects_same_stop_and_toggle_key(self):
        data = make_runtime(stop="f1", toggle="f2", active_stop_overlap=True)
        data["keymap_switch_keys"]["f1"] = "km2"
        coordinator = SimpleNamespace(start=Mock(return_value=True))
        controller = HookController(
            SimpleNamespace(
                data=data,
                key_state_manager=SimpleNamespace(clear=Mock()),
                hook_coordinator=coordinator,
                layout=SimpleNamespace(refresh_keyboard_window=Mock()),
                trigger_panel=SimpleNamespace(update_status=Mock()),
            )
        )
        controller.sync_hook_toggle_buttons = Mock()
        controller.sync_trigger_toggle_buttons = Mock()
        with patch("keyseq.presentation.controllers.hook_controller.messagebox.showerror") as showerror:
            self.assertTrue(controller.validate_hook_configuration())
            showerror.assert_not_called()
            controller.start_hook()
        coordinator.start.assert_called_once()
        self.assertTrue(controller.hook_active)

        data["hook_toggle_key"] = " F1 "
        rejected_coordinator = SimpleNamespace(start=Mock())
        controller = HookController(SimpleNamespace(data=data, hook_coordinator=rejected_coordinator))
        with patch("keyseq.presentation.controllers.hook_controller.messagebox.showerror") as showerror:
            controller.start_hook()
            showerror.assert_called_once()
        rejected_coordinator.start.assert_not_called()

    def test_can_enable_uses_all_map_trigger_records(self):
        data = make_runtime(active_has_trigger=False, include_mappings=False)
        report = analyze_key_overlaps(data, "", "")
        errors = []
        coordinator = HookCoordinator(Mock())
        self.assertTrue(
            coordinator.can_enable_custom_input(
                report.all_triggers,
                lambda *args: errors.append(args),
                has_keymaps=False,
                has_trigger_keys=bool(report.all_trigger_keys),
            )
        )
        self.assertEqual(errors, [])

    def test_replacement_source_in_another_map_counts_as_input(self):
        data = make_runtime(active_has_trigger=False, other_has_trigger=False)
        report = analyze_key_overlaps(data, "", "")
        coordinator = HookCoordinator(Mock())
        controller = HookController(
            SimpleNamespace(
                data=data,
                key_state_manager=SimpleNamespace(clear=Mock()),
                hook_coordinator=coordinator,
                layout=SimpleNamespace(refresh_keyboard_window=Mock()),
                trigger_panel=SimpleNamespace(update_status=Mock()),
            )
        )
        controller.sync_hook_toggle_buttons = Mock()
        controller.sync_trigger_toggle_buttons = Mock()

        controller.start_hook()

        self.assertFalse(report.all_triggers)
        self.assertTrue(report.all_source_keys)
        self.assertTrue(controller.hook_active)
        self.assertTrue(coordinator._input_event_hook_handle)
        coordinator.stop()

    def test_stop_action_and_shadow_notice_are_both_reported(self):
        order = []
        executor = _make_executor(
            on_stop_hook=lambda: order.append("stop"),
            on_shadowed_action=lambda _action, _items: order.append("notice"),
        )
        conflict = AssignmentConflict("f12", "trigger", "stop")
        executor.execute_router_action(StopHookAction(), shadowed=(conflict,))
        self.assertEqual(order, ["stop", "notice"])

        status = _StatusVar("フック: OFF")
        controller = HookController(SimpleNamespace(ui_vars=SimpleNamespace(status_var=status)))
        controller.show_shadowed_assignments(StopHookAction(), (conflict,))
        self.assertIn("停止しました", status.value)
        self.assertIn("フック: OFF", status.value)
        self.assertIn("f12 は停止キーと重複しているため、トリガーは実行されません。", status.value)

    def test_shadow_notice_uses_pause_resume_name_and_keymap_label(self):
        status = _StatusVar("キーマップ: Main")
        controller = HookController(SimpleNamespace(ui_vars=SimpleNamespace(status_var=status)))
        conflicts = (
            AssignmentConflict("f11", "trigger", "toggle"),
            AssignmentConflict("f3", "trigger", "switch"),
            AssignmentConflict("a", "trigger", "mapping"),
            AssignmentConflict("f9", "keymap_switch", "stop", "km2", "Other"),
            AssignmentConflict("f8", "keymap_switch", "toggle", "km3", "Third"),
        )
        controller.show_shadowed_assignments(SendKeyAction("x", "y"), conflicts)
        self.assertIn("f11 は一時停止/再開キーと重複しているため、トリガーは実行されません。", status.value)
        self.assertIn("f3 は切替キーと重複しているため、トリガーは実行されません。", status.value)
        self.assertIn("a は置換と重複しているため、トリガーは実行されません。", status.value)
        self.assertIn("f9 は停止キーと重複しているため、キーマップ Other へ切り替えられません。", status.value)
        self.assertIn("f8 は一時停止/再開キーと重複しているため、キーマップ Third へ切り替えられません。", status.value)
        self.assertIn("キーマップ: Main", status.value)
        controller.show_shadowed_assignments(SendKeyAction("x", "y"), conflicts)
        self.assertEqual(status.value.count("f11 は"), 1)


class _StatusVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def _make_executor(*, on_stop_hook, on_shadowed_action):
    from keyseq.application.action_executor import ActionExecutor

    return ActionExecutor(
        input_gateway=Mock(),
        validate_hotkey=lambda key: ("", key),
        on_action_error=lambda *_: None,
        on_runtime_error=lambda *_: None,
        on_stop_hook=on_stop_hook,
        on_toggle_mode=lambda: None,
        on_select_keymap=lambda _keymap_id: None,
        on_trigger=lambda _key: None,
        on_shadowed_action=on_shadowed_action,
    )


if __name__ == "__main__":
    unittest.main()
