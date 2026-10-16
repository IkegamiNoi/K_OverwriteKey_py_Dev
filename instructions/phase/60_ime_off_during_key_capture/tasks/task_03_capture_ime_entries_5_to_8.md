# task_03_capture_ime_entries_5_to_8

## 目的

取得の入口 #5〜#8（アクションの hotkey 記録・key_hold の「1 キーを記録」・キーボードUI の編集・画面の枠の編集の窓）で、task_01 の部品を使い取得の間だけ IME を OFF にし（暫定 44 §3・§4）、`??` を記録しない扱いに揃える（§5）。実装後にユーザーの実機目視で 8 入口をまとめて確かめる（§8-6）。
**presentation 限定（4 ファイルの配線 + tests_ui）。task_01 の部品・infrastructure・application・domain 不変・JSON スキーマ不変。入口の取得の期間・キーの解釈は変えない。**

## 対象範囲（presentation 限定・既存 4 ファイル + tests_ui 既存 1 への追加）

task_02 と同じく、既存の開始の関数で `begin_key_capture(owner, window)`、既存の停止の関数の取得中のときだけ通る部分で `end_key_capture(owner)`（`keyseq.presentation.key_capture_ime`）。`??` の判定は `tk_keys.is_unresolved_capture_key`。

### `keyseq/presentation/dialogs/action_dialog.py`（#5 hotkey）

* `_start_recording()`: `begin_key_capture(self, self)`（owner = ダイアログ）
* `_stop_recording()`: `self._recording = False` の後に `end_key_capture(self)`（先頭の `self.key_hold_fields.stop_recording()` は既存のまま）
* `_on_key_press`: 名前を作った直後に `??` なら何もせず `"break"`（記録を続ける・案内は出さない）

### `keyseq/presentation/dialogs/action_key_hold_fields.py`（#6 key_hold）

* `start_recording()`: 記録を始める分岐で `begin_key_capture(self, self.dialog)`（owner = この欄のオブジェクト。#5 と別の owner）
* `stop_recording()`: `self.recording = False` の後に `end_key_capture(self)`
* `_on_key_press`: Esc の判定の後、名前を作り `??` なら `self.key_hint` に `UNKNOWN_CAPTURE_KEY_HINT_TEXT` を出して `"break"`（記録を続ける）

### `keyseq/presentation/keyboard_window.py`（#7 キーボードUI の編集）

* `_begin_edit()`: **編集中でないときだけ**（既存の `if not self._editing_source_key` の分岐の中）`begin_key_capture(self, self)`。編集中の別の元キーのクリックでは呼ばない（暫定 44 §4.2 開始の冪等）
* `_cancel_edit()`: `self._editing_source_key = None` の後に `end_key_capture(self)`
* `_on_key_press`: 名前を作った直後に `??` なら `"break"`（編集を続ける・案内は出さない）
* 窓が `_handle_close` を通らずに破棄されたときは部品の `<Destroy>` が戻す（変更不要）

### `keyseq/presentation/dialogs/grid_editor_window.py`（#8 画面の枠の編集の窓）

* `__init__`: `super().__init__(parent)` の後（`grab_modal` より前）に `begin_key_capture(self, self)`。終了は部品の `<Destroy>` のみ（Esc・決定とも destroy に行き着く）
* `on_key`: 名前を作った直後に `??` なら `"break"`（何も入れない）

### `tests_ui/test_capture_ime_entries.py`（task_02 で作成済み・追加）

task_02 と同じく偽の tracker（`patch.object(key_capture_ime, "_default_tracker", ...)`）で:
1. #5: 記録の開始 → OFF・非修飾キーで確定 → ON / Esc（`acquire_focus` してから `event_generate("<Escape>")`）・ボタン・種類の切替（`_sync_hotkey_controls(False)`）・`destroy()` で ON に戻る / `??` は記録せず続ける
2. #6: 記録の開始 → OFF・取得 → ON / Esc・`sync_target()`（対象の切替）・`destroy()` で ON / `??` は記録せず案内が `UNKNOWN_CAPTURE_KEY_HINT_TEXT`
3. #5 と #6 の重なり（#6 の記録中に #5 の `_stop_recording` が #6 を止める経路）で最後に ON に戻る
4. #7: 枠のクリック（`_begin_edit`）→ OFF・取得 → ON / Esc・右クリック（`_on_canvas_right_click`）・`_handle_close`・`destroy()` で ON / 編集中の別の元キーの `_begin_edit` で `get_open` を呼ばない（偽の get の呼び出し回数で確認）/ `??` で編集が続く
5. #8: 窓を開く → OFF・`destroy()`（Esc の `on_escape` で閉じる経路を含む）→ ON / `??` で枠・操作キーに何も入らない

### 設計メモ / 制約

* 部品の `<Destroy>` は `event.widget is window` で絞るため、#6 の window に `self.dialog` を渡しても子の破棄で終わらない
* 既存の `tests_ui`（`test_action_dialog_key_hold.py`・`test_keyboard_window_left_right.py`・`test_grid_editor_window.py` 等）はそのまま通ること
* テストの窓の作り方は既存のテストを手本にする（読むファイル 5）

## 読むファイル

1. `instructions/history/44_ime_off_during_key_capture.md` §3・§4.2・§5
2. `keyseq/presentation/key_capture_ime.py`（全体）/ `keyseq/presentation/tk_keys.py:1-10`
3. 編集対象（全体）: `keyseq/presentation/dialogs/action_dialog.py` / `dialogs/action_key_hold_fields.py` / `keyboard_window.py` / `dialogs/grid_editor_window.py`
4. `tests_ui/test_capture_ime_entries.py`（全体・追加先）
5. テストの手本（窓の作り方の部分だけ）: `tests_ui/test_action_dialog_key_hold.py:1-60,120-140` / `tests_ui/test_keyboard_window_left_right.py:1-60` / `tests_ui/test_grid_editor_window.py:1-60`

## 含まない

* 入口 #1〜#4（task_02 で完了）/ 統合確認（task_04）/ 正本・`codebase_map.md`（task_05）
* task_01 の部品・`own_ime_status.py`・`ime_control.py` の変更 / 取得中のフック再開（idea_48）/ #7 の F キーの名前（idea_47）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_capture_ime_entries -v` が全 pass（task_02 分 + 上記 1〜5）
* 既存の `tests`（`unittest discover -s tests`）・`tests_ui`（`unittest discover -s tests_ui`・同時に 1 本だけ）・`-m tests.smoke_app` が全 pass
* **ユーザーの実機目視**（IME を ON にしてから、8 入口それぞれで取得を始める）:
  a. 押したキー（例: `a`・`1`）がそのまま取得できる
  b. 取得の終了（取得できた・Esc・閉じる）の後、IME が ON に戻っている（元が OFF なら OFF のまま）
  c. #7 の編集中に別の元キーをクリックしても取得できる
  d. 取得中に手で IME を ON にすると、以降の打鍵は取得されない（Esc → 取り直しで取れる）

## 完了条件

- 上記確認 pass・**reviewer 採用**・**ユーザーの実機目視 OK**。
