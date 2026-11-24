# phase.md

## フェーズ名

Win+D から戻したときに入れ子のダイアログが白いまま（win_d_restore_blank_dialog）

## フェーズの目的

Windows で入れ子のダイアログ（プリセット管理 → プリセット追加）を開いたまま Win+D で隠して戻すと、
プリセット追加の窓が白いまま描かれない（毎回再現・phase 75 前の main でも起きる既存の問題）。
原因を実測で確かめ、戻したときに中身が描かれるようにする。
**対象は presentation のみ（主に `keyseq/presentation/modal.py` の最小化からの復帰の処理）・JSON スキーマ不変**。

- 起票元: [idea_61](../../backlog/idea_61_win_d_restore_blank_dialog.md)（2026-11-17・phase 75 の Windows 目視）。
- 主入力（暫定仕様）: なし（直接改訂モード）。
- モード: **直接改訂モード**（局所的・見た目の復帰の修正・タスク 3）。番号対応: phase 80 / 暫定なし / decisions 80。
  task_01 の実測で grab の預かりの規則（`features.md` §4.6「最小化」の条項）を変える必要が分かった場合は、
  止めてユーザーへ報告し、`.claude/rules/spec_change_workflow.md` に従ってモードを選び直す。

## 確定（ユーザー 2026-11-24）

- idea_61 に着手する（phase 80）。

## スコープ

### 含む

- Win+D の後の各窓の状態と `<Map>` / `<Unmap>` / `<Expose>` の届き方の実測（原因の特定）
- 他の入れ子のダイアログ（深さ・親の違い）でも起きるかの確認と、直す範囲の決定
- 復帰の処理の修正（`modal.py` を中心に presentation 内）と `tests_ui` のテスト
- Windows の目視（ユーザー）

### 含まない（後送り）

- 最小化の経路そのものの変更・Mac の挙動（phase 75 task_11c で対応済み）
- タイトルバーの最小化など、Win+D 以外で再現しない経路の作り直し

## このフェーズで読むファイル

1. [idea_61](../../backlog/idea_61_win_d_restore_blank_dialog.md)
2. `keyseq/presentation/modal.py`（`install_minimize_grab_custody` 〜 `_return_grab`・`_restore_modal_focus`）
3. `keyseq/infrastructure/os_backend/windows/backend.py`（`get_backend().window` の Windows 実装・`install_minimize_preparation` ほか）
4. `keyseq/presentation/dialogs/preset_manager.py` / `preset_dialog.py`（再現の窓）
5. `instructions/common/spec_detail/features.md` §4.6「モーダルダイアログの作法」の最小化の項（1163〜1197 行）
6. `instructions/common/codebase_map.md` の modal.py の節
7. `tests_ui/test_minimize_grab_custody.py`
8. 必要時のみ: `.claude_data/state/decisions_archive/17_minimize_grab_custody.md` / `75_mac_support.md`（task_11c）

## タスク

- task_01: 再現と原因の実測（Windows）。Win+D を自動で送って再現できるかを試し、各窓の `wm_state()`・`winfo_viewable()`・イベントの順を記録する。他の入れ子のダイアログでも確かめ、原因と直す範囲・修正案（idea の案 A / B ほか）を出してユーザーが選ぶ。コード変更なし（計測用の一時スクリプトは scratchpad）
- task_02: 修正と tests_ui のテスト（実装 = 既定の実装エージェント）・標準検証・Windows の目視（ユーザー）
- task_03: 記録（正本の追記が要ればユーザー承認のうえ `features.md`・`codebase_map.md`・`decisions_archive/80`・current.md の完了記載・`instructions/backlog/INDEX.md` の idea_61 の行を完了にして `INDEX_done.md` へ移動・`/refactor_check`）

## レビュー方針

- 共通観点は `.claude/rules/review.md`。各タスクは `reviewer`、フェーズ完了判定前は `deep-reviewer` + Codex 敵対的レビュー
- 固有の観点: 既存の grab の預かり（phase 17）と復元後のフォーカス（phase 23 系）の挙動を変えていないか /
  Win+D 以外の最小化（タイトルバー・タスクバー）と Mac の経路に影響しないか / 描き直しの処理が台帳の窓以外へ広がっていないか
