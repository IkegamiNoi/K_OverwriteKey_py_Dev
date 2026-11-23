# session.md

> セッション再開時に最優先で参照する「現在状態」。
> 通常は SubagentStop / PreCompact の自動セーブと `/save_state` の手動セーブで更新される。
> 過去の会話履歴は参照せず、このファイルから状態を復元する。

last_updated: 2026-11-23T12:00:00
phase: instructions/phase/78_action_hotkey_save_validation（アクティブ・2026-11-23 起票・直接改訂モード・起票元 idea_03）。次採番 = phase 79 / 暫定 60 / decisions 79 / 提案書 29 / idea 67
直前の完了フェーズ = **phase 77**（サンプルを config/user/ へ書き出す・`decisions_archive/77_sample_in_user_folder.md`）
last_commit_location: `claude/sample-folder-save-path-d3cd34`（worktree `sample-folder-save-path-d3cd34`・b4d714b7 = phase 77 完了）。phase 78 の起票は worktree `idea-03-ec8eea`（branch `claude/idea-03-ec8eea`）で未コミット
※現在地・SHA はセッション開始時の git 実測値が正

## current
focus: **phase 78 起票済（2026-11-23）・task_01（正本 key_input.md §7.7・§7.9 の改訂）未着手。** アクションの hotkey を OK で validate_hotkey に通し、不正なら拒否・通れば正規化値を保存。
mode: implementing

## last_action
ts: 2026-11-23T12:00:00
who: main
summary: |
  実施: /phase_start で phase 78（action_hotkey_save_validation）を起票。phase.md 新規・current.md の参照先と次採番・backlog INDEX の idea_03 を「着手」へ。
  ユーザー判断（2026-11-23）: ①OK で validate_hotkey（構文＋各キー validate_key_name）を通し不正なら拒否・正規化値を保存 ②既存 sequences/*.json の生値は移行しない・読込時正規化なし ③直接改訂モード。
  reviewer（整合確認）: 修正して採用 → current.md L142 の古い次採番を 79 へ・phase.md の task_01〜03 に L232/L346 同時改訂・accepts_key_name を validate_hotkey より前に置く・codebase_map L912 の呼び出し元の追従を明記。
  日付の訂正: phase 77 の完了日の誤記 2026-11-23 → 2026-11-23（ユーザー指摘）を state・current.md・phase 77 の文書で修正。
result_files:
  - instructions/phase/78_action_hotkey_save_validation/phase.md
  - instructions/phase/current.md
  - instructions/backlog/INDEX.md
verified:
  compile: not_run（文書のみ）

## next_action
- ユーザーの回答待ち: task_01 へ進むか / 先にコミットするか。
- task_01: `/task_new` で `instructions/phase/78_action_hotkey_save_validation/tasks/task_01_spec_key_input.md` を起票 → `key_input.md` L232（§7.7「hotkey のアクションは保存時にキー名を検査しない」）と L346（§7.9 その例外の言い回し）の改訂案をユーザーへ提示して確定 → 正本を編集（メインで可・文書作業）→ reviewer。
- 別件: ブランチ `claude/sample-folder-save-path-d3cd34`・`claude/click-timing-issue-79de93` の push / merge はユーザー。保留中: R4・idea_37。

## blockers
- なし。注記: **Mac で tests_ui を通しで走らせない**（モーダルで止まるモジュールがある・モジュール指定で流す。verifier にも明記）。Mac の python は `../../../.venv/bin/python`
- **【解消・2026-11-22】Codex の書き込み実行（2026-10-14 以降の不具合）**: ユーザーが `~/.codex/config.toml` の `[windows] sandbox` を `elevated` に戻し、Codex 0.171.0 で書き込みのテスト OK（`setup refresh ... errors=[]`）。再発したら `unelevated` に変えて回避（ユーザー操作・常駐の broker〔`app-server-broker.mjs`〕と app-server を止めないと効かない）

## resume_hints
- **ユーザーへの提示は日本語で行う**（2026-09-16 指示）。
- **phase 78 の要点**: 現行の hotkey の OK は `action_dialog.py:253-265` で `accepts_key_name`（他方 OS の修飾キーだけ拒否）→ 生値を保存。揃える相手はプリセット `preset_manager.py:318,354` の `self.parent.validate_hotkey`（`App.validate_hotkey` → `HotkeyService.validate`）。
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
