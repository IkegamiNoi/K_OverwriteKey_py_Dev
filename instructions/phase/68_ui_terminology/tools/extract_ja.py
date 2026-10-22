"""keyseq 配下の日本語を含む文字列リテラル（docstring 除く）を一覧化する。"""
import ast
import re
import sys
from pathlib import Path

JA = re.compile(r"[぀-ヿ一-鿿]")


def docstring_nodes(tree):
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.add(id(body[0].value))
    return ids


def literal_text(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for v in node.values:
            if isinstance(v, ast.Constant):
                parts.append(v.value)
            else:
                parts.append("{" + ast.unparse(v.value) + "}")
        return "".join(parts)
    return None


def main(root, out):
    rows = []
    for path in sorted(Path(root).rglob("*.py")):
        src = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(src)
        docs = docstring_nodes(tree)
        inner = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                for v in node.values:
                    inner.add(id(v))
        for node in ast.walk(tree):
            if id(node) in docs or id(node) in inner:
                continue
            text = literal_text(node)
            if text and JA.search(text):
                rows.append((path.as_posix(), node.lineno, text))
    rows.sort()
    with open(out, "w", encoding="utf-8") as f:
        cur = None
        for p, ln, t in rows:
            if p != cur:
                f.write(f"\n## {p}\n\n")
                cur = p
            f.write(f"- L{ln}: `{t.replace(chr(10), '⏎')}`\n")
    print(len(rows), "strings in", len({r[0] for r in rows}), "files")


main(sys.argv[1], sys.argv[2])
