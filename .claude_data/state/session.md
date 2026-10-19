# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-20T02:30:00
phase: `instructions/phase/63_make_only_keys`（phase 63・暫定 46 v0.4 ユーザー確定済 2026-10-20・decisions 63）。次採番 = phase 64 / 暫定 47 / decisions 64 / 提案書 25 / idea 54
直前の完了フェーズ = **phase 62**（`decisions_archive/62_special_keys_from_layout_only.md`）
last_commit_location: `claude/phase62-trace-file-empty-ddc0c0`（phase 63 の task_01〜03c + 暫定 46 v0.4・task_03d / 03e の起票）。phase 60・61 = `claude/idea-46-3c4cb6` / phase 57 = `claude/crosshair-selection-frame-f4b464` / phase 58・59 = `claude/physical-device-visual-check-79fcd3`。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 63（idea_52）: 計測で原因を特定し暫定 46 を v0.4（リピートなし + 直接置換の枠を灰色がかった緑）へ改訂・ユーザー確定。task_03d / task_03e を起票済み・実装待ち。**
mode: implementing
presence: present

## last_action
ts: 2026-10-20T02:30:00
who: main
summary: |
  計測（Operation_check の make_only_trace.txt）: 送信の最中に届いた物理の押下が keyboard の `is_replaying`（`keyboard/__init__.py:233`・`:377-389`）でフックを通らず OS へ素通り → 無変換（VK_IME_OFF）で IME 切替・リピートの押下が 1 回ずつ抜け・離しの 2 回組の 2 回目が抜けてリピートと取り違え。短い押下は全て正常。
  ユーザー判断（2026-10-20）: 送信の見直しは phase 63 に入れず idea_53 へ。v0.4 = リピートなし・押下だけのキーの直接置換の枠を灰色がかった緑（トリガーは青のまま・内蔵キーボードでも同色は受容）・片方の取りこぼし対策は案 A（「押した」から待ち時間 − 100 ms より前の単独の押下 = 片方の「離した」）。
  Codex 敵対的 needs-attention（high 1・medium 2）→ 全件反映（high は §9 #3 の案 A）。decisions.md に phase 63 の節を新設。
  文書のみ（コード変更なし）。
result_files:
  - instructions/history/46_make_only_keys.md
  - instructions/backlog/idea_53_send_without_dropping_physical_input.md
  - instructions/backlog/INDEX.md
  - instructions/phase/63_make_only_keys/phase.md
  - instructions/phase/63_make_only_keys/tasks/task_03d_no_repeat.md
  - instructions/phase/63_make_only_keys/tasks/task_03e_make_only_key_color.md
  - instructions/phase/current.md
  - .claude_data/state/decisions.md
verified:
  コード変更なし（前回: compile clean / tests 1743 pass / tests_ui 1117 pass / smoke OK）

## next_action
- `codex-implementer` に `instructions/phase/63_make_only_keys/tasks/task_03d_no_repeat.md` の実装を依頼（application 限定・`make_only_keys.py` と tests 2 本・テスト実行は依頼しない）→ 差分を直読み → verifier（compile・対象テスト・tests / tests_ui / smoke。tests_ui は 1 本だけ・taskkill 禁止）→ reviewer → `/task_commit`
- 続けて task_03e（`task_03e_make_only_key_color.md`・presentation 限定・`keyboard_window.py` と新規 `tests_ui/test_make_only_key_color_ui.py`）を同じ流れで
- 両方済んだらユーザーへ実機目視を依頼（暫定 46 §6 #6: 長押しでも 1 文字だけ・IME が切り替わらない・枠の色）。Operation_check の `phase62.json` の `debug_jis_special_key_events` は計測後 false へ戻すよう伝える（起動は Operation_check の `.venv\Scripts\python.exe`）
- 目視 OK → task_04（正本反映・凍結・decisions_archive/63・idea_52 を INDEX_done へ・`/refactor_check`・完了判定前レビュー）
- 別件: external_keyboard_layouts のパスが入れ子に増える件は idea_13 に追記済み（別セッション・ブランチ `claude/lucid-wiles-a6c8d3`・未マージ）
- main へのマージはユーザー

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
