"""Status text formatting shared by compact presentation components."""

from typing import Literal


HookDisplayState = Literal["on", "off", "paused"]
HOOK_STATE_LABELS: dict[HookDisplayState, str] = {
    "on": "ON",
    "off": "OFF",
    "paused": "一時停止",
}


def hook_display_state(hook_active: bool, custom_input_enabled: bool) -> HookDisplayState:
    if not hook_active:
        return "off"
    if not custom_input_enabled:
        return "paused"
    return "on"


def one_line(text: str) -> str:
    """Replace line breaks with spaces so text fits on one UI row."""
    return text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
