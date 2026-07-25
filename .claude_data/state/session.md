# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-24T04:00:00
phase: instructions/phase/04_config_io_controller_split（task_01〜04 完了・task_05 未着手）
last_commit_location: claude/proposal-b-inquiry-7db89e ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 04 task_04（A+A'/B/C を config_io/ 配下3モジュールへ分割・ConfigIoController を114行の完全ファサード化）完了（挙動不変・reviewer 採用・codex-reviewer clean）。次は task_05（呼び出し元30箇所差し替え + 委譲層削除）**。
mode: completed

## last_action
ts: 2026-07-24T04:00:00
who: main
summary: |
  【phase 04 task_04（A+A'/B/C 分割）完了】
  - A（構成セット）+A'（choose_split_base_dir）→ `keymap_set_io.py`（KeymapSetIo）/ B（起動設定）→ `startup_io.py`
    （StartupIo）/ C（共有ダイアログ）→ `io_dialogs.py`（IoDialogs）へ**verbatim 移設**。
  - **ConfigIoController は 387→114 行の完全ファサード**（全メソッドが委譲・task_05 で削除予定）。
    クロスモジュール呼び出しは 2 箇所のみ facade 経由（set_startup_keymap_set→write_startup /
    load_startup_and_config→apply_loaded_data_to_ui）。それ以外は同一クラスタ内 self.。
  - **D/E/F（task_03 分割済）は無変更で動作**（facade 経由で C/A ヘルパを解決）。E の不整合も無変更。
  - **task_02 テストの調整はアクセサ切替を採用**（ユーザー確定・Option A の境界 mock だと apply 周りで
    set_dirty 回数アサーションを緩める必要が出るため）。`_config_set_io`→`app.config_io._keymap_set_io` /
    `_startup_io`→`_startup_io` へ向け、クロスモジュール2箇所（write_startup/apply）のみ facade patch へ。
    **アサーション非緩和で 35 件 pass**（詳細は decisions 04）。
  - Codex 実装・codex-reviewer とも**ハングなし**（Monitor が両ジョブとも JOB_ENDED を正検知）。
  - **レビュー**: reviewer=完了可（採用・アサーション非緩和を git diff で確認）/ codex-reviewer=**指摘なし（clean）**。
result_files:
  - keyseq/presentation/controllers/config_io/{keymap_set_io,startup_io,io_dialogs}.py（新規3ファイル）
  - keyseq/presentation/controllers/config_io_controller.py（A/B/C も委譲化・114行の完全ファサード）
  - tests_ui/test_config_io_characterization_keymap_set_startup.py（アクセサ切替・35件 pass 維持）
  - instructions/phase/04_config_io_controller_split/tasks/task_04_...md（新規）
  - .claude_data/state/decisions.md（task_04 のアクセサ切替判断を記録）
verified:
  compile: clean
  test(tests): pass 86
  test(tests_ui): pass 74          # 19 + 35 + 既存20
  smoke: pass
  production_scope: presentation のみ（application・domain 無変更）

## next_action
- **task_05（呼び出し元30箇所差し替え・案B + 委譲層削除）を起票して着手する**。ConfigIoController の委譲ファサードを
  削除し、呼び出し元 8 ファイル 30 箇所（menu_bar 8 / app.py 7 / file_frame 4 / trigger_box・sequence_box・keymap_box 各3 /
  layout_controller 1 / tests_ui 1）を `app.config_io.<method>` → `app.<新名>.<method>` へ差し替える（暫定仕様 §4=案B）。
  **app に 6 分割オブジェクトを公開**（`app.keymap_set_io` / `app.startup_io` / `app.io_dialogs` / `app.keymap_io` /
  `app.trigger_set_io` / `app.sequence_io`）。分割モジュール間の facade 経由呼び出し（write_startup / apply /
  D/E/F の C/A ヘルパ呼び出し）も新参照へ調整。**特性テストのアクセサ（`_config_set_io` 等）も新 app 参照へ最終調整**。
  差し替え後 `grep -rn "config_io\." keyseq main.py tests tests_ui` で**残存 0 件**を確認（案B の完了条件）。
- その後 **task_06（正本反映: codebase_map.md 更新・暫定仕様 03 凍結・decisions_archive/04 作成・
  current.md 完了記載・/refactor_check）+ 実機目視ゲート**。
- **実装分担**: task_05 は機械的置換中心だが広範。codex-implementer 既定 + Monitor + codex-reviewer 併用
  （phase.md が Codex 統合レビューを本命とする箇所）。Codex 申告は信用せず verifier で `.venv` 再実行。
- **【ユーザー必須ゲート】task_06 正本反映の前に実機目視**（保存/読込/別名保存/Import/Export/起動設定変更/
  keymap・トリガー一覧・シーケンスの個別保存読込）。ここで必ず停止しユーザーへ実機確認を依頼する。
- タスクが緑＋reviewer(+codex-reviewer) 採用なら確認なしで `/save_state`→`/task_commit`（standing 許可）。

## blockers
- なし（task_01〜04 完了・全緑・reviewer 採用・codex-reviewer clean）。次は task_05（呼び出し元差し替え + 委譲層削除）。
- 留意: **codex-implementer は task_03・04 とも実装・review 正常完了**（ハングなし・Monitor 有効）。
  Monitor 運用が有効に機能（両ジョブとも JOB_ENDED を正しく検知・STALLED 誤検知なし）。task_04 でも Monitor をセットで。

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
