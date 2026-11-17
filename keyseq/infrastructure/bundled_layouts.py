"""Install bundled keyboard layout examples into the user configuration."""

import os
from pathlib import Path
import shutil


def install_bundled_layouts(source_dir: Path, user_root: Path) -> bool:
    destination = user_root / "keylayout"
    temporary = user_root / "keylayout.tmp"
    if destination.exists() or not source_dir.is_dir():
        return False

    user_root.mkdir(parents=True, exist_ok=True)
    if temporary.exists():
        shutil.rmtree(temporary)
    try:
        temporary.mkdir()
        for source in source_dir.glob("*.json"):
            shutil.copy2(source, temporary / source.name)
        os.replace(temporary, destination)
    except OSError:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return True
