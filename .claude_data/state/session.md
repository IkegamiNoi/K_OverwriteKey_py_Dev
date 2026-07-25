# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-24T01:20:00
phase: instructions/phase/04_config_io_controller_split（task_01 完了・task_02 未着手）
last_commit_location: claude/proposal-b-inquiry-7db89e ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 04 task_01（特性テスト① C+D/E/F）完了（19件 pass・reviewer 採用・production 無変更）。次は task_02（A+B の特性テスト）**。
mode: completed

## last_action
ts: 2026-07-24T01:20:00
who: main
summary: |
  【phase 04 task_01（特性テスト① C+D/E/F）完了】
  - `tests_ui/test_config_io_characterization.py`（テスト19本）を追加。**分割前の現行コードで固定**。
    C（共有ダイアログ4分岐×2）/ D・E・F（save/save_as/save_to_path/load）を覆う。
  - **E の既存不整合を「現状を正」として固定**: `:440` の到達不能な askyesno が呼ばれないこと・
    `_as` が ask_link_label を呼ばないことを assert（idea_05 言及コメントあり）。「あるべき姿」に書き換えない。
  - 設計制約を遵守: patch は `tkinter` モジュール属性（分割耐性）/ 呼び出し口はアクセサ
    （`_dialog_io` / `_keymap_io` / `_trigger_set_io` / `_sequence_io`・task_05 の差し替えに備える）/
    保存 JSON はバイト列比較（`_expected_json_bytes` で改行差のみ吸収）。
  - 修正経緯: Codex 実装は当初 19件全 ERROR（setUp の `_selected_trigger_idx=None`）→ メインが `=0` 修正 →
    16 pass/3 fail（バイト列比較の LF/CRLF 不一致）→ メインが `_expected_json_bytes` ヘルパ追加で **19件 pass**。
  - **reviewer 判定: 完了可（採用・指摘なし）**。固有4観点（production 無変更 / E 不整合固定 / 分割耐性 patch /
    バイト列比較）すべて OK。reviewer も grep で App._trigger_set_source_path 未定義・:440 到達不能を裏取り。
result_files:
  - tests_ui/test_config_io_characterization.py（新規・19件 pass。コミット対象）
verified:
  compile: clean
  test(tests): pass 86
  test(tests_ui): pass 39          # 既存20 + 新規19
  smoke: pass
  production_untouched: yes        # git diff で keyseq/ の変更 0 件

## next_action
- **task_02（A+B の特性テスト）を起票して着手する**。`/task_new` で
  `task_02_characterization_tests_keymap_set_startup.md`。対象は暫定仕様 §7-2 表の A（構成セット）と B（起動設定）:
  `confirm_save_if_dirty`(3分岐) / `save_keymap_set_to` / `choose_split_base_dir_for_keymap_set` /
  `load_keymap_set_from` / `new_config` / `import_config` / `export_config` / `restore_default` /
  `set_startup_keymap_set`（保存失敗後も続行する現挙動）/ `write_startup` /
  `load_startup_and_config`（3分岐・:261-262 の握りつぶし fallback）。task_01 と同じ設計制約を踏襲。
- その後 task_03（D/E/F 分割）→ task_04（A/B/C 分割）→ task_05（呼び出し元30箇所差し替え）→ task_06（正本反映）。
- **実装分担**: task_02 は特性テスト（production 無変更）なのでメイン or implementer でも可。
  分割本体（task_03〜）は codex-implementer 既定。**Codex 本格投入時はジョブログ停滞の Monitor をセットで**
  （手順は `instructions/common/rules_detail/codex_operations.md`）。
- タスクが緑＋reviewer 採用なら確認なしで `/save_state`→`/task_commit`（ユーザー standing 許可）。

## blockers
- なし（task_01 完了・全緑・reviewer 採用）。次は task_02 の起票・着手。
- 留意: **codex-implementer が不安定**（`collaboration tool: wait` ハング・companion 側の根本原因で再発しうる）。
  分割本体（task_03〜）で本格投入する際はジョブログ停滞の Monitor をセットで。手順は運用手順書参照。

## resume_hints
- **python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree相対）を使う。グローバル `py` は依存欠落で tests_ui/smoke が落ちる。**
- **設計の正は暫定仕様 `instructions/history/03_config_io_controller_split.md`（v0.4）**。phase.md は設計を再定義していない（参照のみ）。
  番号対応: phase 04 / 暫定 03 / decisions 04。
- **phase 04 の絶対前提は「挙動不変」**。特に **E の source_path 不整合とデッドコードを「直さない」**こと
  （善意の修正が最も混入しやすい。reviewer の重点観点。修正は idea_05 で phase 04 完了後）。
- 特性テストの設計制約: **patch は `tkinter` モジュール属性に対して行う**（実装モジュール変数を patch すると
  task_03/04 の分割でテストが壊れる）/ 呼び出し口はテスト内アクセサ（`_dialog_io` / `_keymap_io` /
  `_trigger_set_io` / `_sequence_io`）に集約（task_05 の差し替えに備える）/ 保存 JSON はバイト列比較。
- **【Codex 運用の手順書】ジョブが詰まった / cancel が効かない / ハング検知 / state 手修復は
  `instructions/common/rules_detail/codex_operations.md` を読む**（`.claude/rules/agent_selection.md` 冒頭にポインタ）。
  **Codex 申告のテスト結果は信用せず必ず verifier で `.venv` 再実行**（今回 19件全 ERROR を検出）。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**。
  main リポジトリ側の絶対パスを編集すると commit から漏れる（phase 02・03 で再発）。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認には**直接 `grep`** を使う。
- 行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えず誤解の元）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引あり）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 01_view_ref_cleanup / 02_hotkey_validation / 03_startup_font_settings_cleanup。
- 未着手 idea: idea_03（hotkey 保存時正規化・優先度低）/ idea_05（phase 04 完了後）。
  保留 idea: idea_04（FontSettingsController）/ idea_06（D/E/F 共通化）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
