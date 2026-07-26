# task_06_finalize_records

## 目的

phase 04（ConfigIoController 分割）の**正本反映・記録**を行い、フェーズを完了させる。
実装（分割・差し替え）は task_05 までで完了しており、本タスクは**文書作業のみ**（メインセッションが担当）。

- 前提ゲート: **実機目視のユーザー OK**（保存 / 読込 / 別名保存 / Import / Export / 起動時に読む構成セット指定 /
  keymap・トリガー一覧・出力シーケンスの個別保存読込）。→ **2026-07-26 ユーザー OK 取得済**。
- コード変更は行わない（挙動不変フェーズの最終タスク）。

## 対象と手順

1. **`codebase_map.md` の更新**（暫定仕様 §8）:
   - presentation ツリー図の `controllers/config_io_controller.py` を `controllers/config_io/`（6 ファイル）へ差し替え。
   - 「コントローラ（controllers/）」節の `ConfigIoController` 行を 6 クラス
     （KeymapSetIo/StartupIo/IoDialogs/KeymapFileIo/TriggerSetFileIo/SequenceFileIo）+ App 公開名へ差し替え。
   - App 責務の `config_io.write_startup` → `startup_io.write_startup`。`app.<名>` 例 → `app.keymap_set_io`。
2. **spec_detail への昇格要否判定**: `spec_detail/` に `ConfigIo` / `config_io` の言及があるか再 grep →
   **0 件なら昇格不要**（担当層は `architecture.md §3.5` により `codebase_map.md` が正）。
3. **暫定仕様 03 の凍結**: ヘッダ状態を「凍結・正本反映済」へ更新（以後編集しない）。
4. **`decisions_archive/04_config_io_controller_split.md` を作成**し、`decisions.md` の phase 04 セクションを集約・
   索引化（アーカイブ索引に 1 行追加 + 詳細セクション削除）。
5. **`current.md` の更新**: アクティブフェーズを完了扱いにし、次採番（phase 05 / 暫定 04）を明記。
6. **`/refactor_check` の実行**（変更ファイル対象・M1〜M6。挙動不変フェーズだが判定を出す）。
   判定結果を `decisions_archive/04` と完了報告に記載。
7. 起票元は idea 由来ではない（`current.md`「別タスク化候補」の 598 行項目）ため、**INDEX 移動は不要**。

## 含まない

- コード変更（分割・差し替えは task_05 で完了済）。
- spec_detail の本文更新（昇格不要の見込み。手順 2 で再確認）。
- idea_05 / idea_06 の着手（phase 04 完了後の別フェーズ）。

## 確認

- `codebase_map.md` / 暫定仕様 03 / decisions.md / decisions_archive/04 / current.md の記述が実構成
  （config_io/ 6 クラス・app 公開名）と一致すること。
- フェーズ完了判定前の退行確認（verifier）: compile clean / tests 86 / tests_ui 74 / smoke pass /
  旧ファサード参照 0 件。
- 別視点レビュー（reviewer）: 文書と実装の整合・記録の過不足。

## 完了条件

- 手順 1〜7 をすべて実施。`/refactor_check` 判定を完了報告に含める。
- reviewer 採用。フェーズを完了扱いにできる状態（次採番が明記されている）。
