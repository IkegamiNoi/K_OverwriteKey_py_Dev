"""Guard against untranslated Japanese UI literals in application source.

画面に出る文は tr へ。許可は画面に出ないものだけ。
"""

import ast
from collections import Counter
from pathlib import Path
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
JAPANESE = re.compile(r"[぀-ヿ一-鿿]")
LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical", "log"}
LOG_NAMES = {"logging", "logger", "log", "_logger", "LOGGER", "_log"}

# Each entry is (relative path, enclosing function, exact literal, reason).
ALLOWLIST = [
    ("keyseq/domain/screen_grid/normalize.py", fn, val, "警告ログ専用。normalize_grid の logger.warning にだけ渡る")
    for fn, values in {
        "_key_error": ["キーが空です", "キーが重複しています", "修飾キー ", " です"],
        "_top_layout_with_reason": ["段がありません", "段の形が不正です", "比率が不正です", "列がありません", "列の形が不正です"],
        "_sub_layout_with_reason": ["形が不正です", "段数が不正です", "列数が不正です", "段数・列数が不正です（マスを2つ以上にしてください）", "キー数が不正です"],
    }.items() for val in values
]
# The ratio diagnostic occurs at four distinct return sites.
ALLOWLIST += [("keyseq/domain/screen_grid/normalize.py", "_top_layout_with_reason", "比率が不正です", "警告ログ専用。normalize_grid の logger.warning にだけ渡る") for _ in range(3)]
ALLOWLIST += [("keyseq/infrastructure/win32_window.py", "<module>", value, "ログ専用。_log_once → _logger.exception") for value in [
    "AppUserModelID の設定に失敗しました", "前面ウィンドウのプロセス判定に失敗しました", "前面ウィンドウ HWND の取得に失敗しました",
    "ウィンドウ位置の変更に失敗しました", "マウスボタン状態の取得に失敗しました", "Shift キー状態の取得に失敗しました", "モニター領域の列挙に失敗しました",
    "仮想キーコードからスキャンコードへの変換に失敗しました", "仮想キーコードから文字への変換に失敗しました", "クリック透過ウィンドウの設定に失敗しました"]]
ALLOWLIST += [("keyseq/presentation/dialogs/grid_editor_window.py", "__init__", "編集できる画面がありません", "プログラム側の例外・画面に出ない")]
ALLOWLIST += [("keyseq/presentation/help/help_content.py", "find_text_issues", value, "出荷前の文字検査・テストからだけ呼ばれる") for value in [
    "表示文字列[", " が NFC ではありません", "表示文字列[", " の NFKC に結合文字が含まれています"]]
ALLOWLIST += [("keyseq/presentation/help/help_tab_view.py", "<module>", "・", "区切りの記号・言語に依らない")]


def _docstring_nodes(tree: ast.AST) -> set[int]:
    result: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", ())
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                result.add(id(body[0].value))
    return result


def _message_constants(node: ast.AST) -> set[int]:
    """Log message constants, excluding strings passed to nested calls (screen text)."""
    if isinstance(node, ast.Call):
        return set()
    result = {id(node)} if isinstance(node, ast.Constant) and isinstance(node.value, str) else set()
    for child in ast.iter_child_nodes(node):
        result |= _message_constants(child)
    return result


def inspect_source(source: str, path: str) -> list[tuple[str, int, str, str]]:
    tree = ast.parse(source)
    ignored = _docstring_nodes(tree)
    excluded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in LOG_METHODS and isinstance(node.func.value, ast.Name) and node.func.value.id in LOG_NAMES and node.args:
            excluded.update(_message_constants(node.args[0]))
    found = []
    def visit(node: ast.AST, function: str = "<module>") -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function = node.name
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in ignored | excluded and JAPANESE.search(node.value):
            found.append((path, node.lineno, function, node.value))
        for child in ast.iter_child_nodes(node):
            visit(child, function)
    visit(tree)
    return found


def scan(root: Path, allowlist=()):
    entries = []
    for path in sorted((root / "keyseq").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        entries.extend(inspect_source(path.read_text(encoding="utf-8-sig"), relative))
    actual = Counter((path, function, value) for path, _, function, value in entries)
    allowed = Counter((path, function, value) for path, function, value, _ in allowlist)
    return entries, actual - allowed, allowed - actual


class TestNoJapaneseUiLiterals(unittest.TestCase):
    def test_keyseq_has_only_explicitly_allowed_literals(self):
        entries, unexpected, unused = scan(ROOT, ALLOWLIST)
        self.assertFalse(unexpected, [(p, line, fn, val) for p, line, fn, val in entries if unexpected[(p, fn, val)]])
        self.assertFalse(unused, f"Unused allowlist entries: {unused}")

    def test_allowed_location_rejects_changed_literal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "keyseq").mkdir()
            (root / "keyseq/a.py").write_text('def f():\n return "変更後"\n', encoding="utf-8")
            _, unexpected, _ = scan(root, [("keyseq/a.py", "f", "元の値", "reason")])
            self.assertTrue(unexpected)

    def test_only_first_log_argument_is_excluded(self):
        found = inspect_source('import logging\nlogging.warning("日本語", screen("表示"))\n', "x.py")
        self.assertEqual([item[3] for item in found], ["表示"])
        nested = inspect_source('import logging\nlogging.warning(screen("表示") + "日本語")\n', "x.py")
        self.assertEqual([item[3] for item in nested], ["表示"])

    def test_docstrings_but_not_later_string_expressions_are_excluded(self):
        found = inspect_source('"文書"\ndef f():\n "doc"\n "途中"\n', "x.py")
        self.assertEqual([item[3] for item in found], ["途中"])

    def test_unused_allowlist_entry_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "keyseq").mkdir()
            (root / "keyseq/a.py").write_text('pass\n', encoding="utf-8")
            _, _, unused = scan(root, [("keyseq/a.py", "f", "許可", "reason")])
            self.assertTrue(unused)


if __name__ == "__main__":
    unittest.main()
