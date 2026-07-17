# task_02_domain_hotkey

## 目的

hotkey の**文法検査**を domain 層へ切り出す。暫定仕様
[§4.1](../../../history/01_hotkey_validation.md)（設計の正）に従い
`keyseq/domain/hotkey.py::validate_hotkey_syntax` を新規作成し、
`tk.Tk` もモックも不要な単体テストを付ける（**本フェーズの主目的の一つ＝テスト容易性**）。

**レイヤ制約: domain 層の新規追加のみ**（+ `tests/`）。
**presentation / application / infrastructure は一切変更しない**（差し替えは task_04）。
**挙動不変**: 現行 `App.validate_hotkey`（`keyseq/presentation/app.py:416-446`）の
**ステップ ①〜⑥ をそのまま移す**。

この時点では**移設元（`app.py`）は現行のまま残る**（新モジュールは誰からも呼ばれない）。
それで正しい（1 タスク 1 関心事。差し替えは task_04）。

## 対象範囲（domain の新規追加 + tests）

### 1. `keyseq/domain/hotkey.py`（新規）

```python
def validate_hotkey_syntax(hotkey: str) -> tuple[str, str, list[str]]:
    """hotkey の文法を検証し (エラーメッセージ, 正規化hotkey, 要素リスト) を返す。
    エラーなしならエラーメッセージは ""。キー名の実在は検証しない（infrastructure の関心）。"""
```

現行 `app.py:421-437` の**ステップ ①〜⑥をそのまま移す**（`self.` は無くなる）:

| ステップ | 内容 | 現行 |
|---|---|---|
| ① | `s = (hotkey or "").strip()` → 空なら `("hotkey が空です。", "", [])` | `app.py:421-423` |
| ② | `raw = s.split("+")` | `app.py:426` |
| ③ | `parts = [p.strip().lower() for p in raw]` | `app.py:427` |
| ④ | `any(p == "" for p in parts)` → `("hotkey の '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。", "", [])` | `app.py:429-430` |
| ⑤ | `normalized = "+".join(parts)` | `app.py:433` |
| ⑥ | `len(set(parts)) != len(parts)` → `("hotkey に同じキーが重複しています（例: 'ctrl+ctrl+c'）。", "", [])` | `app.py:436-437` |
| 終 | `return "", normalized, parts` | — |

- **ステップ ⑦（`validate_key_name` によるキー名検証）は含まない**（task_03 の application 側の責務）。
- **エラー時は `(msg, "", [])`**（正規化値は空文字・parts は空リスト）。
- **説明コメントも現行から移す**（`app.py:425, 432, 435` の「split結果を保持して空要素を検出する」等）。
- **順序を変えないこと**。現行は ⑤（normalized 生成）が ⑥（重複検出）より**前**にある。
  出力に影響はないが、**忠実な移設のため順序を保つ**。
- `(hotkey or "")` の `or ""` ガードを**残すこと**（`None` を渡しても落ちない現行挙動）。

#### 制約

- **標準ライブラリのみ**。`keyseq.application` / `keyseq.infrastructure` / `keyseq.presentation` を
  **import しない**（暫定仕様 §6-3 の受け入れ条件）。実際には import 不要な見込み。
- **注入なし・クラスなし・モジュールレベルの純粋関数**（既存 domain スタイル準拠。
  `keyseq/domain/config.py` / `key_identifiers.py` を参照）。
- 型注釈を付ける（`.claude/rules/python_rules.md`）。

### 2. `tests/test_hotkey.py`（新規）

**`App` / `tk.Tk` を生成せず、モックも使わず**、関数を直接呼ぶ
（既存例 `tests/test_key_identifiers.py` に倣う。**unittest** 形式・末尾に
`if __name__ == "__main__": unittest.main()`）。

最低限のケース:

| # | 入力 | 期待 |
|---|---|---|
| 1 | `""` | `("hotkey が空です。", "", [])` |
| 2 | `"   "` | `("hotkey が空です。", "", [])`（strip 経路） |
| 3 | `"ctrl++c"` / `"+ctrl+c"` / `"ctrl+c+"` | `+` 前後空エラー・`("...", "", [])` |
| 4 | `"ctrl+ctrl+c"` | 重複エラー・`("...", "", [])` |
| 5 | `"ctrl+c"` | `("", "ctrl+c", ["ctrl", "c"])` |
| 6 | `" Ctrl + C "` | `("", "ctrl+c", ["ctrl", "c"])`（strip / lower / 再結合） |
| 7 | 単一キー `"f12"` | `("", "f12", ["f12"])` |
| 8 | **責務境界**: 実在しないキー名 `"notakey"` | **`("", "notakey", ["notakey"])`** ＝ **domain はキー名の実在を検証しない**ことを固定する |
| 9 | 不変条件 | 正常時に `normalized == "+".join(parts)` が成り立つこと |

- エラーメッセージは暫定仕様 [§5](../../../history/01_hotkey_validation.md) と**1 文字一致**させること
  （出典は現物 `app.py:423, 430, 437`）。
- **#8 は重要**: 「文法は OK だがキー名は不明」という入力に対し domain がエラーを返さないことを固定する。
  これが後続 task_03 の責務分担（キー名検証は application）の前提になる。

### 設計メモ / 制約

- 移設元 `app.py:416-446` は**この時点では変更しない**。新モジュールは task_04 まで未使用のままで正しい。
- `tests/test_hotkey.py` が `tk` を import していないこと自体が「テスト容易性の達成」の証拠になる
  （暫定仕様 §6-7）。

## 含まない

- `keyseq/application/hotkey_service.py` の作成（**task_03**）
- `app.py` の変更（`validate_hotkey` の委譲化・注入元差し替えは **task_04**）
- **ステップ ⑦（キー名検証 / `validate_key_name`）の実装**（task_03）
- `tests_ui` の変更（task_01 で追加した特性テストは**そのまま無変更で pass** し続けること）
- hotkey 文法・エラーメッセージの変更 / 改善（挙動不変）
- 単キー検証の統一（暫定仕様 §7 スコープ外）

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`。
`.claude/rules/python_rules.md`）。

1. **依存方向**（暫定仕様 §6-3）:
   `git grep -nE "^from|^import" keyseq/domain/hotkey.py` の結果に
   `keyseq.application` / `keyseq.infrastructure` / `keyseq.presentation` が**含まれないこと**
   （標準ライブラリのみ、または import なし）
2. **テスト容易性**（暫定仕様 §6-7）:
   `git grep -nE "tkinter|unittest\.mock|Mock" tests/test_hotkey.py` が **0 件**
   （`tk.Tk` を生成せず・モックも使わずに pass すること）
3. **標準検証 4 項目**:
   - `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py` → clean
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` → **59+N pass**
     （N = `tests/test_hotkey.py` のテスト数。報告に明記）
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` → **16 pass**（変化なし）
   - `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` → **SMOKE OK**
4. **移設元の無変更**: `git diff -- keyseq/presentation/` が**空**（app.py に触れていないこと）
5. **差分の範囲**: `git diff --stat` の対象が `keyseq/domain/hotkey.py`（新規）と
   `tests/test_hotkey.py`（新規）のみ

## 完了条件

- 上記「確認」1〜5 が pass。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点）。重点は
  **①〜⑥ が現行 `app.py:421-437` と 1 文字一致で移設されているか**（エラーメッセージ・順序・
  `or ""` ガード・コメント）と、**⑦を含めていないこと**、**依存方向**。
- 実機目視: **不要**（新モジュールは未使用・既存挙動に影響なし。実機確認は task_04 完了後）。
