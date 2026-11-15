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
        ("Command+Tab", "command+tab"),
        ("Command+Space", "command+space"),
        ("Command+Q", "command+q"),
        ("Command+W", "command+w"),
        ("Command+H", "command+h"),
        ("Command+M", "command+m"),
        ("Option+Command+Esc", "option+command+esc"),
        ("Ctrl+↑", "ctrl+up"),
    ),
    select_line=("command+left", "command+shift+right"),
    copy="command+c",
    paste="command+v",
    switch_app="command+tab",
)
