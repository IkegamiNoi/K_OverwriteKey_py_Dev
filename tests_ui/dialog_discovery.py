"""AST でダイアログを発見する。別名 import・多段継承は拾わない。"""
import ast
from pathlib import Path


PRESENTATION: Path = Path(__file__).resolve().parents[1] / "keyseq" / "presentation"
DIALOGS: Path = PRESENTATION / "dialogs"


def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def find_calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [call for call in ast.walk(node) if isinstance(call, ast.Call) and (
        isinstance(call.func, ast.Name) and call.func.id == name
        or isinstance(call.func, ast.Attribute) and call.func.attr == name
    )]


def dialog_classes() -> list[tuple[Path, ast.ClassDef]]:
    return [
        (path, node)
        for path in sorted(DIALOGS.glob("*.py"))
        for node in parse(path).body
        if isinstance(node, ast.ClassDef) and any(
            isinstance(base, ast.Attribute) and base.attr == "Toplevel"
            or isinstance(base, ast.Name) and base.id == "Toplevel"
            for base in node.bases
        )
    ]
