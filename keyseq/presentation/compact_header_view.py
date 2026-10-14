"""Saved open state for the compact view header sections."""

COMPACT_HEADER_VIEW_KEY = "compact_header_view"


def parse_compact_header_view(raw: object) -> dict[str, bool]:
    if not isinstance(raw, dict):
        return {"hook": True, "display": True}

    hook = raw.get("hook")
    display = raw.get("display")
    return {
        "hook": hook if isinstance(hook, bool) else True,
        "display": display if isinstance(display, bool) else True,
    }
