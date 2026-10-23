# task_08_visual_check_and_promotion

## 目的

実機目視（暫定 51 §6-6）と正本反映（§8）を行い、暫定 51 を凍結してフェーズを閉じる（`.claude/rules/task_execution.md`「フェーズ完了時」）。
**文書作業（正本 `spec_detail/`・`codebase_map.md`・状態ファイル）。コードは実機目視で見つかった不具合の最小修正だけ。**

## 対象範囲

### 1. 実機目視（ユーザー）

確認点（ユーザーへ提示して結果を受け取る）:
1. 詳細表示 / 簡易表示: ボタンの「…」（追加… / キーマップ編集… / トリガー編集… / 編集… / 別名保存… / 読込…）が固定幅（file_frame 18・sequence_box 16・preset_manager 14）で切れていない・「簡易表示」「詳細表示」「最前面に表示」「選んでから実行」「停止キー: 」
2. メニュー: ファイル（別名保存… / サンプル設定に戻す）・設定（参照元を掃除 / 未使用ファイルの整理… / 退避したファイルの管理…）
3. はい / いいえ の確認を替えた 3 ダイアログ（同名ファイルの上書き確認・保存先を計算し直した確認・既定の保存先の外に保存する確認）: ボタン名・Enter / Tab / Esc / ×・本文が切れない（wraplength 560）
4. アクションのダイアログ（file_line の範囲外「何も送らない」・プリセットの枠名）・一覧の書式（`[スクロール] 下3`・`（リピート）`）
5. 未使用ファイルの整理・退避したファイルの管理の題と結果の文
6. キーボードUI の題・画面の枠の編集（キーを振り直す・絞り込む）

### 2. 正本反映（暫定 51 §8 + 統合レビュー 中 2 の確認リスト）

- **用語表の置き場所**: 推奨 = 新ファイル `spec_detail/ui_terms.md`（§2 の表 A1〜A21・§2.2・§3 の規則）。**ユーザー確認のうえ作成**
- UI ラベルの引用の追従（旧ラベルは正本全体を再検索して漏れを拾う）。最低限:
  - A19「別名で保存」: `features.md:453・928-930`・`data_schema/5_08_07_individual_save.md:3`・`codebase_map.md:608`
  - **Q5 の保存値の規定**: `data_schema.md:784`「旧トリガー一覧（<stem>）」→「旧トリガーセット（<stem>）」（今後作る値だけ・保存済みは不変）・`codebase_map.md:953`
  - D11: `features.md:668-669`「Keyboard UI — …」
  - A12: `features.md:830`「OSショートカット（プリセット）」・`data_schema/5_10_04_constraints.md:38`
  - D3: `features.md:932`・`codebase_map.md:625`「参照元を掃除…」/ `features.md:942`「復元する…」「削除する…」
  - C11: `features.md:1155-1156`「振り直し」/ C10: `features.md` §4.7 の「深くする」・`key_input.md:44`
  - C14「確認して実行」: `features.md` §4.2.11 の節名・本文・:120・:321・:446・:528・:1059-1064・`data_schema.md:82・263・330`
  - C3: `features.md:822`「空を送る」/ C15: `data_schema/5_08_05_confirm_dialog.md:17`・`features.md`「モーダルダイアログの作法」の入力先
  - A13「例を復元」: `data_schema/5_08_01_parent_refs.md:32`・`5_08_06_dependency_index.md:7`・`5_08_08_runtime_entry_points.md:5・13`
  - A8「トリガー一覧を保存」: `data_schema.md:273`・`data_schema/5_08_07_individual_save.md:5`・共有状況「別の構成」: `5_08_05_confirm_dialog.md:11`
  - A5・A6・A20: `features.md:6`・`key_input.md:25`「停止トリガー」・「直接切替」（spec_detail・codebase_map の 5 ファイル・UI ラベルの引用か地の文かを判定）
  - A16〜A18: `features.md`・`data_schema.md`・`5_08_01_parent_refs.md`・`5_08_09_orphan_sweep.md`・`5_10_01_data_model.md`・`5_10_04_constraints.md:30`・`codebase_map.md`
  - 一覧の書式（D5・D1）: phase 67 で正本に書いた `[スクロール] 下 3` 等の書式・D 項で表記が変わる引用（`features.md:475・616` ほか）
  - `codebase_map.md`: 新モジュール `config_io/choice_dialog.py` の追記・`hook_frame` の引用（:606）
- 地の文の「省略表示」「フル表示」「keymap」等を UI 用語に揃えるかは、ユーザー確認のうえ決める（推奨: UI ラベルの引用だけ揃え、地の文は据え置き）

### 3. 凍結・記録

- 暫定 51 を凍結（ヘッダ書き換え・§5 の「残る手順」の更新・統合レビュー 低 10〔§3.2 A13 の行番号の注記〕）
- `.claude_data/state/decisions_archive/68_ui_terminology.md`・decisions.md の索引行
- `instructions/phase/current.md` の完了記載（次採番の明記）
- `/refactor_check`（メトリクスは verifier）
- 完了判定前レビュー: `deep-reviewer` + `codex-adversarial-reviewer`

## 読むファイル

1. `instructions/history/51_ui_terminology.md` §6・§8
2. 正本の該当節（上の確認リストの行の周辺だけ）
3. 前フェーズの完了記載の形: `instructions/phase/current.md`・`.claude_data/state/decisions_archive/67_mouse_scroll_action.md`

## 含まない

- 多言語化・ヘルプ・Mac 対応・B 項（内部名の表示名化）

## 確認

- 実機目視 6 項目の結果（ユーザー報告）
- 正本で旧ラベル（暫定 51 §2 のやめる語）を再検索し、残るものは地の文として据え置く理由を報告
- verifier: compileall / tests / tests_ui / smoke（コード修正があった場合）・refactor_check のメトリクス

## 完了条件

- 実機目視 OK・正本反映・凍結・記録・refactor_check・完了判定前レビュー 2 本の反映。
