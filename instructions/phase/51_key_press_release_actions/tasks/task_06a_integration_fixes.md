# task_06a_integration_fixes

## 目的

task_06 の統合レビュー（deep-reviewer H1・M1・L6 / codex-reviewer P2 × 2）の修正（暫定 35 v0.8 §2-19・§2-20・§4.4・§5・§7・§10-7d）。
JSON 不変。修正後に**ユーザーの実機目視**（キーマップの切替で shift が離れる）。

## 対象範囲

### 1. キーマップの切替 / アクティブの削除ですべて離す（H1・M1・§2-19・§5）
- application に解放の口を 1 つ足す: `SequenceRunner` に `release_all_held()`（`held_inputs` が無ければ何もしない・`held_inputs.release_all()` の例外の一覧を既存の `_notify_release_errors`〔`sequence_runner.py:95`〕で知らせる。`run_to_end.py:124-126` の `on_runtime_reset` と同じ知らせ方）
- `keymap_panel/keymap_panel_controller.py` の `activate_keymap_by_id`（:440〜）: **アクティブが実際に変わったとき**（`target_id != active_before` かつ切替が成立した＝`set_active_keymap_id` の後に `active_id == target_id`）に `release_all_held()` を呼ぶ。同じキーマップへの切替では呼ばない。切替が成立しない（`can_switch_keymap` が False・`active_id != target_id`）なら呼ばない
- 同 `_delete_keymap_confirmed`（:315〜）: アクティブを削除するとき（既存の `discard_paused` / `cancel_pending_waits` の分岐）に `release_all_held()` を呼ぶ（削除後の `start_hook` での解放の副作用に頼らない）
- presentation は口を呼ぶだけ（解放の処理を presentation に書かない・§8）

### 2. 送る前の一時的な離すの途中失敗（Codex P2-1・deep L1・§4.4 v0.8）
- `application/action_executor.py:237-248` の `_write_text`: `held_inputs.suspend_keyboard()` の例外も、`write_text` の例外と同じく `held_inputs.release_keyboard()` してから送出する（`suspend_keyboard` を内側の `try` に入れる等）。その後の `_report_held_error` の流れは変えない
- `suspend_keyboard` 自体（`held_inputs.py:171-181`・すべて試してから最初の例外を送出）は変えない

### 3. 「1 キーを記録」で修飾キーの左右を区別（Codex P2-2・§2-20・§7）
- `presentation/dialogs/action_key_hold_fields.py:167` の `_on_key_press`: key_hold の記録では Tk の keysym を左右を区別した名前に変換する: `control_l` → `left ctrl` / `control_r` → `right ctrl` / `shift_l` → `left shift` / `shift_r` → `right shift` / `alt_l` → `left alt` / `alt_r` → `right alt` / `super_l`・`win_l` → `left windows` / `super_r`・`win_r` → `right windows`。それ以外は既存の `normalize_tk_keysym` のまま
- **`presentation/tk_keys.py` の既存の表は変えない**（hotkey の記録等、他の利用箇所の挙動を変えない）。左右の表は key_hold の記録側（同モジュール内または `tk_keys.py` に別の関数として）に置く
- 変換後の名前は `input_gateway.validate_key_name` を通ること（`left ctrl` / `right shift` 等は keyboard ライブラリの名前。通らないものがあれば報告して止める）

### 4. キーマップ一時停止の解放を finally へ（deep L6）
- `presentation/controllers/hook_controller.py:183-193` の `toggle_custom_input_enabled` の一時停止の分岐: `stop_run_to_end` / `cancel_pending_waits` が例外でも `_release_held_inputs()` が走るよう `try/finally` にする（`stop_hook` と同じ作法）

### テスト
- tests（unit）: `release_all_held`（held_inputs あり / なし・エラーの知らせ）/ `_write_text` で `suspend_keyboard` が例外のとき `release_keyboard` が呼ばれ、他の持ち主のキーボードのキーが集合に残らない（マウスは残る）・エラーとして止まる
- tests_ui: キーマップを実際に切り替えると `release_all` 相当で押下中が空になる / 同じキーマップへの切替では残る / アクティブの削除で空になる（偽の gateway で `held_inputs` に押下を入れておく）/ 記録で右 ctrl・右 shift・左 alt 等が左右付きの名前になる（keysym を与えたイベントで `_on_key_press` を呼ぶ）/ 一時停止で `stop_run_to_end` が例外でも離れる
- **実際のキー入力・マウス操作を送らない**（gateway を差し替える）。App を作るテストは既存の `tests_ui/test_keymap_set_history_flow.py:17-34` の ExitStack 手法で実 `config/` を汚さない

## 読むファイル

- `instructions/history/35_key_press_release_actions.md` §2-19〜20・§4.4・§5・§7・§8・§10-7d
- `keyseq/presentation/controllers/keymap_panel/keymap_panel_controller.py:312-345, 440-490`
- `keyseq/application/sequence_runner/sequence_runner.py:90-100`（`_notify_release_errors`）・`run_to_end.py:118-136`（`on_runtime_reset`）
- `keyseq/application/action_executor.py:230-256`・`keyseq/application/held_inputs.py:120-200`
- `keyseq/presentation/dialogs/action_key_hold_fields.py:140-175`・`keyseq/presentation/tk_keys.py`
- `keyseq/presentation/controllers/hook_controller.py:180-230`
- 既存テストの手本: `tests/` の held_inputs・action_executor の key_hold テスト / `tests_ui/test_action_dialog_key_hold.py` / `tests_ui/test_keymap_set_history_flow.py:17-34`

## 含まない

- S2（hotkey の送信の例外）・S3（押し直しの失敗）・L2（離すの送信の失敗）の挙動変更（v0.8 で現状維持と注記）
- L3・L4・L5・L7・L8・L9・L11（task_07 の文書化または見送り）
- 正本の改訂（task_07）

## 確認

- 上記テスト（実行は verifier: compileall・tests・tests_ui・smoke）
- reviewer（5 観点）
- **ユーザーの実機目視**: shift を押したままキーマップを切替キー / 一覧のクリックで切り替えると離れる・同じキーマップでは離れない・記録で右 ctrl が `right ctrl` になる
