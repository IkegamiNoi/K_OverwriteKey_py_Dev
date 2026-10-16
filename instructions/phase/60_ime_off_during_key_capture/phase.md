# phase.md

## フェーズ名

キーの取得中は IME を OFF にする（ime_off_during_key_capture）

## フェーズの目的

キーを押して取得する 8 つの入口（停止 / トグルキー・トリガー・切替キー・複数の切替キー・hotkey・key_hold・キーボードUI の編集・画面の枠の編集の窓）で、
取得の間だけアプリ自身の IME を OFF にして終了で元へ戻し、`??`（判別できないキー）を全入口で記録しないように揃える。
**presentation（取得の寿命の部品の新設・8 入口の配線・`tk_keys.py` の `??` 判定・案内の文言）+ infrastructure（自アプリの IME の開閉を読む・変える状態なしの口の新設）。
application・フック・送信（`ime_control.py`）は変えない。JSON スキーマ不変。**

- 起票元: [idea_46](../../backlog/idea_46_ime_off_during_key_capture.md)（2026-10-16・phase 59 task_04a の実機目視から分離）。
- 主入力（暫定仕様）: [44_ime_off_during_key_capture.md](../../history/44_ime_off_during_key_capture.md)（v0.4・ユーザー確定済 2026-10-16）
- モード: **暫定仕様先行モード**。番号対応: phase 60 / 暫定 44 / decisions 60。

## 確定（ユーザー 2026-10-16）

暫定 44 §2 が正（本書に再掲しない）。要点: 開閉を記録して OFF・終了で復元（API は自スレッド向けの `ImmGetContext` / `ImmSetOpenStatus`）/ 取得の寿命だけを持つ小さな部品を各入口の既存の開始・停止の関数から呼ぶ /
`??` は全入口で記録せず取得を続け、案内の欄がある入口は「このキーは取得できません。別のキーを押してください。（Escでキャンセル）」/ 取得中に手で ON にされても OFF にし直さない / 取得中のフック再開は [idea_48](../../backlog/idea_48_hook_resume_during_key_capture.md) へ分離。

## スコープ

### 含む

- 暫定 44 §3〜§6 の実装とテスト（取得の期間・数と印による開始 / 終了 / `<Destroy>`・失敗時の素通し・`??` の統一と案内）
- 実機目視（IME ON からの取得・暫定 44 §8-6）
- 正本反映（暫定 44 §10）

### 含まない（後送り）

- 暫定 44 §9 のとおり（送信時の IME / 変換中の文字列の取得 / 取得の期間の変更・取得処理の丸ごとの共通化 / 取得中に手で ON にされたときの対処 / idea_45 / idea_47）
- 取得中のフック再開（idea_48）

## このフェーズで読むファイル

1. `instructions/history/44_ime_off_during_key_capture.md`（全体）
2. 取得の部品と口（新設）の参考: `keyseq/infrastructure/ime_control.py`（`_Win32ImeApi` の ctypes の書き方・Windows 以外の扱いのみ。送信側は変えない）/ `keyseq/presentation/tk_keys.py`（`normalize_tk_key_event`・`normalize_key_hold_tk_key_event`）/ `keyseq/presentation/hook_button_texts.py`
3. `<Destroy>` の絞り込みの前例: `keyseq/presentation/controllers/hook_controller.py:50-64`
4. 入口 #1〜#4: `keyseq/presentation/controllers/key_capture.py` / `dialogs/trigger_dialog.py` / `dialogs/keymap_edit_dialog.py` / `dialogs/keymap_switch_batch_dialog.py`
5. 入口 #5〜#8: `dialogs/action_dialog.py`（記録の開始・`_stop_recording`）/ `dialogs/action_key_hold_fields.py` / `keyboard_window.py`（`_begin_edit`・`_cancel_edit`・`_on_key_press`・`_normalize_tk_key`）/ `dialogs/grid_editor_window.py`（`on_key`）・`controllers/keymap_panel/keymap_panel_controller.py:452-467`
6. 正本: `key_input.md` §7.4・§7.7 / `features.md` §4.3「割り当て禁止のキー」/ `codebase_map.md`（取得の各入口・`ime_control`）
7. テスト: `tests/test_ime_control.py`（書き方の参考）/ `tests_ui/test_prohibited_assign_keys_ui.py`（`??` の案内）/ 各入口の既存の tests_ui

## タスク

- task_01: 土台 — infrastructure の自アプリの IME の開閉の口（新モジュール）・presentation の取得の寿命の部品（数・印・開始 / 終了の冪等・`<Destroy>` の絞り込み・失敗時の素通し）・`tk_keys.py` の `??` 判定・案内の文言の変更（#3・#4 の既存テストの追従）と単体テスト（暫定 44 §4・§5・§6・§8-2,3,5）
- task_02: 入口 #1〜#4 の配線（停止 / トグルキー・トリガー・切替キー・複数の切替キー）と `??` の統一（#1 のエラーのダイアログ → 無視・#2 の案内）・tests_ui（暫定 44 §3・§5・§8-1,4）
- task_03: 入口 #5〜#8 の配線（hotkey・key_hold・キーボードUI の編集〔再開始は何もしない〕・画面の枠の編集の窓〔開いている間〕）と `??` の統一（#6 の案内）・tests_ui。**実装後にユーザーの実機目視**（IME ON からの 8 入口の取得・終了で戻る・#7 の別の元キーのクリック・暫定 44 §8-6）
- task_04: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）
- task_05: 正本反映（暫定 44 §10 の昇格〔`key_input.md` §7.4・`features.md` §4.3〕・凍結・`codebase_map.md`）・`decisions_archive/60_ime_off_during_key_capture.md`・decisions.md の索引・current.md の完了記載・idea_46 の INDEX_done への移動・`/refactor_check`

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: 停止の関数のすべての経路で終了が呼ばれる（経路の取りこぼし）/ 数が残る終了・重複した終了・再開始で印と開閉が変わらない / `<Destroy>` は `event.widget is window` で絞る /
  送信側（`ime_control.py`・`ImeController`）を変えていない / 取得の入口の構造（キーの解釈・期間）を変えていない / 状態は presentation の部品が持ち infrastructure は状態なし
