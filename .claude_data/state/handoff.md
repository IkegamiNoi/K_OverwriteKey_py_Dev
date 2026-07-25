# handoff.md

過去の会話履歴は参照しないでください。
このファイルと `.claude_data/state/session.md` を起点に作業を再開してください。

## プロジェクト概要
- 言語/実行: Python（tkinter GUI）。オニオン構成（presentation / application / domain / infrastructure）。
- 対象アプリ: keyseq（キー割り当て/オーバーライドツール）。全体仕様は `instructions/common/`（`app_overview.md` / `codebase_map.md`）参照。
- **python 実行は必ずリポジトリルートの `.venv` を使う**（worktree相対 `..\..\..\.venv\Scripts\python.exe`）。
  依存 keyboard/pyautogui/pynput はこの `.venv` にのみ導入済み。グローバル `py` は使わない（tests_ui/smoke が落ちる）。

## 再開手順
1. `.claude_data/state/session.md` を読む（最重要・最新状態）
2. `.claude_data/state/decisions.md` を読む（判断履歴。完了フェーズは「アーカイブ索引」→ `decisions_archive/<phase>.md`）
3. CLAUDE.md → `instructions/phase/current.md`（**アクティブ: phase 04**）→ `.claude/rules/` の順に必要分を読む
4. **設計の正は暫定仕様 [03_config_io_controller_split.md](../../instructions/history/03_config_io_controller_split.md)（v0.4・ユーザー確定済）**。
   phase.md は設計を再定義していない（参照のみ）。番号対応: phase 04 / 暫定 03 / decisions 04
5. タスク定義 `instructions/phase/04_config_io_controller_split/tasks/task_01_characterization_tests_individual_json.md` を読む
6. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
**phase 04 task_01（特性テスト①）実装中。テストは 19件中 16 pass / 3 fail。残 3 件は保存 JSON のバイト列比較の改行コード不一致。Codex ハングの調査・復旧は完了済**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ず .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py tests_ui
../../../.venv/Scripts/python.exe -m unittest tests_ui.test_config_io_characterization
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
session.md.verified（compile clean / tests pass **86** / tests_ui pass **20 + 新規19本中 16 pass 3 fail** /
smoke pass / production_untouched yes）と一致することを確認する。
`git diff --stat` で **`keyseq/` の変更が 0 件**であることも確認する（task_01 は production 無変更が要件）。

## 次アクション（session.md.next_action より）
- **task_01 の残り 3 件を修正する**（`tests_ui/test_config_io_characterization.py`・未コミット）。対象は
  `test_keymap_save_to_path_writes_bytes_and_reports`(328行付近) /
  `test_trigger_set_save_to_path_writes_bytes_updates_dirty_and_reports`(454行付近) /
  `test_sequence_save_to_path_writes_bytes_updates_trigger_and_marks_dirty`(627行付近)。
  原因は期待値が **LF 決め打ち**なのに実ファイルが **CRLF**（Windows のテキストモード書き込み）。
  **修正方針は確定済**: モジュールレベルに
  `def _expected_json_bytes(text): return text.replace("\n", os.linesep).encode("utf-8")` を追加し 3 箇所から使う。
  **バイト列比較をやめる逃げ（dict 比較 / 改行正規化 / assert 削除）は禁止**（暫定仕様 §7-2・設計メモ③）。
- **実装先はユーザー判断待ち**: (a) codex-implementer 再試行 / (b) implementer またはメインで実施 /
  (c) Codex 再試行 + ジョブログ Monitor でハング検知（メイン推奨は c）。**未回答なら先にユーザーへ確認する**。
- 修正後: verifier で全項目再実行 → reviewer → `/save_state` + `/task_commit` → task_02（A/B の特性テスト）へ。
- 分担（継続）: 実装は codex-implementer 既定・標準検証は verifier・レビューは reviewer（統合時 codex-reviewer 併用）・コミットはメイン。
  **タスクが緑＋reviewer 採用なら確認なしで `/save_state`→`/task_commit`**（ユーザー standing 許可・ただし実機目視/設計確定などのゲートでは停止）。

## 現フェーズの要点（04_config_io_controller_split・進行中）
- 目的: `config_io_controller.py`（**598 行・1クラス・29メソッド**）を `controllers/config_io/` 配下の
  **6 モジュール**（A+A'=構成セット / B=起動設定 / C=共有ダイアログ / D=keymap / E=trigger_set / F=sequence）へ分割。
  **挙動不変が絶対前提**（保存 JSON のバイト列・ダイアログ文言・呼び出し順・例外時分岐を変えない）。presentation 限定・スキーマ不変。
- タスク: task_01/02 = 特性テスト（①C+D/E/F ②A+B）→ task_03/04 = 分割 → task_05 = 呼び出し元 30 箇所の
  差し替え → task_06 = 正本反映。**安全網を先に作ってから分割する**。
- 確定事項: §4=**案B**（呼び出し元を差し替え・恒久ファサードを作らない）/ §5=**案1**（D/E/F を共通化しない）。
- **【最重要】既存バグを「直さない」**: E(trigger_set) の source_path は読み手
  `app._trigger_set_source_path`（**未定義・常に ""**）と書き手 `dirty_tracker.trigger_set_source_path`
  （**read されない**）で分断し、`:440` の askyesno が**到達不能なデッドコード**。
  本フェーズは**そのまま移設**する（修正は idea_05・phase 04 完了後）。reviewer の重点観点。
- 特性テストの設計制約: **patch は `tkinter` モジュール属性に対して行う**（実装モジュール変数を patch すると
  task_03/04 の分割でテストが壊れる）/ 呼び出し口はテスト内アクセサ（`_dialog_io` / `_keymap_io` /
  `_trigger_set_io` / `_sequence_io`）に集約（task_05 の差し替えに備える）/ 保存 JSON はバイト列比較。

## 注意事項・blockers
- blockers: **task_01 未完了**（3 件 fail・修正方針は確定済）。
- **codex-implementer が不安定**。`collaboration tool: wait` から復帰しないハングの根本原因は
  companion 側にあり再発しうる。**Codex を本格投入するタスクではジョブログ停滞の監視（Monitor）をセットで**。
- **【Codex 運用の手順書】ジョブが詰まった / cancel が効かない / ハング検知 / state 手修復は
  `instructions/common/rules_detail/codex_operations.md` を読む**（要点は `.claude/rules/agent_selection.md`
  冒頭のポインタ）。**Codex 申告のテスト結果は信用せず必ず verifier で `.venv` 再実行**（今回 19件全 ERROR を検出）。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/` だけでなく **`instructions/` や code も**、
  main リポジトリ側の絶対パス（パスに `.claude\worktrees\<name>\` を含まない）を編集すると worktree に反映されず commit から漏れる。
  Read/Grep が main 側パスを返すことがあるため、**編集は必ず worktree ルート配下のパス**で行う。
- **【罠】`git grep` は追跡済みファイルのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。
- 行数計測は `wc -l`（PowerShell `Measure-Object -Line` は空行を数えず誤解の元）。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近 3 件: 03_startup_font_settings_cleanup / 02_hotkey_validation / 01_view_ref_cleanup。それ以前は索引参照）。
- 未着手 idea: idea_03（hotkey 保存時正規化・優先度低）/ idea_05（E の不整合・**phase 04 完了後**）。
  保留 idea: idea_04（FontSettingsController）/ idea_06（D/E/F 共通化）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
