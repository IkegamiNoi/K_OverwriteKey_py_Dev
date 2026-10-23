"""after_ja_strings.md から、暫定 51 の「やめる語」・表記規則の対象が残る文字列を候補として抜き出す。"""
import re
import sys
from pathlib import Path

PATTERNS = [
    ("A1", r"キーマップセット|keymap_set(?!\.json の|_)"),
    ("A2", r"(?<![_./])\bkeymap\b(?![_.])"),
    ("A3", r"キーマップを(更新|クリア)|キーマップ送信|キーマップは単キー"),
    ("A4", r"キーマップ元キー|キーマップの元キー"),
    ("A5", r"停止トリガー"),
    ("A6", r"直接切替"),
    ("A7", r"(?<![_.])\bsequence\b(?![_.])"),
    ("A8", r"(?<![_.])\btrigger_set\b(?![_.])"),
    ("A9", r"を読込|読込できません"),
    ("A10", r"キー入力で取得|キーを1回押して"),
    ("A12", r"グローバル|個別プリセット|個別の保存先|組込既定|ホットキープリセット|OSショートカット"),
    ("A13", r"例の設定|例を復元|例の復元"),
    ("A14", r"省略表示|フルに戻す|常に手前"),
    ("A15", r"上位|索引"),
    ("A16", r"孤児|棚卸し"),
    ("A17", r"隔離"),
    ("A18", r"実行単位|マニフェスト"),
    ("A19", r"別名で保存"),
    ("A20", r"通常トリガー|トリガーのキー"),
    ("D1", r"\([^()]*[぀-ヿ一-鿿][^()]*\)"),
    ("D2", r"例[)）]"),
    ("D3", r"\.\.\."),
    ("D4", r"："),
    ("D5", r"[A-Za-z0-9][ ][぀-ヿ一-鿿]|[぀-ヿ一-鿿][ ][A-Za-z0-9]"),
    ("D6", r"既に"),
    ("D7", r"選んでください"),
    ("D8", r"不正"),
    ("D9", r"が空です"),
    ("D11", r"Keyboard UI|デフォルト"),
    ("M9", r"ディレクトリ|走査"),
]


def main(src: str, out: str) -> None:
    rows = []
    path = ""
    for raw in Path(src).read_text(encoding="utf-8").splitlines():
        if raw.startswith("## "):
            path = raw[3:].strip()
            continue
        m = re.match(r"- L(\d+): `(.*)`$", raw)
        if not m:
            continue
        text = m.group(2)
        hits = [name for name, pat in PATTERNS if re.search(pat, text)]
        if hits:
            rows.append(f"| {path}:{m.group(1)} | {','.join(hits)} | `{text}` | |")
    Path(out).write_text(
        "# 残存候補（実装後・機械抽出）\n\n| 場所 | 規則 | 文字列 | 理由 |\n|---|---|---|---|\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )
    print(len(rows))


main(sys.argv[1], sys.argv[2])
