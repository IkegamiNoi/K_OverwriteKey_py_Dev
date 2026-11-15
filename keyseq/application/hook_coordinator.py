from __future__ import annotations

from typing import Callable, Sequence

from keyseq.domain.config import normalize_key_name
from keyseq.shared.i18n import tr


class HookCoordinator:
    def __init__(self, input_gateway):
        self.input_gateway = input_gateway
        self._input_event_hook_handle: object | None = None

    def start(
        self,
        triggers: Sequence[dict],
        on_input_event: Callable[[object], None] | None,
        on_error: Callable[[str, str], None],
        *,
        has_keymaps: bool = False,
        has_trigger_keys: bool | None = None,
        has_grid_keymaps: bool = False,
        on_permission_required: Callable[[], None] | None = None,
    ) -> bool:
        if not self._can_process_input(
            triggers, on_error, has_keymaps=has_keymaps, has_grid_keymaps=has_grid_keymaps,
            has_trigger_keys=has_trigger_keys
        ):
            return False

        self.stop()
        try:
            return self.install_input_event_hook(
                on_input_event, on_error, on_permission_required=on_permission_required,
            )
        except Exception as e:
            on_error(tr("application.hook.start_failed_title"), tr("application.hook.start_failed", error=e))
            self.stop()
            return False

    def can_enable_custom_input(
        self,
        triggers: Sequence[dict],
        on_error: Callable[[str, str], None],
        *,
        has_keymaps: bool = False,
        has_trigger_keys: bool | None = None,
        has_grid_keymaps: bool = False,
    ) -> bool:
        return self._can_process_input(
            triggers, on_error, has_keymaps=has_keymaps, has_grid_keymaps=has_grid_keymaps,
            has_trigger_keys=has_trigger_keys
        )

    def stop(self) -> None:
        self.uninstall_input_event_hook()

    def install_input_event_hook(
        self,
        on_input_event: Callable[[object], None] | None,
        on_error: Callable[[str, str], None],
        *,
        on_permission_required: Callable[[], None] | None = None,
    ) -> bool:
        self.uninstall_input_event_hook()
        if on_input_event is None:
            return True

        try:
            self._input_event_hook_handle = self.input_gateway.register_global_hook(
                on_input_event,
                suppress=True,
            )
            return True
        except PermissionError:
            self._input_event_hook_handle = None
            if on_permission_required is not None:
                on_permission_required()
            else:
                on_error(tr("application.hook.permission_required_title"), tr("application.hook.permission_required_body"))
            return False
        except Exception as e:
            self._input_event_hook_handle = None
            on_error(tr("application.hook.install_failed_title"), tr("application.hook.install_failed", error_type=type(e).__name__, error=e))
            return False

    def uninstall_input_event_hook(self) -> None:
        if self._input_event_hook_handle is None:
            return
        try:
            self.input_gateway.unregister_hook(self._input_event_hook_handle)
        except Exception:
            pass
        self._input_event_hook_handle = None

    def _can_process_input(
        self,
        triggers: Sequence[dict],
        on_error: Callable[[str, str], None],
        *,
        has_keymaps: bool,
        has_grid_keymaps: bool,
        has_trigger_keys: bool | None,
    ) -> bool:
        if has_trigger_keys is None:
            has_trigger_keys = any(normalize_key_name(item.get("key", "")) for item in triggers)
        if not has_trigger_keys and not has_keymaps and not has_grid_keymaps:
            on_error(tr("application.hook.cannot_start_title"), tr("application.hook.no_triggers"))
            return False
        if self._has_usable_triggers(triggers) or has_keymaps or has_grid_keymaps:
            return True
        on_error(tr("application.hook.cannot_start_title"), tr("application.hook.no_actions"))
        return False

    def _has_usable_triggers(self, triggers: Sequence[dict]) -> bool:
        for trigger in triggers:
            key = normalize_key_name(trigger.get("key", ""))
            actions = trigger.get("actions", [])
            if key and isinstance(actions, list) and len(actions) > 0:
                return True
        return False
