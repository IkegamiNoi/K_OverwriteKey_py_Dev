# task_01_characterization_test

## 目的

**安全網**。現行 `App.validate_hotkey`（`keyseq/presentation/app.py:416-446`）の挙動を
**特性テスト（characterization test）で固定する**（暫定仕様 [§4.4](../../../history/01_hotkey_validation.md)）。

本フェーズは hotkey 検証を domain / application へ移す**挙動不変**のリファクタだが、
**現状この検証のテストは 1 件も存在しない**（`tests/` `tests_ui/` とも 0 件）。
移設前に現行挙動をテストで固定し、**task_02〜04 の回帰検出の土台**にする。
このテストが**移設後も無変更で pass すること**が挙動不変の証明になる（暫定仕様 §6-9）。

**実装は一切変更しない**（テスト追加のみ）。**レイヤ制約: テストのみ**。

## 対象範囲（tests_ui のみ・追加のみ）

### `tests_ui/test_app_ui_flows.py`

既存クラス `AppUiFlowsTest`（`setUpClass` で `cls.app` を生成済み）へ、
`self.app.validate_hotkey(...)` を呼ぶテストメソッドを**新規追加**する。

暫定仕様 [§5](../../../history/01_hotkey_validation.md) のエラーメッセージ 4 種 + 正常系を網羅すること。

| # | 観点 | 入力例 | 期待 |
|---|---|---|---|
| 1 | 空 | `""` | `("hotkey が空です。", "")` |
| 2 | 空白のみ | `"   "` | `("hotkey が空です。", "")`（`strip()` 後に空になる経路） |
| 3 | `+` の前後が空 | `"ctrl++c"` / `"+ctrl+c"` / `"ctrl+c+"` | `("hotkey の '+' の前後が空です（例: 'ctrl++c' や '+ctrl+c' や 'ctrl+c+' は不可）。", "")` |
| 4 | 同一キー重複 | `"ctrl+ctrl+c"` | `("hotkey に同じキーが重複しています（例: 'ctrl+ctrl+c'）。", "")` |
| 5 | 不明なキー名 | `"ctrl+<存在しないキー名>"` | エラーメッセージが **`不明なキー名があります: '<そのキー名>'（詳細: ` で始まる**・正規化値は `""` |
| 6 | 正常系 | `"ctrl+c"` | `("", "ctrl+c")` |
| 7 | 正常系（正規化） | `" Ctrl + C "` | `("", "ctrl+c")`（strip / lower / 再結合が効くこと） |

### 設計メモ / 制約

- **#5 のメッセージは完全一致で固定しないこと。** 現行実装は
  `f"不明なキー名があります: '{p}'（詳細: {e}）"` を返し、`{e}` は `keyboard` ライブラリ由来の
  例外メッセージ＝**ライブラリ実装に依存し脆い**。`assertTrue(msg.startswith("不明なキー名があります: 'xxx'（詳細: "))`
  のように**前半部分だけを固定**する（`{p}` が失敗キーを指すことの確認が主目的）。
- **#5 のキー名は実行環境で本当に「不明」になることを確認してから採用すること**（例: `"notakey"`）。
  `keyboard.key_to_scan_codes()` が解決してしまう名前だと正常系になりテストが意図を失う。
  採用した名前と、それが例外になることの確認方法を報告に含める。
- 既存テストの形式に合わせる: **unittest**（`self.assertEqual` / `assertTrue`）。
  `tests_ui/test_app_ui_flows.py` の既存メソッドの書き方に倣う。
- **メソッド名**は `test_validate_hotkey_*` で始める（何のテストか一目で分かるように）。
- テストは `AppUiFlowsTest` に追加する（`setUpClass` の `cls.app` を再利用する。
  **新しい App / tk.Tk を生成しない**＝GUI 生成コストを増やさない）。
- **エラー時の戻り値は常に `(msg, "")`**（正規化値は空文字）。この契約も #1〜#5 で確認すること。

## 含まない

- **実装の変更**（`app.py` に一切触れない）。移設は task_02〜04
- `keyseq/domain/hotkey.py` / `keyseq/application/hotkey_service.py` の新規作成（**task_02 / task_03**）
- `tests/` 側の新テスト（**task_02 / task_03** で層ごとに追加）
- **既存テストのアサーション・メソッド名・テストデータの変更**（追加のみ。暫定仕様 §7 / 計画04 §4-6）
- `dialogs.py` 経由の UI 操作テスト（実機目視で担保・task_04）
- 単キー検証（`validate_key_name` 直接呼び出し箇所）のテスト（暫定仕様 §7 スコープ外）

## 確認

python は必ずリポジトリルートの `.venv` を使う（worktree 相対 `..\..\..\.venv\Scripts\python.exe`。
グローバル `py` は依存欠落で tests_ui / smoke が落ちる。`.claude/rules/python_rules.md`）。

1. **追加テストが pass**:
   `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui -v` で
   追加した `test_validate_hotkey_*` が**すべて pass**し、**tests_ui の総数が 9 → 9+N** に増えている
   （N = 追加したテストメソッド数。報告に明記すること）
2. **標準検証 4 項目**（他がベースラインどおり）:
   - `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py` → clean
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` → **59 pass**（変化なし）
   - `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests_ui` → **9+N pass**
   - `..\..\..\.venv\Scripts\python.exe -m tests.smoke_app` → **SMOKE OK**
3. **実装無変更の確認**: `git diff --stat` の対象が `tests_ui/test_app_ui_flows.py` のみ
   （`keyseq/` 配下に差分が無いこと）
4. **既存テスト無変更の確認**: `git diff -- tests_ui/test_app_ui_flows.py` が**追加のみ**で、
   既存メソッドのアサーション・メソッド名に差分が無いこと

## 完了条件

- 上記「確認」1〜4 が pass。
- **reviewer 採用**（`.claude/rules/review.md` の 5 観点）。
  特に「テストが現行挙動を**正しく**固定しているか（暫定仕様 §5 のメッセージと 1 文字一致しているか）」
  と「#5 が脆い完全一致になっていないか」を重点確認。
- 実機目視: **不要**（テスト追加のみ・実装変更なし）。
