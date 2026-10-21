# phase.md

## フェーズ名

キーの取得で JIS の特殊キーを取る（capture_jis_special_keys）

## フェーズの目的

キーの取得（Tk のキーイベントで 1 キーを記録する 8 入口）で、JIS の特殊キー（無変換・変換・半角/全角・かな）が IME に横取りされ `??` で届き、取得できず IME も切り替わる。
**取得の間だけ keyboard の suppress フックを 1 つ登録し、選んでいるレイアウトの行に当たるキーを抑止して、フックの実行時と同じ名前を取得中の入口へ渡す（アプリの窓が前面のときだけ・押下中は最後の押下から一定時間まで・余韻つき・世代で古い名前を捨てる）。presentation（`key_capture_ime` の隣の取得用のフック・8 入口・`app.py` の配線）+ infrastructure の既存の口（`register_global_hook` / `unregister_hook`・`is_own_process_foreground`）。JSON スキーマ不変。**

- 起票元: [idea_50](../../backlog/idea_50_capture_jis_special_keys.md)（2026-10-17・phase 61 の実機目視から分離。2026-10-21 に key_hold / トリガーの記録ボタンの要望を追記）。
- 主入力（暫定仕様）: [49_capture_jis_special_keys.md](../../history/49_capture_jis_special_keys.md)（v0.3・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: phase 66 / 暫定 49 / decisions 66。

## 確定（ユーザー 2026-10-21）

- 対象の入口 = 取得の 8 入口すべて
- 対象のキー = 選んでいるレイアウトの `scan_code` / `extra_scan_codes` に当たるキーから、テンキー・Esc・修飾キーを除いたもの（コードにキーの表は持たない）
- 対象のキーは抑止する（アプリの窓が前面のときだけ・押下中は最後の押下から一定時間まで・余韻つき）
- 押下中は離しでは外さず、最後の押下から「OS のリピートの待ち + 200 ms」押下が来ないとき外す / 余韻の上限 = 取得の終了から 5 秒（task_01 の実測・暫定 49 v0.4）
- 詳細は暫定 49 §2・§3

## スコープ

### 含む

- 4 キー（と押下だけのキーボードの無変換・変換）のフックでの届き方・抑止と IME の切替の実測（暫定 49 §7a）→ §3-5 の値を暫定 49 へ書く
- 取得用のフック（登録の期間・対象の判定・抑止・重複の除去・余韻・世代・渡し先・`begin_key_capture` の `on_hook_key`・App の設定・未設定なら登録しない）（暫定 49 §3）
- 8 入口の受け取り（Tk のイベントから名前を作る部分と、名前を受けて記録する部分を分け、両方が後者を呼ぶ）（暫定 49 §3-7）
- テスト（偽の gateway・偽のレイアウト・偽の after / 前面の判定・各入口の受け取り。tests_ui は本物のフックを入れない）
- 実機目視（暫定 49 §7-8）
- 正本反映（暫定 49 §9）・暫定 49 の凍結

### 含まない（後送り）

- 記号キーの名前の不一致（idea_45）
- 取得中のフック再開の穴（idea_48）
- 特殊キーを書いていないレイアウトでの取得（暫定 49 §5 の受容）

## このフェーズで読むファイル

1. 主入力: `instructions/history/49_capture_jis_special_keys.md`
2. `keyseq/presentation/key_capture_ime.py`（全体）
3. `keyseq/application/hook_coordinator.py:55-80`（フックの登録・解除）・`keyseq/infrastructure/input_gateway.py:256-262`（`register_global_hook`）
4. `keyseq/presentation/controllers/hook_controller.py:294-315`（フックのスレッドから `after(0)`）・`keyseq/presentation/controllers/layout_controller.py:375-379`（`resolve_key_name_from_scan_code`）
5. `keyseq/domain/numpad_keys.py`（`numpad_name_from_event`）・`keyseq/domain/key_hold.py:10-40`（`MODIFIER_KEY_NAMES`）・`keyseq/infrastructure/win32_window.py:205-225`（`is_own_process_foreground`）
6. 8 入口: `presentation/controllers/key_capture.py`・`dialogs/trigger_dialog.py`・`dialogs/keymap_edit_dialog.py`・`dialogs/keymap_switch_batch_dialog.py`・`dialogs/action_dialog.py`・`dialogs/action_key_hold_fields.py`・`keyboard_window.py`・`dialogs/grid_editor_window.py`（各入口の取得の開始・KeyPress の処理の範囲）
7. 正本: `key_input.md` §7.1・§7.4・§7.5 / `codebase_map.md`（phase 60 の節・key_capture_ime）
8. テスト: `tests_ui/test_capture_ime_entries.py`（tracker の差し替え）・`tests/test_key_capture_ime*.py`（あれば）

## タスク

- task_01: 実測（暫定 49 §7a・`.venv` の小スクリプトで keyboard の suppress フックを入れ、ユーザーが実機で 4 キーと押下だけのキーボードを押す）→ 届き方と IME の切替を記録し、§3-4・§3-5 の一定時間と上限を暫定 49 へ書く（ユーザー確認）
- task_02: 取得用のフック（暫定 49 §3-1〜§3-6・§3-8）+ `begin_key_capture` の `on_hook_key` と世代（§3-6・§3-7 の口）+ `app.py` の設定・テスト（tests）
- task_03: 8 入口の受け取り（暫定 49 §3-7。Tk の道筋と同じ後続の処理）・テスト（tests_ui）
- task_04: 実機目視（暫定 49 §7-8）・正本反映（暫定 49 §9）・暫定 49 凍結・`decisions_archive/66_capture_jis_special_keys.md`・decisions.md の索引・current.md の完了記載・idea_50 を INDEX_done へ・`/refactor_check`・完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- task_02 重点: 素通しは True を明示（None は抑止）/ 対象の判定の順（前面 → テンキー → レイアウト → Esc・修飾キー）/ 登録・解除は UI スレッド・二重に登録しない / 押下中は取得の継続と無関係に最後の押下からの一定時間で外れる（離しでは外さない）・余韻の上限 5 秒 / 余韻の間は対象のキーだけ抑止し受け渡さない / 世代は begin の呼び出しのたび（再度の開始を含む）と実際の終了で進む / 未設定ならフックを登録しない / フックのスレッドで Tk を触らない
- task_03 重点: 各入口で Tk の道筋とフックの道筋が同じ後続の処理を通る（修飾キー単独・禁止のキー・重複・案内・取得の終了・検査）/ #5 の修飾キーとの組み合わせ / #7・#8 の取得の続き方 / 既存の取得の挙動が不変
