# task_02_canonical_reflection

## 目的

phase 49 の確定事項（phase.md「確定」1〜4）を正本へ反映し、phase 49 を閉じる（`.claude/rules/task_execution.md`「フェーズ完了時」）。**文書作業のみ（メイン）・コード不変**。

## 対象範囲

- 正本 `features.md`: §4.5 に「ステータスの見切れのツールチップ」（対象・見切れているときだけ・1 行化前の改行入りの全文・表示中の追従・出し方と閉じ方）を追記 /
  §4.6「省略表示のウィンドウ」の「ステータスの行数の固定」に「欄は 1 行化・ツールチップだけ改行入りの元の文言」を明記（矛盾に読めないように）
- `codebase_map.md`: task_01 で更新済み（確認のみ）
- フェーズ完了判定前レビュー（deep-reviewer + codex-adversarial-reviewer）と指摘の対応
- `decisions_archive/49_status_truncation_tooltip.md` / decisions.md のアーカイブ索引 / current.md の完了記載（次採番）/ idea_40 を `backlog/INDEX_done.md` へ移動 / `/refactor_check`

## 読むファイル

- phase.md（確定 1〜4・task_01 の完了記載）
- 正本 `features.md` §4.5（:386-395）・§4.6「省略表示のウィンドウ」（:470-484）

## 含まない

- コードの変更（レビューで修正が要る場合は枝番タスクを起票する）

## 確認

- 正本が確定 1〜4 を漏れなく含み、§4.6 の「ステータスの行数の固定」と矛盾に読めない

## 完了条件

- 上記をすべて実施し、レビュー 2 種の結果と `/refactor_check` の判定を完了報告に含める（文書のみのため reviewer は deep-reviewer で代える）。
- 実機目視: なし（task_01 で実施済み・2026-10-07 ユーザー OK）。
