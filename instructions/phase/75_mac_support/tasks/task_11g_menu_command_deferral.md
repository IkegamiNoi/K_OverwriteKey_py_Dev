# task_11g_menu_command_deferral

## 目的

aqua では、メニューバーの項目のうちモーダルのダイアログを開き得る処理を `after(0)` で遅らせ、App の待ち行列で 1 つずつ実行し、終了が確定したら待ち行列を捨てる（暫定 57 §5.4「メニューの処理」・v0.25・Codex 敵対的レビュー 2 回を受けた改訂はユーザー判断 2026-11-22）。

- 不具合: Mac でメニューの処理の中からモーダルのダイアログ（`wait_window`）を開くと、ボタンを押しても待ちが戻らず、アプリが応答しなくなる。
  - 実測（2026-11-22・macOS 27.2 / Tk 9.1）: 「設定 → 言語」の切り替えで、確認ダイアログの `choice_dialog.py:62` の `wait_window` から戻らない。開発実行と `.app` の両方で起きる。
  - `set_ui_language` を `after(0)` で遅らせると、確認 → 再起動まで進むことも実測で確かめた。
- task_13b の実機確認（3. 再起動）の前提になる。
- presentation 限定（`views/menu_command_queue.py`〔新規〕・`views/menu_bar.py`・`controllers/layout_controller.py`・`app.py`）。domain / application / infrastructure・設定の JSON のスキーマは変えない。Windows の動作は変えない（即時に呼ぶまま）。

## 対象範囲（presentation 限定・テスト）

### `keyseq/presentation/views/menu_command_queue.py`（新規・menu_bar 専用）

- `MenuCommandQueue(widget)` を置く（aqua の判定は `tk_platform.is_aqua`・モーダルの判定は `modal.is_modal_active`）。
  - `defer(command) -> Callable[[], None]`: aqua でないときは `command` をそのまま返す（同じオブジェクト）。aqua のときは、呼ばれると `command` を待ち行列の末尾に足して、実行の予約（`widget.after(0, ...)`）を 1 つだけ持つ関数を返す。
  - 実行: 実行中でなければ先頭を 1 つ取り出し、実行中の印を立てて呼ぶ。戻ったら（例外でも）印を下ろし、残りがあれば次の予約をする。実行中に予約が来ても次を始めない（前の処理のモーダルの待ちの間に後の処理が走らない）。
  - **モーダルの待ち**: 先頭を取り出す前に `keyseq.presentation.modal.is_modal_active()` を見て、True なら始めずに `after(100, ...)` で見直す（どの経路で開いたモーダル・メッセージの窓の間もメニューの処理を始めない。最小化で grab を外している間〔`modal.py:103-136`〕も True のまま・§5.4）。
  - `cancel_all()`: 待ち行列を空にし、残っている予約を `after_cancel` する（`TclError` は無視）。実行中の処理は止めない。
  - 例外は握りつぶさない。ログに残して、次の処理へ進む（`logging.getLogger(__name__).exception`）。

### `keyseq/presentation/app.py`

- `build_menu_bar` を呼ぶ前（`app.py:503` より前）に `self.menu_commands = MenuCommandQueue(self)` を作る。`app.py:578` の作り直しでは作り直さない（同じ待ち行列を使う）。
- `on_close`:
  - 実行中に再び呼ばれたら何もしない（実行中の印を App に持つ。終了をキャンセルした経路では印を下ろす）。
  - 窓を破棄する直前（今の `self.destroy()` の直前・`app.py:962` 付近の `finally` の中）で `self.menu_commands.cancel_all()` を呼ぶ。
  - 終了をキャンセルした経路（`confirm_save_if_dirty` が False で戻る）では呼ばない（待ち行列はそのまま続く）。

### `keyseq/presentation/views/menu_bar.py`

- `app.menu_commands.defer(...)` で包むもの:
  - すべての `add_command`（ファイル 10・設定 7・ヘルプ 5 の 22 項目。「終了」〔`app.on_close`〕を含む）
  - 言語のラジオボタン（`set_ui_language`）
- 物理キー名のチェックボタン: command を「表示と反映は即時 + 保存だけ遅らせる」関数にする。
  - 押した時点の `app.keymap_set_path` を覚え、`app.layout.apply_keyboard_show_physical_key_labels()` を即時に呼ぶ。
  - 続けて `app.menu_commands.defer(保存)()` を呼ぶ。保存は、そのときの `app.keymap_set_path` が覚えた値と同じときだけ `app.layout.persist_keyboard_layout_selection()` を呼ぶ。
  - Windows では `defer` がそのまま返すので、今と同じ順で即時に保存される。
- フォントの大きさのラジオボタンは今どおり即時（包まない）。
- ラジオボタン・チェックボタンの `variable`・ラベル・accelerator・並び順は変えない。

### `keyseq/presentation/controllers/layout_controller.py`

- `toggle_keyboard_show_physical_key_labels`（`:301-304`）を 2 つに分ける: `apply_keyboard_show_physical_key_labels()`（data への反映と `refresh_keyboard_window`・**未保存の印を立てる**〔`dirty_tracker.set_dirty(True)`〕）と、今の `persist_keyboard_layout_selection()`（保存に成功すれば今どおり `save_keymap_set` が印を下ろす）。`toggle_...` は「apply → persist」として残す（ほかに呼び出し元は無いが、名前を消さない）。

### テスト

- `tests/test_menu_command_queue.py`（新規・widget はモック。`tk.call` の戻り値で aqua を切り替える〔`tests/test_tk_platform.py` の形〕・`after` は呼ばれた関数を記録して手で流す）:
  - aqua でない: `defer` が同じオブジェクトを返す。
  - aqua: 返った関数を呼んでも `command` は呼ばれず、`after(0, ...)` が予約される。流すと `command` が 1 回呼ばれる。
  - 2 つ積んで流すと順に呼ばれる。1 つ目の実行中（その中でもう一度予約を流す）に 2 つ目が始まらない。
  - 1 つ目が例外でも 2 つ目は呼ばれ、例外はログに残る。
  - `cancel_all`: 積んだ処理が呼ばれず、予約が `after_cancel` される。`TclError` で止まらない。
  - モーダルの待ち: `is_modal_active()` が True の間は呼ばれず `after(100, ...)` で見直し、False になってから呼ばれる（patch で切り替える）。`cancel_all` は見直しの予約も取り消す。
- `tests/test_menu_bar_shortcut.py` か新しいテスト（実際の Tk で `build_menu_bar`）:
  - `add_command` の全項目と言語のラジオボタンの command が `defer` を通り、フォントのラジオボタンは通らない（項目はメニューから数える・数で固定しない）。
  - 物理キー名のチェックボタン: aqua の偽装で、invoke すると apply は即時・保存は予約。予約を流す前に `keymap_set_path` を変えると保存されない。
  - 偽の app を使う既存テストに `menu_commands` が無くて影響しないかを確かめる（要るなら偽の app に足す）。
- `apply_keyboard_show_physical_key_labels` が未保存の印を立てる。
- `on_close` のテスト（既存の終了のテストに倣う）: 確定で `cancel_all` が destroy の前に呼ばれる・`confirm_save_if_dirty` が False のとき呼ばれない・実行中の再呼び出しは何もしない。
- tests_ui のメニューの項目を `invoke` するテスト: aqua では処理が予約になるので、`invoke` の直後に `self.app.update()` を挟んで予約を流してから検証する（`update_idletasks()` では `after(0)` が流れない）。Windows ではそのままでも通る。
  - 対象: `test_help_window.py:147,150,166,169`（147・150 は今の `update_idletasks()` を `update()` に）・`test_ui_language.py:150`・`test_keymap_set_history_flow.py:113`・`test_quarantine_manage_flow.py:135`・`test_reference_cleanup_flow.py:334` と `test_orphan_sweep_flow.py:256`（helper の `invoke` の直後・`return` の前）。
  - `patch` の `with` の中で `invoke` しているものは、`update()` も必ず `with` の内側に置く（外に置くと patch が外れた後に本物が走る）。
  - 対象外（メニューの項目ではなくボタン・チェックボタンの `invoke`）: `test_keymap_set_history_flow.py:315`・`test_quarantine_manage_flow.py:300` 以降・`test_choice_dialog.py:163`・`test_select_before_run_ui.py:94` 以降・`test_grid_editor_window.py`・`test_action_dialog_*.py`・`test_dialog_teardown_flows.py:126`・`test_nested_modal_grab.py:501`・`test_app_ui_flows.py:2052`。

## 設計メモ / 制約

- `after(0)` を選ぶ理由: メニューの処理（macOS のメニューバーから呼ばれる処理）をいったん戻し、ふだんのイベントの処理の中で本体を呼ぶため。`after_idle` ではなく `after(0)` にするのは実測で直った形と揃えるため。
- 遅らせるのは aqua だけ（ユーザー判断 2026-11-22・推奨どおり）。Windows で遅らせると、メニューの処理の直後の状態を見るテスト・挙動が変わる。
- ショートカットとメインの窓のボタンは NSMenu の処理を通らないので、止まる不具合は無い。それらが開いたモーダルの間にメニューの処理が割り込む件は、待ち行列の grab の待ちで防ぐ（経路ごとに待ち行列へ入れない・ユーザー判断 2026-11-22）。
- バージョン情報は閉じるのを待たない窓だが `grab_modal`（`version_dialog.py:31`）で開くので `is_modal_active()` が True になり、開いている間はメニューの処理が始まらない。
- メッセージの窓は task_11f の入口（`message_box.py`）が `enter_message_box` / `leave_message_box` で数えるので、`is_modal_active()` で同じく待つ。
- ヘルプの「コピー」の右クリックメニュー（`help_tab_view.py:95`）はダイアログを開かないので対象外。

## 読むファイル

- `instructions/history/57_mac_support.md` §5.4 の「メニューの処理」の行
- `keyseq/presentation/tk_platform.py`（全体）・`keyseq/presentation/views/menu_bar.py`（全体）・`keyseq/presentation/app.py:495-505,570-580,911-962`（menu の組み立てと `on_close`）・`keyseq/presentation/controllers/layout_controller.py:288-305`
- `tests/test_tk_platform.py`（全体・モックの手本）・`tests/test_menu_bar_shortcut.py`（全体）
- `tests_ui/test_reference_cleanup_flow.py:315-345`・`tests_ui/test_orphan_sweep_flow.py:245-270`（メニューの invoke の手本）。ほかの対象（`test_help_window`・`test_ui_language`・`test_quarantine_manage_flow`・`test_keymap_set_history_flow`）は上の行の周りだけ

## 含まない

- 再起動（`MacAppIdentity.relaunch`・`open -n` の要否）と `.app` の実機確認 → task_13b
- `.app` でだけ起きる、保存パネルが置き換えの確認の Cancel の後に固まる件 → task_13b で調査
- メニュー以外の経路（ボタン・ショートカット）から開くダイアログの変更
- macOS のアプリのメニュー（keyseq → 終了 等）の追加

## 確認

- 標準検証（Mac・`../../../.venv/bin/python`・tests_ui は通しで流さない）:
  - `-m compileall -q keyseq main.py tests tests_ui` が clean
  - `-m unittest discover -s tests` が失敗 0・エラー 0（task_13b の後の件数から減らない）
  - `-m tests.smoke_app` が pass
  - tests_ui の `test_reference_cleanup_flow`・`test_orphan_sweep_flow`・`test_quarantine_manage_flow`・`test_keymap_set_history_flow`・`test_ui_language`・`test_help_window` を 1 本ずつ単独で流して失敗 0
- Windows の検証（`test_tk_platform`・`test_menu_bar_shortcut`・上の tests_ui 4 本）は、次の Windows の作業でまとめて行う（残課題として完了報告に書く）。

## 完了条件

- 上記の確認が pass・**reviewer 採用**。
- Mac 実機目視（ユーザー・開発実行）:
  1. メニューから言語を切り替え、確認で「今すぐ再起動」を押すと、keyseq が 1 つだけ起き直る（ラジオボタンの変数が即時に更新されることの確認も兼ねる）。
  2. メニューの「別名保存...」「読込...」「プリセット編集」「バージョン情報」を開いて、閉じられる（ボタンが効き、待ちが戻る）。
  3. 言語・フォントの大きさのメニューのチェックの印が、選んだ項目に付く。
  4. メニューの「終了」を選ぶと閉じる（未保存があれば確認が出て、ボタンが効く）。
  5. 構成フォルダの外に保存した構成セットを開き、メニューの「物理キー名」を切り替えると、表示がすぐ変わり、保存場所の確認が出てボタンが効く。
  6. 構成フォルダの外の構成セットで、画面の「保存」ボタン（と Command+S）を押し、保存場所の確認を開いたまま、メニューバーの「新規作成」と「終了」を選ぶ。確認を閉じるまでどちらも始まらず、閉じた後に順に動く（止まらない・二重に動かない・A が空の構成で上書きされない）。確認を開いたまま App を最小化・復元しても同じ。
  7. 保存済みのセットで言語を切り替え、確認を開いたままメニューの「物理キー名」を切り替えてから「今すぐ再起動」を押すと、未保存の確認が出る（切り替えが黙って消えない）。
