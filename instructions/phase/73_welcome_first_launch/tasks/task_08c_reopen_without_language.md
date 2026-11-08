# task_08c_reopen_without_language

## 目的

再表示の Welcome から Language を外す（暫定 56 v0.7 §7・§10 の 12・ユーザー 2026-11-09）。
**presentation の Welcome + テストのみ。domain / application・JSON スキーマ・言語ファイル不変**。

## 対象範囲

### 1. `keyseq/presentation/welcome/welcome_window.py`

- `_build_content`: Language の行（ラベル・`language_combo`）は `reopen=False` のときだけ作る
- 再表示は上から 基本的な使い方 → サンプル設定の欄 → ボタン行。文言は渡された `language` のまま
- 初回の窓（言語のプレビュー・配列の追従・`WelcomeResult`）は変えない

### 2. `keyseq/presentation/welcome/first_launch.py` `open_welcome_again`

- 窓を閉じた後の言語の比較と `app.set_ui_language` の呼び出しを削除する。フックの停止・再開（try/finally）は保つ

### 3. テスト — `tests_ui/test_welcome_window.py`

- 再表示に `language_combo` が無いことを確かめる（初回にはある）
- `test_open_welcome_again_*`: 閉じた後に `set_ui_language` が呼ばれないこと・フックの再開を確かめる形に直す（言語が変わった場合のテストは「呼ばれない」へ置き換え、重複するテストは統合してよい）

### 設計メモ / 制約

- 窓の文言は `tr_in(self.language, ...)` のままでよい（再表示の `language` は今の言語）
- ソースに日本語の文言を書かない

## 読むファイル

- `keyseq/presentation/welcome/welcome_window.py`・`keyseq/presentation/welcome/first_launch.py`（全体・小さい）
- `tests_ui/test_welcome_window.py`（再表示と `open_welcome_again` のテスト）

## 含まない

- 初回の Welcome の変更・メニュー「Language」の変更
- 正本の更新（task_09）

## 確認

- 上記テストが通る
- `python -m compileall -q keyseq`・`python -m unittest discover -s tests`・`python -m unittest discover -s tests_ui`・`python -m tests.smoke_app` が通る（verifier が `.venv` で実行）

## 完了条件

- 上記確認 pass・**reviewer 採用**
- 実機目視は task_09 で再確認（再表示に Language が無いこと）
