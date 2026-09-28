# task_06_call_dialog

## 目的

アクション編集ダイアログの system の操作に「呼び出し」を加え、呼び出し先を同じトリガー一覧から選び、OK 時に循環などを拒否する（暫定 29 §6・§2-8）。
**presentation（`dialogs/action_control_fields.py`・`dialogs/action_dialog.py`・`controllers/trigger_panel/action_edit.py`）と tests_ui のみ**。判定は task_01 の `domain/call_graph.edit_call_violation` を使う。

## 対象範囲

### `keyseq/presentation/dialogs/action_control_fields.py`

- `SYSTEM_OPERATIONS` に `"呼び出し": OP_CALL` を加える（並び = 「停止」の後・「戻す」の前）。
- 呼び出しを選んだときだけ「呼び出し先」の**読み取り専用ドロップダウン**を出す（他の op の欄は隠す・既存の `sync_system` の分岐に足す）。
  - 候補はコンストラクタで受ける `call_candidates: list[tuple[str, str]]`（`(正規化済みキー, ラベル)`・呼び出し元自身は渡す側で除く）。表示は `キー: ラベル`（ラベルが空ならキーだけ）。グレー表示のトリガーも候補に含める。
  - 編集で開いた行の `target` が候補に無いときは、先頭に `f5（参照先なし）` を加えて選んだ状態で開く。
- 結果（`_build_system_result`）: 呼び出しなら、選んだ候補の**キー**で `{"type": "system", "op": "call", "target": キー, "label": ラベル}`。
  未選択・参照先なしの項目を選んだまま → 「呼び出し先を選んでください」/「呼び出し先のトリガーがありません（f5）」を出して None（閉じない）。
  コンストラクタで受ける `call_check: Callable[[str], str | None] | None` があれば呼び、文言が返れば出して None（閉じない）。
- `load`: 呼び出しの行なら「呼び出し」と呼び出し先を選ぶ。

### `keyseq/presentation/dialogs/action_dialog.py`

- コンストラクタに `call_candidates: list[tuple[str, str]] | None = None`・`call_check: Callable[[str], str | None] | None = None` を追加し、`ActionControlFields` へ渡す。

### `keyseq/presentation/controllers/trigger_panel/action_edit.py`

- 追加・編集の両方で、**アクティブなトリガー一覧**（`domain/keymap_triggers.py` の口で取得する。presentation に `"triggers"` の直値を書かない）から
  呼び出し元（今選んでいるトリガー）以外の `(正規化済みキー, ラベル)` を一覧順で作って `call_candidates` に渡す。
- `call_check = lambda target: edit_call_violation(呼び出し元のキー, target, find_trigger)`（`find_trigger` = 同じトリガー一覧で正規化済みキーからトリガーを引く関数）を渡す。
- それ以外の追加・編集の流れ（単独登録の制限・末尾に追加・位置の調整）は変えない。

### テスト（`tests_ui/test_action_dialog_control.py`）

1. 「呼び出し」を選ぶと呼び出し先のドロップダウンだけが出る（回数・カウンター名・ミリ秒は隠れる）/ 候補の表示 `キー: ラベル`・ラベル空はキーだけ
2. 選んで OK → `{"type": "system", "op": "call", "target": "f5", "label": ...}` / 未選択で OK → 閉じない
3. `call_check` が文言を返すと閉じない（偽の関数で）/ None なら閉じる
4. 編集で開く: 候補にある target → 選ばれる / 候補に無い target → 先頭に `f5（参照先なし）` が選ばれた状態で、そのまま OK すると閉じない
5. 既存の system の操作（停止・戻す等）の並びと結果が不変
- `action_edit.py` の配線は、既存の UI テスト（`tests_ui/test_trigger_panel_controller_action_edit.py` 等）の書き方で、候補に自分自身が入らないこと・`call_check` が `edit_call_violation` の結果を返すことを 1 件ずつ確かめる。

## 読むファイル

- `instructions/history/29_sequence_call.md` §6
- `keyseq/presentation/dialogs/action_control_fields.py`（全体・編集対象）/ `keyseq/presentation/dialogs/action_dialog.py:1-60`・`:110-170`
- `keyseq/presentation/controllers/trigger_panel/action_edit.py`（全体・編集対象）
- `keyseq/domain/call_graph.py`（`edit_call_violation`）/ `keyseq/domain/keymap_triggers.py`（アクティブなトリガー一覧の口）
- `tests_ui/test_action_dialog_control.py:1-60`・`tests_ui/test_trigger_panel_controller_action_edit.py:1-60`（書き方の手本）

## 含まない

- 一覧の表示・間隔の欄（task_07）/ 改名時の参照の書き換え（task_08）/ 正本（task_10）

## 確認

- `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq tests_ui` が clean
- `unittest tests_ui.test_action_dialog_control tests_ui.test_trigger_panel_controller_action_edit -v` / `discover -s tests` / `-s tests_ui` / `tests.smoke_app` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**（観点: 候補の作り方〔自分を除く・一覧順・グレーも含む・`"triggers"` 直値なし〕/ 参照先なしの初期値 / OK 時の拒否で閉じない / 既存の操作の不変 / 先取りなし）。
- 実機目視: task_08 でまとめて実施。
