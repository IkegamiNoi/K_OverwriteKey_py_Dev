from __future__ import annotations

import logging
import sys
from pathlib import Path

from keyseq.infrastructure.os_backend import app_relaunch


_LOG = logging.getLogger(__name__)


class MacAppIdentity:
    def apply_process_identity(self, app_id: str) -> bool: return True
    def relaunch(self, startup_cwd: str) -> OSError | None:
        return app_relaunch.relaunch_app(startup_cwd)

    def app_data_root(self, dev_root: Path) -> Path:
        if getattr(sys, "frozen", False):
            return Path.home() / "Library" / "Application Support" / "keyseq"
        return dev_root
