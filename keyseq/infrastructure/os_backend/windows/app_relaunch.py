"""Restart the application after its current window has closed."""
import logging
import subprocess
import sys


def relaunch_app(startup_cwd: str) -> OSError | None:
    """Start the same command in its original working directory."""
    try:
        subprocess.Popen([sys.executable, *sys.argv], cwd=startup_cwd)
    except OSError as error:
        logging.getLogger(__name__).exception("Could not restart the app")
        return error
    return None
