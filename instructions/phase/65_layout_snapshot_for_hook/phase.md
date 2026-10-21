# phase.md

## フェーズ名

受け取りと送信が同じレイアウトの写しを使う（layout_snapshot_for_hook）

## フェーズの目的

フックの受け取りが打鍵ごとに外部レイアウトの JSON を読み直し（フックのスレッドでファイルを読み、失敗時は Tk を操作）、送信は登録時の値を引くため、起動中に JSON を書き換えると食い違う。また押したままのキーは離す時点のレイアウトで引き直すため、離しの失敗と切替が重なると元のキーが押されたまま残る。
**受け取り・送信・キーボードUI を `LayoutController` のレイアウトの写し 1 つへそろえ（差し替えは UI スレッドだけ・選び直しと読み直しのとき）、押したままのキーは押したときの送り方で送る。presentation（`LayoutController`）+ application（`held_inputs`・`key_repeat`）+ infrastructure（`input_gateway` の送り方の値）。JSON スキーマ不変。**

- 起票元: [idea_51](../../backlog/idea_51_layout_snapshot_for_hook.md)（2026-10-18・暫定 45 の Codex 敵対的レビューから分離）。
- 主入力（暫定仕様）: [48_layout_snapshot_for_hook.md](../../history/48_layout_snapshot_for_hook.md)（v0.3・ユーザー確定済）
- モード: **暫定仕様先行モード**。番号対応: phase 65 / 暫定 48 / decisions 65。

## 確定（ユーザー 2026-10-21）

- 外部レイアウトの JSON の変更は選び直し（同じレイアウトでも）・読み直しのときだけ反映（監視しない）
- 押したままのキーは押したときの送り方で送る（離し・一時的な離しと押し直し・リピートの送り直し・補償の離し）
- 1 打鍵の中で判定と押下状態の記録が別の写しで名前を引き得るのは受容（暫定 48 §5）
- 詳細は暫定 48 §2

## スコープ

### 含む

- 写し `_active_layout`（暫定 48 §3）・ユーザーの選び直しで読み直し・`get_current_keyboard_layout` の読み直しと失敗の通知の削除
- `KeySend` と `resolve_send` / `press_send` / `release_send` / `identity_of`・`held_inputs` の送り方の記録・リピーターの callback（暫定 48 §4）
- テスト（偽 gateway・偽リピーターの更新を含む・暫定 48 §9）
- 実機目視（暫定 48 §7-7）
- 正本反映（暫定 48 §9）・暫定 48 の凍結

### 含まない（後送り）

- ファイルの変更の監視・読込失敗の通知の追加・JSON の書式（暫定 48 §8）
- 1 打鍵の中の 2 回の解決の統一（受容・暫定 48 §5）
- 送信の最中の物理の入力（idea_53・保留）

## このフェーズで読むファイル

1. 主入力: `instructions/history/48_layout_snapshot_for_hook.md`
2. `keyseq/presentation/controllers/layout_controller.py`（全体）
3. `keyseq/presentation/keyboard_layouts.py:1-40`・`:272-295`（`KeyboardLayout` / `BUILTIN_LAYOUTS` / `collect_keyboard_layouts`）
4. `keyseq/application/held_inputs.py`（全体）・`keyseq/application/key_repeat.py`（全体）
5. `keyseq/infrastructure/input_gateway.py:120-222`・`:278-360`（送信と解決）
6. `keyseq/presentation/app.py:130-200`（配線）
7. 正本: `key_input.md` §7.1 :13・§7.7 :193-214 / `features.md` :713 / `codebase_map.md`（LayoutController・held_inputs・input_gateway の節）
8. テスト: `tests/test_layout_controller_scan_code.py`・`tests/test_held_inputs.py`・`tests/test_held_inputs_repeat.py`・`tests/test_action_executor_key_hold.py`・`tests/test_sequence_runner_key_hold.py`・`tests/test_input_gateway_send.py`・`tests/test_key_repeat.py`・`tests/test_input_gateway_repeat.py`

## タスク

- task_01: レイアウトの写し（presentation・暫定 48 §3）・ユーザーの選び直しで読み直し・テスト
- task_02: 押したままのキーを押したときの送り方で送る（infrastructure `KeySend` + application `held_inputs` / `key_repeat`・暫定 48 §4。押し直しは公開の `press_key` を経由せず記録の送り方で送る内部の道筋〔§4-4〕）・テスト（偽 gateway の更新）
- task_03a: `identity_of` の未定義名 `key` を `send.key` へ（task_03 の完了判定前レビュー deep 指摘 2・infrastructure 1 行 + テスト 1 件）
- task_03: 実機目視（暫定 48 §7-7）・正本反映（暫定 48 §9）・暫定 48 凍結・`decisions_archive/65_layout_snapshot_for_hook.md`・decisions.md の索引・current.md の完了記載・idea_51 を INDEX_done へ・`/refactor_check`・完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- task_01 重点: 写しを差し替える箇所が UI スレッドだけ・解放 → 差し替えの順 / 読み手が `keyboard_layout_id` と entries を別々に読まない / フックの経路でファイルを読まず Tk を触らない / 選び直しの読み直しの順（解放 → 読み直し → id → 写し → 保存）/ プログラムからの選択は読み直さない
- task_02 重点: application が `KeySend` の型を import しない / 既存の `press_key` / `release_key` / `key_identity` の送り方が不変（keyboard の種類はキー名で送る）/ 記録のある送信がすべて記録の送り方を使う（離し・一時的な離し・押し直し・リピート・補償）/ リピートの記録が無ければ止まる
