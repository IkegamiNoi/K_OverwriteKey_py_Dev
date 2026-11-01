# task_04_keys_action_dialogs

## 目的

アクションの編集まわりの dialogs の、画面に出る日本語の文言を文言キーへ移す（暫定 55 §3・§6.1・§6.3。キー移行 2）。
task_02 で作ったラベルの関数（コード → ラベル）も `tr` を返す形にする。**presentation の dialogs 4 ファイル限定・
日本語の文言は 1 文字も変えない・JSON スキーマ不変**。

## 対象範囲（presentation/dialogs の下記 4 ファイル限定）

- `dialogs/action_control_fields.py`（約 54）・`dialogs/action_dialog.py`（約 51）・`dialogs/action_key_hold_fields.py`（約 23）・
  `dialogs/action_mouse_scroll_fields.py`（約 12）（括弧内は日本語の文字列リテラルの概数・docstring とログ専用を除く）
- task_02 のラベルの関数（`_system_labels`・`_out_of_range_labels`・`_target_labels`・`_edge_labels`・`_button_labels`・`_direction_labels` 等）は
  関数の形のまま中身を `tr("<キー>")` にする（呼び出し時に評価されるので可）。

### 移し方（task_03 / 03b と同じ）

- 画面に出る文字列リテラルを `tr("<キー>", **params)` に替え、`keyseq/shared/i18n/locales/ja.json` に**今と同じ日本語**を足す。
  f-string は名前付きの差し込みへ（式は差し込み前に変数へ）。文言中の `{` `}` は `{{` `}}`。連結・条件で組み立てる文は出力が今と同じになる
  まとまった文のキーにする。
- **モジュール定数・クラス属性・既定引数に `tr(...)` を書かない**。
- キーの名前は `<領域>.<画面や部品>.<用途>`（例 `action_dialog.key_hold.target.key`）。既存キー（`common.*` 等）は同じ意味なら共用する
  （`ja.json` を見て重複を作らない）。
- `ja.json` は 2 スペースの字下げ・UTF-8・領域ごとにまとめる。`en.json` にはキーを足さない（英訳は task_08）。
- **対象外のまま残す**: ログ専用・docstring・コメント・キーの名前・JSON キー・保存されるデータ値・**アクションの種類の内部名**
  （`hotkey` / `mouse_click` 等。Combobox に出している種類の値の表示名化は task_08）・`ENCODINGS` の `UTF-8` / `Shift_JIS`。
  `hook_button_texts.py` の互換定数（`CAPTURE_*` / `UNKNOWN_CAPTURE_KEY_HINT_TEXT`）を使っている箇所は今のまま（task_05 で定数ごとキー化）。
  判断に迷ったものは残し、報告に列挙する。

### テスト

- 既存テスト（日本語の表示を assert しているもの）は期待する日本語を変えずに通ること。`tests_ui/test_internal_value_codes.py` の
  ラベル関数の差し替えテストが通ること。

## 設計メモ / 制約

- 日本語の文言（全角・半角・改行・空白・句読点）を 1 文字も変えない。
- 対象の 4 ファイルと `ja.json`・追従が要るテスト以外は触らない。

## 読むファイル

1. `instructions/history/55_multilingual_ui.md` §3.2・§6
2. `keyseq/shared/i18n/__init__.py`・`keyseq/shared/i18n/locales/ja.json`（既存キーの確認）
3. 対象の 4 ファイル（全体）
4. 対象の文言を assert しているテスト（`grep` で文言を探して該当箇所だけ）

## 含まない

- 残りの dialogs・help・互換定数の仕上げ（task_05）/ application・domain・infrastructure（task_06）
- `en.json` の英訳・アクションの種類の表示名（task_08）/ 日本語リテラルの静的検査（task_10）

## 確認

- 対象 4 ファイルに、画面に出る日本語の文字列リテラルが残っていない（報告で残した理由のあるものを除く）
- `ja.json` が JSON として正しく、全キーの値が文字列 / en のキーが ja の部分集合（`tests/test_i18n.py`）
- 既存テスト全 pass（`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui`）・`-m compileall keyseq` clean・
  `-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**（削除行の日本語と `ja.json` の値の機械照合を含む）。
- 実機目視は task_12 でまとめて実施。
