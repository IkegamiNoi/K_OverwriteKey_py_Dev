from dataclasses import dataclass


JIS_LAYOUT_ID = "jis"
JIS_LAYOUT_PATH = "user/keylayout/jis.json"


@dataclass(frozen=True)
class WelcomeResult:
    language: str
    layout_id: str
    start: str


def estimate_layout_id(language: str) -> str:
    return JIS_LAYOUT_ID if language == "ja" else "us_tkl"
