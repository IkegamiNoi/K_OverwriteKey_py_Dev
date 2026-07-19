# task_05_finalize_records

## 目的

フェーズ 03 の**正本反映・記録**（最終タスク）。実装は完了・実機目視 OK 済み。文書作業として
昇格判断・凍結・各記録を確定する（`.claude/rules/task_execution.md`「フェーズ完了時」チェックリスト）。
本タスクは**メインセッションが直接行う文書作業**（`.claude/rules/agent_selection.md`：正本反映タスクの例外）。

- 実装コード（`keyseq/`）は変更しない。ドキュメント / state ファイルのみ。

## 対象範囲（文書・state のみ）

1. **正本昇格判断**: `instructions/common/spec_detail/` に起動設定/フォントの担当層を規定する節があるか調査済
   → **昇格不要**（grep で `startup`/`font_delta`/`coerce` 該当ファイル 0 件。担当層は `architecture.md §3.5` により
   `codebase_map.md` が正。挙動不変ゆえ仕様変更なし）。spec_detail は更新しない。
2. **暫定仕様 02 の凍結**: `instructions/history/02_startup_font_settings_cleanup.md` の状態表記を
   「v1.0・主入力・未凍結」→「**v1.0・凍結（フェーズ 03 完了・正本は codebase_map.md）**」へ更新。
3. **`codebase_map.md` 更新**: 
   - presentation ツリーに `startup_settings.py`（起動設定ローダ）を追記。
   - App 責務: フォント差分の coerce と起動設定読込が App から外れたこと（`theme.coerce_font_delta` /
     `startup_settings.load_startup_settings`）、フォント適用が `_apply_font_delta` / `set_ui_font_delta` に分割されたことを反映。
   - `theme.py` に `coerce_font_delta`（フォント差分正規化の唯一点）を追記。
   - UiVars: `ui_font_delta_pt` を**コンストラクタ引数**で受け取る（App private 直読みを廃止）ことを反映。
4. **`decisions_archive/03_startup_font_settings_cleanup.md` 作成**: 判断履歴（設計確定5件・敵対的レビュー反映3件・
   テスト再編判断・昇格要否・refactor_check 判定・コミット一覧・検証/レビュー/実機目視結果）を集約。
5. **`decisions.md` 索引更新**: 「アーカイブ索引」表に 03 の 1 行を追加。
6. **`current.md` 更新**: 「現在の参照先」を 03 完了として整理（旧フェーズ要約行は削除）、直近完了フェーズに 03 を反映、
   次採番 `04_<topic>` を明記。
7. **`backlog/INDEX.md` → `INDEX_done.md`**: idea_02 の行を完了状態（対応フェーズ・判断リンク）に更新して INDEX_done へ移動。
8. **`/refactor_check` 実行**: メトリクス収集（M1〜M6）は `verifier` へ委任、判定はメイン。結果を完了報告に記載。

## 含まない

- 実装コードの変更。案B（FontSettingsController）の新設。idea_03 への着手。
- spec_detail の更新（上記1のとおり昇格不要）。

## 確認

- `git grep` / `grep` で昇格不要の裏取り（spec_detail に startup/font/coerce の担当層記述が無いこと）。
- 標準検証は task_04 で全緑確認済（本タスクはコード無変更のため再実行は任意）。
- リンク・節番号の整合（codebase_map / decisions_archive / INDEX_done のリンク切れなし）。
- `/refactor_check` の判定（要/不要）を完了報告と decisions_archive に記載。

## 完了条件

- 上記「対象範囲」1〜8 をすべて実施・**reviewer 採用**（文書整合の観点）。
- フェーズ 03 を完了扱いにできる状態（current.md 次採番明記・idea_02 クローズ・暫定仕様凍結）。
- 実機目視: 済（task_04 後・ユーザー OK 2026-07-20）。
