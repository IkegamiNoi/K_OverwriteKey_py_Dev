# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-28T08:00:00
phase: `instructions/phase/06_child_file_save_dialog`（保存系リデザイン **Phase β**）
last_commit_location: claude/phase-beta-bfbdd2 ※現在地はセッション開始時の git 実測値が正

## current
focus: **Phase β task_02（trigger_set の source_path 接続 + 既定命名の stem 基準化）完了。次は task_03（保存計画の型と application 側実行契約）の `/task_new` 起票**。
mode: implementing

## last_action
ts: 2026-07-28T08:00:00
who: main
summary: |
  【task_02（trigger_set_source_and_naming）完了】実装は `codex-implementer` へ委任。暫定仕様 05 §6・§7。
  - **idea_05 解消**: `trigger_set_file_io` の保存経路が読んでいた**存在しない App 属性**
    `_trigger_set_source_path` を `dirty_tracker.trigger_set_source_path` へ接続（2 箇所）。
    keymap / sequence と対称になり、source_path あり→直接上書き / なし→衝突ダイアログ。
    到達不能だった「読込で持ってきた…別名で保存しますか？」`askyesno` は **§7 どおり復活させず削除**。
  - **trigger_set 既定命名**: 固定 `TRIGGER_SET_RELATIVE_PATH`（`user/trigger_sets/default.json`）を廃止し、
    `TRIGGER_SETS_RELATIVE_DIR` + 新規 `_default_trigger_set_path()`（**keymap_set の stem 基準**・
    空 stem は `"default"`）へ。`split_base_dir`（構成セット周辺保存）経路も同様にした
    （§6 本文は config_root 内が対象だが、同一フォルダ複数セットで同じ衝突が起きるため趣旨に合わせた。reviewer 承認）。
  - **後方互換**: 既定 keymap_set（`default.json`）なら stem = `default` で保存先は従来どおり。
    `SaveLoadRoundTripTest::test_round_trip_preserves_content` は**書き換えずに pass**。
    読込側・keymap_set 索引・`_is_default_trigger_set_area`（→ sequences は `user/sequences/` のまま）は無変更。
  - `hotkey_presets` / keymaps / sequences の命名は不変（指摘④「trigger_set のみ変更」を遵守）。
  - `dirty_tracker.trigger_set_imported` は**唯一の読み手が消えたが撤去せず残置**（task_05 で使うか判断 →
    使わなければ task_07 の `/refactor_check` で撤去可否を判定）。
result_files:
  - keyseq/application/config_service.py
  - keyseq/presentation/controllers/config_io/trigger_set_file_io.py
  - tests/test_config_service.py（`TriggerSetDefaultPathTest` 5 件新規 + 既存 1 件の期待値更新）
  - tests_ui/test_config_io_characterization.py（既存 1 件を改名・拡張 + 新規 1 件）
  - instructions/phase/06_child_file_save_dialog/tasks/task_02_trigger_set_source_and_naming.md（新規）
verified:
  compile: clean
  tests: pass 102（97 + 新規 5）
  tests_ui: pass 86（85 + 新規 1）
  smoke: pass
  review: reviewer = **完了可**（重点 7 点すべて OK）。参考指摘 1 件 = slugify 後に別々の keymap_set 名が
    同一 stem へ丸まる衝突（例 `game*.json` と `game?.json` → `game_.json`）は受入条件 8 の範囲外・将来の穴

## next_action
- **task_03（`save_plan_execution`）を `/task_new` で起票する**。内容は暫定仕様 05 §2・§8:
  保存計画の型（子ごとに 保存 / 別名パス / スキップ ＋ 依存関係）と **application 側の実行契約**
  （事前検証 → 書き込み / パスが変わる子の上位は保存必須 / **行ごとの粒度**〔選んだ子だけ書く〕/
  失敗時は旧索引を維持）。`save_runtime_data` を計画駆動へ作り替える。
  **既定計画＝全保存でダイアログ導入前の既存挙動と等価**であることを確認してから task_05 へ進む（挙動変更の切り分け）。
  起票前に、`save_runtime_data` の書き込み順を固定している既存テスト（`tests_ui/test_config_io_characterization*.py`）を
  grep で洗い出してタスク定義へ明記する。
- 起票後: `codex-implementer` へ委任（テスト実行は依頼しない）→ `verifier` 実測 → `reviewer` → `/save_state` + `/task_commit`。

## blockers
- なし。

## resume_hints
- **python は必ずリポジトリルートの `.venv` を使う**（worktree 相対 `..\..\..\.venv\Scripts\python.exe`）。
  グローバル `py` は依存欠落で tests_ui/smoke が落ちる。
- **Phase β の設計の正は暫定仕様 [05](../../instructions/history/05_child_file_save_dialog.md)（v0.2・ユーザー確定済）**。
  フェーズ中は正本 `spec_detail/` を直接改訂せず、task_07 で昇格＋凍結する。
- **Phase β の勘所**（暫定仕様の指摘①〜④由来。実装時に後退しやすい）:
  ① 未知の参照元・別の上位に属す子は**別名保存が既定**（安全側）/ ② 保存計画は
  **presentation が決定・application が実行**（application に tkinter 依存を持ち込まない）/
  ③ パスが変わる子の上位は**保存必須**・失敗時は**旧索引維持**・**行ごとの粒度**（他 sequence を巻き込まない）/
  ④ 既定命名の変更は **trigger_set のみ**（keymap_set stem 基準。現状は固定 `user/trigger_sets/default.json`）。
- **task_01 で入った土台**（後続はこれを使う): `PARENT_REFS_KEY = "_parent_refs"`（子JSON 側）/
  `INTERNAL_{KEYMAP,SEQUENCE,TRIGGER_SET}_PARENT_REFS`（runtime 側。trigger_set のみ `data` トップレベル）/
  `_normalize_parent_refs`（**未知は `None`・既知ゼロは `[]`**）/ `_merge_parent_ref`（重複排除・順序保持）。
- **task_02 で入った変更**: trigger_set の保存先は `_default_trigger_set_path()`（keymap_set stem 基準）。
  個別保存経路は `dirty_tracker.trigger_set_source_path` を読む（keymap / sequence と対称）。
- **`config_service.py` は 1262 行 →（task_02 で微増）**。分割是非は**フェーズ末の `/refactor_check` で判定**する
  （task 途中では触らない。reviewer からの申し送り）。
- **申し送り（task_04/05 で考慮 or refactor_check）**: ① slugify 後に別々の keymap_set 名が同一 stem へ丸まる
  衝突（受入条件 8 の範囲外）② `dirty_tracker.trigger_set_imported` は読み手不在の残置状態。
- Phase β の主な触点: `config_service.save_runtime_data`(200-252) / `_build_split_save_payloads`(456-) /
  `config_io/keymap_set_io.py`(`save_keymap_set_to`:78-102) / `controllers/dirty_state.py`（idea_05 の当事者）/
  `config_io/io_dialogs.py`（`choose_save_path_with_collision`）。
- **保存系リデザインの番号対応**: α=phase05/暫定04〔完了〕 / **β=phase06/暫定05〔進行中〕** /
  γ=phase07/暫定06〔独立・未着手〕 / プリセット=phase08/暫定07〔β とカスケード除外で協調〕。
- **Phase α の成果は正本 `spec_detail/data_schema.md` §5.4 配下が正**（新規/Import/空起動で keymap_set パスが空 →
  保存は別名保存 / 既定はディレクトリ `config/user/keymap_sets/` / 子ファイルは全セット共有〔β の課題〕/
  レガシー `settings/` 経路のみ実装未追従 = idea_09）。
- config_io は `controllers/config_io/` の 6 クラスへ分割済（App が `app.keymap_set_io` 等で直接公開）。
- **レビュアーは 2 本立て**: `reviewer`（sonnet・単一タスクの実装差分）/ `deep-reviewer`（opus・設計文書 /
  複数タスクを跨ぐ差分 / フェーズ完了判定）。使い分けは `.claude/rules/agent_selection.md` のレビュー表が正。
  出力の作法は `.claude/rules/output_style.md`。
- **【Codex 運用の手順書】ジョブが詰まった / cancel が効かない / ハング検知 / state 手修復は
  `instructions/common/rules_detail/codex_operations.md` を読む**。**Codex 申告のテスト結果は信用せず必ず verifier で再実行**。
  **Codex は python をまったく実行できない**（サンドボックス制約・回避不能）→ 委任にテスト実行を含めない。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**（main 側を編集すると commit から漏れる）。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認には**直接 `grep`** を使う。
  行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えない）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 03_startup_font_settings_cleanup / 04_config_io_controller_split / 05_keymap_set_new_and_default_dir。
- 未着手 idea: idea_03（hotkey 保存時正規化・優先度低）/ idea_07（参照元の掃除・**β 完了後**）/
  idea_08（keymap_set 個別プリセット・プリセット案2 完了後）/ idea_09（レガシー settings/ フォールバック・α の積み残し）。
  保留 idea: idea_04（FontSettingsController）/ idea_06（D/E/F 共通化・**β で達成見込み**）。idea_05 は β が内包（着手中）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
