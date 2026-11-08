import os

from keyseq.shared.i18n import current_language

from .welcome_result import WelcomeResult, estimate_layout_id


def run_first_launch_welcome(app) -> WelcomeResult:
    """Return defaults without a window; replacement point for the Welcome UI."""
    language = current_language()
    return WelcomeResult(language, estimate_layout_id(language), "sample")


def is_first_launch(paths) -> bool:
    return not (
        os.path.exists(paths.preferred_startup_path())
        or os.path.exists(paths.resolve_startup_path())
    )
