# task_06_spec_promotion

## 目的

phase 58 の最終タスク。暫定 42 v0.3 を正本 `instructions/common/spec_detail/` へ昇格して凍結し、判断履歴を集約し、フェーズの完了記載と `/refactor_check` を行う（`.claude/rules/task_execution.md`「フェーズ完了時」・暫定 42 §11）。
**文書作業（メインセッション）。コードは変えない（refactor_check の提案の実施はユーザー承認後・別タスク）。**

## 対象範囲

- 正本への昇格（暫定 42 §3〜§5 + decisions phase 58 の task_04・task_05 の決定）:
  - `features.md` §4.5: ステータス欄のフックの 3 状態とキーマップは名前だけ（一時メッセージは名前 + 状態のまま）
  - `features.md` §4.6「フル表示の幅配分」: 最小幅にスクロールバーの幅 / 最小の高さの式（H・ceil(H/2)）と「何も切れない」→「スクロールで届く」/ フル表示へ戻るときに最小の大きさを解除してから復元
  - `features.md` §4.6 に新しい小節「フル表示の 3 枠のスクロール（phase 58）」（構造・中身の窓の高さ・測り直しの契機〔Canvas と中身の Frame の `<Configure>` 各 1 つ = 指摘 3〕・出すのは収まらない枠だけ・隠すとき先頭へ・ホイール・Tab の自動スクロールなし・位置は保存しない）
  - `features.md` §4.6「省略表示のウィンドウ」の最小の高さ（開いている上部の枠だけ数える・開閉で測り直す）と新しい小節「省略表示の上部の開閉（phase 58）」
  - `features.md` §4.6「確認して実行のチェック」のフォント +3 の受容の記述を phase 58 で解消した旨へ
  - `data_schema.md` §5.4: `compact_header_view`（検証・書き込み契機・両方書く・未知のキーは保持しない）と config.json が作られる契機
- `codebase_map.md`: `views/full_view/scroll_area.py`・`controllers/compact_header_controller.py`・`presentation/compact_header_view.py`・`get_active_keymap_name`・ステータスの書式・`pane_measure` の測り方
- 暫定 42 の凍結（状態の行）
- `.claude_data/state/decisions_archive/58_window_size_fit.md` の作成・`decisions.md` の phase 58 節を移し索引に 1 行
- `instructions/phase/current.md` の完了記載（次採番 = phase 59 / 暫定 43 / decisions 59 / 提案書は refactor_check の結果で決まる）・handoff の既知の問題「フル表示の高さ（phase 50）」の解消
- `/refactor_check`（M1〜M6 のメトリクスは verifier・判定と提案書の起票はメイン）
- フェーズ完了判定前のレビュー（`deep-reviewer` + `codex-adversarial-reviewer`）
- 起票元 idea は無い（backlog の移動は不要）

## 含まない

- コードの変更（refactor_check の提案の実施は承認後に別タスク）

## 確認

- 正本の各節が暫定 42 v0.3 と decisions phase 58 の決定に一致する（完了判定前レビューで確認）
- 暫定 42 の状態が「凍結」・正本からのリンクが切れていない

## 完了条件

- 上記がすべて済み、完了判定前レビューの採用分を反映・`/refactor_check` の判定を完了報告に記載
