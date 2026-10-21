# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-21T19:00:00
phase: instructions/phase/66_capture_jis_special_keys（進行中・暫定仕様先行・暫定 49 v0.3 確定 / decisions 66）。次採番 = phase 67 / 暫定 50 / decisions 67 / 提案書 25 / idea 55
直前の完了フェーズ = **phase 65**（`decisions_archive/65_layout_snapshot_for_hook.md`）
last_commit_location: `claude/muhenkan-key-hold-error-dialog-a77a67`。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 66 起票済（キーの取得で JIS の特殊キーを取る・idea_50・暫定 49 v0.3 確定）。次は task_01（4 キーのフックでの届き方の実測・ユーザーの実機の打鍵が要る）。**
mode: implementing
presence: present

## last_action
ts: 2026-10-21T19:00:00
who: main
summary: |
  phase 66 起票: 暫定 49 v0.1 → deep-reviewer 修正して採用 → v0.2 → Codex 敵対的 needs-attention 2 件 → v0.3 → ユーザー確定（§6 の 3 点を推奨どおり）。
  phase.md（タスク 4）・current.md・INDEX（idea_50 着手）・decisions.md の phase 66 節。/phase_start の整合確認 reviewer 修正して採用（軽微 2 件を反映）。
result_files:
  - instructions/history/49_capture_jis_special_keys.md
  - instructions/phase/66_capture_jis_special_keys/phase.md
  - instructions/phase/current.md
  - instructions/backlog/INDEX.md
  - .claude_data/state/decisions.md
verified:
  compile: clean（phase 65 task_03a 時点・本ターンは文書のみ）
  tests: pass 1779（skipped 7）
  tests_ui: pass 1122
  smoke: pass

## next_action
- task_01 を `/task_new` で起票し、実測用の小スクリプト（`.venv`・keyboard の suppress フック・時間で自動終了）を用意して、ユーザーに実機で 4 キー（半角/全角・無変換・変換・かな）と押下だけのキーボードを押してもらう（暫定 49 §7a）→ 届き方と IME の切替を記録し、§3-4・§3-5 の一定時間と上限を暫定 49 へ書く（ユーザー確認）
- その後 task_02（取得用のフック）を `codex-delegating-implementer` か `codex-implementer` へ

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
