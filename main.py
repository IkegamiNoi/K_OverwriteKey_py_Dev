import os
from tkinter import messagebox

from keyseq.infrastructure.os_backend import get_backend
from keyseq.presentation.app import App
from keyseq.shared.i18n import tr

APP_USER_MODEL_ID = "keyseq.app"


def main() -> None:
    get_backend().app.apply_process_identity(APP_USER_MODEL_ID)
    startup_cwd = os.getcwd()
    app = App(first_launch_welcome=True)
    app.mainloop()
    if app.restart_requested:
        error = get_backend().app.relaunch(startup_cwd)
        if error is not None:
            messagebox.showerror(
                tr("dialog.language_restart.title"),
                tr("dialog.language_restart.failed", error=error),
            )


if __name__ == "__main__":
    main()

