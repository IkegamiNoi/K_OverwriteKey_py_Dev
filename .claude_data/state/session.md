# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-26T12:00:00
phase: instructions/phase/04_config_io_controller_split（**task_01〜06 完了＝フェーズ完了**。次は phase 05 未確定）
last_commit_location: claude/task-06-proceed-eb9f1b ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 04（config_io_controller 分割）task_06（正本反映）まで完了＝フェーズ完了。実機目視 OK 済・全緑・reviewer 採用・refactor_check 不要。次フェーズ 05 未確定（有力候補 idea_05）**。
mode: completed

## last_action
ts: 2026-07-26T12:00:00
who: main
summary: |
  【phase 04 task_06（正本反映・記録）完了＝フェーズ完了】文書作業のみ・コード変更なし。
  - `codebase_map.md`: presentation ツリー図に `controllers/config_io/`（6ファイル）追記 / コントローラ節の
    ConfigIoController 行を6クラス（KeymapSetIo/StartupIo/IoDialogs/KeymapFileIo/TriggerSetFileIo/SequenceFileIo）
    + App 公開名へ差し替え / `config_io.write_startup`→`startup_io.write_startup` / `app.config_io`例→`app.keymap_set_io`。
  - spec_detail 昇格要否: `config_io` 言及0件（再grep）→ **昇格不要**（担当層は codebase_map.md が正・architecture §3.5）。
  - 暫定仕様 03 を**凍結**（ヘッダ「凍結・正本反映済」）。`decisions_archive/04_config_io_controller_split.md` 新規作成し
    decisions.md の phase 04 詳細を集約・索引化（詳細セクション削除）。
  - `current.md`: アクティブ=なし（04完了）/ 次採番 phase 05・暫定 04 明記 / idea_05 を有力候補・idea_06 の条件充足更新。
  - task_06 定義起票。**/refactor_check 判定=不要**（M3 の同型3ブロックは既存重複の移設で idea_06〔保留〕がカバー済＝既知。他は非該当）。
  - **検証**: verifier=全緑（compile clean / tests 86 / tests_ui 74 / smoke pass / 旧ファサード参照0件）。
    **レビュー**: reviewer=完了可（採用・指摘なし・文書と実構成が完全一致）。
result_files:
  - instructions/common/codebase_map.md（ツリー図 + コントローラ節を6クラス構成へ）
  - instructions/history/03_config_io_controller_split.md（凍結・正本反映済ヘッダ）
  - .claude_data/state/decisions_archive/04_config_io_controller_split.md（新規・判断集約 + refactor_check判定）
  - .claude_data/state/decisions.md（アーカイブ索引に04追加 + 詳細セクション削除）
  - instructions/phase/current.md（04完了・次採番05/暫定04）
  - instructions/phase/04_config_io_controller_split/tasks/task_06_finalize_records.md（新規起票）
verified:
  compile: clean
  test(tests): pass 86
  test(tests_ui): pass 74          # 19 + 35 + 既存20
  smoke: pass
  refactor_check: 不要
  production_scope: コード変更なし（文書のみ）

## next_action
- **phase 04 は完了（task_01〜06・実機目視 OK・全緑・reviewer 採用・refactor_check 不要）**。残りは `/task_commit` で
  task_06 の文書変更をコミットするのみ（standing 許可により実行済／実行予定）。
- **次フェーズ（phase 05）は未確定**。着手時はユーザーに方針確認し `/phase_start` で起票する。有力候補は
  **[idea_05](../../instructions/backlog/idea_05_trigger_set_source_path_inconsistency.md)**（trigger_set の source_path 不整合修正。
  phase 04 完了により着手条件を満たした・**挙動変更を伴うため暫定仕様先行モード＝spec_change_workflow の仕様変更フロー**）。
  他候補: idea_03（アクション hotkey 保存正規化・優先度低）/ idea_04（FontSettingsController・保留）/ idea_06（D/E/F 共通化・保留）。

## blockers
- なし（phase 04 完了）。

## resume_hints
- **python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree相対）を使う。グローバル `py` は依存欠落で tests_ui/smoke が落ちる。**
- phase 04 は完了・アーカイブ済（判断は `decisions_archive/04_config_io_controller_split.md` が正）。config_io は
  `controllers/config_io/` の6クラスへ分割済（App が `app.keymap_set_io` 等で直接公開・`config_io` 名は消滅）。
- **次候補 idea_05（E=trigger_set の source_path 不整合修正）は挙動変更を伴う**。着手時は spec_change_workflow の
  仕様変更フロー（暫定仕様先行モード）で。既存不整合の詳細は暫定仕様 03 §1「既存の不整合」/ idea_05 に記載。
- **【Codex 運用の手順書】ジョブが詰まった / cancel が効かない / ハング検知 / state 手修復は
  `instructions/common/rules_detail/codex_operations.md` を読む**（`.claude/rules/agent_selection.md` 冒頭にポインタ）。
  **Codex 申告のテスト結果は信用せず必ず verifier で `.venv` 再実行**（今回 19件全 ERROR を検出）。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**。
  main リポジトリ側の絶対パスを編集すると commit から漏れる（phase 02・03 で再発）。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認には**直接 `grep`** を使う。
- 行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えず誤解の元）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引あり）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 02_hotkey_validation / 03_startup_font_settings_cleanup / 04_config_io_controller_split。
- 未着手 idea: idea_05（trigger_set source_path・**着手条件充足＝有力候補**）/ idea_03（hotkey 保存時正規化・優先度低）。
  保留 idea: idea_04（FontSettingsController）/ idea_06（D/E/F 共通化）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
