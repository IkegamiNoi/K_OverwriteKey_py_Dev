# task_06_finalize_records

## 目的

Phase α（task_01〜05）で確定した挙動を**正本へ昇格**し、暫定仕様 04 を凍結して記録類を整える。
フェーズ完了判定を行う最終タスク。

- 根拠: 暫定仕様 [04](../../../history/04_keymap_set_new_and_default_dir.md) **§10 正本反映** /
  `.claude/rules/task_execution.md`「フェーズ完了時」/ `.claude/rules/spec_change_workflow.md`（昇格 + 凍結）。
- **文書作業のみ**。`keyseq/` 配下・テストは**一切変更しない**（`/refactor_check` が提案書を起票する場合も
  実施はユーザー承認後）。
- 担当: **メインセッション**（`agent_selection.md`「フェーズ末の正本反映タスクはメインが直接行ってよい」）。

## 対象範囲（文書のみ）

### 1. 正本 `instructions/common/spec_detail/data_schema.md`

- **§5.5 split 読込**: `config/config.json` の `keymap_set_path` について、**空になる 3 経路**
  （新規作成 / Import 成功 / 起動時に stored セット不在）と、**空のときの保存は別名保存**になることを追記。
  あわせて**既定の保存先はディレクトリ `config/user/keymap_sets/`**（固定 `default.json` ではない）ことと、
  別名保存の初期ファイル名 `keymap_set.json` を明記する。
- **§5.6 個別JSON（`:65`）**: 「trigger_set の新規保存ファイル名は現在の keymap_set ファイル名由来にする」に
  **keymap_set が未設定（空パス）時のフォールバック = `trigger_set.json`** を追記する
  （**deep-reviewer 指摘1**。現状の実装が正本未定義だった箇所）。
- **`prompt_if_missing`**: 正本に記述は**無い**（grep 0 件）ため削除対象なし。§5.1「未定義キーは無視する」で
  既存値の残置は説明済み → **追記しない**（撤去したキーを正本へ書き足さない）。

### 2. 正本 `instructions/common/codebase_map.md`

- **App**（`:101` 付近）: 起動時に**設定ディレクトリ骨格を一括作成**する（`config/user/{keymap_sets,keymaps,
  trigger_sets,hotkey_presets,sequences}`）こと、**config.json は起動時に書かない**（初回保存時に作成）ことを追記。
- **KeymapSetIo**（`:128`）: 「新規作成 = 空パス / 保存は空パスなら別名保存へ分岐 / Import 成功時は無条件で空」を追記。
- **StartupIo**（`:129`）: 「起動時 stored セットが読めない場合は無言で空データ起動し `keymap_set_path` を空にする」を追記。
- **指摘7（参考・1 行）**: 保存のたびに `config.json` の `keymap_set_path` が保存先へ更新される既存挙動を
  補足する（Phase β の判断材料。**挙動変更はしない**）。

### 3. 暫定仕様 04 の凍結

`instructions/history/04_keymap_set_new_and_default_dir.md` 冒頭の状態行を
**「凍結（正本へ昇格済・phase 05 完了 2026-07-28）」**へ更新し、昇格先（`data_schema.md` §5.5・§5.6 /
`codebase_map.md`）を明記する。**本文の設計記述は改変しない**（凍結 = 履歴として保存）。

### 4. 記録類

- `.claude_data/state/decisions_archive/05_keymap_set_new_and_default_dir.md` を新規作成
  （既存アーカイブの書式に合わせる。task_01〜06 の判断・deep-reviewer 指摘 1〜7 の処遇・
  実機目視結果・`/refactor_check` 判定を集約）。
- `.claude_data/state/decisions.md`: 「アーカイブ索引」へ 1 行追加し、本体の
  **「## 2026-07-28 (phase 05 …)」節はアーカイブへ移して削除**する。
- `instructions/phase/current.md`: 「現在の参照先」から phase 05 の項を**完了フェーズの 1 行要約 + アーカイブ
  リンク**へ差し替え、旧フェーズの要約行を整理する（直近 3 件まで）。次採番（phase `06_<topic>` /
  暫定仕様 `08_<topic>`）を確認・更新する。
- `instructions/backlog/INDEX.md`: **起票元 idea は無い**（ユーザー要望起票）ため `INDEX_done.md` への移動対象なし。
  本フェーズで新規起票した [idea_09](../../../backlog/idea_09_legacy_settings_save_path_fallback.md) は
  **未着手のまま INDEX に残す**（移動しない）。

### 5. `/refactor_check`

`.claude/commands/refactor_check.md` に従って実行する。**メトリクス収集（手順 1〜2・M1〜M6）は `verifier` へ委任**し、
判定と（必要なら）提案書起票はメインが行う。判定結果は完了報告と `decisions_archive/05` に記載する。

## 含まない

- `keyseq/` 配下・`tests/` `tests_ui/` の変更（**本タスクは文書のみ**）。
- [idea_09](../../../backlog/idea_09_legacy_settings_save_path_fallback.md) の実装
  （レガシー `settings/` 配下の `default.json` フォールバック。ユーザー判断で後続フェーズ送り）。
- deep-reviewer 指摘3（`app.py:64` の初期化と `config_paths.resolve_keymap_set_path` の引数なし分岐が
  実質デッド）/ 指摘4（`DEFAULT_KEYMAP_SET_FILENAME` を ConfigPaths へ寄せる代替案）/ 指摘6（`app_module.os.makedirs`
  patch と実装のずれ）→ いずれも**記録のみ**。修正が要ると判断したら `/refactor_check` の提案書または idea として
  起票し、実施はユーザー承認後。
- Phase β/γ/プリセットの起票（`/phase_start`）。
- `/refactor_check` が「要」と判定した場合のリファクタ実施（提案書起票まで）。

## 確認

1. `data_schema.md` / `codebase_map.md` の追記が**実装と一致**していること（該当コードを読んで確認）。
2. `grep -rn "prompt_if_missing" instructions/common/` — 正本に記述が無いこと（追記していないこと）。
3. 暫定仕様 04 の状態行が「凍結」になっていること。
4. `decisions.md` 本体に phase 05 節が残っていないこと（索引 1 行 + アーカイブへ移動済）。
5. `current.md` の「現在の参照先」と次採番が更新されていること。
6. `/refactor_check` を実行し、判定結果（要 / 不要 + 根拠）を報告に含めること。
7. **コード差分ゼロ**: `git diff --stat` に `keyseq/` `tests/` `tests_ui/` が含まれないこと。

## 完了条件

- 上記確認 1〜7 が pass。
- レビュー: **フェーズ完了判定のため `deep-reviewer` + `codex-adversarial-reviewer` を併用**する
  （`.claude/rules/agent_selection.md` のレビュー表）。観点は「正本と実装の整合」「昇格漏れ」
  「記録類の整合（採番・リンク・索引）」。
- 実機目視は **task_05 で完了済**（本タスクでは不要）。
- 完了後、`instructions/phase/current.md` の更新をもって **Phase α 完了**とする。
