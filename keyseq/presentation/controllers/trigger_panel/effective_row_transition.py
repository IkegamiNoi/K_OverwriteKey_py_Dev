"""Guard effective-row replacement and clear its key-scoped runtime state."""

from collections.abc import Callable, Sequence
from typing import Any

from keyseq.domain.trigger_duplicates import (
    effective_rows_by_key,
    replaced_effective_keys,
)


def clear_trigger_state(app, key: str) -> None:
    """Use the same cleanup for deletion and effective-row replacement."""
    trigger_set_id = app._active_trigger_set_id()
    app._indices.pop(key, None)
    app.state.loop_frames_for(trigger_set_id).pop(key, None)
    app.sequence_runner.cancel_pending_wait(key)
    app.state.forget_trigger(trigger_set_id, key)


def apply_effective_row_transition(
    app, before: Sequence[Any], after: Sequence[Any], apply: Callable[[], None],
) -> bool:
    """Check the proposed rows before mutation, then apply and clean up."""
    replaced = replaced_effective_keys(before, after)
    removed = effective_rows_by_key(before).keys() - effective_rows_by_key(after).keys()
    for key in sorted(replaced):
        if app.sequence_runner.has_active_execution(key):
            app._set_flash_message(f"{key} は実行中のため、有効なトリガーを入れ替えられません")
            return False
    apply()
    for key in sorted(replaced | removed):
        clear_trigger_state(app, key)
    return True
