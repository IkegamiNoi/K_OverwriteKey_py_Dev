# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-24T09:00:00
phase: なし（phase 68 = instructions/phase/68_ui_terminology は 2026-10-24 完了）。次採番 = phase 69 / 暫定 52 / decisions 69 / 提案書 26 / idea 55
直前の完了フェーズ = **phase 68**（UI 文言の用語統一・`decisions_archive/68_ui_terminology.md`）
last_commit_location: `claude/help-text-review-c94d50`（暫定 51・phase 68 起票・task_01）。phase 67 は `claude/nice-banach-b5d556`。main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 68 完了（2026-10-24・UI 文言の用語統一）。アクティブなフェーズなし・次フェーズはユーザー判断（予定 = ヘルプ → 多言語対応 → Mac 対応）。**
mode: completed
presence: present

## last_action
ts: 2026-10-24T09:00:00
who: main
summary: |
  phase 68 task_08: 実機目視 OK（保存先を計算し直した後の確認は省略）→ 正本反映（新規 ui_terms.md・正本 19 ファイルの引用と地の文・見出しの改名）・暫定 51 凍結・decisions_archive/68・current.md 完了。
  完了判定前レビュー: Codex 敵対的 needs-attention 1（「…」の省略を簡易表示に誤置換 → 修正）/ deep-reviewer 修正して完了可（37 件 → tools/promotion_fixes.md で反映）。/refactor_check = 推奨 → 提案書 25 起票・多言語化で吸収（保留）。
result_files:
  - instructions/common/spec_detail/ui_terms.md（新規）・features.md・data_schema.md と子ファイル・key_input.md・architecture.md・codebase_map.md・app_overview.md
  - instructions/history/51_ui_terminology.md（凍結）・instructions/modified_proposal/25_refactor_child_kind_labels.md
  - .claude_data/state/decisions_archive/68_ui_terminology.md・decisions.md・instructions/phase/current.md
verified:
  compile: clean（最後のコード変更 a373d08 時点）
  tests: pass 1819（skipped 7）
  tests_ui: pass 1149
  smoke: pass

## next_action
- 次フェーズの選択はユーザー判断（`/phase_start`）。予定 = ヘルプの作成 → 多言語対応（提案書 25・内部名の表示名化を吸収）→ Mac 対応
- main へのマージはユーザー（PR は作らない）。phase 68 のブランチ = `claude/help-text-review-c94d50`

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
