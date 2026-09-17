# task_04_promote_to_spec

## 目的

phase 20 の最終タスク。暫定仕様 18（v0.5）と task_03b の修正内容を正本へ昇格し、暫定仕様を凍結してフェーズを完了する
（`.claude/rules/task_execution.md`「フェーズ完了時」・暫定 §7）。**文書作業のみ・コード不変**（`agent_selection.md` によりメインが直接行う）。

## 対象範囲（文書のみ）

### 正本 `instructions/common/spec_detail/features.md` §4.6「フル表示の幅配分」

- 「最小幅」項の「高さは制約しない。」を削り、新しい項「**最小の高さ**」を追加（暫定 §2・§3-1〜§3-5 の要点 + task_03b）:
  一覧の既定の行数（6 / 6 / 9）が基準 / 最小の高さ = フル表示中のウィンドウの要求高さ（一時メッセージは 1 行分）/ 測る契機（幅と同じ）と順序
  （両端の幅の適用後・**フル表示へ戻るときは表示内容の更新をすべて済ませてから**〔deep-reviewer 指摘 5〕）/ ドラッグ後も保つ /
  最小未満なら最小まで広げ、**広げた高さは後で最小が下がっても縮めない**（task_03b）/ 最大化中は触らない / 画面超過ははみ出し受容 / 複数行の一時メッセージの切れは受容 / 保存しない。
- 「省略表示との関係」に高さの解除を追記。節番号・見出しは変えない。`data_schema.md` は変更なし（暫定 §7）。

### `instructions/common/codebase_map.md`

- `pane_layout_controller.py` / `pane_measure.py` のツリー注記、PaneLayoutController 節（`window_min_height`・`apply_layout` の測定と geometry・ドラッグ後の minsize）、
  FullView 節（一覧の `height` = 最小の高さの基準）、App の View 切替（`show_full_view` は表示内容の更新後に `on_full_view_shown`）。

### 凍結・記録

- `instructions/history/18_full_view_min_height.md`: ヘッダを「凍結済・v0.5」へ（phase 19 の暫定 17 と同じ書式）。
- `.claude_data/state/decisions_archive/20_full_view_min_height.md` を新規作成し、`decisions.md` の phase 20 節を移して「アーカイブ索引」へ 1 行追加。
- `instructions/phase/current.md`: 「現在の参照先」を完了状態へ（アクティブなし / 直近の領域の数行更新 / 直前の完了フェーズ = 20）・次採番（phase 21 / 暫定 19 / decisions 21）。
- `instructions/backlog/INDEX.md` の idea_22 行を完了にして `INDEX_done.md` へ移動。
- `/refactor_check` を実行し判定を完了報告に含める（メトリクス収集は `verifier`）。

## 読むファイル

1. `instructions/history/18_full_view_min_height.md`（§2・§3・§7）/ `instructions/phase/20_full_view_min_height/integration_result.md`
2. `features.md` §4.6「フル表示の幅配分」/ `codebase_map.md` の該当行（`rg -n`）
3. 書式の手本: `decisions_archive/19_full_view_header_width.md` / `INDEX_done.md` の idea_21 行 / `history/17_full_view_header_width.md` のヘッダ

## 含まない

- コードの変更（refactor_check が推奨を出しても、実施はユーザー承認後の別タスク）。
- 指摘 4（保留）の対応。

## 確認

- 正本の記述が実装（`pane_layout_controller.py` の `apply_layout` / `pane_measure.py` / `app.py` の `show_full_view`）と一致（`rg` で裏取り）。
- 暫定 18 の §5 受け入れ条件がすべて integration_result / テストで満たされている。
- リンク切れなし（新規・移動した行の相対パス）。
- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`（採否はユーザー）。

## 完了条件

- 上記確認・`/refactor_check` 実施・**reviewer 採用**（完了判定前レビューの採否反映後）。
- 実機目視は task_03 で実施済み。
