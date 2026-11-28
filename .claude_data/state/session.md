# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-28T18:00:00
phase: なし（phase 83 = ダイアログを開いている間にヘルプを操作できるようにする は 2026-11-28 完了・`decisions_archive/83_help_input_during_modal.md`）。次採番 = phase 84 / 暫定 64 / decisions 84 / 提案書 30 / idea 72
直前の完了フェーズ = **phase 83**（ダイアログを開いている間にヘルプを操作できるようにする・`decisions_archive/83_help_input_during_modal.md`）
last_commit_location: `claude/idea-60-be6a81`（worktree `idea-60-be6a81`・Mac・8fcee257 = task_05 まで）。push / merge はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 83 完了（2026-11-28・正本反映・暫定 63 凍結・refactor_check 不要）。アクティブなフェーズなし。次フェーズはユーザー判断で `/phase_start`。**
mode: completed

## last_action
ts: 2026-11-27T09:50:00
who: main
summary: |
  実施: task_03 完了（Windows も OK・reviewer 修正して採用）→ task_04 完了（modal.py の口・最後の入力先・grab の代わりの持ち主の解決・verifier pass・reviewer 採用・7a8ec77d）→ task_05 を起票し codex-delegating-implementer で実装。
  task_05 のメインの修正: 親が生きている破棄は作り直さない（_orphan_parent）/ App.state は AppState で上書き → wm_state / 新テストに fix_language / スクロールは先頭の位置（@0,0）も控え置き終えてから restore_scroll / 新しく開くときは初期フォーカスを入れる（reviewer 指摘 1）/ 作り直し後に持ち主を確かめ直す（reviewer 指摘 2・失敗時はし直さない形に修正済み）。
  verifier: 修正前の 4 回目までで tests 2247・関連 13 モジュール pass（test_minimize_grab_custody の 2 件はロック中は task_04 前のコミットでも落ちる）。最後の修正後の検証は画面のロックで GUI テストが止まり無効。
  ユーザー判断: タスクの連続実行を許可（2026-11-27）・/away（戻る予定 未定）。
result_files:
  - keyseq/presentation/help/help_window_controller.py・help_window.py・help_tab_view.py・keyseq/presentation/modal.py・keyseq/presentation/app.py（task_05・未コミット）
  - tests_ui/test_help_follow.py（新規）・test_help_window.py・test_dialog_help_buttons.py・test_minimize_grab_custody.py・test_modal_app_foreground.py（task_05・未コミット）
  - instructions/phase/83_help_input_during_modal/tasks/task_05_help_follow.md
verified:
  compile: clean（最後の修正の前）
  tests: pass 2247（同上）
  tests_ui: 最後の修正後は未検証（画面のロックで止まる）

## next_action
- 次フェーズはユーザー判断で `/phase_start`（候補は `instructions/backlog/INDEX.md`）。
- ブランチ `claude/idea-60-be6a81`（phase 83・最終 = task_07 のコミット）ほか（`claude/idea-58-be6d8d`〔phase 82〕・`claude/idea-62-048dd1`〔phase 81〕等）の push / merge はユーザー。
- 台帳の置き場: 別タスク化候補 = `instructions/backlog/deferred_tasks.md` / 提案書 = `instructions/modified_proposal/INDEX.md` / 暫定仕様 = `instructions/history/README.md`。

## blockers
- なし。注記: Mac で落ちうる probe・GUI テストを流すときは、画面のロック中は Tk が止まる・Python が落ちると次の起動で「ウインドウを再度開きますか？」で止まる（decisions_archive/83 の残存リスク）。 **Mac で tests_ui を通しで走らせない**（モーダルで止まるモジュールがある・モジュール指定で流す。verifier にも明記）。Mac の python は `../../../.venv/bin/python`
- **【解消・2026-11-22】Codex の書き込み実行（2026-10-14 以降の不具合）**: ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `elevated` に戻し、Codex 0.171.0 で書き込みのテスト OK（`setup refresh ... errors=[]`）。再発したら `unelevated` に変えて回避（ユーザー操作・常駐の broker〔`app-server-broker.mjs`〕と app-server を止めないと効かない）

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **phase 78 の要点**: hotkey のアクションの OK は `action_dialog.py` の `on_ok` で `accepts_key_name`（他方 OS の修飾キー・phase 75 の文言）→ `self.parent.validate_hotkey`（`App.validate_hotkey` → `HotkeyService.validate`）→ 正規化値を保存。tests_ui の fake root で ActionDialog の hotkey の OK を呼ぶなら `root.validate_hotkey` を設定する（`test_action_dialog_key_hold.py` / `labels.py` の setUp）。
- **phase 77 の要点**: 初回のサンプルは `config/user/`（`sample_install.SAMPLE_DIR = "user"`）。構成セットが無いときは `_find_conflicting_children` が `save_plan_execution.preview_child_payloads` と既存の子を照合（lexists・sort_keys の json 文字列比較）。旧 `config/sample/` は書かない・孤児の掃除の経路 5 で参照だけ残す。symlink のテストは Windows の特権不足で skip（Mac で一度流すと確証）。
- **phase 76 の要点**: 実効値（値が入った名前は値・それ以外は開始値・それも無ければ 0）は `keyseq/application/counter_values.py`（`CounterValues(dict)`・`counter_value`・`counter_start`・`counter_display_values`・`counter_starts_of`）に 1 か所。保留は `(op, name, amount)`。開始値は構成セットの `counter_starts`（`domain/sequence_control.normalize_counter_starts`）→ `App._sync_control_vars_from_data` で `AppState.set_counter_starts`。ダイアログは開始値を `_dialog_counter_start` で返し、`action_edit._apply_counter_start_result` が行の追加・置換の成立後に書く。新しい種類 `counter_text` は `ActionExecutor.execute` の 1 分岐。
- **Codex の傾向（phase 76 で実測）**: テストを書き漏らす（task_01・04 は 2 回目の依頼で追加）・既存テストの途中に新しいテストを差し込む（task_01）・タスク定義の一部（通知のラベル）を落とす（task_03）。依頼文に「既存テストの途中に差し込まない」を書き、差分を直読みしてから verifier へ。
- **tests_ui は同時に 1 本だけ**走らせる。verifier には **`taskkill` で python.exe を一括終了しないこと**を必ず書く。
- **画面の文言（phase 72 以降）**: 新しい文言は `keyseq/shared/i18n/locales/ja.json` と `en.json` の両方にキーを足し、ソースに日本語を書かない（静的テスト）。`tr` はモジュール定数・import 時に評価しない。`App(` を作る / 文言を assert する新しいテストモジュールは import 直後に `fix_language("ja")`。英語は `ui_terms.md` §2・§3（E1〜E7）に従う。
- tests_ui の窓の大きさのテスト（`test_compact_window.py:298`・`test_pane_window_width_persistence.py:236,275` の `pending`）が負荷で落ちることがある。**tests_ui の App() は worktree の `config/config.json`（ユーザーの手元の設定・gitignore）を読む**ので結果が手元の設定に左右される。Codex は python を実行できずテスト修正が手探りになる → 失敗はメインがトレースを読んで原因を絞ってから委任する。
- **`__version__`** はユーザーが直接またはユーザーの指示でだけ変更する（Claude が独断で上げない）。
- **Codex は Python で既存ファイルを編集しようとして失敗することがある** → 依頼文に「apply_patch で編集・Python を使わない」と書く（phase 71）。
- **素の `python` を Bash で呼ばない**（必ず `..\..\..\.venv\Scripts\python.exe`）。Bash の heredoc の前に `cat > file` を単独で書かない（stdin 待ちでハングする）。
- **Codex は互換の工夫・テストの期待値の推測を足すことがある**。差分を直読みしてから verifier / reviewer へ。Codex は LF を混ぜることがある（コミットは git が正規化）。
- `tests_ui/test_action_dialog_control.py` の 2 件は Tk ルートを作るモジュールの後に同じプロセスで走らせると落ちる（既存の実行順依存・current.md「テスト負債」）。
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜46・48〜59）の条項を実装の根拠に引かない（正本 `spec_detail/` が正）。
- **【Codex のプロセス】** companion は作業フォルダごとに `app-server-broker.mjs serve` を常駐させ、`codex app-server` は呼び出し後も残る。worktree を多く使うと codex.exe が溜まる。`codex-delegating-implementer` は 180 秒を超えるとバックグラウンドへ移る → 出力ファイルの更新時刻で進み具合を見る。
- **【罠・phase 58】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（`style="TLabelframe.Label"` なら同じ）
