from __future__ import annotations

from keyseq.domain.default_profile import MACOS_DEFAULT_PROFILE
from keyseq.infrastructure.os_backend.contracts import Capabilities, OsBackend


def create_backend() -> OsBackend:
    from .app_identity import MacAppIdentity
    from .ime_backend import MacImeBackend
    from .keyboard_backend import MacKeyboardBackend
    from .mouse_backend import MacMouseBackend
    from .tk_key_translator import MacTkKeyTranslator
    from .window_backend import MacWindowBackend

    keyboard = MacKeyboardBackend()
    return OsBackend(
        Capabilities(True, True, False, False), MacImeBackend(), MacWindowBackend(),
        MacTkKeyTranslator(keyboard), MacAppIdentity(), keyboard, MacMouseBackend(),
        default_profile=MACOS_DEFAULT_PROFILE,
        queued_hook_dispatch=True,
        platform_key="darwin",
    )
