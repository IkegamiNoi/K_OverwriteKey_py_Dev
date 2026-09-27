# task_03_stop_dialog

## 目的

アクション編集ダイアログの system の操作に「停止」を加える（暫定 28 §5）。一覧の `[stop]` 表示は task_01 で済み。
その後、ユーザーの実機目視で停止の動作を確かめる（暫定 28 §6）。
**presentation（`action_control_fields.py`）と tests_ui のみ**。

## 対象範囲

### `keyseq/presentation/dialogs/action_control_fields.py`

- `SYSTEM_OPERATIONS` に `"停止": OP_STOP` を加える（並び = 「待機」の後・「戻す」の前）。入力欄は出さない（`sync_system` の既存の分岐で、ループ・カウンター・待機の欄がすべて隠れること）。
- 結果は既存の else 経路で `{"type": "system", "op": "stop", "label": <ラベル>}` になること（新しい分岐は不要）。編集で開いたとき（`load`）は「停止」が選ばれること。

### `tests_ui/test_action_dialog_control.py`

- 既存の `test_system_wait_back_and_rewind` の書き方に合わせ、「停止」を選ぶと `{"type": "system", "op": "stop", "label": ...}` になる / 入力欄（回数・カウンター名・ミリ秒）が隠れる /
  `{"type": "system", "op": "stop"}` を編集で開くと「停止」が選ばれる、を確かめる。

## 読むファイル

- `instructions/history/28_sequence_stop_and_call.md` §5
- `keyseq/presentation/dialogs/action_control_fields.py:1-40`・`:140-230`
- `tests_ui/test_action_dialog_control.py:1-100`

## 含まない

- 一覧の表示（task_01 で済み）/ 正本・codebase_map（task_05）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests_ui` が clean
- `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_action_dialog_control -v` が全 pass
- `unittest discover -s tests` / `-s tests_ui` が全 pass・`-m tests.smoke_app` が pass
- **実機目視（ユーザー）**:
  1. 追加ダイアログの system の操作に「停止」があり、選ぶと入力欄が出ない。一覧に `[stop]` と出る
  2. 連続実行のトリガー `[A, 停止, B]` を押すと A だけ送って止まり、「次に実行」が B。もう一度押すと B を送って止まる
  3. `[A, カウンター+1, 停止, B]` の連続実行: A の後に止まり、一覧のカウンター値がその場で +1。戻すでカウンターも戻る
  4. 単発のトリガー `[A, 停止, B]` は 1 回目 A、2 回目 B（停止で押下を消費しない）
  5. 停止の行を一覧で選んでから連続実行を始めると、停止を読み飛ばして次から実行する

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 入力欄の表示・結果の形・既存の操作の並びと挙動の不変）。
- 実機目視: **本タスクで実施**（ユーザー報告をもって完了）。
