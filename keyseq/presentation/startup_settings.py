from keyseq.presentation.theme import coerce_font_delta


def load_startup_settings(config_service, startup_path, *, on_read_error) -> dict:
    """startup.json を読み、型ガードと font_delta 正規化を施した dict を返す。
    読込例外時は on_read_error(exc) を呼び既定 dict を返す。未知キーは全て保持する。
    """
    startup = {}
    try:
        startup = config_service.load_startup(startup_path)
    except Exception as exc:
        startup = {}
        on_read_error(exc)
    if not isinstance(startup, dict):
        startup = {}
    startup["ui_font_delta_pt"] = coerce_font_delta(startup.get("ui_font_delta_pt", 0))
    return startup
