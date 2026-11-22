# task_03_counter_text_action

## 目的

新しい種類 `counter_text`（「カウンターの値を入力」）の実行を加える。カウンターの実効値（task_02）を 10 進の文字列にして、text と同じ経路・send guard で入力する通常アクション（暫定 58 §3.4・§2.5・§2.9）。
**application の `action_executor.py`・domain の定数・文言（ja / en）限定**。runner の経路は変えない（file_line 以外の通常アクションは既に `execute` を通る）。一覧の表示・編集ダイアログの種類の候補・ヘルプは変えない。

## 対象範囲（application + domain の定数 + 文言）

### `keyseq/domain/sequence_control.py`

- 定数 `ACTION_TYPE_COUNTER_TEXT: str = "counter_text"` を `ACTION_TYPE_FILE_LINE` の隣に足す。

### `keyseq/application/action_executor.py`

- `execute` に `counter_text` の分岐を足す（`text` の分岐の後・`key_hold` の前あたり）:
  1. `counter` が str で trim 後に空でなければその名前 / それ以外は空。
  2. 空なら実行時エラー「カウンター名が空です」（既存キー `application.action_executor.counter_empty`）を `_report_held_error` で通知して `False`。
     通知する行の写しの `value` 欄にはカウンター名（空なら空文字）を入れる（`value` キーが無い種類のため・暫定 58 §3.4）。ラベルがあれば既存の通知と同じくメッセージに含める（file_line の `_file_line_error_message` の形を手本にしてよい・新しい文言キーが要るなら ja / en の両方に足す）。
  3. `self._get_counter` が `None` なら既存キー `counter_callback_missing` で同じく通知して `False`。
  4. `str(self._get_counter(name))` を `self._write_text(...)` で送る。送信の例外は `text` と同じキー `text_send_failed` で通知して `False`（止まる系）。成功は `True`。
- 種別不正の文言（`application.action_executor.invalid_type` / `invalid_type_labeled`）の列挙に `counter_text` を足す（`key_hold` の後）。

### 文言（`keyseq/shared/i18n/locales/ja.json`・`en.json` の両方）

- 上の `invalid_type` / `invalid_type_labeled` の列挙の更新（両言語）。新しいキーを足した場合は両方に足す。

### テスト（追加・修正。**テストの実行はしない**）

- 新規 `tests/test_action_executor_counter_text.py`（`tests/test_action_executor_file_line.py` / `test_action_executor_type.py` の作り方を手本に）:
  - 値 5 / −3 / 0 が `"5"` / `"-3"` / `"0"` として `_write_text` の経路（send guard を含む既存の経路）で送られ `True`。
  - `counter` が空・空白・非文字列 → 「カウンター名が空です」で通知・何も送らない・`False`。通知の写しの `value` がカウンター名。ラベルありの通知。
  - `get_counter` が無い → 通知・`False`。
  - 送信の例外 → `text_send_failed` で通知・`False`。
  - 種類の判定が大文字小文字・前後の空白を許す（既存の種類と同じ）。
- 種別不正の文言を完全一致で見ている既存テスト（`tests/test_action_executor_type.py` など）があれば列挙の更新に合わせる。
- runner から通常アクションとして 1 ステップを消費することのテスト（`tests/test_sequence_runner.py` の text の行のテストを手本に 1 件）: `[counter_text n]` を単発で実行すると送られ、位置が次へ進む。停止の行の判定で「送った」に数える（`tests/test_sequence_runner_stop.py` の手本に 1 件）。

## 設計メモ / 制約

- 主入力 = 暫定 58 §3.4（独立した種類・通常アクション・text と同じ経路・空名はエラー・通知の値はカウンター名）。
- 値は `get_counter`（`presentation/app.py` が task_02 で `counter_value` に変更済み）から取る。`ActionExecutor` は `AppState` を直接読まない。
- `counter_text` は file_line と違い**読込の保留を経ない**（runner の `ACTION_TYPE_FILE_LINE` の分岐に足さない）。
- 一覧の値表示（`domain/config.py` の `format_action_list_item`・`action_list_rendering.py`）は task_04、ダイアログの種類の候補は task_05。ここでは触らない。
- 編集は apply_patch で行い、Python のスクリプトでファイルを書き換えない。互換の工夫・テストの期待値の推測を足さない。

## 読むファイル

- `instructions/history/58_counter_expansion.md` §3.4（主入力）
- `keyseq/application/action_executor.py:57-160,255-270`（`_file_line_error_message`・`execute`・`_write_text`）
- `keyseq/domain/sequence_control.py:11-13`
- `keyseq/shared/i18n/locales/ja.json` / `en.json` の `application.action_executor.*`（`grep -n "application.action_executor"`）
- 手本のテスト: `tests/test_action_executor_file_line.py`・`tests/test_action_executor_type.py`・`tests/test_sequence_runner.py` の text の行のテスト・`tests/test_sequence_runner_stop.py`

## 含まない

- 一覧・簡易表示・呼び出し先の表示枠の `[counter_text] n (=5)`（task_04）
- 編集ダイアログの種類の候補・入力欄・候補の名前・ヘルプ・`ui_terms.md`（task_05・task_07）
- 正本 `spec_detail/` の更新（task_07）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests` clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests.test_action_executor_counter_text tests.test_action_executor_type tests.test_action_executor_file_line tests.test_sequence_runner tests.test_sequence_runner_stop` 全 pass
- `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` 全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視なし（task_06 でまとめて実施）。
