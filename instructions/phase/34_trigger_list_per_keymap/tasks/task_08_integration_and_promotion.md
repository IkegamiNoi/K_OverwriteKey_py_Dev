# task_08_integration_and_promotion

## 目的

phase 34 の統合確認と正本反映（フェーズ最終タスク・`.claude/rules/task_execution.md`「フェーズ完了時」）。
暫定仕様 25（v0.5）を正本 `instructions/common/spec_detail/` へ昇格して凍結し、記録を整えてフェーズを完了する。

## 対象範囲

1. **統合レビュー**（phase 34 の全差分・base = `b27336e`）: `deep-reviewer` + `codex-reviewer`。指摘は採否をユーザー確認のうえ反映。
   持ち越し 4 件（`config_service/__init__.py` の肥大 / `parent_refs_cleanup.py` 318 行 / 実行位置の `id(triggers)` キャッシュ /
   個別キーマップ保存経路の正規化の非対称）を統合レビューの観点に含める。
2. **正本反映**（暫定 25 §12 の対象・メインが文書作業として行う）:
   - `data_schema.md`: §5.1 / §5.2 / §5.4 / §5.5 / §5.6（keymap の `trigger_set_path`・`id` を書く・既定名・trigger_set 既定名）と
     子ファイル 5_08_01〜5_08_09 の該当節（親 = keymap・移行時の後処理の例外・runtime 内部キー・source なし子・除外撤廃と帰結・行の表示・依存 3 段・個別保存・入口台帳・参照辿り 3 段と keymap_set 判別）。
   - `key_input.md` §7（優先順位・重複規則・停止 / トグルとの重なりの扱い）。
   - `features.md`（キーマップ管理・トリガー一覧・連続実行中の切替禁止・一時停止の表示・一時メッセージの表示先）。
   - `codebase_map.md`（runtime データ形・`domain/keymap_triggers.py`・`application/key_overlap.py`・trigger_set の未保存管理・参照辿り 3 段・個別保存計画）。
   - 暫定 25 のヘッダを「凍結（2026-09-26・正本反映済）」へ。
3. **記録**: `.claude_data/state/decisions_archive/34_trigger_list_per_keymap.md`（decisions.md 末尾の phase 34 節を集約）+ decisions.md のアーカイブ索引 1 行・本文から phase 34 節を削除 /
   `instructions/phase/current.md`（アクティブ = なし・直前の完了フェーズ・直近の領域・次採番 35 / 26）。起票元 idea は無し（idea_36 は関連のみ・未着手のまま）。
4. **`/refactor_check`**（メトリクス収集は `verifier`・判定と提案書起票はメイン）。
5. **フェーズ完了判定前レビュー**: `deep-reviewer` + `codex-adversarial-reviewer`。

## 確認

- 正本反映後も `..\..\..\.venv\Scripts\python.exe -m unittest discover -s tests` / `tests_ui` / `tests.smoke_app` が pass（文書のみの変更だがコード修正が入った場合）。
- 暫定 25 §10 の受け入れ条件 1〜26 が満たされていることの対応表（統合レビューで確認）。

## 完了条件

- 上記すべて実施・フェーズ完了判定前レビューの指摘に対応・ユーザーの完了承認。

## 結果（2026-09-27・完了）

- 途中の改訂で暫定 25 は v0.7・受け入れ条件は 1〜37 に拡張（task_07c〜07e）。凍結日は 2026-09-27。
- 統合レビュー → task_07c / 07d、完了判定前レビュー → task_07e で対応。実機目視 OK（ユーザー 2026-09-27）。
- `/refactor_check` = 推奨 → 提案書 13 → task_09 で実施済。最終実測 `tests` 669（skip 7）/ `tests_ui` 576 / smoke OK。
