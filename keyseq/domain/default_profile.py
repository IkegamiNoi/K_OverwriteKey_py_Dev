"""Built-in default hotkey presets and sample actions for supported platforms."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DefaultProfile:
    hotkey_presets: tuple[tuple[str, str], ...]
    select_line: tuple[str, ...]
    copy: str
    paste: str
    switch_app: str


WINDOWS_DEFAULT_PROFILE = DefaultProfile(
    hotkey_presets=(
        ("Alt+Tab", "alt+tab"),
        ("Win+D", "windows+d"),
        ("Win+E", "windows+e"),
        ("Ctrl+Shift+Esc", "ctrl+shift+esc"),
        ("Win+R", "windows+r"),
        ("Win+Tab", "windows+tab"),
        ("Win+X", "windows+x"),
        ("Alt+F4", "alt+f4"),
    ),
    select_line=("home", "shift+end"),
    copy="ctrl+c",
    paste="ctrl+v",
    switch_app="alt+tab",
)


MACOS_DEFAULT_PROFILE = DefaultProfile(
    hotkey_presets=(
        ("Command+Tab", "windows+tab"),
        ("Command+Space", "windows+space"),
        ("Command+Q", "windows+q"),
        ("Command+W", "windows+w"),
        ("Command+H", "windows+h"),
        ("Command+M", "windows+m"),
        ("Option+Command+Esc", "alt+windows+esc"),
        ("Ctrl+↑", "ctrl+up"),
    ),
    select_line=("windows+left", "windows+shift+right"),
    copy="windows+c",
    paste="windows+v",
    switch_app="windows+tab",
)
