# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-15T00:50:00
phase: **58_window_size_fit**（画面サイズの調整・2026-10-14 起票・主入力 = 暫定 42 v0.3 ユーザー確定済）。次採番 = phase 59 / 暫定 43 / decisions 59 / 提案書 24
直前の完了フェーズ = **phase 57**（`decisions_archive/57_grid_crosshair_nudge.md`）
last_commit_location: `claude/codex-process-management-9b8bfd`（phase 58 task_02 = 実機目視待ち）。phase 57 のブランチ `claude/crosshair-selection-frame-f4b464` と合わせ main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: away（戻る予定 2026-10-15T07:30）
focus: **phase 58 task_02 実装・検証済（コミット済）・ユーザーの実機目視待ち。task_03 は未着手（task_02 の目視 OK 後に着手）。**
mode: pending_user_check

## last_action
ts: 2026-10-15T00:50:00
who: main
summary: |
  task_01 コミット（d8135d7）。task_02（省略表示の「フック」「表示」の Expander・compact_header_view の保存・refresh_minimum_height）を codex-implementer で実装 →
  reviewer 修正して採用（focus_get の KeyError 吸収・重複の整理・テスト追加）+ verifier の失敗 2 件（labelwidget の TLabel で枠が 4px 高くなり区切りのテストが失敗〔probe で実測〕/ 全件実行でフォーカスが取れない）を修正。
  見出しは style="TLabelframe.Label"（元と同じ 58px）。
verified:
  compile: pass / tests: 1662 OK（skip 7）/ tests_ui: 1061 OK / smoke OK / 生成物なし（verifier）
  review: reviewer 修正して採用 → 指摘 1〜3 を反映済（4・3(d) は参考のため見送り）

## next_action
- **【ユーザー確認待ち】task_02 の実機目視**（`main.py` を .venv で起動 → 省略表示へ）:
  1. 「フック」「表示」の見出しをクリック → 閉じると `▸ フック` / `▸ 表示` の 1 行・トリガー一覧の欄が伸びる・ウィンドウの大きさが変わらない
  2. 開いたときの見出し（`▾ フック`）の見た目が従来の枠の見出しと同じ（高さ・色）
  3. 閉じた状態で再起動 → 閉じたまま起動する
  4. （task_01）キーマップを一時停止 → 幅 270 の省略表示のステータス欄に `フック: 一時停止` が見える
  → OK なら task_02 を完了（/task_commit は不要・実装は 2026-10-15 のコミットに含む。session と current の記録のみ）→ task_03（定義を起票して codex-implementer）
- その後: task_03 → task_04（実機目視あり）→ task_05（統合）→ task_06（正本反映）
- main へのマージはユーザー（phase 57 = `claude/crosshair-selection-frame-f4b464` / phase 58 = `claude/codex-process-management-9b8bfd`）

## blockers
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
