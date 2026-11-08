# task_08d_completion_review_fixes

## 目的

フェーズ完了前レビュー（deep-reviewer）の採用分を直す（ユーザー 2026-11-09「推奨どおり」）。
**presentation + テストのみ。domain / application・JSON スキーマ不変**。

## 対象範囲

### 1. 「サンプル設定に戻す」で全キーマップを未保存に（暫定 56 §5.3・`data_schema` §5.8.8）— `keyseq/presentation/controllers/config_io/keymap_set_io.py` `restore_default`

- 今はアクティブのキーマップのトリガーと、キーなしの `mark_trigger_set_dirty()`（アクティブ分のみ）だけに印を付けている
- **全キーマップ**のトリガーセットと、その全トリガーの出力シーケンスに印を付ける（`keyseq/domain/keymap_triggers.py` の `iter_trigger_sets` と、`dirty_state.py` の `mark_trigger_set_dirty(key)` / `mark_sequence_dirty` を使う。シグネチャは実物で確かめる）
- キーマップの印（既存のループ）と他の処理は変えない

### 2. 警告の前に本体を表示（暫定 56 §3）— `keyseq/presentation/app.py` `_finish_first_launch`

- サンプルの書き出し失敗の `messagebox.showwarning` より先に `deiconify()` する（隠れた親の下に警告が出ないように）。他の順序は変えない。`deiconify` は 1 回だけ

### 3. テスト

- tests_ui: 実際の既定データ（3 キーマップ）で `restore_default` を実行し、全キーマップのトリガーセットと全シーケンスが未保存になる（`tests_ui/test_config_io_characterization_keymap_set_startup.py` の復元のテストの近く。`new_default_data` のモックを使っている setUp に注意）
- tests_ui: `tests_ui/test_first_launch_flow.py` で、警告の時点で `deiconify` が済んでいる順序を確かめる

## 読むファイル

- `keyseq/presentation/controllers/config_io/keymap_set_io.py:680-712`
- `keyseq/presentation/controllers/dirty_state.py`（mark 系）・`keyseq/domain/keymap_triggers.py:1-70`
- `keyseq/presentation/app.py` の `_finish_first_launch`
- 上記テストの該当箇所

## 含まない

- 正本・暫定仕様の更新（メインが task_09 で行う）・他の指摘（保留 / 除外）

## 確認

- `python -m compileall -q keyseq`・`python -m unittest discover -s tests`・`python -m unittest discover -s tests_ui`・`python -m tests.smoke_app` が通る（verifier が `.venv` で実行）

## 完了条件

- 上記確認 pass・**reviewer 採用**
