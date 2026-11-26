# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-26T13:00:00
phase: instructions/phase/82_scroll_direction_setting（スクロールのアクションの向きの反転・起票元 idea_58・暫定仕様先行モード・主入力 = 暫定 62 v0.4 ユーザー確定済）。次採番 = phase 83 / 暫定 63 / decisions 83 / 提案書 30 / idea 71
直前の完了フェーズ = **phase 81**（キー置換の置換先に英字の大文字・`decisions_archive/81_uppercase_replacement_target.md`）
last_commit_location: `claude/idea-62-048dd1`（worktree `idea-62-048dd1`・Windows・phase 81 完了）。push / merge はユーザー
※現在地・SHA はセッション開始時の git 実測値が正（今回の作業は worktree `idea-58-be6d8d`・Mac・未コミット）

## current
focus: **phase 82 task_01 完了（verifier pass・reviewer 採用）→ task_02 へ。ユーザーがタスクの連続実行を許可（2026-11-26・task_03 の実機目視で止まる）。**
mode: implementing

## last_action
ts: 2026-11-26T14:00:00
who: implementer
summary: |
  起票分をコミット（c6ee58a5）。task_01（domain + application）と task_02（presentation）のタスク定義を起票。
  task_01 を codex-implementer で実装: domain/mouse_scroll.py に ScrollInvert・NO_SCROLL_INVERT・coerce_scroll_invert・scroll_invert_to_json・apply_scroll_invert / ActionExecutor に get_scroll_invert（行ごとに try 内で読む）/ テスト 2 ファイルの末尾に追加。差分をメインで直読み済。verifier: compileall clean / 対象 25 pass / tests 2238 pass（skip 34）。reviewer 採用（指摘 2 = コンストラクタ経由の配線は task_02 の tests_ui で担保）。
result_files:
  - instructions/phase/82_scroll_direction_setting/tasks/task_01_domain_application_invert.md・task_02_presentation_menu_and_save.md（新規）
  - keyseq/domain/mouse_scroll.py・keyseq/application/action_executor.py・tests/test_mouse_scroll.py・tests/test_action_executor_mouse_scroll.py
verified:
  compile: clean（task_01）
  tests: pass 2238（skip 34・Mac・task_01）

## next_action
- task_02 を `codex-delegating-implementer` へ委任（本体 7 ファイル・テスト 3 ファイル・既存の期待値の変更 = test_menu_bar_deferral.py:32,33,46,47,50,51 → 量の目安に当たる。子の起動の有無を decisions へ 1 行）→ 直読み → verifier（tests_ui はモジュール指定）→ reviewer → コミット。
- task_03 = 統合確認（verifier）→ deep-reviewer + codex-reviewer → 実機目視はユーザー（Windows / macOS）で停止。

## blockers
- なし。注記: **Mac で tests_ui を通しで走らせない**（モーダルで止まるモジュールがある・モジュール指定で流す。verifier にも明記）。Mac の python は `../../../.venv/bin/python`
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
