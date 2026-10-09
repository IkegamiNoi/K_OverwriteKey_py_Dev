# task_05_spec_promotion

## 目的

phase 50 の最終タスク。暫定 34（v0.6・ユーザー確定済）を正本 `instructions/common/spec_detail/` へ昇格し、暫定 34 を凍結する（暫定 34 §12・`.claude/rules/task_execution.md`「フェーズ完了時」）。
文書作業のみ（メインセッションが直接行う・`agent_selection.md`）。コード不変・スキーマ不変（キーは task_01 で実装済み）。

## 対象範囲（文書のみ）

### 正本
- `features.md`: §4.2.5（待機明けの選び直しの参照）/ §4.2.6（`target` の無い戻す・先頭への対象 = 一覧の選択・使えなければ直前のトリガー・押した戻す・先頭へ自身を選ばない）/
  §4.2.10（確認して実行の判定の位置）/ 新節 §4.2.11「確認して実行」/ §4.5「一時的な案内」の列挙 / §4.6「UI と同期する実行系設定」・「確認して実行のチェック」（フォント +3 のはみ出しの受容を含む）
- `data_schema.md`: §5.3「select_before_run」（keymap_set・sequence・trigger・単一 JSON の最上位キー〔L7〕）/ §5.6 trigger_set の型の表・sequence / §5.9.1 の参照
- `key_input.md` §7.3: リピートの印（L8）
- `codebase_map.md`: phase 50 の置き場（L8）

### 状態・履歴
- 暫定 34 の冒頭を凍結に（§3 の控えの前提〔L4〕・send_wait の行番号・条件 8 / §8 の言い回しは凍結で据え置き〔正本側を正しく書く〕）
- `.claude_data/state/decisions_archive/50_select_before_run.md`・`decisions.md` のアーカイブ索引・`instructions/phase/current.md`・phase.md
- 起票元 idea なし（idea_39 は一部取り込みの記載を 2026-10-09 に追記済み・INDEX に残す）

## 読むファイル

- `instructions/history/34_select_before_run.md`（全体）
- `instructions/common/spec_detail/features.md` §4.2.3・§4.2.5・§4.2.6・§4.2.10・§4.5・§4.6 末尾 / `data_schema.md` §5.1〜5.3・§5.6・§5.9.1 / `key_input.md` §7.3
- `instructions/common/codebase_map.md` の phase 46 の項

## 含まない

- idea_39 の残り（直前のトリガーの廃止ほか・次フェーズ以降）
- フォント +3 のはみ出しの解消（受容・2026-10-09 ユーザー判断）

## 確認

- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（正本整合・未定義挙動・矛盾）
- `/refactor_check`（メトリクスは verifier・判定はメイン）
- 既存テスト（tests / tests_ui / smoke）は task_04c 時点で pass（本タスクはコード不変）
