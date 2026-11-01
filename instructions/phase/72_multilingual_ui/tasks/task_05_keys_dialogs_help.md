# task_05_keys_dialogs_help

## 目的

残りの dialogs と help の、画面に出る日本語の文言を文言キーへ移し、task_03 / 03b / 04 で日本語のまま残した互換定数を
呼び出し元と一緒にキー化して消す（暫定 55 §3・§3.4・§6.1・§6.3。キー移行 3）。これで presentation の画面の文言はすべてキーになる。
**presentation 限定・日本語の文言は 1 文字も変えない・JSON スキーマ不変**。

## 対象範囲（presentation の下記限定）

### 対象ファイル（括弧内は日本語の文字列リテラルの概数・docstring とログ専用を除く）

- `dialogs/` のうち task_04 の 4 ファイル（action_control_fields / action_dialog / action_key_hold_fields / action_mouse_scroll_fields）以外の全ファイル
  （preset_manager 45・keymap_edit_dialog 11・trigger_dialog 8・preset_dialog 8・keymap_switch_batch_dialog 8・grid_editor_window 7・
  orphan_sweep_dialog 6・quarantine_manage_dialog 5・layout_delete_dialog 5・reference_cleanup_dialog 3・keymap_set_history_dialog ほか）
- `help/` 配下の全ファイル（help_content 20〔本文の検証エラー文・窓内に出る〕・license_window 6・version_dialog 5・help_window 5・
  third_party 4・help_tab_view 3・help_button 1）。**ヘルプの本文（`help_ja.json` の中身）とライセンス本文はキー化しない**（言語ごとのファイル。暫定 55 §3.4・§6.2）。

### 互換定数の仕上げ（定数ごとキー化し、日本語の定数を残さない）

- `hook_button_texts.py` の `CAPTURE_IDLE_TEXT` / `CAPTURE_ACTIVE_TEXT` / `CAPTURE_TEXTS` / `UNKNOWN_CAPTURE_KEY_HINT_TEXT`:
  既にある `capture_idle_text()` / `capture_active_text()` と同じ形の関数（`capture_texts()`・`unknown_capture_key_hint_text()` 等）にし、
  使っている全ファイル（`dialogs/action_key_hold_fields.py:8,242`・`keymap_edit_dialog.py`・`keymap_switch_batch_dialog.py`・`trigger_dialog.py`）と
  テスト（tests_ui の 7 ファイル程度）を追従させる。キーは既存の `hook_button.capture_*` を使い、無いものだけ足す。
- `keymap_set_history_text.py` の残りの公開定数（6〜23 行・`READ_ONLY_NOTICE` ほか）: 値をキーにして呼び出し元で `tr`、または関数にする。
  呼び出し元 = `dialogs/keymap_set_history_dialog.py`・`controllers/config_io/keymap_set_history_io.py:78`（`text.READ_ONLY_NOTICE`）・
  `tests_ui/test_keymap_set_history_flow.py:296` ほか。

### 移し方（task_03 / 03b / 04 と同じ）

- 画面に出る文字列リテラルを `tr("<キー>", **params)` に替え、`keyseq/shared/i18n/locales/ja.json` に**今と同じ日本語**を足す。
  f-string は名前付きの差し込みへ。文言中の `{` `}` は `{{` `}}`。連結・条件で組み立てる文は出力が今と同じになるまとまった文のキーにする。
- **モジュール定数・クラス属性・既定引数に `tr(...)` を書かない**。
- キーは `<領域>.<画面や部品>.<用途>`。**既存キーを使い回すときは値が完全に同じか必ず確かめる**（「…」の有無・全角 / 半角・句読点。
  task_04 で「プリセット編集」と「プリセット編集…」を取り違えた例がある）。
- `ja.json` は 2 スペースの字下げ・UTF-8・領域ごとにまとめる。`en.json` にはキーを足さない（英訳は task_08）。
- **対象外のまま残す**: ログ専用・docstring・コメント・キーの名前・JSON キー・保存されるデータ値・ファイル名・アクションの種類の内部名・
  ヘルプ本文とライセンス本文・出荷前の文字検査など画面に出ない文。判断に迷ったものは残し、報告に列挙する。

### テスト

- 既存テスト（日本語の表示を assert しているもの）は期待する日本語を変えずに通ること。定数を直接比べているテストは関数 / `tr(...)` を通す比較へ。

## 設計メモ / 制約

- 日本語の文言（全角・半角・改行・空白・句読点）を 1 文字も変えない。
- 互換定数の削除に要る最小限（上記の呼び出し元）以外、task_03〜04 で済んだファイルは触らない。

## 読むファイル

1. `instructions/history/55_multilingual_ui.md` §3.2・§3.4・§6
2. `keyseq/shared/i18n/__init__.py`・`keyseq/shared/i18n/locales/ja.json`（既存キーの確認）
3. 対象ファイル（全体）・`hook_button_texts.py`・`keymap_set_history_text.py`
4. 互換定数の呼び出し元（上記）と、対象の文言を assert しているテスト（`grep` で該当箇所だけ）

## 含まない

- application・domain・infrastructure（task_06）/ `en.json` の英訳・アクションの種類の表示名（task_08）/ `help_en.json`（task_09）/
  日本語リテラルの静的検査（task_10）

## 確認

- presentation 全体（`keyseq/presentation/`）に、画面に出る日本語の文字列リテラルが残っていない（報告で残した理由のあるものを除く）
- 互換定数 `CAPTURE_*`・`UNKNOWN_CAPTURE_KEY_HINT_TEXT`・`keymap_set_history_text` の日本語の定数が無い
- `ja.json` が JSON として正しく、全キーの値が文字列 / en のキーが ja の部分集合（`tests/test_i18n.py`）
- 既存テスト全 pass（`..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `-s tests_ui`）・`-m compileall keyseq` clean・
  `-m tests.smoke_app` OK

## 完了条件

- 上記確認 pass・**reviewer 採用**（削除行の日本語と `ja.json` の値の**完全一致**の機械照合を含む）。
- 実機目視は task_12 でまとめて実施。
