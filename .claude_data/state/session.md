# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-01T16:30:00
phase: instructions/phase/72_multilingual_ui（**アクティブ** = 画面の文言の多言語対応・暫定 55 v0.3 ユーザー確定済・decisions 72）。次採番 = phase 73 / 暫定 56 / decisions 73 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 71**（タスクバーのアイコン・`decisions_archive/71_taskbar_status_icon.md`）
last_commit_location: `claude/multilingual-support-ff44eb`（phase 72）。phase 71 一式は `claude/taskbar-app-status-indicator-f73d28` にもあり、main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 72 進行中（task_04 完了・次 task_05）。** i18n 基盤・内部値の分離・キー移行 1 / 1b / 2（presentation のうち残りの dialogs・help 以外すべて・ja.json 約 604 キー）まで済み。
mode: implementing
presence: away（戻る予定 未定）

## last_action
ts: 2026-11-01T16:30:00
who: main
summary: |
  task_04（キー移行 2 = アクションの編集の dialogs 4 ファイル）: codex-implementer は着手せず返ったため codex-delegating-implementer（Sol medium・サブエージェント 2）で再依頼 → ja.json に 94 キー・task_02 のラベル関数を tr へ・呼び出し時に tr するテストを追加。
  reviewer 修正して採用 → 必須 1 件（プリセット編集の窓のタイトルに「…」が付く = `menu.settings.preset_edit` の誤用）をメインで `app.preset.title` へ修正。それ以外は機械照合で不一致 0・差し込み名の食い違い 0・import 時の tr 0。
  **task_05 へ引き継ぎ（再掲）**: keymap_set_history_text の dialogs も使う定数（READ_ONLY_NOTICE ほか）は `config_io/keymap_set_history_io.py:78`・`tests_ui/test_keymap_set_history_flow.py:296` と一緒に tr へ / hook_button_texts の CAPTURE_* / UNKNOWN_CAPTURE_KEY_HINT_TEXT（`action_key_hold_fields.py:8,242` も使う）は定数ごとキー化。
result_files:
  - keyseq/presentation/dialogs/{action_control_fields,action_dialog,action_key_hold_fields,action_mouse_scroll_fields}.py
  - keyseq/shared/i18n/locales/ja.json / tests_ui/test_internal_value_codes.py
  - instructions/phase/72_multilingual_ui/tasks/task_04_keys_action_dialogs.md / instructions/phase/current.md
verified:
  compile: pass
  tests: pass（1888・skip 7）
  tests_ui: pass（1225〔タイトル修正の前〕・修正後に test_action_dialog_control pass）
  smoke: pass

## next_action
- task_05（キー移行 3 = 残りの dialogs〔preset_manager 45・keymap_edit 11・trigger 8・preset 8・keymap_switch_batch 8・grid_editor_window 7・orphan_sweep 6・quarantine_manage 5・layout_delete 5・reference_cleanup 3・keymap_set_history_dialog ほか〕・help/〔help_content の検証エラー文 20・license_window 6・version_dialog 5・help_window 5・third_party 4・help_tab_view 3・help_button 1〕・互換定数の仕上げ〔上記〕）を `instructions/phase/72_multilingual_ui/tasks/task_05_keys_dialogs_help.md` に起票（task_04 の定義を手本に）→ codex-delegating-implementer → verifier + reviewer（並行可・機械照合は完全一致で）
- 以降 phase.md の順に task_06〜12。task_07（英語の用語・アクションの種類の表示名）と task_12（実機目視）はユーザー判断が要る
- main へのマージはユーザー（PR は作らない）

## blockers
- **【回避中】Codex の書き込み実行（2026-10-14 18:24 以降の不具合）**: Codex の更新（0.162.x・cua_node runtime a9ba…・17:22〜18:25）以降、`~/.codex/.sandbox/sandbox.2026-10-14.log` に `setup refresh had errors`（node_repl.exe の ACL 更新が「別のプロセスが使用中」で失敗）。読み取り専用（レビュー・調査）は通る。再起動では直らない。**2026-10-15 ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `unelevated` に変更 → 常駐の broker・app-server を止めて再実行で書き込み可**。Codex の更新で直ったら `elevated` に戻す（ユーザー操作）。設定を変えたら常駐の broker（`app-server-broker.mjs`）と app-server を止めないと効かない

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **phase 72**: `App(` を作る / 画面の文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")` を書く（無いと `ui_language` 未設定の環境で英語になり落ちる・静的テストが検出）。`tr` はモジュール定数・import 時に評価しない。
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
