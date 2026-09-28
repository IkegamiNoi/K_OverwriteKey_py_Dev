# task_09d_discard_dialog

## 目的

暫定 29 v0.6 §4.7 の**presentation 側**を実装する: 一時停止中のものを捨てる前の警告のダイアログと、その配線（連続実行の開始・戻す / 先頭へ・キーマップの切替 / 削除）。
application 側の口（一時停止中のものの一覧・確認して捨てる・確認中の印・`can_switch_keymap`）は task_09c で実装済みの前提。

## 対象範囲

1. **警告のダイアログ**: OK / キャンセル。**OK に初期フォーカス**（Enter で OK・Esc でキャンセル）。文言「一時停止中の実行を破棄します。」+ 捨てるトリガーのキーの一覧 +「よろしいですか？」。
   最前面に出す（フォーカスが取れない場合は受容）。**`suspend_hook_for_dialog` を使わない**（停止操作に当たり一時停止中のものを打ち切るため）。
   `tkinter.messagebox.askokcancel(..., default="ok")` 等の既存の標準ダイアログで足りればそれを使う（新しい部品を作らない）。置き場所は既存の確認ダイアログの慣習に合わせる。
2. **runner への注入**（`keyseq/presentation/app.py`）: task_09c の確認の callback に 1 のダイアログを渡す。
3. **キーマップの切替**（`keymap_panel_controller.py` `activate_keymap_by_id`）: `can_switch_keymap` が許しても一時停止中のものがあれば、task_09c の「確認して捨てる」を通し、OK のときだけ切り替える
   （同じキーマップへの切替〔変化なし〕は確認しない）。キャンセル・照合でやめた場合は切り替えず一覧の表示を戻す（`refresh_keymap_list_ui`）。
   連続実行が実行中のときの拒否（`show_keymap_switch_blocked`）は既存どおり。
4. **アクティブのキーマップの削除**（同 `delete` の経路・`:277-287` 付近）: 一時停止中のものがあれば、**既存の削除の確認を先に**出し、「はい」の後に 1 の警告を出す。**両方 OK のときだけ**捨てて削除する。
5. **確認中の切替キーの無視**: 確認中の印が立っている間は、キーマップの切替キー（`action_executor` の `SelectKeymapAction` の経路・`activate_keymap_by_id`）を無視する（警告の入れ子を作らない）。
6. **テスト**（`tests_ui/`）: ダイアログの文言・キー一覧・既定ボタン（messagebox を差し替えて呼び出し引数を確認する程度でよい）/ 切替で一時停止中があれば確認・OK で切替・キャンセルで切り替わらない /
   削除の 2 回の確認の両方 OK で削除・どちらかのキャンセルで何も変わらない / 確認中の切替キーの無視 / ダイアログでフックが止まらない（`suspend_hook_for_dialog` を呼ばない）。

## 読むファイル

- `instructions/history/29_sequence_call.md` **§4.7**・§8-4b
- task_09c で追加された runner の口（`keyseq/application/sequence_runner/` の該当モジュール）
- `keyseq/presentation/app.py`（runner の生成・`on_select_keymap`・`can_switch_keymap` の配線 `:120-140` 付近）
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py`（`:260-330`・`activate_keymap_by_id`）
- `keyseq/application/action_executor.py:183-205`（`SelectKeymapAction`）/ `keyseq/presentation/controllers/hook_controller.py:44-70`（ダイアログ用のフックの一時停止＝使わない）
- 関係する `tests_ui/test_keymap_*.py`

## 含まない

- application 側の判定・一時停止・照合（task_09c）/ 正本（task_10）
