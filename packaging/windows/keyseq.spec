# -*- mode: python ; coding: utf-8 -*-

import glob
import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
SOURCE_PACKAGES = {"mouseinfo": "0.1.3", "pynput": "1.8.2"}
SOURCES_DIR = os.path.join(ROOT, "packaging", "sources")
SOURCE_EXTENSIONS = (".tar.gz", ".zip")


def files(pattern):
    return sorted(glob.glob(os.path.join(ROOT, pattern)))


def require_files(pattern, destination):
    result = [(path, destination) for path in files(pattern)]
    if not result:
        raise FileNotFoundError(f"No files matched {pattern!r}")
    return result


def read_version():
    text = open(os.path.join(ROOT, "keyseq", "__init__.py"), encoding="utf-8").read()
    return re.search(r'^__version__ = "([^"]+)"', text, re.M).group(1)


def collect_distribution():
    dist = os.path.join(DISTPATH, "keyseq")
    with open(os.path.join(dist, "README.txt"), "w", encoding="utf-8", newline="\n") as output:
        with open(os.path.join(ROOT, "packaging", "README_dist.txt"), encoding="utf-8") as source:
            output.write(source.read().replace("{version}", read_version()))
    archives = os.listdir(SOURCES_DIR) if os.path.isdir(SOURCES_DIR) else []
    selected = []
    for package, version in SOURCE_PACKAGES.items():
        expected = {f"{package}-{version}{ext}".casefold() for ext in SOURCE_EXTENSIONS}
        matches = [name for name in archives if name.casefold() in expected]
        if not matches:
            raise FileNotFoundError(f"Missing source archive: {package}-{version} in {SOURCES_DIR}")
        selected += matches
    destination = os.path.join(dist, "sources")
    shutil.rmtree(destination, ignore_errors=True)
    os.makedirs(destination)
    for name in sorted(selected):
        shutil.copy2(os.path.join(SOURCES_DIR, name), destination)


block_cipher = None
icon_path = os.path.join(ROOT, "packaging", "windows", "keyseq.ico")
icon = icon_path if os.path.isfile(icon_path) else None
layout_names = ("us_tkl.json", "us_mac.json", "jis.json", "jis_mac.json", "de.json")
datas = [(os.path.join(ROOT, "LICENSE"), ".")]
datas += require_files("keyseq/presentation/help/content/help_*.json", "keyseq/presentation/help/content")
datas += require_files("keyseq/presentation/help/content/third_party/*.json", "keyseq/presentation/help/content/third_party")
datas += require_files("keyseq/presentation/help/content/third_party/*.txt", "keyseq/presentation/help/content/third_party")
datas += require_files("keyseq/presentation/status_icon/images/*.png", "keyseq/presentation/status_icon/images")
datas += require_files("keyseq/shared/i18n/locales/*.json", "keyseq/shared/i18n/locales")
for name in layout_names:
    path = os.path.join(ROOT, "config", "user", "keylayout", name)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    datas.append((path, "config/user/keylayout"))

a = Analysis([os.path.join(ROOT, "main.py")], pathex=[ROOT], binaries=[], datas=datas,
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=["keyseq.infrastructure.os_backend.macos"],
             noarchive=False, optimize=0, module_collection_mode={"pynput": "py"})
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="keyseq", debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, console=False, icon=icon)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, upx_exclude=[], name="keyseq")
collect_distribution()
