# task_07_spec_promotion

## 目的

phase 57 の最終タスク。暫定 41 v0.4 を正本 `instructions/common/spec_detail/` へ昇格して凍結し、判断履歴を集約し、フェーズの完了記載と `/refactor_check` を行う（`.claude/rules/task_execution.md`「フェーズ完了時」・暫定 41 §11）。
**文書作業（メインセッション）。コードは変えない（refactor_check の提案の実施はユーザー承認後・別タスク）。**

## 対象範囲

- 正本への昇格（暫定 41 §4〜§8 + task_06 で決めた受容事項）:
  - `features.md` §4.7: 用語（クリック点・操作・操作キー・固定の操作キー）/ キーの意味の表（操作で書き直し・矢印）/ 優先順位・Shift・何もしない場合 / suppress する集合（実効の集合）/ キーリピート / クリック点の移動 / 枠の窓の十字 / 編集の窓のパネルの操作キーの欄・Esc の順・ドラッグ中の十字（色 = 枠の線の色）/ OK の検査 / 自動割当・振り直し / 受容（手編集で操作キーが矢印と重なる・別名は効かない・0px の枠）/ スコープ外
  - `data_schema/5_06_01_keymap_grid.md`: `ops`（正規化・保存・`ops_of`・取り込み）・読込時の固定の予約キー = 修飾キーだけ・受容（保存し直していない手編集）
  - `key_input.md` §7.3: 枠の振り分けの優先順位（枠のキー > 操作キー）・フックが見るのは `suppress_keys` 1 本（深さ ≥1 の印は廃止）・固定の予約キーの変更・操作キーの OK の検査
  - `codebase_map.md`「画面の枠」節（deep-reviewer 指摘 7 の一覧）
- 暫定 41 の凍結（状態の行）
- `.claude_data/state/decisions_archive/57_grid_crosshair_nudge.md` の作成・`decisions.md` の phase 57 節を移し索引に 1 行
- `instructions/phase/current.md` の完了記載（次採番 = phase 58 / 暫定 42 / decisions 58 / 提案書は refactor_check の結果で決まる）
- `/refactor_check`（M1〜M6 のメトリクスは verifier・判定と提案書の起票はメイン）
- フェーズ完了判定前のレビュー（`deep-reviewer` + `codex-adversarial-reviewer`）
- 起票元 idea は無い（backlog の移動は不要）

## 含まない

- コードの変更（refactor_check の提案の実施は承認後に別タスク）

## 確認

- 正本の各節が暫定 41 v0.4 と task_06 の決定に一致する（完了判定前レビューで確認）
- 暫定 41 の状態が「凍結」・正本からのリンクが切れていない

## 完了条件

- 上記がすべて済み、完了判定前レビューの採用分を反映・`/refactor_check` の判定を完了報告に記載
