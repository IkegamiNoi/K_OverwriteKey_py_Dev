from keyseq.presentation.app import App
from keyseq.infrastructure.win32_window import set_app_user_model_id

APP_USER_MODEL_ID = "keyseq.app"


def main() -> None:
    set_app_user_model_id(APP_USER_MODEL_ID)
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()

