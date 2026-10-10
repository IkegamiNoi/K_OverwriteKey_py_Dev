# phase.md

## フェーズ名

key_hold のキーリピート（key_hold_auto_repeat）

## フェーズの目的

key_hold で押したままにした通常キーを、離すまで OS の設定の間隔でキーリピートさせる（合成の押下は Windows がリピートしないため、文字入力で 1 文字しか入らない問題の解消）。
**domain / application / infrastructure / presentation。key_hold の JSON に任意キー `repeat`（bool）を追加（後方互換・キーの無い既存の行はリピートしない）。リピートのタイマーは新規の application クラス `KeyRepeater`（UI スレッドの `after`）。**

- 起票元: [idea_41](../../backlog/idea_41_key_hold_auto_repeat.md)（2026-10-10 phase 51 task_05 の実機目視・2026-10-11 着手決定）。
- 主入力（暫定仕様）: [36_key_hold_auto_repeat.md](../../history/36_key_hold_auto_repeat.md)（v0.4・ユーザー確定済 2026-10-11）
- モード: **暫定仕様先行モード**。番号対応: phase 52 / 暫定 36 / decisions 52。

## 確定（ユーザー 2026-10-11）

暫定 36 §2 の 1〜9 が正（本書に再掲しない）。要点: 間隔は OS の設定 / 修飾キー以外 / 押す行に「リピートする」チェック（新規 ON・既存のキー無しは OFF）/
同時に 1 つ・最後のキー / 一覧に ` (リピート)` / 知らせの前に止め、表示中はリピートしない / 対象を含む hotkey・直接置換の前に止める。

## スコープ

### 含む

- 暫定 36 §3〜§6 の実装とテスト（データ §3・実行 §4・UI §5・責務 §6）
- 正本反映（暫定 36 §10）

### 含まない（後送り）

- 暫定 36 §9 のとおり（マウスの連打・アプリ独自の間隔・修飾キーのリピート・複数キーの同時リピート・物理キーとの協調・IME 系キーの除外）

## このフェーズで読むファイル

1. `instructions/history/36_key_hold_auto_repeat.md`（全体）
2. `keyseq/application/held_inputs.py`（全体）・`keyseq/application/action_executor.py`（`_execute_key_hold`・`_execute_hotkey`・`_send_mapped_key`・`_write_text`）
3. `keyseq/infrastructure/input_gateway.py`（`press_key`・`key_identity`・拡張キーの送信）
4. `keyseq/domain/key_hold.py`・`keyseq/domain/config.py`（`format_action_list_item`）
5. `keyseq/presentation/app.py`（`HeldInputs` の生成・`after` の配線）・`controllers/hook_controller.py`（`show_action_error`）・知らせの口（`app.py` の runner の `notify_error` 等）
6. `keyseq/presentation/dialogs/action_key_hold_fields.py`・`dialogs/action_dialog.py`（key_hold の組み直し :230-250）
7. 正本: `instructions/common/spec_detail/features.md` §4.2.12・§4.6 / `data_schema.md` §5.11.9 / `key_input.md` §7.7 / `codebase_map.md` の phase 51 の項

## タスク

- task_01: domain + infrastructure — `repeat` の判定・修飾キーの判定（keyboard の別名を列挙）・一覧の書式 ` (リピート)`（§3・§4.6・§5）/ OS のリピート設定の取得と換算（§6）とテスト — **完了**（2026-10-11・codex-implementer・reviewer 採用・import の並びをメインで修正。tests 1458 / tests_ui 935 / smoke pass〔tests_ui の 1 回目に無関係の flaky 1 件・再実行で pass〕）
- task_02: application — `KeyRepeater`（開始・切替・止める・text の前後・送り直し・古い予約・失敗・表示中の抑止の口）と `HeldInputs` / `ActionExecutor`（key_hold の repeat・対象を含む hotkey・直接置換の前に止める）の連携とテスト（§4・§6）
- task_03: presentation — App の配線（`after` / 間隔の取得 / 知らせの口）・知らせの前に止める / 表示中の抑止・ダイアログの「リピートする」チェック（表示の切替・ON で始まる場合・組み直し）とテスト（§4.8・§5）。**実装後にユーザーの実機目視**（暫定 36 §8 の 12〜14。15 は task_04）
- task_04: 統合確認（tests / tests_ui / smoke・deep-reviewer + codex-reviewer）と**ユーザーの実機目視**（暫定 36 §8 の 15・修正があればその分の再目視）
- task_05: 正本反映（暫定 36 §10 の昇格・凍結）・`decisions_archive/52_key_hold_auto_repeat.md`・decisions.md の索引・current.md の完了記載・idea_41 を INDEX_done へ・`/refactor_check`

## レビュー方針

- 各タスク: `reviewer`（5 観点）・既存テスト（tests / tests_ui / smoke）の通過を完了条件に含める
- 重点: **リピートが止まらずに keydown が送られ続ける経路が無いか**（§4.3 の止める場所・phase 51 の自動で離す入口すべて・離す失敗・補償の失敗・アプリ終了・古い予約）/
  予約の取り消し漏れ / 表示中の抑止（入れ子・断った開始の非復活）/ text の前後で元の対象だけ再開 / 対象を含む hotkey・直接置換の判定（同じキーの判定）/
  送り直しで表示の更新を起こさない / 修飾キーの別名 / UI スレッドの外で送らない / テストが実入力を送らない・実 `config/` を汚さない
- 統合確認（task_04）: `deep-reviewer` + `codex-reviewer` / 完了判定前（task_05）: `deep-reviewer` + `codex-adversarial-reviewer`
- 実機目視（ユーザー・**ホスト OS**。VirtualBox のゲストでは物理キーが届かない場合がある）: task_03・task_04
