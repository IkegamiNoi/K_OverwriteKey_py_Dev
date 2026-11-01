"""入力取得UIで使う共通文言とキーボード選択幅の定数。"""

from keyseq.shared.i18n import tr


def capture_idle_text() -> str:
    return tr("hook_button.capture_idle")


def capture_active_text() -> str:
    return tr("hook_button.capture_active")


def capture_texts() -> tuple[str, str]:
    return capture_idle_text(), capture_active_text()


def unknown_capture_key_hint_text() -> str:
    return tr("hook_button.capture_unknown_key_hint")


HOOK_START_TEXT = "hook_button.start"
HOOK_STOP_TEXT = "hook_button.stop"
HOOK_TOGGLE_TEXTS = (HOOK_START_TEXT, HOOK_STOP_TEXT)

TRIGGER_DISABLE_TEXT = "hook_button.trigger_disable"
TRIGGER_ENABLE_TEXT = "hook_button.trigger_enable"
TRIGGER_TOGGLE_TEXTS = (TRIGGER_DISABLE_TEXT, TRIGGER_ENABLE_TEXT)

KEYBOARD_LAYOUT_COMBO_WIDTH = 12
