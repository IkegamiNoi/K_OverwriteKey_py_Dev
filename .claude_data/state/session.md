# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-07-24T00:30:00
phase: instructions/phase/04_config_io_controller_split（task_01 実装中・未完了）
last_commit_location: claude/proposal-b-inquiry-7db89e ※現在地はセッション開始時の git 実測値が正

## current
focus: **phase 04 task_01（特性テスト①）実装中。テストは 19件中 16 pass / 3 fail。残 3 件は保存 JSON のバイト列比較の改行コード不一致。Codex ハングの調査・復旧は完了済**。
mode: implementing

## last_action
ts: 2026-07-24T00:30:00
who: main
summary: |
  【phase 04 起票 → task_01 実装 → Codex ハング調査・復旧】
  - **暫定仕様 03 を v0.4（ユーザー確定済）で起票**。reviewer（修正して採用）+ codex-adversarial-reviewer
    （No-ship・指摘4件全採用）を通過。§4=**案B**（呼び出し元30箇所を差し替え・恒久ファサードを作らない）/
    §5=**案1**（同型ブロックD/E/Fは共通化しない）で確定。
  - **既存バグを発見**（敵対的レビュー指摘 → 実コードで裏取り）: E(trigger_set) の source_path が
    読み手 `app._trigger_set_source_path`（**未定義・常に ""**）と書き手 `dirty_tracker.trigger_set_source_path`
    （**read されない**）で分断。`:440` の askyesno が**到達不能なデッドコード**。
    **本フェーズでは直さずそのまま移設**する（→ idea_05）。
  - idea_04（FontSettingsController・保留）/ idea_05（E の不整合・phase 04 完了後）/
    idea_06（D/E/F 共通化・保留）を起票。phase 04 を起票（task 6本）。task_01 を起票。
  - **task_01 実装（codex-implementer 委任）**: `tests_ui/test_config_io_characterization.py`（690行・
    テスト19本）が生成された。verifier 実行の結果 **当初 19件全 ERROR** → メインが setUp の
    `_selected_trigger_idx = None`（property setter が int 化するため不可）を `= 0` へ修正 → **16 pass / 3 fail**。
  - **Codex ハングの原因を特定・復旧**: companion のジョブが `collaboration tool: wait` から復帰せず
    running のまま滞留し、`shared session` ランタイムのため後続タスクが `phase: starting` で全て詰まっていた。
    codex.exe 再起動では解消しない（記録は state ファイル側）。`cancel` も (1) Git Bash の MSYS パス変換で
    `taskkill /PID` が壊れる (2) 対象 PID 消滅済みだと記録を残したまま終了する、の二重で効かず。
    **state.json + ジョブ JSON の 2 件を running → cancelled へ手動修復**（バックアップ取得済）。Active jobs は解消。
result_files:
  - instructions/history/03_config_io_controller_split.md（新規・v0.4・ユーザー確定済）
  - instructions/backlog/idea_04 / idea_05 / idea_06 + INDEX.md（新規3件・行追加）
  - instructions/phase/04_config_io_controller_split/phase.md（新規）+ tasks/task_01_...md（新規）
  - instructions/phase/current.md（参照先を phase 04 へ・次採番 05 / 暫定 04）
  - tests_ui/test_config_io_characterization.py（**新規・未コミット・3件 fail 中**）
verified:
  compile: clean
  test(tests): pass 86
  test(tests_ui): pass 20 + 新規19本中 16 pass / 3 fail
  smoke: pass
  production_untouched: yes        # git diff で keyseq/ の変更 0 件を確認済

## next_action
- **task_01 の残り 3 件を修正する**（`tests_ui/test_config_io_characterization.py`）。対象は
  `test_keymap_save_to_path_writes_bytes_and_reports`(328行付近) /
  `test_trigger_set_save_to_path_writes_bytes_updates_dirty_and_reports`(454行付近) /
  `test_sequence_save_to_path_writes_bytes_updates_trigger_and_marks_dirty`(627行付近)。
  原因は期待値が **LF 決め打ち**なのに実ファイルが **CRLF**（Windows のテキストモード書き込み）。
  **修正方針は確定済**: モジュールレベルに
  `def _expected_json_bytes(text): return text.replace("\n", os.linesep).encode("utf-8")` を追加し 3 箇所から使う。
  **バイト列比較をやめる逃げ（dict 比較 / 改行正規化 / assert 削除）は禁止**（暫定仕様 §7-2・設計メモ③）。
- **実装先はユーザー判断待ち**（`/save_handoff` 実行時点で未回答）: (a) codex-implementer 再試行 /
  (b) implementer または メインで実施 / (c) Codex 再試行 + ジョブログ Monitor でハング検知（メイン推奨は c）。
- 修正後は verifier で全項目再実行（新規19件 全 pass・tests 86・tests_ui 20+19・smoke・`keyseq/` 変更 0 件）→
  reviewer レビュー → `/save_state` + `/task_commit`。
- その後 task_02（A/B の特性テスト）へ。

## blockers
- **task_01 未完了**（3 件 fail・修正方針は確定済）。
- **codex-implementer が不安定**。ジョブは復旧したが `collaboration tool: wait` ハングの根本原因は
  companion 側にあり再発しうる。再委任するならジョブログの監視をセットで行う。

## resume_hints
- **python は必ず `..\..\..\.venv\Scripts\python.exe`（worktree相対）を使う。グローバル `py` は依存欠落で tests_ui/smoke が落ちる。**
- **設計の正は暫定仕様 `instructions/history/03_config_io_controller_split.md`（v0.4）**。phase.md は設計を再定義していない（参照のみ）。
  番号対応: phase 04 / 暫定 03 / decisions 04。
- **phase 04 の絶対前提は「挙動不変」**。特に **E の source_path 不整合とデッドコードを「直さない」**こと
  （善意の修正が最も混入しやすい。reviewer の重点観点。修正は idea_05 で phase 04 完了後）。
- 特性テストの設計制約: **patch は `tkinter` モジュール属性に対して行う**（実装モジュール変数を patch すると
  task_03/04 の分割でテストが壊れる）/ 呼び出し口はテスト内アクセサ（`_dialog_io` / `_keymap_io` /
  `_trigger_set_io` / `_sequence_io`）に集約（task_05 の差し替えに備える）/ 保存 JSON はバイト列比較。
- **【Codex 運用】ジョブ状態は `node "<plugin>/scripts/codex-companion.mjs" status --all` で確認する**。
  **Bash からのみ `shared session` が見える**（PowerShell だと `direct startup` で「No job found」になる）。
  `cancel` を Bash から打つ場合は `MSYS2_ARG_CONV_EXCL='*'` を付けないと `taskkill /PID` が壊れる。
  state: `C:\Users\ikega\.claude\plugins\data\codex-inline\state\worktree-state-tracking-da2833-*\`
- **【訂正】Codex は `.venv` python を実行できる**（今回のジョブログで `pwsh` 経由の実行が exit 0 を確認）。
  ただし **Codex の申告を鵜呑みにせず verifier で再実行する運用は維持**（今回 19件全 ERROR を検出できた）。
- **【罠】state ファイル・`instructions/` 配下・code は必ず worktree のパスで編集する**。
  main リポジトリ側の絶対パスを編集すると commit から漏れる（phase 02・03 で再発）。
- **【罠】`git grep` は追跡済みファイルしか検索しない**。新規（未追跡）ファイルの確認には**直接 `grep`** を使う。
- 行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えず誤解の元）。
- 過去の判断は `.claude_data/state/decisions.md`（アーカイブ索引あり）+ `decisions_archive/<phase>.md`。
  完了済の直近 3 件: 01_view_ref_cleanup / 02_hotkey_validation / 03_startup_font_settings_cleanup。
- 未着手 idea: idea_03（hotkey 保存時正規化・優先度低）/ idea_05（phase 04 完了後）。
  保留 idea: idea_04（FontSettingsController）/ idea_06（D/E/F 共通化）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
