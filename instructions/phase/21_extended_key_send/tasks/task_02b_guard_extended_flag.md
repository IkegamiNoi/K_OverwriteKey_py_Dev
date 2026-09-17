# task_02b_guard_extended_flag

## 目的

task_02 の二次レビュー（`deep-reviewer`）の採用分を反映する（ユーザー判断 2026-09-19）。

- **指摘 1（中）**: 既存テストは `_send_extended_event` を差し替えているため、**KEYEVENTF_EXTENDEDKEY を外しても 8 本すべて通る**（本フェーズの本質が守られていない）。
- **指摘 8a（低）**: 非公開モジュール `keyboard._canonical_names` からの import を、公開 API `keyboard.normalize_name`（0.13.5 で公開・メイン実測）へ変える。

**infrastructure 1 ファイル + tests 1 ファイル**。挙動は変えない。

## 対象範囲

### `keyseq/infrastructure/input_gateway.py`

- `from keyboard._canonical_names import normalize_name` を削除し、`keyboard.normalize_name(...)` を使う（`import keyboard` は既存）。呼び出し位置・例外処理（失敗時は `None`）は変えない。

### `tests/test_input_gateway_send.py`

- テストを 1 本追加（既存 8 本は変えない）: **拡張キーフラグが実際に付いていることの検証**。
  `unittest.mock.patch.object(input_gateway_module, "ctypes")` で `ctypes` ごと差し替え、`InputGateway().press_key("right")` / `release_key("right")` を呼び、
  `mock.windll.user32.keybd_event` が `(0x27, 0x4D, 0x0001, 0)` と `(0x27, 0x4D, 0x0003, 0)`（EXTENDEDKEY / EXTENDEDKEY|KEYUP）で呼ばれることを検証する。
  `_send_extended_event` は patch しない（フラグの合成を通すため）。

### 設計メモ / 制約

- 挙動不変。`_EXTENDED_KEYS` の値・`send_hotkey` の分岐・押す / 離す順は変えない。
- 既存 8 本の期待値は変えない。落ちたら**期待値を弱めず**報告する。

## 読むファイル

1. `keyseq/infrastructure/input_gateway.py`（全体・編集対象）
2. `tests/test_input_gateway_send.py`（全体・編集対象）

## 含まない

- 保留にした 4 件（途中失敗時に先行キーが実際に出る / `,` 区切りの将来対応 / 離す側の例外の記録 / `requirements.txt` のバージョン固定）= **記録のみ**（task_02 の判断履歴へ）。
- 実機目視・完了処理（**task_02**）。

## 確認

実行は `verifier`。python は `..\..\..\.venv\Scripts\python.exe`。**`git checkout --` などの復元操作は使わない**（未コミットの実装が巻き戻るため）。

1. `-m compileall -q keyseq main.py tests tests_ui` が clean。
2. `-m unittest tests.test_input_gateway_send -v` が全 pass（9 項目）。
3. `-m unittest discover -s tests` が全 pass / `-m tests.smoke_app` が SMOKE OK。
4. **変異検査**: `_send_extended_event` の `flags` から `_KEYEVENTF_EXTENDEDKEY` を外した状態で追加テストが失敗することを確認し、元に戻す（ファイルのコピーを別名で退避してから編集し、コピーで戻す）。

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は **task_02** で実施。
