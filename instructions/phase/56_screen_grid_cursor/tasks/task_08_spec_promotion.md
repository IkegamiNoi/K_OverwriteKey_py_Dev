# task_08_spec_promotion

## 目的

phase 56 の最終タスク。暫定 40 v0.7 を正本 `instructions/common/spec_detail/` へ昇格して凍結し、判断履歴を集約し、フェーズの完了記載と `/refactor_check` を行う（`.claude/rules/task_execution.md`「フェーズ完了時」・暫定 40 §13）。
**文書作業（メインセッション）。コードは変えない（refactor_check の提案の実施はユーザー承認後・別タスク）。**

## 対象範囲

- 正本への昇格（暫定 40 §13 + task_07 で決めた挙動）:
  - `data_schema.md` §5.6「keymap」・§5.2 に `grid` の 1 行 + 新しい子 `data_schema/5_06_01_keymap_grid.md`（JSON・正規化・保存・4 経路・識別子・`label_position`）
  - `features.md` に新節 §4.7「画面の枠でカーソル移動・クリック」（表示の条件・世代・操作キー・suppress・クリック・枠の窓・ダイアログ・編集の窓・失敗時の扱い）+ §4.3・§4.5・§4.6 からの参照 1 行ずつ
  - `key_input.md` §7.3（振り分けの順序に枠の操作・予約キー・表に枠のキーを足さない注記）・§7.4（編集の窓のキーの取り込みの名前）
  - `nonfunctional.md`（座標系・DPI・Win32 の窓の扱い）
  - `codebase_map.md`（新規モジュールと既存の変更点）
- 暫定 40 の凍結（状態の行）と L7（§4.2「モニタの番号」→ 識別子と列挙時の矩形）・L3（細分化は OK で常に検査）を正本側で明記
- `phase.md` の L7（主入力の版数 v0.7・実機目視の対象に task_06b）
- `.claude_data/state/decisions_archive/56_screen_grid_cursor.md` の作成・`decisions.md` の phase 56 節を移し索引に 1 行
- `instructions/phase/current.md` の完了記載（次採番 = phase 57 / 暫定 41 / decisions 57 / 提案書 23〔22 は本フェーズの refactor_check で起票〕）
- `/refactor_check`（M1〜M6 のメトリクスは verifier・判定と提案書の起票はメイン）
- フェーズ完了判定前のレビュー（`deep-reviewer` + `codex-adversarial-reviewer`）
- 起票元 idea は無い（backlog の移動は不要）

## 含まない

- コードの変更（refactor_check の提案の実施は承認後に別タスク）
- idea_44・idea_45

## 確認

- 正本の各節が暫定 40 v0.7 と task_07 の決定に一致する（完了判定前レビューで確認）
- 暫定 40 の状態が「凍結」・正本からのリンクが切れていない

## 完了条件

- 上記がすべて済み、完了判定前レビューの採用分を反映・`/refactor_check` の判定を完了報告に記載
