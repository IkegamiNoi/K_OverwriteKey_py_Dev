# task_03_application_hotkey_service

## 目的

hotkey 検証の**合成 + キー名検証**を application 層に置く。暫定仕様
[§4.2](../../../history/01_hotkey_validation.md)（設計の正）に従い
`keyseq/application/hotkey_service.py::HotkeyService` を新規作成し、fake を注入する単体テストを付ける。

task_02 で作った domain の文法検査（`validate_hotkey_syntax`）を呼び、
現行 `App.validate_hotkey` の**ステップ ⑦（キー名検証）**を担当して、
**現行と同一の公開契約 `(error, normalized)`** を返す。

**レイヤ制約: application 層の新規追加のみ**（+ `tests/`）。
**presentation / domain / infrastructure は一切変更しない**（差し替えは task_04）。
**挙動不変**。

この時点でも**移設元（`app.py`）は現行のまま残る**（新サービスは誰からも呼ばれない）。
それで正しい（差し替えは task_04）。

## 対象範囲（application の新規追加 + tests）

### 1. `keyseq/application/hotkey_service.py`（新規）

暫定仕様 §4.2 の実装形を**そのまま**実装する:

```python
from __future__ import annotations

from typing import Callable

from keyseq.domain.hotkey import validate_hotkey_syntax


class HotkeyService:
    def __init__(self, *, validate_key_name: Callable[[str], None]) -> None:
        self._validate_key_name = validate_key_name

    def validate(self, hotkey: str) -> tuple[str, str]:
        """(エラーメッセージ, 正規化hotkey) を返す。App.validate_hotkey と同一契約。"""
        error_message, normalized, parts = validate_hotkey_syntax(hotkey)
        if error_message:
            return error_message, ""

        try:
            for p in parts:
                self._validate_key_name(p)
        except Exception as e:
            return f"不明なキー名があります: '{p}'（詳細: {e}）", ""

        return "", normalized
```

- **公開契約は 2 タプル `(error, normalized)`**（domain の 3 タプルは内部インターフェース）。
- **文法エラーが優先**（domain がエラーを返したら `validate_key_name` を呼ばずに即 return）＝現行の順序。
- **domain から受け取った `parts` をそのまま使う**。**`normalized.split("+")` による再構成をしない**
  （暫定仕様 §2-設計判断 2 / 受け入れ条件 §6-5）。
- `from __future__ import annotations` + `from typing import Callable`
  （既存 `keyseq/application/action_executor.py` のスタイルに合わせる）。

#### ⚠️ 実装形の厳守（最大の事故ポイント）

**必ず明示的な `for` ループで書くこと。内包表記 / `map` / `any` / `all` を使ってはならない。**

理由（正確に）: `except` 節が**ループ変数 `p` を参照**して失敗キーをメッセージに埋める。
**Python 3 では内包表記のループ変数は外側スコープへ漏れない**ため、内包表記等で書くと
`except` 内の `p` が `NameError` になり、**エラーメッセージを返す代わりに例外が送出される
＝挙動が変わる**（実証済み）。現行 `app.py:440-446` も明示的な `for` ループで書かれている。

> 補足: 暫定仕様 §4.2 は「`try` を各要素の内側に置くと `p` の値がずれる」と書いているが、
> この理由付けは不正確（`try` をループ内側に置いても `p` は同じ値になり挙動は等価）。
> **ただし §4.2 が規定する実装形そのものは正しい**（現行 `app.py` と同型）ため、
> 上記コードの形を採用する。真の禁止事項は**内包表記等でループ変数を漏らさなくすること**。

- 例外の捕捉は現行と同じく `except Exception`（`validate_key_name` は不正時に元例外を再 raise する）。
- **最初に失敗したキーで return する**（残りの要素を検証しない）＝現行と同じ早期 return。
- エラーメッセージは現物 `app.py:444` の
  `f"不明なキー名があります: '{p}'（詳細: {e}）"` と**1 文字一致**（暫定仕様 §5-4）。

### 2. `tests/test_hotkey_service.py`（新規）

**fake の `validate_key_name` を注入**して検証する（**`tk.Tk` を生成しない**・
`unittest.mock` は使わず**手書きの fake で足りる**）。形式は **unittest**（既存 `tests/` に準拠・
末尾に `if __name__ == "__main__": unittest.main()`）。

| # | 観点 | 期待 |
|---|---|---|
| 1 | 文法エラー（`""`）| `("hotkey が空です。", "")`。**`validate_key_name` が 1 度も呼ばれない**（文法エラー優先） |
| 2 | 文法エラー（`"ctrl++c"`）| `+` 前後空メッセージ・`("...", "")`・fake 未呼び出し |
| 3 | 文法エラー（`"ctrl+ctrl+c"`）| 重複メッセージ・`("...", "")`・fake 未呼び出し |
| 4 | 正常系 `"ctrl+c"` | `("", "ctrl+c")`。fake が `["ctrl", "c"]` の順で呼ばれた |
| 5 | 正規化 `" Ctrl + C "` | `("", "ctrl+c")`。fake が `["ctrl", "c"]`（正規化後の値）で呼ばれた |
| 6 | 不明キー | fake が raise → `("不明なキー名があります: 'notakey'（詳細: <例外の str>）", "")` |
| 7 | **失敗キーの特定** | `"ctrl+notakey"`（`ctrl` は OK・`notakey` で raise）→ メッセージに **`'notakey'`** が入る（`'ctrl'` ではない） |
| 8 | **最初の失敗で止まる** | `"bad1+bad2"`（両方 raise）→ **`'bad1'` が報告され、fake の呼び出しは 1 回だけ**（早期 return） |
| 9 | 公開契約 | 戻り値が**2 要素タプル**であること（domain の 3 タプルを漏らしていない） |

- **#7 / #8 が実装形の正しさ（ループ変数・早期 return）を検証する核**。必ず入れること。
- fake は呼び出し履歴を記録できる形にする（例: 呼ばれたキー名を list に append するクロージャ / 小さなクラス）。

### 設計メモ / 制約

- 移設元 `app.py:416-446` は**この時点では変更しない**。新サービスは task_04 まで未使用のままで正しい。
- **`git grep` は追跡済みファイルしか検索しない**。新規ファイルは未追跡のため、
  確認の grep は**直接 `grep`** を使うこと（`git grep` だと「0 件」と出るが検索されていないだけ）。

## 含まない

- `app.py` の変更（`validate_hotkey` の委譲化・`HotkeyService` の生成・注入元差し替えは **task_04**）
- `keyseq/domain/hotkey.py` の変更（task_02 で完成済み）
- `application/action_executor.py` の変更（暫定仕様 §7 スコープ外。注入元が変わるのみ・シグネチャ不変）
- `tests_ui` の変更（task_01 の特性テストは**そのまま無変更で pass** し続けること）
- hotkey 文法・エラーメッセージの変更 / `validate_key_name` の例外→戻り値化（暫定仕様 §7）

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。

1. **parts 再構成の禁止**（暫定仕様 §6-5）:
   `grep -n 'split("+")' keyseq/application/hotkey_service.py` が **0 件**
   （※ `git grep` ではなく直接 `grep`。新規ファイルは未追跡のため）
2. **実装形**（暫定仕様 §6-6）: `hotkey_service.py` が**明示的な `for` ループ**で書かれ、
   内包表記 / `map` / `any` / `all` を使っていないこと
3. **依存方向**: `grep -nE "^from|^import" keyseq/application/hotkey_service.py` の結果が
   `__future__` / `typing` / **`keyseq.domain.hotkey` のみ**で、
   `keyseq.presentation` / `keyseq.infrastructure` を import していないこと
4. **テスト容易性**: `grep -nE "tkinter|tk\.Tk" tests/test_hotkey_service.py` が **0 件**
5. **標準検証 4 項目**:
   - `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py` → clean
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` → **68+N pass**
     （N = `tests/test_hotkey_service.py` のテスト数。報告に明記）
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` → **16 pass**（変化なし）
   - `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` → **SMOKE OK**
6. **移設元の無変更**: `git diff -- keyseq/presentation/ keyseq/domain/` が**空**
7. **差分の範囲**: 新規 `keyseq/application/hotkey_service.py` と `tests/test_hotkey_service.py` のみ

## 完了条件

- 上記「確認」1〜7 が pass。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点）。重点は
  **実装形（明示的 `for` ループ・try の範囲・早期 return）**、
  **エラーメッセージが `app.py:444` と 1 文字一致**、**文法エラー優先の順序**、
  **parts を再構成していないこと**、**⑦以外を持ち込んでいないこと**。
- 実機目視: **不要**（新サービスは未使用・既存挙動に影響なし。実機確認は task_04 完了後）。
