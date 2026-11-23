# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-24T03:00:00
phase: instructions/phase/77_sample_in_user_folder（サンプルを config/user/ へ書き出す・2026-11-23 起票・主入力 = 暫定 59 v0.2 ユーザー確定済）。次採番 = phase 78 / 暫定 60 / decisions 78 / 提案書 29 / idea 67
直前の完了フェーズ = **phase 76**（カウンター機能の拡張・`decisions_archive/76_counter_expansion.md`）
last_commit_location: `claude/sample-folder-save-path-d3cd34`（worktree `sample-folder-save-path-d3cd34`・4819cdb7 = phase 77 task_01）。push / merge はユーザー
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 77 完了判定前レビュー: deep = 完了可（低 5）・codex-adversarial = needs-attention（medium 4・1/3/4 は実測で事実）。採否案（Codex1/3 採用 → task_03a〔構成セットも lexists・比較を json.dumps(sort_keys=True) の文字列で〕・Codex2/4 除外〔正本にリンク構成は扱わない・「辿れる全ファイル」を 3 種と明記〕・deep1/2/5 採用・3/4 除外）をユーザーへ提示し回答待ち。**
mode: pending_review

## last_action
ts: 2026-11-24T00:30:00
who: main
summary: |
  phase 77 task_01（`tasks/task_01_sample_write_to_user.md`）完了。`sample_install.py` の書き出し先を `user/`・構成セットが無いとき書き出す 13 子を照合（中身が同じなら衝突にしない・違えば何も書かず incomplete〔error = "Sample files already exist: <相対パス>"〕）。`save_plan_execution.preview_child_payloads`（書き込みなし）を追加。`app.py` の起動設定を `user/keymap_sets/sample.json`。`orphan_scan.py` 不変。application + presentation 1 行。
  codex-implementer（Luna high）実装 → verifier で Codex のテストの誤り 2 件（配置クラス違い・loaded keymaps に path キー無し）→ 再依頼で修正 → 再検証 pass → reviewer 採用（参考 = except のコメント・任意で不採用）。
result_files:
  - keyseq/application/config_service/sample_install.py
  - keyseq/application/config_service/save_plan_execution.py
  - keyseq/presentation/app.py
  - tests/test_sample_install.py
  - tests/test_orphan_scan.py
  - tests_ui/test_first_launch_flow.py
  - instructions/phase/77_sample_in_user_folder/tasks/task_01_sample_write_to_user.md
  - instructions/phase/77_sample_in_user_folder/phase.md
verified:
  compile: clean
  tests: pass 2275（失敗 0・skip 7）
  tests_ui: pass 9（test_first_launch_flow のみ）
  smoke: pass

## next_action
- ユーザーが採否案を承認したら: decisions_archive/77 に採否を追記 → task_03a 起票（sample_install.py:63 の exists → lexists・_find_conflicting_children の比較を sort_keys の json 文字列に・テスト 2 件）→ codex-implementer → verifier → reviewer → 正本の 2 行（リンク構成は扱わない・check の対象 3 種）・暫定 59 の 4 行目削除・decisions_archive に refactor_check の M1〜M6 実測値 → コミット → phase 77 完了。
- 別件: ブランチ `claude/click-timing-issue-79de93` の push / merge はユーザー。保留中: R4・idea_37。

## blockers
- なし。注記: **Mac で tests_ui を通しで走らせない**（モーダルで止まるモジュールがある・モジュール指定で流す。verifier にも明記）。Mac の python は `../../../.venv/bin/python`
- **【解消・2026-11-22】Codex の書き込み実行（2026-10-14 以降の不具合）**: ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `elevated` に戻し、Codex 0.171.0 で書き込みのテスト OK（`setup refresh ... errors=[]`）。再発したら `unelevated` に変えて回避（ユーザー操作・常駐の broker〔`app-server-broker.mjs`〕と app-server を止めないと効かない）

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
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
- 過去の判断は `decisions.md`「アーカイブ索引」→ `decisions_archive/<phase>.md`。凍結済の暫定仕様（`instructions/history/` の 04〜46・48〜57）の条項を実装の根拠に引かない（暫定 58 は phase 76 の主入力・未凍結）。
- **【Codex のプロセス】** companion は作業フォルダごとに `app-server-broker.mjs serve` を常駐させ、`codex app-server` は呼び出し後も残る。worktree を多く使うと codex.exe が溜まる。`codex-delegating-implementer` は 180 秒を超えるとバックグラウンドへ移る → 出力ファイルの更新時刻で進み具合を見る。
- **【罠・phase 58】ttk.LabelFrame の `labelwidget` に既定の ttk.Label を使うと枠の要求高さが 4px 増える**（`style="TLabelframe.Label"` なら同じ）
