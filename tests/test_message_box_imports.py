import ast
import unittest
from pathlib import Path


class MessageBoxImportTests(unittest.TestCase):
    def test_tkinter_messagebox_imports_use_wrapper(self):
        root = Path(__file__).resolve().parents[1] / "keyseq" / "presentation"
        violations = []
        for path in root.rglob("*.py"):
            if path.name == "message_box.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "tkinter":
                    if any(alias.name == "messagebox" for alias in node.names):
                        violations.append(f"{path}:{node.lineno}")
                elif isinstance(node, ast.Import):
                    if any(alias.name == "tkinter.messagebox" for alias in node.names):
                        violations.append(f"{path}:{node.lineno}")
        self.assertEqual(violations, [])
