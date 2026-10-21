# task_03_spec_reflection

## 目的

phase 65 の正本反映とフェーズ完了処理（暫定 48 §9）。task_01・task_02 の実装（レイアウトの写し・押したときの送り方）を正本へ昇格し、暫定 48 を凍結する。
**文書のみ・コード変更なし。**

## 対象範囲（文書のみ）

- `instructions/common/spec_detail/key_input.md`
  - §7.1 :13: フックの実行時のキー名は `LayoutController` のレイアウトの写しを引く（ファイルを読み直さない）
  - §7.7 :201: 4 は「登録済みのレイアウト」→「レイアウトの写し」（差し替えは UI スレッドだけ・選び直しと読み直しのとき）
  - §7.7 :205-214: 解放 → 写しの差し替えの順・ユーザーの選び直しでも読み直す / 受容 :212 を削除 / :213 を「押したままのキーは押したときの送り方で送る」へ / :214 を暫定 48 §5 の受容（解放の失敗の窓の間の key_hold・1 打鍵の中の 2 回の解決）へ
- `instructions/common/spec_detail/features.md` §4.6 :713: 外部レイアウトの JSON の変更は選び直し（同じレイアウトでも）・読み直しのときに反映（監視しない）
- `instructions/common/codebase_map.md`: `LayoutController`（写し `_active_layout`・`_refresh_active_layout`・選択で読み直す）/ `held_inputs`（`HeldInput.send`）/ `key_repeat`（callback `send(identity, key)`）/ `input_gateway`（`KeySend` / `resolve_send` / `press_send` / `release_send` / `identity_of`）
- 暫定 48 の凍結（状態行）
- `.claude_data/state/decisions_archive/65_layout_snapshot_for_hook.md` の作成・`decisions.md` の phase 65 節を移しアーカイブ索引へ 1 行
- `instructions/phase/current.md`: 完了記載・次採番（phase 66 / 暫定 49 / decisions 66）
- `instructions/backlog/INDEX.md` の idea_51 行を完了にして `INDEX_done.md` へ移動
- `/refactor_check` の判定記録
- 完了判定前レビュー（`deep-reviewer` + `codex-adversarial-reviewer`）

## 読むファイル

1. `instructions/history/48_layout_snapshot_for_hook.md`（§3〜§5・§9）
2. `instructions/common/spec_detail/key_input.md:13`・`:193-214`
3. `instructions/common/spec_detail/features.md:708-716`
4. `instructions/common/codebase_map.md:319`・`:763-791`・`:827-831`
5. `.claude_data/state/decisions_archive/64_external_layout_path_base.md`（書式の手本）

## 含まない

- コードの変更
- 暫定 48 §8 のスコープ外（ファイルの監視・読込失敗の通知・JSON の書式・idea_53）

## 確認

- 正本の記述が実装（`layout_controller.py:178-185`・`:196-202`・`:218-228`・`:281-287`・`held_inputs.py:149-156`・`:179-209`・`:221-289`・`key_repeat.py:20-41`・`input_gateway.py:285-385`）と一致
- リンク切れなし（idea_51 を INDEX_done へ移した後の参照）
- `/refactor_check`: `git diff 09f366f..HEAD -- keyseq/` で M1〜M6 判定

## 完了条件

- 上記確認・**reviewer 採用**（フェーズ完了判定のため `deep-reviewer` + `codex-adversarial-reviewer`）。
- 実機目視: 暫定 48 §7-7 ①② を 2026-10-21 ユーザーが OK と確認（本タスクの前提）。
