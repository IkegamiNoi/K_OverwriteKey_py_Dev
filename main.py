import os
from tkinter import messagebox

from keyseq.infrastructure.app_relaunch import relaunch_app
from keyseq.infrastructure.win32_window import set_app_user_model_id
from keyseq.presentation.app import App
from keyseq.shared.i18n import tr

APP_USER_MODEL_ID = "keyseq.app"


def main() -> None:
    set_app_user_model_id(APP_USER_MODEL_ID)
    startup_cwd = os.getcwd()
    app = App()
    app.mainloop()
    if app.restart_requested:
        error = relaunch_app(startup_cwd)
        if error is not None:
            messagebox.showerror(
                tr("dialog.language_restart.title"),
                tr("dialog.language_restart.failed", error=error),
            )


if __name__ == "__main__":
    main()

