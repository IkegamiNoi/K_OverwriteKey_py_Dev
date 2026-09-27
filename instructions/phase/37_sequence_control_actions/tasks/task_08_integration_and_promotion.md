# task_08_integration_and_promotion

## 目的

phase 37 の統合確認と正本反映（フェーズ最終タスク・`.claude/rules/task_execution.md`「フェーズ完了時」）。
暫定仕様 26（v0.5）を正本 `instructions/common/spec_detail/` へ昇格して凍結し、記録を整えてフェーズを完了する。

## 対象範囲

1. **統合レビュー**（phase 37 の全差分・base = `3dc6ee8`）: `deep-reviewer` + Codex 標準レビュー（Luna xhigh〔プラグイン〕と Sol medium〔`codex review -c` 直接〕の比較つき）
   → 指摘は task_07b（と実機目視の指摘 → task_07c / 07d）で対応済み。
2. **フェーズ完了判定前レビュー**: `deep-reviewer` + `codex-adversarial-reviewer`（config 既定 = Sol medium）。指摘は採否をユーザー確認のうえ反映。
3. **正本反映**（暫定 26 §16 の対象・メインが文書作業として行う）:
   - `data_schema.md` §5.11（種別の表へ system / file_line・§3 のキー・file_line の行の規定・実行時エラー）/ §5.11.5（旧ビルドの扱い）。
   - `features.md` §4.2（実行モデル: ステップ・先行処理とカウンターの保留・ループ・カウンター・待機・戻す / 先頭へ・単独登録）/ §4.6「一覧の表示形式」（表示名・周回・カウンター値・色分け）と編集 UI（「末尾に追加」・ループの対・移動規則）。
   - `codebase_map.md`（新モジュール: `domain/sequence_control.py`・`domain/sequence_editing.py`・`application/sequence_steps.py`・`application/sequence_history.py`・
     `application/file_line_reader.py`・`presentation/dialogs/action_control_fields.py`・`presentation/controllers/action_list_rendering.py`・色値）。
   - 暫定 26 のヘッダを「凍結（2026-09-27・正本反映済）」へ。
4. **記録**: `.claude_data/state/decisions_archive/37_sequence_control_actions.md` + decisions.md のアーカイブ索引 1 行 /
   `instructions/phase/current.md`（アクティブ = なし・直前の完了フェーズ・直近の領域・次採番 38 / 27・別タスク化候補〔統合レビュー Low の L3・L4・L6・L8〜L11・L13・L14〕）。
   起票元 idea は無し（idea_37 は関連のみ・未着手のまま）。
5. **`/refactor_check`**（メトリクス収集は `verifier`・判定と提案書起票はメイン）。持ち越しの肥大: `trigger_panel_controller.py` 711 行・`action_dialog.py` 449 行・`sequence_runner.py` 347 行。

## 確認

- 正本反映後も `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `tests_ui` / `tests.smoke_app` が pass（コード修正が入った場合）。
- 暫定 26 §14 の受け入れ条件の対応表（完了判定前レビューで確認）。

## 完了条件

- 上記すべて実施・フェーズ完了判定前レビューの指摘に対応・ユーザーの完了承認（実機目視は task_07d 後に OK 済み・2026-09-27）。
