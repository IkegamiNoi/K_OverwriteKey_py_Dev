# phase.md

## フェーズ名

出力シーケンスの制御アクション・第 2 弾 前半 = 停止（sequence_stop）

## フェーズの目的

出力シーケンスの system 種別に**停止**（`op: stop`）を加え、連続実行をそこで区切れるようにする（次の押下で続きをまた連続実行・単発では読み飛ばす）。

**JSON スキーマ変更あり**（op の追加のみ・既存の種別・キーは不変）。**domain（定数・表示）/ application（advance・先行処理・連続実行の終了）/ presentation（編集ダイアログ）**に跨る。

- 起票元: 暫定 26 §13（phase 37 で合意した第 2 弾の方針）/ ユーザー判断「第 2 弾に着手・停止と呼び出しを分ける」（2026-09-27）。呼び出しは phase 40。
- 主入力（暫定仕様）: [28_sequence_stop_and_call.md](../../history/28_sequence_stop_and_call.md)（v0.4・ユーザー確定済 2026-09-27）。
- モード: **暫定仕様先行モード**。番号対応: phase 39 / 暫定 28 / decisions 39。

## 確定（ユーザー 2026-09-27）

暫定仕様 28 §2 が正。要点:

- 連続実行は停止の行で終える（位置は停止の次・間隔を置かない）。単発は読み飛ばす。
- その連続実行で通常アクションを送る前の停止は読み飛ばす（一時停止 → 再開は同じ連続実行）。
- 停止で終えるときは保留中のカウンター操作をその場で反映する。停止は他の行と混ぜてよい。

## スコープ

### 含む

暫定仕様 28 の §3〜§5 と §6 の受け入れ条件。

### 含まない（後送り）

暫定仕様 28 §7・§9（呼び出し = phase 40 / ジャンプ / カウンター条件分岐）。

## このフェーズで読むファイル

1. [暫定仕様 28](../../history/28_sequence_stop_and_call.md)（主入力。§1 の現状監査に `ファイル:行` の入口あり）
2. `instructions/common/spec_detail/data_schema.md` §5.11.5・§5.11.6、`features.md` §4.2.1・§4.2.2・§4.6「一覧の表示形式」「出力シーケンスの編集」
3. `instructions/common/codebase_map.md`「出力シーケンスの制御アクション」節
4. 実装の入口: `keyseq/domain/sequence_control.py` / `keyseq/application/sequence_steps.py` / `keyseq/application/sequence_runner/` /
   `keyseq/presentation/dialogs/action_control_fields.py`

## タスク

依存順。各タスクの定義は着手時に `tasks/task_NN_<topic>.md` へ起票する（`/task_new`）。

- task_01: domain と実行の中核（暫定 §3・§4: `OP_STOP`・表示 `[stop]` / `advance`・`settle_after_normal` に連続実行かどうかと読み飛ばしの要否を渡し、停止で終えることを返す） — **完了**（2026-09-28。`stop_ends_run` 引数・`stopped` フィールド）
- task_02: runner の組み込み（暫定 §4.1: 連続実行の終了・位置・間隔なし・保留の反映と戻す履歴 / 読み飛ばしの印〔開始で消す・一時停止で保つ・file_line の完了も数える〕/ 単発の読み飛ばし） — **完了**（2026-09-28。`_run_to_end_sent`・`_finish_run_to_end_normal_action` が停止を返す）
- task_03: 編集ダイアログ（暫定 §5: system の操作に「停止」）・実機目視
- task_04: 統合確認（テストスイート全体・smoke。統合レビュー = deep-reviewer + codex-reviewer）
- task_05: 正本反映（暫定 28 §8: `data_schema.md` §5.11.5・§5.11.6 / `features.md` §4.2.1・§4.2.2・4.2.8 新設・§4.6 / `codebase_map.md` /
  暫定 28 の凍結〔§9 は phase 40 の起票元として参照される〕/ `decisions_archive/39_sequence_stop.md` / current.md 完了記載 / `/refactor_check`）

## レビュー方針

- 各タスク: reviewer（5 観点）。**既存の連続実行・単発・待機・file_line の挙動が停止を含まないシーケンスで不変**かを必ず確認する。
- 重点: 読み飛ばしの印の境界（一時停止 → 再開・file_line の完了・待機の続き）/ 先行処理で停止に達したときの位置と保留の反映・戻す履歴 1 段 / 単発の先頭への回り込み（開始位置で終える規則）と停止。
- 統合・フェーズ完了判定前は deep-reviewer + Codex レビュー（`.claude/rules/agent_selection.md`）。
