# task_02c_order_with_leading_extended

## 目的

フェーズ完了判定前レビュー（`deep-reviewer`）の採用分を反映する（ユーザー判断 2026-09-19）。

- **指摘 4（低）**: `send_hotkey` の拡張キー経路のテスト 3 本はいずれも「通常キーが先・拡張キーが最後・拡張キー 1 個」の形しかなく、
  **「記述順に押して逆順に離す」（正本 §7.7）が壊れても検出できない**（例: 実装を「通常キーを先にまとめて押す」形へ変えても既存 3 本は通る）。

**tests 1 ファイルのみ。production コードは変更しない。**

## 対象範囲

### `tests/test_input_gateway_send.py`

- `InputGatewaySendTests` にテストを 1 本追加（既存 9 本は変えない）。既存の `setUp`（`send` / `press` / `release` / `ext` を
  `self.events` へ attach_mock する形）をそのまま使い、`self.events.mock_calls` の**完全一致**で順序を固定する。
- 検証する形は次の 2 つ（`subTest` でまとめてよい）:
  1. **拡張キーが先頭 + 通常キーが後**: `send_hotkey("right ctrl+c")` →
     `call.ext(0xA3, 0x1D, key_up=False)` → `call.press("c")` → `call.release("c")` → `call.ext(0xA3, 0x1D, key_up=True)`
  2. **拡張キーが 2 個**: `send_hotkey("right ctrl+insert")` →
     `call.ext(0xA3, 0x1D, key_up=False)` → `call.ext(0x2D, 0x52, key_up=False)` → `call.ext(0x2D, 0x52, key_up=True)` → `call.ext(0xA3, 0x1D, key_up=True)`
- 仮想キー / スキャンコードは `keyseq/infrastructure/input_gateway.py` の `_EXTENDED_KEYS` の値に合わせる
  （`right ctrl` = `(0xA3, 0x1D)` / `insert` = `(0x2D, 0x52)`）。

### 設計メモ / 制約

- **production コードは 1 行も変えない**（`input_gateway.py` は読むだけ）。挙動不変。
- 既存テストの期待値・`setUp` は変えない。落ちたら**期待値を弱めず**報告する。

## 読むファイル

1. `tests/test_input_gateway_send.py`（全体・編集対象）
2. `keyseq/infrastructure/input_gateway.py`（`_EXTENDED_KEYS` と `send_hotkey`・読むだけ）

## 含まない

- production の変更・`_EXTENDED_KEYS` への追加。
- 記録のみ / 保留にしたレビュー指摘（3・5・6・8・9）と文書修正（指摘 2・7）= **task_02** で扱う。

## 確認

実行は `verifier`。python は `..\..\..\.venv\Scripts\python.exe`。**`git checkout --` などの復元操作は使わない**。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests.test_input_gateway_send -v` が全 pass（10 項目）。
3. `-m unittest discover -s tests` が全 pass。
4. **変異検査**: `send_hotkey` の押下ループを `keys` ではなく「通常キーを先に押す」順へ書き換えると追加テストが失敗することを確認し、元に戻す
   （ファイルのコピーを別名で退避してから編集し、コピーで戻す）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 記録・フェーズ完了処理は **task_02**。
