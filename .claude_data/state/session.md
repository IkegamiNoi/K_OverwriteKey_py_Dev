# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-26T00:00:00
phase: instructions/phase/04_config_io_controller_split（task_01〜05 完了・task_06=正本反映のみ残・**実機目視ゲート待ち**）
last_commit_location: claude/proposal-b-inquiry-7db89e ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 04 task_05（ConfigIo/ファサード削除 + 呼び出し元30箇所を6分割オブジェクトへ差し替え・案B）完了（挙動不変・config_io 名消滅・reviewer 採用・codex-reviewer clean）。分割は全完了。残るは task_06（正本反映）のみで、その前に実機目視のユーザー必須ゲート**。
mode: completed

## last_action
ts: 2026-07-26T00:00:00
who: main
summary: |
  【phase 04 task_05（呼び出し元差し替え + ファサード削除）完了】
  - 案B: `config_io_controller.py` を削除し、App が6分割オブジェクトを直接公開
    （keymap_set_io / startup_io / io_dialogs / keymap_io / trigger_set_io / sequence_io・app.py:142-147）。
  - 差し替え: 外部30箇所（menu_bar 8 / file_frame 4 / keymap/sequence/trigger_box 各3 / layout 1 / app.py 7）+
    内部クロスモジュール9箇所（self._app.config_io.X → self._app.<owner>.X）。**config_io 名は完全消滅**。
  - テスト3ファイルのアクセサを owner へ最終調整（メイン担当）。cross-cluster patch も owner へ
    （trigger_set の confirm→keymap_set_io / write_startup→startup_io / apply→keymap_set_io）。アサーション非緩和。
  - Codex 実装・codex-reviewer とも**ハングなし**（Monitor が両ジョブとも JOB_ENDED を正検知）。
  - **レビュー**: reviewer=完了可（採用・参考指摘1件=古いコメント→修正済）/ codex-reviewer=**指摘なし（clean）**。
  【（以下は前タスク: task_04 A+A'/B/C 分割・完了）】
  - A（構成セット）+A'（choose_split_base_dir）→ `keymap_set_io.py`（KeymapSetIo）/ B（起動設定）→ `startup_io.py`
    （StartupIo）/ C（共有ダイアログ）→ `io_dialogs.py`（IoDialogs）へ**verbatim 移設**。
    ConfigIoController を114行の完全ファサード化。テスト調整はアクセサ切替（decisions 04）。reviewer 採用/codex-reviewer clean。
    ※詳細は decisions 04 と task_05 コミット手前の task_04 コミット（67f8f19）参照。
result_files:
  - keyseq/presentation/controllers/config_io_controller.py（**削除**・ファサード消滅）
  - keyseq/presentation/app.py（6分割オブジェクトを直接公開・内部7箇所差し替え）
  - keyseq/presentation/controllers/config_io/*.py（内部クロスモジュール9箇所を facade→owner）
  - views/menu_bar.py / full_view/{file_frame,keymap_box,sequence_box,trigger_box}.py / layout_controller.py（外部差し替え）
  - tests_ui/{test_config_io_characterization, ..._keymap_set_startup, test_startup_font_characterization}.py（アクセサを owner へ）
  - instructions/phase/04_config_io_controller_split/tasks/task_05_...md（新規）/ decisions.md（task_05 記録）
verified:
  compile: clean
  test(tests): pass 86
  test(tests_ui): pass 74          # 19 + 35 + 既存20
  smoke: pass
  production_scope: presentation のみ（application・domain 無変更）

## next_action
- **【最優先・ユーザー必須ゲート】実機目視を依頼する**。task_05 でファサード削除・呼び出し元差し替えが完了し、
  分割は全完了。**task_06（正本反映）に進む前に、ユーザーが実機でアプリを動かして確認**する:
  保存 / 読込 / 別名で保存 / Import / Export / 起動時に読む構成セット指定 /
  keymap・トリガー一覧・出力シーケンスの個別保存・読込。**目視 OK を得るまで task_06 に着手しない**。
- **実機目視 OK 後に task_06（正本反映）を起票・着手する**（`/task_new` → 実装はメイン=文書作業）:
  - `instructions/common/codebase_map.md` の「コントローラ（controllers/）」節を更新
    （ConfigIoController 削除 / config_io パッケージ6クラス〔KeymapSetIo/StartupIo/IoDialogs/KeymapFileIo/
    TriggerSetFileIo/SequenceFileIo〕を app.<名>.<method> で参照する構成へ / ツリー図 :44）。
  - **暫定仕様 03 を凍結**（ヘッダを「凍結・正本反映済」へ）。**spec_detail 昇格の要否を判定**
    （§8: config_io の担当層記述が spec_detail にあるか grep。無ければ昇格不要＝担当層は codebase_map.md が正）。
  - `decisions_archive/04_config_io_controller_split.md` を作成し decisions.md phase 04 セクションを集約・索引化。
  - `current.md` の完了記載・次採番（phase 05 / 暫定 04）。
  - 起票元は `current.md` 別タスク化候補（idea 由来ではないため INDEX 移動は不要）。
  - **`/refactor_check` 実行**（変更ファイル対象・M1〜M6。挙動不変フェーズだが判定は出す）。
- タスクが緑＋reviewer 採用なら確認なしで `/save_state`→`/task_commit`（standing 許可）。

## blockers
- **task_05 完了。次は実機目視のユーザー必須ゲート**（ここで停止）。目視 OK 後に task_06（正本反映）。
- 分割は全完了（config_io 名消滅・controller 削除・app が6オブジェクト公開・全緑）。
- 留意: **codex-implementer は task_03・04・05 とも実装・review 正常完了**（ハングなし・Monitor 有効）。
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
