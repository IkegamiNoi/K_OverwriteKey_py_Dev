# task_03_capture_entries

## 目的

暫定 49 v0.5 §3-6・§3-7 の入口側。取得の 8 入口が `begin_key_capture(owner, window, on_hook_key)` で受け取りの関数を渡し、取得用のフック（task_02）から届いた名前を、**Tk の KeyPress から作った名前と同じ後続の処理**で記録する。取得の対象を変える入口は `begin` を通して世代を進める（§3-6）。
**presentation 限定（8 入口のファイル）・`key_capture_ime.py` / `key_capture_hook.py` / domain / application / infrastructure は不変・スキーマ不変。既存の Tk の道筋の挙動は不変。**

## 対象範囲（presentation 限定・8 入口）

各入口で、KeyPress の処理を「Tk のイベントから名前を作る部分（`normalize_tk_key_event` 等・`??` の判定を含む）」と「名前を受けて記録する部分（それより後ろ全部: Esc・修飾キー単独・禁止のキー・重複・案内・値の設定・取得の終了・検査）」に分け、KeyPress の処理は前者 → 後者を呼ぶ。後者を `on_hook_key` として `begin_key_capture` に渡す。受け取りの関数は、**取得中でなければ何もしない**（KeyPress の処理の先頭の判定と同じ）。名前の作り方・判定・文言は変えない。

1. #1 `presentation/controllers/key_capture.py`（停止 / トグルキー・owner の窓 = ルート）: `start()` の `begin_key_capture(self, self._app, …)`。`on_keypress` の `??` の判定より後ろを分ける
2. #2 `presentation/dialogs/trigger_dialog.py`: `_start_capture` / `_on_capture_keypress`
3. #3 `presentation/dialogs/keymap_edit_dialog.py`: `_start_capture` / `_on_capture_keypress`
4. #4 `presentation/dialogs/keymap_switch_batch_dialog.py`: `_start_capture` / `_on_capture_keypress`（記録先は今の `_capture_index`）
5. #5 `presentation/dialogs/action_dialog.py`（hotkey の記録）: `_start_recording` / `_on_key_press`。届いた名前は修飾キーでない（フック側で除外済み）ので、非修飾キーとして今の `_mods_down` と組み合わせて確定する（`_last_nonmod` を設定 → `_update_hotkey_preview(finalize=True)` → `_stop_recording()` の今の流れ）
6. #6 `presentation/dialogs/action_key_hold_fields.py`（key_hold の「1 キーを記録」・owner の窓 = ダイアログ）: `start_recording` / `_on_key_press`。届いた名前をそのまま `key_var` に入れて記録を止める（Escape の判定は keysym なので受け取り側には不要）
7. #7 `presentation/keyboard_window.py`（キーボードUI の編集）: `_begin_edit` は**元キーのクリックのたびに** `begin_key_capture(self, self, …)` を呼ぶ（今は編集の始めの 1 回だけ。フックの一時停止は今どおり始めの 1 回だけ）。`_on_key_press` の `??` の判定より後ろを分ける
8. #8 `presentation/dialogs/grid_editor_window.py`（画面の枠の編集の窓・取得は窓を閉じるまで続く）: `begin_key_capture(self, self, …)`（`__init__`）。`on_key` の `??` の判定より後ろを分ける。**記録先（枠の選択 `self.selected`・パネルの `op_selected` / `sub_selected`）が変わるたびに `begin_key_capture(self, self, 同じ関数)` を呼んで世代を進める**（取得中の再度の開始は IME に触らない）

### テスト（tests_ui）

- 新規 `tests_ui/test_capture_hook_entries.py`（`tests_ui/test_capture_ime_entries.py` の作りを手本に、tracker を差し替えて App を作り、setUp で `tracker.set_capture_hook(None)` にして本物のフックを入れない）: 8 入口それぞれで取得を始め、tracker に記録された受け取りの関数を `muhenkan` で呼ぶと、KeyPress で同じ名前が来たときと同じ記録になる（値・取得の終了）。取得中でないときは何もしない。#5 は修飾キーを押したまま（`_mods_down` に ctrl）で `ctrl+muhenkan`。#7 は別の元キーのクリックで世代が進む。#8 は選択の変更で世代が進む
- 既存の tests_ui は変えない（挙動が不変であることの確認）

## 読むファイル

1. `instructions/history/49_capture_jis_special_keys.md`（§3-6・§3-7）
2. `keyseq/presentation/key_capture_ime.py`（`begin_key_capture` の引数・`_owners` の記録）
3. 8 入口: `controllers/key_capture.py:55-175`・`dialogs/trigger_dialog.py:85-125`・`dialogs/keymap_edit_dialog.py:150-190`・`dialogs/keymap_switch_batch_dialog.py:210-262`・`dialogs/action_dialog.py:340-400`・`dialogs/action_key_hold_fields.py:160-202`・`keyboard_window.py:470-525`・`dialogs/grid_editor_window.py:55-80`・`:170-260`（選択の変更）と `GridEditorPanel` の `op_selected` / `sub_selected` を変える箇所
4. `tests_ui/test_capture_ime_entries.py`（手本）

## 含まない

- `key_capture_ime.py` / `key_capture_hook.py` の変更（task_02 で完了）
- 名前の作り方の統一（idea_45）・取得中のフック再開の穴（idea_48）
- 正本の更新・実機目視（task_04）

## 確認

- `compileall` clean / tests 全 pass（1791）/ tests_ui 全 pass（1122 + 新規）/ smoke pass
- 差分の直読み: 各入口の KeyPress の処理の挙動が不変（分けただけ）/ 受け取りの関数が取得中でなければ何もしない / #7・#8 の begin の追加が取得中の再度の開始（IME に触らない）になっている

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視: task_04 でまとめて実施。
