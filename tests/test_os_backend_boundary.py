from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BACKEND_INIT = "infrastructure/os_backend/__init__.py"
ALLOWLIST = {
    ("infrastructure/input_gateway.py", "platform"),
    ("infrastructure/input_gateway.py", "windows_import"),
    ("presentation/modal.py", "windows_import"),
}
WINDOW_IMPORTS = {"ctypes", "winreg", "msvcrt", "keyboard"}
MAC_IMPORTS = {"objc", "Quartz", "AppKit", "Foundation", "CoreFoundation", "ApplicationServices", "HIServices", "Cocoa"}


def _imports(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


def judge_platform(source: str) -> bool:
    tree = ast.parse(source)
    return any((isinstance(n, ast.Attribute) and n.attr == "platform" and isinstance(n.value, ast.Name) and n.value.id == "sys") or
               (isinstance(n, ast.ImportFrom) and n.module == "sys" and any(a.name == "platform" for a in n.names))
               for n in ast.walk(tree))


def judge_os_imports(source: str) -> set[str]:
    return _imports(ast.parse(source)) & (WINDOW_IMPORTS | MAC_IMPORTS)


def judge_private_backend_imports(source: str) -> bool:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import) and any(alias.name.startswith("keyseq.infrastructure.os_backend") for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("keyseq.infrastructure.os_backend"):
            if node.module != "keyseq.infrastructure.os_backend" or any(a.name in {"windows", "macos", "contracts"} for a in node.names):
                return True
    return False


def _is_platform_package_target(node: ast.ImportFrom) -> bool:
    platform_modules = ("keyseq.infrastructure.os_backend.windows", "keyseq.infrastructure.os_backend.macos")
    if node.level == 0:
        if node.module == "keyseq.infrastructure.os_backend":
            return any(alias.name in {"windows", "macos"} for alias in node.names)
        return bool(node.module) and any(node.module == base or node.module.startswith(base + ".") for base in platform_modules)
    if node.level == 1:
        if node.module:
            return node.module in {"windows", "macos"} or node.module.startswith(("windows.", "macos."))
        return any(alias.name in {"windows", "macos"} for alias in node.names)
    return False


def judge_eager_platform_imports(source: str) -> bool:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and _is_platform_package_target(node):
            return True
        if isinstance(node, ast.Import) and any(
            a.name == base or a.name.startswith(base + ".")
            for a in node.names
            for base in ("keyseq.infrastructure.os_backend.windows", "keyseq.infrastructure.os_backend.macos")
        ):
            return True
    return False


def _violations(path: str, source: str) -> set[str]:
    found: set[str] = set()
    if judge_platform(source) and path != BACKEND_INIT:
        found.add("platform")
    os_imports = judge_os_imports(source)
    windows_path = path.startswith("infrastructure/os_backend/windows/")
    macos_path = path.startswith("infrastructure/os_backend/macos/")
    if (os_imports & WINDOW_IMPORTS and not windows_path) or (os_imports & MAC_IMPORTS and not macos_path):
        found.add("windows_import")
    if not path.startswith("infrastructure/os_backend/") and judge_private_backend_imports(source):
        found.add("private_backend_import")
    if path == BACKEND_INIT and judge_eager_platform_imports(source):
        found.add("eager_platform_import")
    return found


class OsBackendBoundaryTests(unittest.TestCase):
    def test_keyseq_import_boundaries(self) -> None:
        observed: set[tuple[str, str]] = set()
        for file in (ROOT / "keyseq").rglob("*.py"):
            relative = file.relative_to(ROOT / "keyseq").as_posix()
            observed.update((relative, kind) for kind in _violations(relative, file.read_text(encoding="utf-8-sig")))
        self.assertFalse(observed - ALLOWLIST)

    def test_allowlist_entries_still_have_violations(self) -> None:
        for path, kind in ALLOWLIST:
            source = (ROOT / "keyseq" / path).read_text(encoding="utf-8-sig")
            self.assertIn(kind, _violations(path, source), (path, kind))

    def test_judges_detect_examples_and_clean_sources(self) -> None:
        self.assertTrue(judge_platform("import sys\nx = sys.platform"))
        self.assertTrue(judge_platform("from sys import platform"))
        self.assertFalse(judge_platform("import os"))
        self.assertEqual(judge_os_imports("import ctypes, Quartz"), {"ctypes", "Quartz"})
        self.assertFalse(judge_os_imports("import os"))
        self.assertTrue(judge_private_backend_imports("from keyseq.infrastructure.os_backend.windows import backend"))
        self.assertTrue(judge_private_backend_imports("import keyseq.infrastructure.os_backend.windows.backend"))
        self.assertTrue(judge_private_backend_imports("from keyseq.infrastructure.os_backend import windows"))
        self.assertFalse(judge_private_backend_imports("from keyseq.infrastructure.os_backend import get_backend"))
        self.assertTrue(judge_eager_platform_imports("from .windows import backend"))
        self.assertTrue(judge_eager_platform_imports("from keyseq.infrastructure.os_backend.windows.backend import create_backend"))
        self.assertTrue(judge_eager_platform_imports("from keyseq.infrastructure.os_backend import windows"))
        self.assertTrue(judge_eager_platform_imports("from . import windows"))
        self.assertFalse(judge_eager_platform_imports("from .contracts import Capabilities"))
        self.assertFalse(judge_eager_platform_imports("def load():\n    from .windows import backend"))


if __name__ == "__main__":
    unittest.main()
