# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-14T23:25:00
phase: **58_window_size_fit**（画面サイズの調整・2026-10-14 起票・主入力 = 暫定 42 v0.3 ユーザー確定済）。次採番 = phase 59 / 暫定 43 / decisions 59 / 提案書 24
直前の完了フェーズ = **phase 57**（`decisions_archive/57_grid_crosshair_nudge.md`）
last_commit_location: `claude/crosshair-selection-frame-f4b464`（phase 57 task_09_fix = phase 57 の最終）。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: present
focus: **phase 58 起票済（phase.md・current.md・reviewer 整合チェック = 軽微 2 件反映）。次 = task_01（ステータス欄の 3 状態）。**
mode: implementing

## last_action
ts: 2026-10-14T22:00:00
who: main
summary: |
  ユーザー要望（フル表示の 3 枠を枠ごとにスクロール・下限はメイン領域の今の最小の半分 / 省略表示のフック・表示を Expander で開閉し保存 / ステータス欄のフックを ON・OFF・一時停止の 3 状態）を
  暫定 42 `instructions/history/42_window_size_fit.md` v0.1 に起票（確定事項 = §2）。起票時 deep-reviewer = 修正して採用（未反映）。利用上限で中断。

## next_action
- **暫定 42 v0.2 反映済（起票時 deep-reviewer の指摘をすべて反映）・Codex 敵対的レビュー = needs-attention 1 件（medium: §8-1 案 B は吸収先が無く切れる〔`pane_width_rules.py:114-124`・`features.md` §4.6 で裏取り済〕→ 案 A を必須にし受け入れ条件へ「最小幅で 3 枠ともスクロールバーが出ても切れない」を追加）**
- **phase 58 起票済（2026-10-14）**。次 = task_01 → task_02 → task_03 → task_04 → task_05（統合）→ task_06（正本反映）
- main へのマージはユーザー（ブランチ `claude/crosshair-selection-frame-f4b464`）

## blockers
- なし

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- 画面の枠（phase 56・57）の地図 = `codebase_map.md`「画面の枠（phase 56・57）」。振り分けは `suppress_keys` 1 本（`screen_grid_session._publish_snapshot`）/ 操作キーは `domain/screen_grid/ops.py`。
- **【罠・phase 57 で実証】Windows の Tk で位置の反映の保留中に `wm_attributes("-topmost", True)` を呼ぶと窓が `0,0` へ戻る**（`geometry` の直後に `update_idletasks()`）。**Tk の測り直しは after_idle だと配置の計算より先に走ることがある**（測る前に `update_idletasks()`）・`<Configure>` で configure し返すと無限ループになり得る（値が変わったときだけ・結び付けは 1 つ）。
- **プロセスは pyautogui の import でシステム DPI 対応**（`.venv/Lib/site-packages/pyautogui/_pyautogui_win.py:17`）。検証は本番の起動経路で
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜41）の条項を実装の根拠に引かない。
- **【Codex のプロセス・2026-10-14 実測】** companion は作業フォルダ（cwd）ごとに `app-server-broker.mjs serve` を常駐させ、その下の `codex app-server`（+ sandbox の runner・node）は**呼び出し後も残る（再利用のための設計）**。
  worktree ごとに 1 組ずつ増えるため、worktree を多く使うと codex.exe が溜まる。Codex デスクトップアプリ（ChatGPT.exe）配下の codex.exe は別物。不調時は Windows の再起動で解消した
