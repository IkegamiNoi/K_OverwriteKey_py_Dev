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
3. CLAUDE.md → `instructions/phase/current.md`（現在アクティブなフェーズなし・次採番 04）→ `.claude/rules/` の順に必要分を読む
4. **次フェーズは未確定**。着手候補は `instructions/backlog/INDEX.md`。新フェーズ着手はユーザー方針確認 → `/phase_start` で起票
5. session.md.next_action から作業を再開する

## 現在の作業の 1 行サマリ
**フェーズ 03_startup_font_settings_cleanup 完了（task_01〜05・挙動不変・実機目視 OK）。次フェーズ未確定（ユーザー方針確認待ち）**。

## 最初に確認するコマンド（.venv python 必須）
```bash
# worktree ルートで実行。python は必ず .venv を使う
../../../.venv/Scripts/python.exe -m compileall -q keyseq main.py
../../../.venv/Scripts/python.exe -m unittest discover -s tests
../../../.venv/Scripts/python.exe -m unittest discover -s tests_ui
../../../.venv/Scripts/python.exe -m tests.smoke_app
```
session.md.verified（compile clean / tests pass **86** / tests_ui pass **20** / smoke pass）と一致することを確認する。

## 次アクション（session.md.next_action より）
- **フェーズ 03 完了。次フェーズは未確定** → ユーザーに方針確認する。着手候補（`instructions/backlog/INDEX.md`）:
  - [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の保存時正規化・優先度低・要設計）。
  - 案B（FontSettingsController 新設）: phase 03 で見送り。フォント設定拡張が必要になった時点で初期化順序設計を詰めて idea 化。
- 次フェーズ着手時は `/phase_start` で起票（次採番 phase 04）。暫定仕様が必要なら独立採番の暫定 03 を起票。
- 分担（継続）: 実装は codex-implementer 既定・標準検証は verifier・レビューは reviewer（統合時 codex-reviewer 併用）・コミットはメイン。
  **タスクが緑＋reviewer 採用なら確認なしで `/save_state`→`/task_commit`**（ユーザー standing 許可・ただし実機目視/設計確定などのゲートでは停止）。

## 直前フェーズの要点（03_startup_font_settings_cleanup・完了）
- 起動設定/フォント3メソッドを整理し **4 負債**（①責務混在 ②controller→App private 逆参照 ③初期化順序制約 ④ui_vars 直読み）を挙動不変で解消。
- 実装結果: coerce→`theme.coerce_font_delta`（純関数）/ 起動設定ローダ→新規 `presentation/startup_settings.py`（`config_service` 直依存・未知キー全保持・`on_read_error` 注入）/ `set_ui_font_delta` 案A分割（`_apply_font_delta` 抽出）/ `UiVars.__init__(self, master, ui_font_delta_pt)` 引数化。**案B（FontSettingsController）は見送り＝将来 idea**。
- 記録: 暫定仕様 02 を **v1.0 で凍結**。**spec_detail 昇格は不要**（startup/font の担当層記述なし＝担当層は codebase_map.md が正）。`/refactor_check`: 不要（M1〜M6 非該当）。
- 詳細・判断・コミット一覧は `decisions_archive/03_startup_font_settings_cleanup.md` が正。

## 注意事項・blockers
- blockers: なし（フェーズ 03 完了・全緑・実機目視 OK・git は task_05 までコミット済）。
- **【罠・再発済】worktree と main は別コピー**。`.claude_data/` だけでなく **`instructions/`（codebase_map.md・backlog INDEX 等）や code も**、
  main リポジトリ側の絶対パス（パスに `.claude\worktrees\<name>\` を含まない）を編集すると worktree に反映されず commit から漏れる。
  Read/Grep が main 側パスを返すことがあるため、**編集は必ず worktree ルート配下のパス**で行う（phase 03 task_05 で reviewer が検出）。
- 分担の罠: Codex は sandbox から `.venv` python を起動できない。**Codex 申告のテスト結果は信用せず必ず verifier で `.venv` 実行**。
- **【罠】`git grep` は追跡済みファイルのみ検索**。新規（未追跡）ファイルの確認は**直接 `grep`**。
- **app.py の行数計測は `wc -l`**（phase 03 完了時 448 行）。PowerShell `Measure-Object -Line` は空行を数えず誤解の元。
- `config_io_controller.py` が 598 行で 600 行目安に接近（`current.md`「別タスク化候補」に記録・次フェーズの /refactor_check で再判定）。
- 完了フェーズの詳細・判断は `decisions.md`「アーカイブ索引」+ `decisions_archive/<phase>.md` が正
  （直近: 03_startup_font_settings_cleanup / 02_hotkey_validation / 01_view_ref_cleanup。それ以前は索引参照）。
- 未着手 idea: [idea_03](../../instructions/backlog/idea_03_action_hotkey_save_normalization.md)（アクション hotkey の保存時正規化・優先度低）。
- 会話履歴の再現を試みない。想定外の差分を見つけたら `.claude/rules/anti_patterns.md` に従う。
