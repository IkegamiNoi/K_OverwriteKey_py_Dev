# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-21T12:00:00
phase: なし（phase 64 は 2026-10-21 完了）。次採番 = phase 65 / 暫定 47 / decisions 65 / 提案書 25 / idea 55
直前の完了フェーズ = **phase 64**（`decisions_archive/64_external_layout_path_base.md`）
last_commit_location: `claude/external-key-layout-persistence-a9eaa2`（phase 64 task_01a・task_02・完了）。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 64 完了（2026-10-21・外部キーレイアウトのパス基準の統一・idea_13）。アクティブなフェーズなし・次フェーズはユーザー判断（`/phase_start`）。**
mode: idle
presence: present

## last_action
ts: 2026-10-21T12:00:00
who: main
summary: |
  task_01 実機目視 OK（ユーザー）。task_02: 正本 5_08_09_orphan_sweep.md（superset の理由・旧表記は移行しない）・codebase_map・decisions_archive/64・索引・current.md 完了・idea_13 を INDEX_done へ。/refactor_check 不要。
  完了判定前レビュー: Codex 敵対的 中 1（解決 2 回で相対 config_root のとき config/ が増える）→ task_01a で修正（codex-implementer・reviewer 完了可）/ deep-reviewer 完了可・中 1（単一 JSON の取り込みは正規化しない）= ユーザー判断で受容・低 2 を文書へ。
result_files:
  - keyseq/application/config_service/split_loading.py
  - tests/test_config_service.py
  - tests/test_layout_controller_registration.py
  - instructions/common/spec_detail/data_schema/5_08_09_orphan_sweep.md
  - instructions/common/codebase_map.md
  - .claude_data/state/decisions_archive/64_external_layout_path_base.md
verified:
  compile: clean
  tests: pass 1763（skipped 7）
  tests_ui: pass 1122
  smoke: pass

## next_action
- 次フェーズはユーザー判断（残件: idea_53 送信の最中の素通り / idea_54 IME の切り替え / idea_50・51・48・45 ほか）
- main へのマージはユーザー（本ブランチ `claude/external-key-layout-persistence-a9eaa2`）
- 利用者側: 既存の構成セット JSON の `external_keyboard_layouts` の旧表記（`config\user\…`・`config/config/…`・`keylayout\…`）は手で `user/keylayout/<file>.json` へ直す

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
