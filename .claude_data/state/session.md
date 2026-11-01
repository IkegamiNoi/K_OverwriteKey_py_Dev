# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-01T17:20:00
phase: instructions/phase/72_multilingual_ui（**アクティブ** = 画面の文言の多言語対応・暫定 55 v0.3 ユーザー確定済・decisions 72）。次採番 = phase 73 / 暫定 56 / decisions 73 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 71**（タスクバーのアイコン・`decisions_archive/71_taskbar_status_icon.md`）
last_commit_location: `claude/multilingual-support-ff44eb`（phase 72）。phase 71 一式は `claude/taskbar-app-status-indicator-f73d28` にもあり、main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 72 進行中（task_05 完了・次 task_06）。** presentation の画面の文言はすべてキー化済み（ja.json 約 704 キー・互換定数は解消）。残りは内側の層の文言（task_06）→ 英語の用語の確定（task_07・ユーザー確認）→ 英訳。
mode: implementing
presence: away（戻る予定 未定）

## last_action
ts: 2026-11-01T17:20:00
who: main
summary: |
  task_05（キー移行 3 = 残りの dialogs・help・互換定数の仕上げ）を codex-delegating-implementer（サブエージェント 3）で実装。ja.json に 100 キー・hook_button_texts の CAPTURE_* / UNKNOWN_CAPTURE_KEY_HINT_TEXT を関数へ・keymap_set_history_text の定数をキーへ（全呼び出し元・テスト追従）・help_content の検証エラー文 14 か所をキー化（日本語の完全一致テスト追加）・ヘルプ本文とライセンス本文はキー化せず。Codex が作った報告ファイル task_05_report.md は削除（内容確認済み）。
  reviewer 採用（AST の多重集合で完全一致照合・既存キーの使い回しの誤用なし・import 時の tr 0）。参考: preset_manager.py:6 の import の並び（未対応・軽微）。
result_files:
  - keyseq/presentation/dialogs/ の残り・keyseq/presentation/help/ 一式・hook_button_texts.py・keymap_set_history_text.py・config_io/keymap_set_history_io.py（計 36 ファイル）
  - keyseq/shared/i18n/locales/ja.json / tests_ui/test_preset_manager_i18n.py（新規）ほかテストの追従
  - instructions/phase/72_multilingual_ui/tasks/task_05_keys_dialogs_help.md / instructions/phase/current.md
verified:
  compile: pass
  tests: pass（1890・skip 7）
  tests_ui: pass（1227）
  smoke: pass

## next_action
- task_06（キー移行 4 = application / domain / infrastructure の画面に出る文〔約 286 リテラル・ログ専用と仕分け〕・既定の文言 `application/config_service/split_loading.py:381`）を `instructions/phase/72_multilingual_ui/tasks/task_06_keys_inner_layers.md` に起票（task_05 の定義を手本に・内側の層は `keyseq.shared.i18n` を import してよい〔暫定 55 §3.1〕・例外 / 戻り値の文として画面に出るものは作る時点で tr・ログ専用は残す）→ codex-delegating-implementer → verifier + reviewer（並行可・完全一致の照合）
- その次の task_07（英語の用語・表記の規則・アクションの種類の表示名を暫定 55 へ追記）は**ユーザー確認が要る**ので、起票して案を作ったら止まる（不在なら /away の終了処理）
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
