# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-10-15T15:30:00
phase: **58_window_size_fit**（画面サイズの調整・2026-10-14 起票・主入力 = 暫定 42 v0.3 ユーザー確定済）。次採番 = phase 59 / 暫定 43 / decisions 59 / 提案書 24
直前の完了フェーズ = **phase 57**（`decisions_archive/57_grid_crosshair_nudge.md`）
last_commit_location: `claude/physical-device-visual-check-79fcd3`（phase 58 task_02 完了・実機目視 OK）。phase 57 のブランチ `claude/crosshair-selection-frame-f4b464` と合わせ main へのマージはユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
presence: away（戻る予定 2026-10-15T07:30）
focus: **phase 58 task_06（正本反映）実施中: 正本・codebase_map・凍結・decisions_archive・提案書 24 まで済。ユーザー判断待ち 2 件（Codex 敵対的の指摘 = 表示を閉じるとキーボードでフル表示へ戻れない / 提案書 24 の承認と時期）。**
mode: pending_user_decision

## last_action
ts: 2026-10-15T15:30:00
who: main
summary: |
  task_05a コミット（787f83a）。task_06: features.md §4.5・§4.6（新節「フル表示の 3 枠のスクロール」「省略表示の上部の開閉」）・data_schema §5.4（compact_header_view）・codebase_map を更新、
  暫定 42 を凍結、decisions.md の phase 58 節を decisions_archive/58 へ移した（索引行は未追加）。/refactor_check = 推奨（M3・M4）→ 提案書 24（compact_header_controller の見出しの文言・区画の列挙と余白・pane_measure の 3 枠のタプル）。
  完了判定前レビュー: deep-reviewer 修正して採用（文書の修正は反映済・残りは索引 / current.md / handoff の完了記載）/
  codex-adversarial needs-attention 1 件（裏取り済: 省略表示の「表示」を閉じるとフル表示へ戻る手段が「フルに戻す」ボタンだけで、閉じた見出しは ttk.Label でキーボードで開けない。
  暫定 42 §4 の「キーボード操作の表示切替は効く」は前提の誤り = 表示切替のショートカットは無い）。

## next_action
- **【ユーザー判断待ち】** ①Codex の指摘（キーボードだけで戻れない）の扱い ②提案書 24 の承認と実施時期
- 判断後: （①でコード修正なら task_06a）→（②承認なら task_07_refactor）→ decisions.md の索引に 58 の行 → current.md の完了記載（次採番 phase 59 / 暫定 43 / decisions 59 / 提案書 25）→ handoff の既知の問題「フル表示の高さ（phase 50）」を解消済みに
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
