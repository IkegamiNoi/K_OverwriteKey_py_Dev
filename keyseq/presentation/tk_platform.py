def is_aqua(widget) -> bool:
    return widget.tk.call("tk", "windowingsystem") == "aqua"


def screen_distance(widget, option: str) -> int:
    """Convert a screen-distance option to pixels; Tk 9 returns defaults with units like 10c or 2.25p."""
    return int(widget.winfo_pixels(widget.cget(option)))


def primary_modifier(widget) -> str:
    return "Command" if is_aqua(widget) else "Control"


def accelerator_text(widget, windows_text: str) -> str:
    if not is_aqua(widget):
        return windows_text
    return windows_text.replace("Ctrl+", "Command-").replace("Alt+", "Option-").replace("Shift+", "Shift-")
