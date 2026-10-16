# task_02_capture_ime_entries_1_to_4

## 目的

取得の入口 #1〜#4（停止 / トグルキー・トリガーキー・切替キー・複数キーマップの切替キー）で、task_01 の部品を使い取得の間だけ IME を OFF にし（暫定 44 §3・§4）、`??` を記録しない扱いに揃える（§5）。
**presentation 限定（4 ファイルの配線 + tests_ui）。task_01 の部品・infrastructure・application・domain 不変・JSON スキーマ不変。入口の取得の期間・キーの解釈は変えない。**

## 対象範囲（presentation 限定・既存 4 ファイル + tests_ui 新規 1）

各入口で、**既存の開始の関数の中**で `begin_key_capture(owner, window)`、**既存の停止の関数の中**（取得中のときだけ通る部分）で `end_key_capture(owner)` を呼ぶ（`keyseq.presentation.key_capture_ime`）。`owner` は入口のオブジェクト自身（`self`）。
`??` の判定は `tk_keys.is_unresolved_capture_key` を使う（各入口で `== "??"` を書かない）。

### `keyseq/presentation/controllers/key_capture.py`（#1）

* `start()`: `begin_key_capture(self, self._app)`（停止キーとトグルキーのコントローラはそれぞれ別の owner）
* `stop()`: `self.capturing = False` の後に `end_key_capture(self)`
* `on_keypress`: 名前を作った直後、Esc の判定より前に、`is_unresolved_capture_key(key)` なら **何もせず `"break"`**（取得を続ける・案内の欄はない・エラーのダイアログを出さない）

### `keyseq/presentation/dialogs/trigger_dialog.py`（#2）

* `_start_capture()`: `begin_key_capture(self, self)` / `_stop_capture()`: 取得中のときに `end_key_capture(self)`
* `_on_capture_keypress`: `??` なら `self.hint` に `UNKNOWN_CAPTURE_KEY_HINT_TEXT` を出して `"break"`（取得を続ける）

### `keyseq/presentation/dialogs/keymap_edit_dialog.py`（#3）

* `_start_capture()` / `_stop_capture()` に begin / end（#2 と同じ）
* `_on_capture_keypress`: `key == "??"` を `is_unresolved_capture_key(key)` に置き換え（挙動は不変）

### `keyseq/presentation/dialogs/keymap_switch_batch_dialog.py`（#4）

* `_start_capture(index)` / `_stop_capture()` に begin / end（owner はダイアログ自身。取得は同時に 1 行だけ）
* `_on_capture_keypress`: `key == "??"` を `is_unresolved_capture_key(key)` に置き換え（挙動は不変）

### `tests_ui/test_capture_ime_entries.py`（新規）

`key_capture_ime._default_tracker` を偽の `get_open` / `set_open` を注入した `KeyCaptureImeTracker` に差し替えて（`patch.object`）、実機の IME に触らずに確かめる。#1〜#4 それぞれで:
1. IME ON で取得を開始 → OFF になる・取得できたで終了 → ON に戻る
2. Esc（#2〜#4 は `bind_escape_close` / `_on_escape` の経路、#1 は `on_keypress` の Esc）・ボタンでの停止・ダイアログの `destroy()` のいずれでも ON に戻る（入口ごとに少なくとも取得できた・Esc・destroy の 3 経路）
3. `??`（`SimpleNamespace(keysym="??", keycode=229, state=0)` 等）は記録せず取得が続く。#2 は案内の欄が `UNKNOWN_CAPTURE_KEY_HINT_TEXT` になる。#1 は `messagebox.showerror` を呼ばない（patch して確認）
4. #1 の停止キーの取得中にトグルキーの取得へ切り替えたとき（`app.py:697-709` の排他）、最後に ON に戻る

### 設計メモ / 制約

* 停止の関数は冒頭の「取得中でなければ return」の後で end を呼ぶ（重複した停止で end が二重に呼ばれても部品側で冪等だが、取得中でない停止で呼ぶ必要はない）
* ダイアログの `destroy()` は既に停止の関数を呼んでいる（`trigger_dialog.py:72-74`・`keymap_edit_dialog.py:134-136`・`keymap_switch_batch_dialog.py:203-205`）。部品の `<Destroy>` は保険として残る
* 既存の tests_ui はそのまま通ること（既存のテストが取得を始めると実機の API が呼ばれるが、対象はテストのプロセス自身の入力コンテキストのみ）

## 読むファイル

1. `instructions/history/44_ime_off_during_key_capture.md` §3・§4.2・§5
2. `keyseq/presentation/key_capture_ime.py`（全体・呼ぶ口）/ `keyseq/presentation/tk_keys.py:1-10`（`is_unresolved_capture_key`）
3. 編集対象（全体）: `keyseq/presentation/controllers/key_capture.py` / `dialogs/trigger_dialog.py` / `dialogs/keymap_edit_dialog.py` / `dialogs/keymap_switch_batch_dialog.py`
4. `keyseq/presentation/dialogs/escape_close.py`（Esc の経路）/ `keyseq/presentation/app.py:690-712`（#1 の排他）
5. テストの手本: `tests_ui/test_prohibited_assign_keys_ui.py:1-60,190-215`（ダイアログの作り方・`??` の案内のテスト）

## 含まない

* 入口 #5〜#8（hotkey・key_hold・キーボードUI の編集・画面の枠の編集の窓）の配線と `??` の統一・実機目視（task_03）
* 統合確認（task_04）/ 正本・`codebase_map.md`（task_05）
* task_01 の部品・`own_ime_status.py`・`ime_control.py` の変更 / 取得中のフック再開（idea_48）

## 確認

* `..\..\..\.venv\Scripts\python.exe -m compileall -q keyseq main.py tests tests_ui` が clean
* `..\..\..\.venv\Scripts\python.exe -m unittest tests_ui.test_capture_ime_entries -v` が全 pass（上記 1〜4）
* 既存の `tests`（`unittest discover -s tests`）・`tests_ui`（`unittest discover -s tests_ui`・同時に 1 本だけ）・`-m tests.smoke_app` が全 pass

## 完了条件

- 上記確認 pass・**reviewer 採用**。
- 実機目視は task_03 でまとめて実施（本タスクでは行わない）。
