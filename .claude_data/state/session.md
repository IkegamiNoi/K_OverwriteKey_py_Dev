# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-15T11:30:00
phase: **58_window_size_fit**（画面サイズの調整・2026-10-14 起票・主入力 = 暫定 42 v0.3 ユーザー確定済）。次採番 = phase 59 / 暫定 43 / decisions 59 / 提案書 24
直前の完了フェーズ = **phase 57**（`decisions_archive/57_grid_crosshair_nudge.md`）
last_commit_location: `claude/physical-device-visual-check-79fcd3`（phase 58 task_02 完了・実機目視 OK）。phase 57 のブランチ `claude/crosshair-selection-frame-f4b464` と合わせ main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: away（戻る予定 2026-10-15T07:30）
focus: **phase 58 task_04 完了（2026-10-15 ユーザー実機目視 OK）。task_05（統合確認）実施中 = deep-reviewer + codex-reviewer。**
mode: reviewing

## last_action
ts: 2026-10-15T11:00:00
who: main
summary: |
  task_03 コミット（750ee83）。task_04（pane_measure: H = 3 枠の「飾り + 中身の要求高さ」の最大・最小の高さ = 今の値 − panes の要求高さ + ceil(H/2)・
  3 枠の最小幅に各枠のスクロールバーの要求幅を常に加算）を codex-implementer で実装。既存テストの「最小で何も切れない」を「最下段までスクロールで届く」へ置換。
  verifier の失敗 2 件をメインが修正: ①省略表示の minsize（+3 で高さ 707）が残ったままフル表示の geometry を復元して 707 で止まる既存の潜在不具合
  （以前はフル表示の最小 931 が常に大きく隠れていた）→ `app.show_full_view` で復元前に `release_window_min_size()` ②新規テストの前提（最小で出力シーケンスにスクロールバーが出ない）の誤り。
  reviewer 指摘 1（一時メッセージのラベルが無いと新しい式を通らない）も修正。
  参考値: 最小の高さ フォント 0 = 541（旧 798）/ +3 = 635（旧 931・画面 966 に収まる）。
verified:
  compile: pass / tests: 1662 OK（skip 7）/ tests_ui: 1072 OK / smoke OK / config 不変（verifier）
  review: reviewer 採用（本体）+ 追加修正 3 点も採用。参考: テスト補強の残り（ホイールの配送が vacuous になり得る・テスト内の補助の重複）

## next_action
- **task_05**（統合確認）: 退行テストは task_04 の最終検証（da679a3 と同じコード・全 pass）を流用。`deep-reviewer` + `codex-reviewer`（`git diff 33dea2a..HEAD`）→ 指摘の裏取り → 採否をユーザーと決める
- その後: task_06（正本反映・凍結・decisions_archive・current.md・/refactor_check・完了判定前レビュー deep-reviewer + codex-adversarial-reviewer）
- main へのマージはユーザー（phase 57 = `claude/crosshair-selection-frame-f4b464` / phase 58 = `claude/physical-device-visual-check-79fcd3`）

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
