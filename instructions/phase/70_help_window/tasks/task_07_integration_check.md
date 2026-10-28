# task_07_integration_check

## 目的

phase 70（ヘルプの作成・暫定 53 v0.6）の task_01〜06a を跨いだ統合確認。テストスイート全体・smoke の実測と、複数タスクを跨ぐ差分の二次レビュー
（`.claude/rules/agent_selection.md` のレビュー表「統合テスト」= `deep-reviewer` + `codex-reviewer`）。
**コードの変更は、レビューで採用した指摘の最小の修正だけ。**

## 対象範囲（検証とレビュー・指摘の修正）

- verifier: `compileall` / `unittest discover -s tests` / `unittest discover -s tests_ui`（1 本だけ・並列にしない）/ `-m tests.smoke_app`
  （task_06a の完了時点 6e0badf で全 pass 済み。修正が入った場合に再実測する）
- `deep-reviewer`: phase 70 の全差分（`git diff 4a5b202..HEAD -- keyseq tests tests_ui`）を暫定 53 v0.6 に照らして（5 観点 + 前提・未定義挙動・矛盾・正本整合・代替案）
- `codex-reviewer`: 同じ範囲の標準レビュー
- 持ち越しの確認事項: (1) task_04 の参考 = 空の大分類を開ける分岐 `_category_visible` の要否（本文が入った今）/ (2) task_05 の参考 = 読み取り専用 Text での Ctrl+C（task_08 の実機目視へ回すかを決める）
- 採用した指摘の修正（実装は既定の実装エージェント・数行ならメイン）

## 読むファイル

- `instructions/history/53_help_window.md`（v0.6 全体）・`instructions/phase/70_help_window/phase.md`

## 含まない

- 正本 `spec_detail/`・`ui_terms.md` A22・`codebase_map.md` への昇格・暫定 53 の凍結・decisions_archive・`/refactor_check`・実機目視（task_08）

## 確認

- 上記 4 コマンドが全 pass（修正が入った場合）
- `deep-reviewer` と `codex-reviewer` の指摘を採否（ユーザー判断）で整理し、採用分を修正して再実測

## 完了条件

- 確認 pass・二次レビューの採用分を反映・**reviewer の採用**（統合確認では deep-reviewer の結論を以て代える）
- 実機目視は task_08 でまとめて実施

## 結果（2026-10-28）

- 二次レビュー: deep-reviewer = 修正して完了可（中 1・低 10）/ codex-reviewer = P2 × 1（deep の 1 と同じ）
- **採否（ユーザー判断 2026-10-28・推奨どおり）**:
  - 採用・今直す: 1（コピーに隠れた文字）/ 2（`_category_visible` の空の大分類の分岐を削除）/ 5（選択の色をハイライトより上に）/ 6（空白だけの入力 = 空と同じ）/ 7（`HelpWindow.apply_topmost` の握りつぶしを外す）
  - task_08: 3（フック ON での Ctrl+C・右クリック「コピー」を実機目視へ）/ 4（見出しのダブルクリックを目視・気になれば直す）/ 8（正本は 14 件・BSD 3 条項で書く）/ 10（正本の残存リスクに 1 行）
  - 保留: 9（終了時のテストの前提）/ 除外: 11

### 修正の内容（今直す 5 件）

1. `keyseq/presentation/help/help_tab_view.py` `_copy`: 選択範囲のうち表示中の文字だけをコピーする（Tk の `get -displaychars`）。
2. 同 `_category_visible`: 空の大分類を開く分岐（`not category.items and category.id in self._open`）を削除。その分岐だけを確かめる tests_ui のケースを削除する。
5. 同 `_build_text`: `sel` タグを `highlight` より上へ（`tag_raise("sel")`）。
6. `keyseq/presentation/help/help_window.py`: 件数の表示・自動で開く等の「入力が空でない」の判定を、検索語（`parse_query` の結果）が空でないかで行う（空白だけ = 空と同じ）。
7. 同 `apply_topmost`: `except Exception: pass` を外す（呼び出し元の `app.py` がログ付きで捕捉している）。

### 修正後の確認

- 実装: メイン（数行）。テスト追加 = 空白だけの入力 / コピーで閉じた・絞り込みで隠れた文字が入らない（クリップボードは差し替え）。
- reviewer = 採用。参考の `tag_raise("sel")` の位置（本文を作った後へ）を反映。
- 全体: compileall clean / tests 1856（skip 7）/ tests_ui 1197 / smoke OK。位置の移動後にヘルプ関連 43 件を再実行して pass。
- 完了: 統合確認 pass・二次レビューの採用分を反映済み。
