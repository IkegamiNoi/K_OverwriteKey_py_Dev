# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-01T01:30:00
phase: **アクティブなフェーズ = なし**（phase 71 = タスクバーのアイコンで状態を表示は 2026-11-01 完了・暫定 54 v0.4 凍結・`decisions_archive/71_taskbar_status_icon.md`）。次採番 = phase 72 / 暫定 55 / decisions 72 / 提案書 28 / idea 56
直前の完了フェーズ = **phase 71**（タスクバーのアイコン）。予定 = 多言語対応 → Mac 対応（次フェーズはユーザー判断で `/phase_start`）
last_commit_location: `claude/taskbar-app-status-indicator-f73d28`（phase 71 一式）。main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 71 完了（2026-11-01）。** 窓のアイコンの右上にステータス欄と同じ 3 状態の印（白い正方形の上の緑の円 / 赤の正方形 / 黄の棒 2 本）・土台はサンプル画像（ユーザーが差し替え）・子窓は既定のアイコンで追従・起動時に AppUserModelID。実機目視すべて OK・refactor_check = 不要。
mode: completed
presence: present

## last_action
ts: 2026-11-01T01:30:00
who: main
summary: |
  task_05 = 実機目視 OK → 正本反映（features §4.5「タスクバーのアイコン」・同梱物の段落・architecture・codebase_map）・暫定 54 凍結・decisions_archive/71・current.md・idea_55 を INDEX_done へ・refactor_check 不要（M4・M6 の境界事例を別タスク化候補へ）。
  完了判定前レビュー: Codex 敵対的 approve / deep-reviewer 修正して完了可 → 1・2・3 を文書で反映・4 保留・5 除外。コード変更なし（文書のみ）。
result_files:
  - instructions/common/spec_detail/features.md
  - instructions/common/spec_detail/architecture.md
  - instructions/common/codebase_map.md
  - instructions/history/54_taskbar_status_icon.md
  - instructions/phase/current.md
  - instructions/phase/71_taskbar_status_icon/tasks/task_05_canon_and_close.md
  - instructions/backlog/INDEX.md / INDEX_done.md
  - .claude_data/state/decisions_archive/71_taskbar_status_icon.md / decisions.md
verified:
  compile: pass
  tests: pass（1867・skip 7）
  tests_ui: pass（1210）
  smoke: pass

## next_action
- 次フェーズはユーザー判断（予定 = 多言語対応 → Mac 対応）。`/phase_start`
- main へのマージはユーザー（PR は作らない）
- 土台の画像の差し替え（任意・ユーザー）: `keyseq/presentation/status_icon/images/app_icon_16.png` / `app_icon_32.png` を同じ名前の正方形 PNG で置き換え → 起動して見え方を確認

## blockers
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: Codex の更新（0.162.x・cua_node runtime a9ba…・17:22〜18:25）以降、`~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が「別のプロセスが使用中」で失敗）。読み取り専用（レビュー・調査）は通る。再起動では直らない。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **phase 71**: タスクバーのアイコンは AppUserModelID（`main.py`）が無いと出ない。`App()` を直接作る tests_ui / smoke では設定されない。保留 2 件は current.md「別タスク化候補」。
- **`__version__`** はユーザーが直接またはユーザーの指示でだけ変更する（Claude が独断で上げない）。
- **Codex は Python で既存ファイルを編集しようとして失敗することがある** → 依頼文に「apply_patch で編集・Python を使わない」と書く（phase 71）。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- カーソルグリッド（旧称「画面の枠」・phase 56・57）の地図 = `codebase_map.md`「カーソルグリッド（phase 56・57）」。振り分けは `suppress_keys` 1 本（`screen_grid_session._publish_snapshot`）/ 操作キーは `domain/screen_grid/ops.py`。
- **【罠・phase 57 で実証】Windows の Tk で位置の反映の保留中に `wm_attributes("-topmost", True)` を呼ぶと窓が `0,0` へ戻る**（`geometry` の直後に `update_idletasks()`）。**Tk の測り直しは after_idle だと配置の計算より先に走ることがある**（測る前に `update_idletasks()`）・`<Configure>` で configure し返すと無限ループになり得る（値が変わったときだけ・結び付けは 1 つ）。
- **プロセスは pyautogui の import でシステム DPI 対応**（`.venv/Lib/site-packages/pyautogui/_pyautogui_win.py:17`）。検証は本番の起動経路で
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜41）の条項を実装の根拠に引かない。
- **【Codex のプロセス・2026-10-14 実測】** companion は作業フォルダ（cwd）ごとに `app-server-broker.mjs serve` を常駐させ、その下の `codex app-server`（+ sandbox の runner・node）は**呼び出し後も残る（再利用のための設計）**。
  worktree ごとに 1 組ずつ増えるため、worktree を多く使うと codex.exe が溜まる。Codex デスクトップアプリ（ChatGPT.exe）配下の codex.exe は別物。2026-10-14 の不調はプロセスの溜まりではなく Codex の更新が原因（blockers 参照・再起動では直らない）
- **【罠・phase 58 task_02 で実測】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（vista・58 → 62px。矢印の字形とは無関係）。`style="TLabelframe.Label"` なら元と同じ 58px・同じ見た目
