# task_07_call_display_and_interval

## 目的

一覧で呼び出しを `[call] <キー>（<呼び出し先のラベル>）` と表示し（参照先なしも示す）、「間隔(ms)」の欄を連続実行 OFF でも編集できるようにする（暫定 29 §6・§2-2・§2-7）。
**presentation（`controllers/action_list_rendering.py`・`controllers/trigger_panel/trigger_panel_controller.py`・`views/full_view/sequence_box.py`）と tests_ui のみ**。
表示の形は task_01 の `format_control_value(resolve_call=...)` が作る（ここでは解決関数を配線するだけ）。

> 注意: 仕様書の `f5` は例示のキー。実装は実際のキーを使う（固定の文字列を埋め込まない）。

## 対象範囲

### 一覧の表示（`action_list_rendering.py`・`trigger_panel_controller.py`）

- `build_action_rows(..., resolve_call=None)`・`format_next_action_summary(..., resolve_call=None)` を追加し、`format_action_list_item` へそのまま渡す。
- `trigger_panel_controller.py` の呼び出し 2 箇所（一覧の行・「次に実行」の要約）で `resolve_call` を渡す: `target` を `normalize_key_name` し、
  **アクティブなトリガー一覧**（`domain/keymap_triggers.py` の口・`"triggers"` の直値を書かない）で一致するトリガーがあれば `(キー, そのトリガーのラベル〔trim・空なら ""〕)`、無ければ `(キー, None)` を返す関数。
- 呼び出し以外の行の表示は変えない。

### 間隔の欄（`trigger_panel_controller.py`・`sequence_box.py`）

- 「間隔(ms)」の入力欄を、**連続実行の ON / OFF に関係なく編集可能**にする（トリガーを選んでいないときの無効化は既存どおり）。連続実行のチェックの切替などで欄を無効にしている箇所をすべて直す。
- 連続実行 OFF のトリガーでも、欄の値を従来どおりそのトリガーの `run_to_end_delay_ms` へ保存する（保存の経路が連続実行 ON のときだけに限られていれば外す）。
- 見出しを `間隔(ms)` から **`間隔(ms)・呼び出し時も使用`** に変える（`sequence_box.py`）。

### テスト（tests_ui）

- 一覧の表示（既存の `tests_ui/test_action_list_rendering.py` の書き方）: 呼び出し先にラベルあり → `[call] <キー>（ラベル）` / ラベル空 → `[call] <キー>` / 参照先なし → `[call] <キー>（参照先なし）` /
  行のラベルが後ろに付く / 「次に実行」の要約も同じ / 呼び出し以外の行は不変。キーは例示以外（例 `f7`・`z9`）も使う。
- 間隔の欄: 連続実行 OFF のトリガーを選んでも欄が `normal` / 値を変えると `run_to_end_delay_ms` に保存される / トリガー未選択では従来どおり無効 / 見出しの文言。

## 読むファイル

- `instructions/history/29_sequence_call.md` §6
- `keyseq/presentation/controllers/action_list_rendering.py`（全体・編集対象）
- `keyseq/presentation/controllers/trigger_panel/trigger_panel_controller.py:180-200`・`:255-290`・`:335-370`（一覧の組み立て・欄の有効 / 無効・間隔の保存）
- `keyseq/presentation/views/full_view/sequence_box.py:40-60`
- `keyseq/domain/keymap_triggers.py`（アクティブなトリガー一覧の口）/ `keyseq/domain/sequence_control.py` の `format_control_value` の `resolve_call` の仕様
- `tests_ui/test_action_list_rendering.py:1-40`（書き方の手本）/ 間隔の欄を扱う既存の UI テスト（`grep -rn "run_to_end_delay" tests_ui` で見つかるもの 1 つ）

## 含まない

- 改名時の参照の書き換え・実機目視（task_08）/ 正本（task_10）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests_ui` が clean
- 追加・変更したテスト・`discover -s tests` / `-s tests_ui` / `tests.smoke_app` が全 pass・`grep -rn '"triggers"' keyseq/presentation` が 0 件

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 解決関数の配線〔同じトリガー一覧・参照先なし〕/ 固定のキーを埋め込んでいない / 欄が OFF でも編集・保存できる / 既存の表示・保存の不変 / 先取りなし）。
- 実機目視: task_08 でまとめて実施。
