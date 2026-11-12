import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from keyseq.application.hook_coordinator import HookCoordinator
from keyseq.application.input_router import InputRoute, SelectKeymapAction, SendKeyAction, StopHookAction
from keyseq.application.key_overlap import AssignmentConflict, analyze_key_overlaps
from keyseq.presentation.controllers.hook_controller import HookController


from keyseq.shared.i18n import fix_language

fix_language("ja")


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
    def test_hook_controller_default_dispatch_uses_after_for_both_routes(self):
        action = StopHookAction()
        route = InputRoute(actions=(action,))
        make_only_result = SimpleNamespace(routes=(route,), generation=7, accept=False)
        app = _make_dispatch_app(route)
        controller = HookController(app)
        controller._execute_reserved_action = Mock()
        controller._execute_make_only_action = Mock()

        controller.on_input_event(object())
        app.after.assert_called_once()
        controller._execute_reserved_action.assert_not_called()
        regular_callback = app.after.call_args.args[1]
        self.assertEqual(app.after.call_args.args[0], 0)
        regular_callback()
        controller._execute_reserved_action.assert_called_once_with(action, ())

        app.after.reset_mock()
        app.make_only_keys.handle.return_value = make_only_result
        self.assertFalse(controller.on_input_event(object()))
        app.after.assert_called_once()
        controller._execute_make_only_action.assert_not_called()
        make_only_callback = app.after.call_args.args[1]
        make_only_callback()
        controller._execute_make_only_action.assert_called_once_with(action, (), 7)
        self.assertEqual(app.after.call_args.args[0], 0)

    def test_hook_controller_injected_dispatch_handles_both_routes(self):
        action = StopHookAction()
        route = InputRoute(actions=(action,))
        make_only_result = SimpleNamespace(routes=(route,), generation=9, accept=False)
        scheduled = []
        dispatch = _FakeHookDispatcher(scheduled)
        app = _make_dispatch_app(route)
        controller = HookController(app, dispatch=dispatch)
        controller._execute_reserved_action = Mock()
        controller._execute_make_only_action = Mock()

        controller.on_input_event(object())
        self.assertEqual(len(scheduled), 1)
        controller._execute_reserved_action.assert_not_called()
        scheduled.pop()()
        controller._execute_reserved_action.assert_called_once_with(action, ())
        app.after.assert_not_called()

        app.make_only_keys.handle.return_value = make_only_result
        self.assertFalse(controller.on_input_event(object()))
        self.assertEqual(len(scheduled), 1)
        controller._execute_make_only_action.assert_not_called()
        scheduled.pop()()
        controller._execute_make_only_action.assert_called_once_with(action, (), 9)
        self.assertEqual(dispatch.dispatch.call_count, 2)
        app.after.assert_not_called()

    def test_keymap_discard_only_clears_current_reservation(self):
        event = Mock()
        route = InputRoute(actions=(SelectKeymapAction("km2"),), accept=False)
        app = _make_dispatch_app(route)
        app._keymap_switch_in_progress = Mock()
        dispatcher = _FakeHookDispatcher([])
        controller = HookController(app, dispatch=dispatcher)
        controller._execute_reserved_action = Mock()
        controller.on_input_event(event)
        queued = dispatcher.dispatch.call_args
        discard_a = queued.kwargs["on_discard"]
        controller._clear_keymap_switch_in_progress()
        app._keymap_switch_in_progress.clear.reset_mock()
        controller.on_input_event(event)
        discard_b = dispatcher.dispatch.call_args.kwargs["on_discard"]
        discard_a()
        app._keymap_switch_in_progress.clear.assert_not_called()
        discard_b()
        app._keymap_switch_in_progress.clear.assert_called_once_with()

    def test_stop_action_is_priority_and_stale_generation_does_nothing(self):
        route = InputRoute(actions=(StopHookAction(),), accept=False)
        app = _make_dispatch_app(route)
        dispatcher = _FakeHookDispatcher([])
        controller = HookController(app, dispatch=dispatcher)
        controller.hook_active = True
        controller._execute_reserved_action = Mock()
        controller.on_input_event(object())
        self.assertTrue(dispatcher.dispatch.call_args.kwargs["priority"])
        queued_stop = dispatcher.dispatch.call_args.args[0]
        controller._hook_generation += 1
        queued_stop()
        controller._execute_reserved_action.assert_not_called()

    def test_dispatch_overload_passes_through_and_schedules_one_priority_stop(self):
        route = InputRoute(actions=(SendKeyAction("a", "b"),), accept=False)
        app = _make_dispatch_app(route)
        dispatcher = _FakeHookDispatcher([], results=[False, True])
        controller = HookController(app, dispatch=dispatcher)
        controller.stop_hook = Mock()
        with patch("keyseq.presentation.controllers.hook_controller.messagebox.showwarning") as warning:
            self.assertTrue(controller.on_input_event(object()))
            self.assertTrue(controller._overloaded.is_set())
            self.assertEqual(dispatcher.dispatch.call_count, 2)
            self.assertTrue(dispatcher.dispatch.call_args.kwargs["priority"])
            stop_run = dispatcher.dispatch.call_args.args[0]
            self.assertTrue(controller.on_input_event(object()))
            self.assertEqual(app.input_router.handle.call_count, 1)
            self.assertEqual(app.make_only_keys.handle.call_count, 1)
            self.assertEqual(dispatcher.dispatch.call_count, 2)
            stop_run()
            controller.stop_hook.assert_called_once()
            warning.assert_called_once()

    def test_overload_does_not_dispatch_remaining_actions_or_make_only_actions(self):
        route = InputRoute(actions=(SendKeyAction("a", "b"), StopHookAction()), accept=False)
        app = _make_dispatch_app(route)
        dispatcher = _FakeHookDispatcher([], results=[False, True])
        controller = HookController(app, dispatch=dispatcher)
        with patch("keyseq.presentation.controllers.hook_controller.messagebox.showwarning"):
            self.assertTrue(controller.on_input_event(object()))
        self.assertEqual(dispatcher.dispatch.call_count, 2)  # rejected action + one priority stop
        app.make_only_keys.handle.return_value = SimpleNamespace(
            routes=(route,), generation=1, accept=False,
        )
        self.assertTrue(controller.on_input_event(object()))
        self.assertEqual(dispatcher.dispatch.call_count, 2)

    def test_make_only_dispatch_rejection_marks_overload_and_stops_once(self):
        route = InputRoute(actions=(SendKeyAction("a", "b"),), accept=False)
        app = _make_dispatch_app(InputRoute())
        app.make_only_keys.handle.return_value = SimpleNamespace(
            routes=(route,), generation=1, accept=False,
        )
        dispatcher = _FakeHookDispatcher([], results=[False, True])
        controller = HookController(app, dispatch=dispatcher)
        controller.stop_hook = Mock()
        with patch("keyseq.presentation.controllers.hook_controller.messagebox.showwarning") as warning:
            self.assertTrue(controller.on_input_event(object()))
            self.assertTrue(controller._overloaded.is_set())
            self.assertEqual(dispatcher.dispatch.call_count, 2)
            dispatcher.dispatch.call_args.args[0]()
            controller.stop_hook.assert_called_once()
            warning.assert_called_once()

    def test_stale_overload_stop_does_not_stop_restarted_hook(self):
        route = InputRoute(actions=(SendKeyAction("a", "b"),), accept=False)
        dispatcher = _FakeHookDispatcher([], results=[False, True])
        controller = HookController(_make_dispatch_app(route), dispatch=dispatcher)
        controller.stop_hook = Mock()
        with patch("keyseq.presentation.controllers.hook_controller.messagebox.showwarning") as warning:
            self.assertTrue(controller.on_input_event(object()))
            stale_stop = dispatcher.dispatch.call_args.args[0]
            controller._hook_generation += 1
            stale_stop()
        controller.stop_hook.assert_not_called()
        warning.assert_not_called()

    def test_timer_dispatch_rejection_stops_remaining_routes_and_schedules_stop_once(self):
        route = InputRoute(actions=(SendKeyAction("a", "b"), StopHookAction()))
        app = _make_dispatch_app(InputRoute())
        dispatcher = _FakeHookDispatcher([], results=[False, True])
        controller = HookController(app, dispatch=dispatcher)
        controller.schedule_make_only_routes((route, route), 1)
        self.assertTrue(controller._overloaded.is_set())
        self.assertEqual(dispatcher.dispatch.call_count, 2)
        self.assertTrue(dispatcher.dispatch.call_args.kwargs["priority"])
        controller.schedule_make_only_routes((route,), 1)
        self.assertEqual(dispatcher.dispatch.call_count, 2)

    def test_timer_actions_use_switch_discard_and_stop_run_guards(self):
        dispatcher = _FakeHookDispatcher([])
        app = _make_dispatch_app(InputRoute())
        app._keymap_switch_in_progress = Mock()
        controller = HookController(app, dispatch=dispatcher)
        controller._execute_make_only_action = Mock()
        route = InputRoute(actions=(SelectKeymapAction("km2"), StopHookAction()))
        controller.schedule_make_only_routes((route,), 1)
        select_call, stop_call = dispatcher.dispatch.call_args_list
        self.assertFalse(select_call.kwargs["priority"])
        select_call.kwargs["on_discard"]()
        app._keymap_switch_in_progress.clear.assert_called_once_with()
        self.assertTrue(stop_call.kwargs["priority"])
        self.assertIsNone(stop_call.kwargs["on_discard"])
        controller._hook_generation += 1
        stop_call.args[0]()
        controller._execute_make_only_action.assert_not_called()

    def test_stop_priority_run_executes_when_generation_is_current(self):
        route = InputRoute(actions=(StopHookAction(),), accept=False)
        app = _make_dispatch_app(route)
        dispatcher = _FakeHookDispatcher([])
        controller = HookController(app, dispatch=dispatcher)
        controller.hook_active = True
        controller._execute_reserved_action = Mock()
        controller.on_input_event(object())
        dispatcher.dispatch.call_args.args[0]()
        controller._execute_reserved_action.assert_called_once()

    def test_start_clears_overload_and_stop_invalidates_dispatcher(self):
        app = _make_dispatch_app(InputRoute())
        app.data = make_runtime()
        app.key_state_manager = SimpleNamespace(clear=Mock())
        app.make_only_keys = SimpleNamespace(clear=Mock())
        app.hook_coordinator = SimpleNamespace(start=Mock(return_value=True))
        app.hook_coordinator.stop = Mock()
        app.layout.refresh_keyboard_window = Mock()
        app.trigger_panel = SimpleNamespace(update_status=Mock())
        app.sequence_runner = SimpleNamespace(stop_run_to_end=Mock(), cancel_pending_waits=Mock())
        app.held_inputs = SimpleNamespace(release_all=Mock(return_value=[]))
        dispatcher = _FakeHookDispatcher([])
        controller = HookController(app, dispatch=dispatcher)
        controller.sync_hook_toggle_buttons = Mock()
        controller.sync_trigger_toggle_buttons = Mock()
        controller._overloaded.set()
        generation_before_start = controller._hook_generation
        controller.start_hook()
        self.assertFalse(controller._overloaded.is_set())
        self.assertGreater(controller._hook_generation, generation_before_start)
        controller.stop_hook()
        dispatcher.invalidate.assert_called_once_with()

    def test_grid_keymaps_allow_start_and_resume_without_triggers_or_mappings(self):
        gateway = SimpleNamespace(register_global_hook=Mock(return_value="handle"),
                                  unregister_hook=Mock())
        coordinator = HookCoordinator(gateway)
        errors = Mock()
        self.assertTrue(coordinator.start([], lambda _event: None, errors,
                                          has_grid_keymaps=True, has_trigger_keys=False))
        self.assertTrue(coordinator.can_enable_custom_input([], errors,
                                                            has_grid_keymaps=True,
                                                            has_trigger_keys=False))
        self.assertEqual(errors.call_count, 0)

    def test_start_accepts_all_map_triggers_and_replacement_sources(self):
        data = make_runtime(active_has_trigger=False, include_mappings=False)
        controller = HookController(
            SimpleNamespace(
                after=Mock(),
                data=data,
                key_state_manager=SimpleNamespace(clear=Mock()),
                make_only_keys=SimpleNamespace(clear=Mock()),
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
                after=Mock(),
                data=data,
                key_state_manager=SimpleNamespace(clear=Mock()),
                make_only_keys=SimpleNamespace(clear=Mock()),
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
        controller = HookController(SimpleNamespace(after=Mock(), data=data, hook_coordinator=rejected_coordinator))
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
                after=Mock(),
                data=data,
                key_state_manager=SimpleNamespace(clear=Mock()),
                make_only_keys=SimpleNamespace(clear=Mock()),
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
        flash = _StatusVar("停止しました")
        set_flash_message = Mock(side_effect=flash.set)
        controller = HookController(
            SimpleNamespace(
                after=Mock(),
                ui_vars=SimpleNamespace(status_var=status, flash_message_var=flash),
                _set_flash_message=set_flash_message,
            )
        )
        controller.show_shadowed_assignments(StopHookAction(), (conflict,))
        set_flash_message.assert_called_once()
        message = set_flash_message.call_args.args[0]
        self.assertIn("停止しました", message)
        self.assertIn("f12は停止キーと重複しているため、トリガーは実行されません。", message)
        self.assertEqual(status.value, "フック: OFF")

    def test_shadow_notice_uses_pause_resume_name_and_keymap_label(self):
        status = _StatusVar("キーマップ: Main")
        set_flash_message = Mock()
        controller = HookController(
            SimpleNamespace(
                after=Mock(),
                ui_vars=SimpleNamespace(status_var=status),
                _set_flash_message=set_flash_message,
            )
        )
        conflicts = (
            AssignmentConflict("f11", "trigger", "toggle"),
            AssignmentConflict("f3", "trigger", "switch"),
            AssignmentConflict("f9", "keymap_switch", "stop", "km2", "Other"),
            AssignmentConflict("f8", "keymap_switch", "toggle", "km3", "Third"),
        )
        controller.show_shadowed_assignments(SendKeyAction("x", "y"), conflicts)
        set_flash_message.assert_called_once()
        message = set_flash_message.call_args.args[0]
        self.assertIn("f11は一時停止/再開キーと重複しているため、トリガーは実行されません。", message)
        self.assertIn("f3は切替キーと重複しているため、トリガーは実行されません。", message)
        self.assertIn("f9は停止キーと重複しているため、キーマップ Other へ切り替えられません。", message)
        self.assertIn("f8は一時停止/再開キーと重複しているため、キーマップ Third へ切り替えられません。", message)
        self.assertEqual(status.value, "キーマップ: Main")
        controller.show_shadowed_assignments(SendKeyAction("x", "y"), conflicts)
        repeated_message = set_flash_message.call_args.args[0]
        self.assertEqual(repeated_message.count("f11は"), 1)
        self.assertEqual(repeated_message, message)
        self.assertEqual(set_flash_message.call_count, 2)


class _StatusVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _FakeHookDispatcher:
    def __init__(self, scheduled, results=None):
        self.dispatch = Mock(side_effect=self._dispatch)
        self.invalidate = Mock()
        self.close = Mock()
        self._scheduled = scheduled
        self._results = list(results or [])

    def _dispatch(self, run, **kwargs):
        result = self._results.pop(0) if self._results else True
        if result:
            self._scheduled.append(run)
        return result


def _make_dispatch_app(route):
    return SimpleNamespace(
        after=Mock(),
        data={},
        layout=SimpleNamespace(
            resolve_key_name_from_scan_code=Mock(return_value=""),
            should_debug_special_key_event=Mock(return_value=False),
        ),
        make_only_keys=SimpleNamespace(handle=Mock(return_value=None)),
        input_router=SimpleNamespace(handle=Mock(return_value=route)),
    )


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
        on_trigger=lambda _key, _repeat: None,
        on_shadowed_action=on_shadowed_action,
    )


if __name__ == "__main__":
    unittest.main()
