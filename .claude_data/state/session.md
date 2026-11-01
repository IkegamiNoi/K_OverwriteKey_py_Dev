# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-01T11:45:00
phase: instructions/phase/72_multilingual_ui（**アクティブ** = 画面の文言の多言語対応・暫定 55 v0.3 ユーザー確定済・decisions 72）。次採番 = phase 73 / 暫定 56 / decisions 73 / 提案書 28 / idea 57
直前の完了フェーズ = **phase 71**（タスクバーのアイコン・`decisions_archive/71_taskbar_status_icon.md`）
last_commit_location: `claude/multilingual-support-ff44eb`（phase 72）。phase 71 一式は `claude/taskbar-app-status-indicator-f73d28` にもあり、main へのマージはユーザー（PR は作らない）
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 72 進行中（task_01 完了・次 task_02）。** 日英の切替（設定・次回起動から反映）の基盤 `keyseq/shared/i18n` とメニュー「言語 / Language」・ヘルプの読む順まで入った。既存の文言のキー化は task_03〜06。
mode: implementing
presence: away（戻る予定 未定）

## last_action
ts: 2026-11-01T11:45:00
who: main
summary: |
  phase 72 起票（暫定 55 v0.3 確定・phase.md 12 タスク・idea_56）→ task_01（i18n 基盤）を codex-delegating-implementer（Sol medium・サブエージェント 2 使用）で実装。
  新規 `keyseq/shared/i18n`（tr / tr_in 位置専用・en → ja → キーのフォールバック・available_languages・resolve_language〔既定 en〕・fix_language / reset_for_tests）・locales ja / en（4 キー）。
  presentation: App が画面を作る前に言語を決める（起動時警告は決定後）・`set_ui_language`（保存 + 選んだ言語で再起動の知らせ）・ui_language_var・メニューの言語 cascade・ヘルプの読む順。shared は他層を import しない（層の新設）。
  テスト: 104 ファイルへ `fix_language("ja")`・静的テスト（`test_*.py` に限定）・メインで tests_ui/test_ui_language.py:79 の str() 化・smoke への固定を取り消し・app.py の import の並び。
  reviewer 採用（修正不要・参考 2 件 = 過剰な固定は無害 / import の並び → 反映）。
result_files:
  - keyseq/shared/__init__.py / keyseq/shared/i18n/{__init__.py,catalog.py,locales/ja.json,locales/en.json}
  - keyseq/presentation/app.py / ui_vars.py / views/menu_bar.py / help/help_content.py
  - tests/test_i18n.py / test_i18n_startup_preservation.py / test_i18n_test_language_fixed.py / test_help_content.py / tests_ui/test_ui_language.py + 既存 104 ファイル（言語固定）
  - instructions/history/55_multilingual_ui.md / instructions/phase/72_multilingual_ui/ / instructions/phase/current.md / instructions/backlog/{INDEX.md,idea_56_more_ui_languages.md}
  - .claude_data/state/decisions.md
verified:
  compile: pass
  tests: pass（1888・skip 7）
  tests_ui: fail 1 → 修正後に該当ファイル 6 件 pass（全体の再実行は task_02 の実測で兼ねる）
  smoke: pass

## next_action
- task_02（表示文字列の内部値の分離）を `/task_new` で `instructions/phase/72_multilingual_ui/tasks/task_02_internal_values.md` に起票 → codex-implementer で実装 → verifier（tests / tests_ui 全体〔task_01 の修正後の全体確認を兼ねる〕/ smoke）→ reviewer。対象は暫定 55 §1・§6.3 の比較箇所（`dialogs/action_key_hold_fields.py`・`action_dialog.py:262`・`controllers/keymap_panel/keymap_add_flow.py`）＋ 仕分けで見つかる箇所
- 以降 phase.md のタスク順に task_03〜12。task_07（英語の用語・アクションの種類の表示名）と task_12（実機目視）はユーザー判断が要る
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
