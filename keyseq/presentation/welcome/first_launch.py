import os

from keyseq.shared.i18n import current_language

from .welcome_result import WelcomeResult
from .welcome_window import WelcomeWindow


def run_first_launch_welcome(app) -> WelcomeResult:
    """Wait for the first-launch window and return the confirmed choices."""
    window = WelcomeWindow(app, language=current_language())
    app.wait_window(window)
    return window.result


def is_first_launch(paths) -> bool:
    return not (
        os.path.exists(paths.preferred_startup_path())
        or os.path.exists(paths.resolve_startup_path())
    )
