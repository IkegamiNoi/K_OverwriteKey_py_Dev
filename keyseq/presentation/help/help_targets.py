"""ダイアログから開く主要機能タブの飛び先。"""

SEQUENCE = "sequence"
KEYMAP = "keymap"
TRIGGER = "trigger"
PRESET = "preset"
KEYMAP_SET = "keymap_set"
CLEANUP = "cleanup"
KEYBOARD_UI = "keyboard_ui"

DIALOG_TARGETS: tuple[str, ...] = (
    SEQUENCE, KEYMAP, TRIGGER, PRESET, KEYMAP_SET, CLEANUP, KEYBOARD_UI,
)
