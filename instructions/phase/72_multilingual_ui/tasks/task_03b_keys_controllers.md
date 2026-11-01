# task_03b_keys_controllers

## 目的

presentation の controllers のうち `config_io/`・`keymap_panel/`・`trigger_panel/` の、画面に出る日本語の文言を文言キーへ移す
（暫定 55 §3・§6.1・§6.3。キー移行 1b・2026-11-01 に task_03 から分割）。あわせて task_03 で日本語のまま残した互換定数のうち、
この範囲が使うものを呼び出し元と一緒にキー化する。**presentation 限定・日本語の文言は 1 文字も変えない・JSON スキーマ不変**。

## 対象範囲（presentation の下記限定）

### 対象ファイル（括弧内は日本語の文字列リテラルの概数・docstring とログ専用を除く）

- `controllers/config_io/` 配下の全ファイル（keymap_set_io 58・child_save_dialog 28・sequence_file_io 24・keymap_file_io 24・
  trigger_set_file_io 20・quarantine_manage_io 14・hotkey_presets_io 11・child_save_rows 11・io_dialogs 10・orphan_sweep_io 7・
  reference_cleanup_io 5・child_save_columns 5 ほか）
- `controllers/keymap_panel/` 配下の全ファイル（keymap_panel_controller 71・keymap_add_flow 9・keymap_list_edit 7 ほか）
- `controllers/trigger_panel/` 配下の全ファイル（action_edit 38・trigger_row_edit 29・trigger_panel_controller 24・trigger_list_edit 5 ほか）

### 互換定数（task_03 で日本語のまま残したもの）

- `reference_cleanup_text.py` の `CLEANUP_EMPTY_MESSAGE` → キーにして、呼び出し元（`config_io/reference_cleanup_io.py`）で `tr` する。
- `status_text.py` の `HOOK_STATE_LABELS` → 値を文言キーにして、呼び出し元（`trigger_panel/trigger_panel_controller.py` ほか）で `tr` する。
  `tests/test_status_text.py` は期待する日本語を変えずに `tr(...)` を通した比較へ直す。
- `keymap_set_history_text.py` の公開定数（6〜28 行）のうち、`config_io/keymap_set_history_io.py` **だけ**が使うもの → キーにして呼び出し元で `tr`。
  `dialogs/keymap_set_history_dialog.py` も使う定数は task_05 で扱うので残す。
- 定数をキーにしたら、日本語の定数は残さない（同じ日本語を 2 か所に持たない）。

### 移し方（task_03 と同じ）

- 画面に出る文字列リテラルを `tr("<キー>", **params)` に替え、`keyseq/shared/i18n/locales/ja.json` に**今と同じ日本語**を足す。
  f-string は名前付きの差し込みへ（式は差し込み前に変数へ）。文言中の `{` `}` は `{{` `}}`。連結・条件で組み立てる文は出力が今と同じになる
  まとまった文のキーにする（語の断片をキーにしない）。
- **モジュール定数・クラス属性・既定引数に `tr(...)` を書かない**。定数の表は値をキーにして表示する時点で `tr`、または表を関数にする（task_02 の形）。
  task_02 で作ったラベルの関数（`keymap_add_flow._kind_titles` / `_kind_row_labels`）も `tr` を返す形へ。
- キーの名前は `<領域>.<画面や部品>.<用途>`。task_03 で作った `common.*` 等の既存キーは、同じ意味なら共用する（`ja.json` を見て重複を作らない）。
- `ja.json` は 2 スペースの字下げ・UTF-8・領域ごとにまとめる。`en.json` にはキーを足さない（英訳は task_08）。
- **対象外のまま残す**: ログ専用の文言・docstring・コメント・キーの名前・JSON キー・保存されるデータ値・ファイル / フォルダ名
  （`config.json` 等）・アクションの種類の内部名（表示名化は task_08）。判断に迷ったものは残し、報告に列挙する。

### テスト

- 既存テスト（日本語の表示を assert しているもの）は、期待する日本語を変えずに通ること。定数を直接比べているテストは `tr(...)` を通した比較へ。

## 設計メモ / 制約

- 日本語の文言（全角・半角・改行・空白・句読点）を 1 文字も変えない。
- 対象外のファイル（dialogs・help・内側の層・task_03 で済んだファイル）は、互換定数の削除に要る最小限（上記の 3 ファイル）以外は触らない。

## 読むファイル

1. `instructions/history/55_multilingual_ui.md` §3.2・§6
2. `keyseq/shared/i18n/__init__.py`・`keyseq/shared/i18n/locales/ja.json`（既存キーの確認）
3. 対象ファイル（全体）と `reference_cleanup_text.py`・`status_text.py`・`keymap_set_history_text.py`
4. 対象の文言を assert しているテスト（`grep` で文言を探して該当箇所だけ）

## 含まない

- `dialogs/`（task_04・05）/ `help/`（task_05）/ application・domain・infrastructure（task_06）
- `en.json` の英訳・アクションの種類の表示名（task_08）/ 日本語リテラルの静的検査（task_10）

## 確認

- 対象ファイルに、画面に出る日本語の文字列リテラルが残っていない（ログ専用・docstring・報告で残した理由のあるものを除く）
- `ja.json` が JSON として正しく、全キーの値が文字列 / en のキーが ja の部分集合（`tests/test_i18n.py`）
- 既存テスト全 pass（`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui`）・`-m compileall keyseq` clean・
  `-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**（削除行の日本語と `ja.json` の値の機械照合を含む）。
- 実機目視は task_12 でまとめて実施。
