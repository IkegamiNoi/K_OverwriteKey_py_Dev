# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-15T18:30:00
phase: **なし**（phase 58 = 画面サイズの調整は 2026-10-15 完了）。次採番 = phase 59 / 暫定 43 / decisions 59 / 提案書 25
直前の完了フェーズ = **phase 58**（`decisions_archive/58_window_size_fit.md`）
last_commit_location: `claude/physical-device-visual-check-79fcd3`（phase 58 一式・完了）。phase 57 のブランチ `claude/crosshair-selection-frame-f4b464` と合わせ main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: away（戻る予定 2026-10-15T07:30）
focus: **phase 58 完了（2026-10-15）。アクティブなフェーズなし・次フェーズはユーザー判断（`/phase_start`）。**
mode: idle

## last_action
ts: 2026-10-15T18:30:00
who: main
summary: |
  ユーザー判断 2 件（2026-10-15）: ①Codex 敵対的の指摘 → task_06a（省略表示の上部の見出しを Tab + Enter / Space で開閉・07058a0）②提案書 24 → task_07_refactor で実施。
  正本反映（task_06）・凍結・decisions_archive/58・decisions.md の索引・current.md の完了記載・handoff の既知の問題の解消まで済。
verified:
  task_06a: tests 1662 OK / tests_ui 1077 OK / smoke OK（verifier）・reviewer 採用
  task_07_refactor: compileall / tests 1662 OK / smoke OK / 対象 UI 5 モジュール OK・reviewer 修正して採用（範囲外の整形を戻した）。
  tests_ui 全体は `test_compact_window` の 3 件が FAIL（下記 blockers）= 環境要因（phase 開始時点 33dea2a でも同じ 3 件が落ちることを一時 worktree で確認）

## next_action
- **次フェーズはユーザー判断**（`/phase_start`）
- **`tests_ui.test_compact_window` の 3 件を、2 台目のモニタを外した状態（または画面構成を戻した状態）で再実行して pass を確認する**（下記 blockers）
- main へのマージはユーザー（phase 57 = `claude/crosshair-selection-frame-f4b464` / phase 58 = `claude/physical-device-visual-check-79fcd3`）

## blockers
- **【環境】`tests_ui.test_compact_window` の 3 件が 2026-10-15 夕方から FAIL**（`test_automatic_full_view_and_maximized_sizes_are_not_saved` / `test_compact_resize_is_saved_after_quiet_period_once` / `test_destroy_cancels_pending_size_save`）。
  phase 58 開始時点（33dea2a）でも同じく落ち、同日の昼の全体実行では pass。測定時は 2 台目のモニタが接続（仮想画面の高さ 1734・最大化の高さ 895）・CPU 66%。
  省略表示で +45px 広げた直後に WM が大きさを変え（315×865）`compact_window_size` の保存が走る。画面構成を戻して再実行し、pass ならコードの問題ではない
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: Codex の更新（0.162.x・cua_node runtime a9ba…・17:22〜18:25）以降、`~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が「別のプロセスが使用中」で失敗）。読み取り専用（レビュー・調査）は通る。再起動では直らない。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

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
  worktree ごとに 1 組ずつ増えるため、worktree を多く使うと codex.exe が溜まる。Codex デスクトップアプリ（ChatGPT.exe）配下の codex.exe は別物。2026-10-14 の不調はプロセスの溜まりではなく Codex の更新が原因（blockers 参照・再起動では直らない）
- **【罠・phase 58 task_02 で実測】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（vista・58 → 62px。矢印の字形とは無関係）。`style="TLabelframe.Label"` なら元と同じ 58px・同じ見た目
